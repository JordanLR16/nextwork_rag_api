import RecipeCarousel from "../components/recipes/RecipeCarousel";
import RecipeGrid from "../components/recipes/RecipeGrid";

const featuredRecipes = [
  {
    id: "featured-1",
    title: "Lemon Herb Chicken Bowls",
    description: "Bright skillet chicken with rice, greens, and a fast pan sauce.",
    time: "35 min",
    servings: "4",
  },
  {
    id: "featured-2",
    title: "Ginger Salmon Noodles",
    description: "Soy-ginger salmon over chilled noodles with crisp vegetables.",
    time: "25 min",
    servings: "2",
  },
];

const publicRecipes = [
  {
    id: "public-1",
    title: "Tomato Lentil Soup",
    category: "Vegetable",
    description: "A steady weeknight soup with pantry lentils and canned tomatoes.",
    time: "45 min",
    source: "Public",
  },
  {
    id: "public-2",
    title: "Garlic Butter Shrimp",
    category: "Seafood",
    description: "Quick shrimp with lemon, parsley, and enough sauce for bread.",
    time: "15 min",
    source: "Public",
  },
  {
    id: "public-3",
    title: "Miso Mushroom Pasta",
    category: "Pasta",
    description: "Savory mushrooms folded into a glossy miso cream sauce.",
    time: "30 min",
    source: "Public",
  },
];

export default function HomePage() {
  return (
    <div className="page-stack">
      <section>
        <div className="section-heading">
          <h1>Home</h1>
          <p>Featured recipes and the newest public additions.</p>
        </div>
        <RecipeCarousel recipes={featuredRecipes} />
      </section>

      <section>
        <div className="section-heading">
          <h2>New Public Recipes</h2>
        </div>
        <RecipeGrid recipes={publicRecipes} />
      </section>
    </div>
  );
}
