from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dependencies import get_db, verify_add_api_key
from ..schemas.recipes import RecipeIn
from ..services import recipes
from .errors import internal_error

router = APIRouter(tags=["recipes"])


@router.post("/recipes", dependencies=[Depends(verify_add_api_key)])
def add_recipe(payload: RecipeIn, db: Session = Depends(get_db)):
    try:
        return {"status": "success", "id": recipes.create_recipe(db, payload)}
    except Exception:
        raise internal_error("Add recipe failed")


@router.get("/recipes")
def list_recipes(db: Session = Depends(get_db)):
    try:
        records = recipes.list_recipes(db)
        return {"count": len(records), "recipes": records}
    except Exception:
        raise internal_error("List recipes failed")
