import RecipeExpansionButton from "../components/layout/RecipeExpansionButton";
import RecipeGrid from "../components/recipes/RecipeGrid";
import AddRecipeForm from "../components/recipes/AddRecipeForm";

const savedRecipes = [
  {
    id: "saved-1",
    title: "Sunday Red Sauce",
    category: "Pasta",
    description: "Saved family-style tomato sauce with sausage and basil.",
    time: "2 hr",
    source: "Saved",
  },
  {
    id: "saved-2",
    title: "Crispy Potato Hash",
    category: "Starch",
    description: "A flexible breakfast hash for leftover vegetables.",
    time: "40 min",
    source: "Saved",
  },
];

export default function RecipeBookPage() {
  return (
    <div className="page-stack">
      <section>
        <div className="section-heading">
          <h1>Recipe Book</h1>
          <p>Saved recipes from your knowledge base.</p>
        </div>
        <RecipeGrid recipes={savedRecipes} />
      </section>
      <RecipeExpansionButton title="Add Recipe">
        <AddRecipeForm />
      </RecipeExpansionButton>
    </div>
  );
}
