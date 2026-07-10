export default function RecipeCard({ recipe }) {
  return (
    <article className="recipe-card">
      <p className="eyebrow">{recipe.category}</p>
      <h3>{recipe.title}</h3>
      <p>{recipe.description}</p>
      <div className="card-footer">
        <span>{recipe.time}</span>
        <span>{recipe.source}</span>
      </div>
    </article>
  );
}
