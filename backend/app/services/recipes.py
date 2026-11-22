import uuid

from sqlalchemy.orm import Session

from ..repositories import recipes
from ..schemas.recipes import RecipeIn


def create_recipe(db: Session, payload: RecipeIn, owner_id: str) -> str:
    recipe_id = str(uuid.uuid4())
    try:
        recipe = recipes.add(db, payload.model_dump(), recipe_id, owner_id)
        db.commit()
        db.refresh(recipe)
    except Exception:
        db.rollback()
        raise
    return recipe_id


def list_recipes(db: Session, owner_id: str) -> list[dict]:
    return [recipes.serialize(recipe) for recipe in recipes.list_all(db, owner_id)]
