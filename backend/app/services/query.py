"""Keyword selection, context formatting, and answer generation orchestration."""

import json
import re
from collections.abc import Callable

from sqlalchemy.orm import Session

from ..repositories import pantry, recipes

STOPWORDS = {
    "a", "an", "and", "are", "can", "do", "for", "from", "how", "i", "in",
    "is", "it", "make", "me", "my", "of", "on", "recipe", "recipes", "the",
    "to", "what", "with", "you",
}


def search_context(query: str, n_results: int, db: Session) -> list[str]:
    terms = list(dict.fromkeys(
        word for word in re.findall(r"\w+", query.lower()) if word not in STOPWORDS
    ))[:20]
    if not terms:
        return []
    matched_recipes = recipes.search(db, terms, n_results)
    items = pantry.search(db, terms, n_results - len(matched_recipes))
    docs = [
        f"Recipe: {recipe.title}\nIngredients: {', '.join(json.loads(recipe.ingredients))}"
        f"\nInstructions: {recipe.instructions}"
        for recipe in matched_recipes
    ]
    docs.extend(
        f"Pantry: {item.name}; quantity: {item.quantity if item.quantity is not None else 'unspecified'} {item.unit or ''}"
        for item in items
    )
    return docs


def answer_question(query: str, n_results: int, db: Session, generate: Callable) -> dict:
    docs = search_context(query, n_results, db)
    context = "\n\n".join(docs)
    if not context:
        return {"answer": "I do not have enough information to answer that.", "context_count": 0}
    answer = generate(prompt=(
        "You are a recipe assistant. Answer briefly using only the provided context. "
        "Do not invent ingredients or steps. If the context does not answer the question, "
        "say you do not have enough information.\n\n"
        f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    ))
    return {"answer": answer.get("response", ""), "context_count": len(docs)}
