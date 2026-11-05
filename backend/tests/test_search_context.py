import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.services.query import search_context
from backend.app.db.base import Base
from backend.app.models import PantryItem, Recipe


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([
            Recipe(id="rice", title="Spinach rice", author_name="Demo",
                   ingredients=json.dumps(["spinach", "rice", "eggs"]),
                   instructions="Cook rice and wilt spinach.", tags="[]", substitutions="[]"),
            Recipe(id="soup", title="Spinach soup", author_name="Demo",
                   ingredients=json.dumps(["spinach", "broth"]),
                   instructions="Simmer the soup.", tags="[]", substitutions="[]"),
            PantryItem(id="egg", name="Eggs", quantity=8, unit="eggs"),
        ])
        session.commit()
        yield session
    engine.dispose()


def test_question_matches_keywords_and_ranks_recipe(db):
    docs = search_context("How do I make spinach rice?", 1, db)
    assert len(docs) == 1
    assert "Recipe: Spinach rice" in docs[0]
    assert "Ingredients: spinach, rice, eggs" in docs[0]
    assert "Cook rice and wilt spinach." in docs[0]


def test_ingredient_search_includes_pantry_quantity(db):
    docs = search_context("What can I make with eggs?", 3, db)
    assert len(docs) == 2
    assert "Recipe: Spinach rice" in docs[0]
    assert "Pantry: Eggs; quantity: 8.0 eggs" in docs[1]


@pytest.mark.parametrize("question", ["What can I make?", "%%%", "unicorn"])
def test_no_relevant_keywords_returns_no_context(db, question):
    assert search_context(question, 3, db) == []


def test_search_is_case_insensitive_and_ignores_duplicate_terms(db):
    assert search_context("SPINACH spinach RICE rice", 3, db) == search_context("spinach rice", 3, db)


def test_equal_scores_are_sorted_by_title(db):
    docs = search_context("spinach", 2, db)
    assert len(docs) == 2
    assert docs[0].startswith("Recipe: Spinach rice\n")
    assert docs[1].startswith("Recipe: Spinach soup\n")


def test_search_matches_tags_and_instructions(db):
    recipe = db.get(Recipe, "soup")
    recipe.tags = json.dumps(["comfortfood"])
    db.commit()
    assert search_context("comfortfood", 3, db)[0].startswith("Recipe: Spinach soup\n")
    assert search_context("wilt", 3, db)[0].startswith("Recipe: Spinach rice\n")


def test_underscore_in_search_is_literal_not_sql_wildcard(db):
    assert search_context("spina_h", 3, db) == []


def test_pantry_without_quantity_formats_unspecified_context(db):
    db.add(PantryItem(id="salt", name="Salt"))
    db.commit()
    docs = search_context("salt", 1, db)
    assert len(docs) == 1
    assert docs[0].strip() == "Pantry: Salt; quantity: unspecified"
