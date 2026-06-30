import json
import logging
import os
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from database import DATABASE_URL, PantryItem, Recipe, init_db, get_db, wait_for_db

try:
    import ollama
except ImportError:
    ollama = None

logger = logging.getLogger("rag_api")
logging.basicConfig(level=logging.INFO)


def get_env_list(name: str, default: list[str]) -> list[str]:
    """Parse a comma-separated env var into a list, with a default fallback."""
    raw_value = os.getenv(name, "")
    if not raw_value.strip():
        return default
    return [item.strip() for item in raw_value.split(",") if item.strip()]


MODEL_NAME = os.getenv("MODEL_NAME", "tinyllama")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "").strip()
ADD_API_KEY = os.getenv("ADD_API_KEY", "").strip()
DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
CORS_ORIGINS = get_env_list("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
DATABASE_BACKEND = "postgres" if DATABASE_URL.startswith("postgres") else "sqlite"

app = FastAPI(title="RAG API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    """Input payload for /query requests."""
    q: str = Field(min_length=1)
    n_results: int = Field(default=3, ge=1, le=10)


class AddKnowledgeRequest(BaseModel):
    """Input payload for /add requests."""
    text: str = Field(min_length=1)


class RecipeIn(BaseModel):
    title: str = Field(min_length=1)
    ingredients: list[str] = Field(default_factory=list)
    instructions: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


class PantryItemIn(BaseModel):
    name: str = Field(min_length=1)
    quantity: float | None = None
    unit: str | None = None


def verify_add_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    """Enforce optional API-key protection for the /add endpoint."""
    if ADD_API_KEY and x_api_key != ADD_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


def generate_completion(prompt: str):
    """Generate an LLM response using Ollama, optionally via a custom host."""
    if ollama is None:
        raise RuntimeError("ollama is not installed. Install dependencies first.")
    if OLLAMA_HOST:
        client = ollama.Client(host=OLLAMA_HOST)
        return client.generate(model=MODEL_NAME, prompt=prompt)
    return ollama.generate(model=MODEL_NAME, prompt=prompt)


def serialize_recipe(recipe: Recipe) -> dict:
    return {
        "id": recipe.id,
        "title": recipe.title,
        "ingredients": json.loads(recipe.ingredients),
        "instructions": recipe.instructions,
        "tags": json.loads(recipe.tags),
    }


def serialize_pantry_item(item: PantryItem) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "quantity": item.quantity,
        "unit": item.unit,
    }


def search_context(query: str, n_results: int, db: Session) -> list[str]:
    pattern = f"%{query}%"
    recipes = db.execute(
        select(Recipe.instructions)
        .where(
            or_(
                Recipe.title.ilike(pattern),
                Recipe.instructions.ilike(pattern),
                Recipe.tags.ilike(pattern),
            )
        )
        .limit(n_results)
    ).scalars().all()
    pantry = db.execute(
        select(PantryItem.name).where(PantryItem.name.ilike(pattern)).limit(n_results)
    ).scalars().all()
    docs = [*recipes, *pantry]
    return docs[:n_results]


@app.on_event("startup")
def on_startup():
    wait_for_db()
    init_db()


@app.get("/health")
def health_check():
    """Return basic service status and active runtime configuration."""
    return {
        "status": "ok",
        "database": DATABASE_BACKEND,
        "model": MODEL_NAME,
    }


@app.post("/query")
def query(payload: QueryRequest, db: Session = Depends(get_db)):
    """Retrieve context from the database and return a generated answer."""
    try:
        docs = search_context(payload.q, payload.n_results, db)
        context = "\n\n".join(docs) if docs else ""

        if not context:
            return {
                "answer": "I do not have enough information to answer that.",
                "context_count": 0,
            }

        answer = generate_completion(
            prompt=(
                "You are a retrieval assistant. Use the provided context first. "
                "If context is empty, say you do not have enough information.\n\n"
                f"Context:\n{context}\n\nQuestion: {payload.q}\n\nAnswer:"
            )
        )
        return {
            "answer": answer.get("response", ""),
            "context_count": len(docs),
        }
    except RuntimeError as exc:
        logger.error("Query dependency error: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logger.exception("Query request failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/add")
def add_knowledge(payload: AddKnowledgeRequest, _: None = Depends(verify_add_api_key)):
    """Store new text as a knowledge item in the database."""
    raise HTTPException(status_code=501, detail="Use /recipes or /pantry for structured data")


@app.post("/recipes")
def add_recipe(payload: RecipeIn, db: Session = Depends(get_db), _: None = Depends(verify_add_api_key)):
    """Add a structured recipe to the recipe book."""
    try:
        recipe_id = str(uuid.uuid4())
        recipe = Recipe(
            id=recipe_id,
            title=payload.title,
            ingredients=json.dumps(payload.ingredients),
            instructions=payload.instructions,
            tags=json.dumps(payload.tags),
        )
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        return {"status": "success", "id": recipe_id}
    except Exception:
        logger.exception("Add recipe failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/recipes")
def list_recipes(db: Session = Depends(get_db)):
    """Return all stored recipes from the database."""
    try:
        recipes = db.execute(select(Recipe)).scalars().all()
        return {"count": len(recipes), "recipes": [serialize_recipe(r) for r in recipes]}
    except Exception:
        logger.exception("List recipes failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/pantry")
def add_pantry_item(
    payload: PantryItemIn,
    db: Session = Depends(get_db),
    _: None = Depends(verify_add_api_key),
):
    """Add or update an item in the user's pantry."""
    try:
        item_id = str(uuid.uuid4())
        item = PantryItem(
            id=item_id,
            name=payload.name,
            quantity=payload.quantity,
            unit=payload.unit,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return {"status": "success", "id": item_id}
    except Exception:
        logger.exception("Add pantry failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/pantry")
def list_pantry(db: Session = Depends(get_db)):
    """Return all pantry items."""
    try:
        items = db.execute(select(PantryItem)).scalars().all()
        return {"count": len(items), "items": [serialize_pantry_item(i) for i in items]}
    except Exception:
        logger.exception("List pantry failed")
        raise HTTPException(status_code=500, detail="Internal server error")


