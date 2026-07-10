export default function PantryIngredientList({ ingredients }) {
  return (
    <div className="ingredient-list">
      {ingredients.map((ingredient) => (
        <article key={ingredient.id} className="ingredient-row">
          <div>
            <h3>{ingredient.name}</h3>
            <p>{ingredient.category}</p>
          </div>
          <span>{ingredient.quantity}</span>
        </article>
      ))}
    </div>
  );
}
