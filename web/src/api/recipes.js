import { getJson, postJson } from "./client";

export function askKnowledgeBase(question, nResults = 3) {
  return postJson("/query", { q: question, n_results: nResults });
}

export async function listRecipes() {
  const data = await getJson("/recipes");
  return data.recipes.map((recipe) => ({
    ...recipe,
    category: recipe.tags[0] || "Recipe",
    source: recipe.author_name,
  }));
}

export function addRecipe(recipe) {
  return postJson("/recipes", recipe);
}
