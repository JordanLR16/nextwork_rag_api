import RecipeExpansionButton from "../components/layout/RecipeExpansionButton";
import RecipeGrid from "../components/recipes/RecipeGrid";
import AddRecipeForm from "../components/recipes/AddRecipeForm";
import useRecipes from "../hooks/useRecipes";

export default function RecipeBookPage() {
  const { recipes, loading, error, reload } = useRecipes();
  return (
    <div className="page-stack">
      <section>
        <div className="section-heading">
          <h1>Recipe Book</h1>
        </div>
        {loading && <p role="status">Loading recipes...</p>}
        {error && <p className="error" role="alert">{error}</p>}
        {!loading && !error && !recipes.length && <p>No recipes saved yet.</p>}
        <RecipeGrid recipes={recipes} />
      </section>
      <RecipeExpansionButton title="Add Recipe">
        <AddRecipeForm onSaved={reload} />
      </RecipeExpansionButton>
    </div>
  );
}
