"""Recipe storage mapping and queries. Callers own the transaction."""

import json

from sqlalchemy import case, or_, select
from sqlalchemy.orm import Session

from ..models import Recipe


def add(db: Session, data: dict, recipe_id: str) -> Recipe:
    fields = dict(data)
    for name in ("ingredients", "substitutions", "tags"):
        fields[name] = json.dumps(fields[name])
    recipe = Recipe(id=recipe_id, **fields)
    db.add(recipe)
    return recipe


def list_all(db: Session) -> list[Recipe]:
    return db.execute(select(Recipe)).scalars().all()


def search(db: Session, terms: list[str], limit: int) -> list[Recipe]:
    if not terms or limit <= 0:
        return []
    matches = [or_(
        *(column.icontains(term, autoescape=True) for column in (
            Recipe.title, Recipe.ingredients, Recipe.instructions, Recipe.tags,
        ))
    ) for term in terms]
    score = sum(case((match, 1), else_=0) for match in matches)
    return db.execute(
        select(Recipe).where(or_(*matches))
        .order_by(score.desc(), Recipe.title, Recipe.id).limit(limit)
    ).scalars().all()


def serialize(recipe: Recipe) -> dict:
    return {
        "id": recipe.id, "title": recipe.title, "author_name": recipe.author_name,
        "ingredients": json.loads(recipe.ingredients), "instructions": recipe.instructions,
        "substitutions": json.loads(recipe.substitutions), "tagline": recipe.tagline,
        "description": recipe.description, "tags": json.loads(recipe.tags),
    }
