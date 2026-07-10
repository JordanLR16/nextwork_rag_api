import FeaturedRecipe from "./FeaturedRecipe";

export default function RecipeCarousel({ recipes }) {
  return (
    <div className="carousel" aria-label="Featured recipes">
      {recipes.map((recipe) => (
        <FeaturedRecipe key={recipe.id} recipe={recipe} />
      ))}
    </div>
  );
}
