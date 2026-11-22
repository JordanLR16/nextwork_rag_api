import pytest
from sqlalchemy import event, select
from sqlalchemy.exc import SQLAlchemyError

from backend.app.cli.seed_demo import PANTRY, RECIPES, seed_demo
from backend.app.db.session import Database
from backend.app.models import PantryItem, Recipe, User
from backend.app.schemas.pantry import PantryItemIn
from backend.app.schemas.recipes import RecipeIn
from backend.app.services.pantry import create_item
from backend.app.services.recipes import create_recipe


@pytest.fixture
def session():
    database = Database("sqlite://")
    database.initialize()
    try:
        with database.session_factory() as db:
            db.add(User(id="test-owner", issuer="test", subject="owner", is_active=True))
            db.commit()
            yield db
    finally:
        database.dispose()


@pytest.mark.parametrize("create,payload,model", [
    (create_recipe, RecipeIn(title="Toast", author_name="Cook", instructions="Toast bread."), Recipe),
    (create_item, PantryItemIn(name="Rice"), PantryItem),
])
def test_failed_write_rolls_back_and_session_can_be_reused(session, create, payload, model):
    def fail_commit(db):
        # Flush first so rollback must undo an actual insert, not only pending state.
        db.flush()
        raise SQLAlchemyError("Simulated commit failure")

    event.listen(session, "before_commit", fail_commit)
    try:
        with pytest.raises(SQLAlchemyError, match="Simulated commit failure"):
            create(session, payload, "test-owner")
    finally:
        event.remove(session, "before_commit", fail_commit)

    assert not session.in_transaction()
    assert session.execute(select(model)).scalars().all() == []
    saved_id = create(session, payload, "test-owner")
    assert session.get(model, saved_id) is not None


def test_demo_seed_is_repeatable_and_preserves_user_edits(session):
    assert seed_demo(session, "test-owner") == len(RECIPES) + len(PANTRY)
    recipe = session.execute(select(Recipe).where(Recipe.title == RECIPES[0]["title"])).scalar_one()
    recipe.title = "My edited demo recipe"
    session.commit()
    assert seed_demo(session, "test-owner") == 0
    assert session.get(Recipe, recipe.id).title == "My edited demo recipe"
    assert len(session.execute(select(Recipe)).scalars().all()) == len(RECIPES)
    assert len(session.execute(select(PantryItem)).scalars().all()) == len(PANTRY)


def test_seed_is_personal_to_each_user(session):
    session.add(User(id="second-owner", issuer="test", subject="second-owner", is_active=True))
    session.commit()
    expected_count = len(RECIPES) + len(PANTRY)
    assert seed_demo(session, "test-owner") == expected_count
    assert seed_demo(session, "second-owner") == expected_count
    assert seed_demo(session, "test-owner") == 0
    for owner_id in ("test-owner", "second-owner"):
        assert len(session.execute(select(Recipe).where(Recipe.owner_id == owner_id)).scalars().all()) == len(RECIPES)
        assert len(session.execute(select(PantryItem).where(PantryItem.owner_id == owner_id)).scalars().all()) == len(PANTRY)
