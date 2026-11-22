from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_current_user
from ..schemas.recipes import RecipeIn
from ..services import recipes
from .errors import internal_error

router = APIRouter(tags=["recipes"])


@router.post("/recipes")
def add_recipe(payload: RecipeIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        return {"status": "success", "id": recipes.create_recipe(db, payload, user.id)}
    except Exception:
        raise internal_error("Add recipe failed")


@router.get("/recipes")
def list_recipes(db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        records = recipes.list_recipes(db, user.id)
        return {"count": len(records), "recipes": records}
    except Exception:
        raise internal_error("List recipes failed")
