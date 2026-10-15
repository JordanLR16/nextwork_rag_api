import RecipeCarousel from "../components/recipes/RecipeCarousel";
import RecipeGrid from "../components/recipes/RecipeGrid";
import useRecipes from "../hooks/useRecipes";

export default function HomePage() {
  const { recipes, loading, error } = useRecipes();
  return (
    <div className="page-stack">
      <section>
        <div className="section-heading">
          <h1>Home</h1>
        </div>
        {loading && <p role="status">Loading recipes...</p>}
        {error && <p className="error" role="alert">{error}</p>}
        {!loading && !error && !recipes.length && <p>No recipes saved yet.</p>}
        <RecipeCarousel recipes={recipes.slice(0, 2)} />
      </section>

      <section>
        <div className="section-heading">
          <h2>Recipe Collection</h2>
        </div>
        <RecipeGrid recipes={recipes} />
      </section>
    </div>
  );
}
