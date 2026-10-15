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
          <dt>Ingredients</dt>
          <dd>{recipe.ingredients.length}</dd>
        </div>
        <div>
          <dt>Author</dt>
          <dd>{recipe.author_name}</dd>
        </div>
      </dl>
    </article>
  );
}
