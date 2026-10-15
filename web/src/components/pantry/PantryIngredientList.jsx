export default function PantryIngredientList({ ingredients }) {
  return (
    <div className="ingredient-list">
      {ingredients.map((ingredient) => (
        <article key={ingredient.id} className="ingredient-row">
          <div>
            <h3>{ingredient.name}</h3>
          </div>
          <span>{[ingredient.quantity, ingredient.unit].filter((value) => value != null && value !== "").join(" ") || "On hand"}</span>
        </article>
      ))}
    </div>
  );
}
