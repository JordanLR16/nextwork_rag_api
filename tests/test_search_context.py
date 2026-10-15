import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import search_context
from database import Base, PantryItem, Recipe


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
