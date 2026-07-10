import { useState } from "react";
import { addRecipeKnowledge } from "../../api/recipes";

export default function AddRecipeForm() {
  const [recipe, setRecipe] = useState({
    title: "",
    description: "",
    ingredients: "",
    instructions: "",
    prepTime: "",
    cookTime: "",
    servings: "",
    category: "",
  });
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");

  const updateField = (field, value) => {
    setRecipe((currentRecipe) => ({ ...currentRecipe, [field]: value }));
  };

  const onAddRecipe = async (event) => {
    event.preventDefault();
    setStatus("");

    if (!recipe.title.trim() || !recipe.ingredients.trim() || !recipe.instructions.trim()) {
      setStatus("Please enter a title, ingredients, and instructions.");
      return;
    }

    const recipeText = [
      `Title: ${recipe.title}`,
      recipe.description && `Description: ${recipe.description}`,
      recipe.category && `Category: ${recipe.category}`,
      recipe.servings && `Servings: ${recipe.servings}`,
      recipe.prepTime && `Prep time: ${recipe.prepTime}`,
      recipe.cookTime && `Cook time: ${recipe.cookTime}`,
      `Ingredients:\n${recipe.ingredients}`,
      `Instructions:\n${recipe.instructions}`,
    ]
      .filter(Boolean)
      .join("\n\n");

    try {
      setLoading(true);
      const data = await addRecipeKnowledge(recipeText);
      setStatus(`Added successfully. id: ${data.id}`);
      setRecipe({
        title: "",
        description: "",
        ingredients: "",
        instructions: "",
        prepTime: "",
        cookTime: "",
        servings: "",
        category: "",
      });
    } catch (error) {
      setStatus(`Failed to add recipe: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={onAddRecipe} className="stack">
      <label htmlFor="recipeTitle">Title</label>
      <input
        id="recipeTitle"
        type="text"
        value={recipe.title}
        onChange={(event) => updateField("title", event.target.value)}
        placeholder="Sunday red sauce"
      />

      <label htmlFor="recipeDescription">Description</label>
      <textarea
        id="recipeDescription"
        value={recipe.description}
        onChange={(event) => updateField("description", event.target.value)}
        rows={2}
        placeholder="A short summary of the recipe"
      />

      <div className="form-grid">
        <div className="stack">
          <label htmlFor="recipeCategory">Category</label>
          <input
            id="recipeCategory"
            type="text"
            value={recipe.category}
            onChange={(event) => updateField("category", event.target.value)}
            placeholder="Pasta"
          />
        </div>
        <div className="stack">
          <label htmlFor="recipeServings">Servings</label>
          <input
            id="recipeServings"
            type="text"
            value={recipe.servings}
            onChange={(event) => updateField("servings", event.target.value)}
            placeholder="4"
          />
        </div>
      </div>

      <div className="form-grid">
        <div className="stack">
          <label htmlFor="recipePrepTime">Prep time</label>
          <input
            id="recipePrepTime"
            type="text"
            value={recipe.prepTime}
            onChange={(event) => updateField("prepTime", event.target.value)}
            placeholder="15 min"
          />
        </div>
        <div className="stack">
          <label htmlFor="recipeCookTime">Cook time</label>
          <input
            id="recipeCookTime"
            type="text"
            value={recipe.cookTime}
            onChange={(event) => updateField("cookTime", event.target.value)}
            placeholder="45 min"
          />
        </div>
      </div>

      <label htmlFor="recipeIngredients">Ingredients</label>
      <textarea
        id="recipeIngredients"
        value={recipe.ingredients}
        onChange={(event) => updateField("ingredients", event.target.value)}
        rows={5}
        placeholder="List ingredients, one per line"
      />

      <label htmlFor="recipeInstructions">Instructions</label>
        <textarea
        id="recipeInstructions"
        value={recipe.instructions}
        onChange={(event) => updateField("instructions", event.target.value)}
        rows={6}
        placeholder="Add the cooking steps"
        />

      <button type="submit" disabled={loading}>
        {loading ? "Adding..." : "Add to Knowledge Base"}
      </button>
      {status && <p className="status">{status}</p>}
    </form>
  );
}
