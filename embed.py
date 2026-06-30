import json
import uuid
from pathlib import Path

from database import SessionLocal, init_db, PantryItem, Recipe

SEED_FILE = Path("./k8s.txt")


def _load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def add_recipe(db, item):
    recipe_id = str(uuid.uuid4())
    recipe = Recipe(
        id=recipe_id,
        title=item.get("title", "Untitled Recipe"),
        ingredients=json.dumps(item.get("ingredients", [])),
        instructions=item.get("instructions", ""),
        tags=json.dumps(item.get("tags", [])),
    )
    db.add(recipe)
    return recipe_id


def add_pantry_item(db, item):
    item_id = str(uuid.uuid4())
    pantry_item = PantryItem(
        id=item_id,
        name=item.get("name", ""),
        quantity=item.get("quantity"),
        unit=item.get("unit"),
    )
    db.add(pantry_item)
    return item_id


def main():
    init_db()
    seed_path = SEED_FILE

    if not seed_path.exists():
        print(f"Seed file not found: {seed_path}")
        return

    data = None
    if seed_path.suffix.lower() == ".json":
        data = _load_json(seed_path)

    with SessionLocal() as db:
        if isinstance(data, list) and data and isinstance(data[0], dict):
            if "instructions" in data[0]:
                saved = 0
                for item in data:
                    add_recipe(db, item)
                    saved += 1
                db.commit()
                print(f"Imported {saved} recipes into the database")
                return
            if "name" in data[0]:
                saved = 0
                for item in data:
                    add_pantry_item(db, item)
                    saved += 1
                db.commit()
                print(f"Imported {saved} pantry items into the database")
                return
            print("JSON seed file format not recognized; expected recipe or pantry item objects.")
            return

        text = seed_path.read_text(encoding="utf-8").strip()
        if not text:
            print("Seed file is empty.")
            return

        add_recipe(db, {
            "title": seed_path.stem,
            "ingredients": [],
            "instructions": text,
            "tags": [],
        })
        db.commit()
        print(f"Imported plain-text seed as a recipe: {seed_path.stem}")


if __name__ == "__main__":
    main()
