const CATEGORY_COLORS = {
  meat: "#b85450",
  poultry: "#d07a46",
  seafood: "#3f7f93",
  vegetable: "#5f8f4e",
  veggie: "#5f8f4e",
  starch: "#c99a2e",
  pasta: "#d3a43b",
};

export default function RecipeCard({ recipe }) {
  const category = recipe.category?.trim().toLowerCase();
  const categoryColor = CATEGORY_COLORS[category] ?? "#81796a";

  return (
    <article
      className="recipe-card"
      style={{ "--category-color": categoryColor }}
    >
      <p className="eyebrow">{recipe.category}</p>
      <h3>{recipe.title}</h3>
      <p>{recipe.description}</p>
      <div className="card-footer">
        <span>{recipe.time}</span>
        <span>{recipe.source}</span>
      </div>
      <div className="recipe-card__category-bar" aria-hidden="true" />
    </article>
  );
}
