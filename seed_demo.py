"""Insert demo records once without replacing existing recipes or pantry items."""
import json

from database import PantryItem, Recipe, SessionLocal, init_db, wait_for_db

RECIPES = [
    {
        "id": "demo-spinach-rice",
        "title": "Spinach Rice Bowl",
        "description": "A quick rice bowl with garlicky spinach and a fried egg.",
        "ingredients": ["1 cup jasmine rice", "2 cups water", "2 cups spinach", "2 eggs", "1 clove garlic", "1 tbsp olive oil", "Salt"],
        "instructions": "For spinach rice bowls, rinse 1 cup jasmine rice. Add rice and 2 cups water to a pot, bring to a boil, cover and simmer for 15 minutes. Rest for 5 minutes. Heat 1 tbsp olive oil in a skillet, add minced garlic and cook for 30 seconds. Add 2 cups spinach and cook until wilted, about 2 minutes. Fry 2 eggs. Divide rice and spinach between 2 bowls and top each with an egg. Season with salt. Serves 2.",
        "tags": ["Vegetable", "spinach", "rice", "eggs"],
    },
    {
        "id": "demo-tomato-lentil",
        "title": "Tomato Lentil Soup",
        "description": "A hearty soup made with lentils and canned tomatoes.",
        "ingredients": ["1 cup dried lentils", "1 can diced tomatoes", "1 onion", "1 clove garlic", "4 cups vegetable broth", "1 tbsp olive oil"],
        "instructions": "To make tomato lentil soup, dice an onion and mince a clove of garlic. Heat olive oil in a pot and soften the onion for 5 minutes. Add garlic and cook for 30 seconds. Add rinsed lentils, canned tomatoes and vegetable broth. Simmer for 25 to 30 minutes until the lentils are tender. Serves 4.",
        "tags": ["Vegetable", "lentils", "tomato", "soup"],
    },
    {
        "id": "demo-lemon-chicken",
        "title": "Lemon Herb Chicken",
        "description": "Skillet chicken with lemon, garlic, and parsley.",
        "ingredients": ["2 chicken breasts", "1 lemon", "1 clove garlic", "1 tbsp olive oil", "2 tbsp parsley", "Salt"],
        "instructions": "For lemon herb chicken, season 2 chicken breasts with salt. Heat olive oil in a skillet. Cook the chicken for 6 to 8 minutes per side until its internal temperature reaches 165 F. Add minced garlic and cook for 30 seconds. Add the juice of 1 lemon and 2 tbsp chopped parsley. Rest the chicken for 5 minutes before slicing. Serves 2.",
        "tags": ["Poultry", "chicken", "lemon"],
    },
]

PANTRY = [
    {"id": "demo-rice", "name": "Jasmine rice", "quantity": 2, "unit": "lb"},
    {"id": "demo-spinach", "name": "Spinach", "quantity": 1, "unit": "bunch"},
    {"id": "demo-eggs", "name": "Eggs", "quantity": 8, "unit": "eggs"},
    {"id": "demo-lentils", "name": "Dried lentils", "quantity": 1, "unit": "lb"},
    {"id": "demo-tomatoes", "name": "Canned tomatoes", "quantity": 2, "unit": "cans"},
]


def main():
    wait_for_db()
    init_db()
    added = 0
    with SessionLocal() as db:
        for record in RECIPES:
            if db.get(Recipe, record["id"]) is None:
                data = {**record, "author_name": "Demo Kitchen", "substitutions": "[]"}
                data["ingredients"] = json.dumps(data["ingredients"])
                data["tags"] = json.dumps(data["tags"])
                db.add(Recipe(**data))
                added += 1
        for record in PANTRY:
            if db.get(PantryItem, record["id"]) is None:
                db.add(PantryItem(**record))
                added += 1
        db.commit()
    print(f"Added {added} demo records. Existing data preserved.")


if __name__ == "__main__":
    main()
