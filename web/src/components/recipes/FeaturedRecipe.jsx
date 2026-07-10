export default function FeaturedRecipe({ recipe }) {
  return (
    <article className="featured-recipe">
      <div>
        <p className="eyebrow">Featured</p>
        <h3>{recipe.title}</h3>
        <p>{recipe.description}</p>
      </div>
      <dl className="recipe-meta">
        <div>
          <dt>Time</dt>
          <dd>{recipe.time}</dd>
        </div>
        <div>
          <dt>Serves</dt>
          <dd>{recipe.servings}</dd>
        </div>
      </dl>
    </article>
  );
}
