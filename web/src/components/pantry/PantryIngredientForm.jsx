export default function PantryIngredientForm() {
  return (
    <form className="panel stack">
      <h2>Add Ingredient</h2>
      <label htmlFor="ingredientName">Ingredient</label>
      <input id="ingredientName" type="text" placeholder="e.g. sweet potatoes" />
      <label htmlFor="ingredientQuantity">Quantity</label>
      <input id="ingredientQuantity" type="text" placeholder="e.g. 3 medium" />
      <button type="button">Save Ingredient</button>
    </form>
  );
}
