import { useState } from "react";
import { pantryApi } from "../../api/pantry";

export default function PantryIngredientForm({ onSaved }) {
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [unit, setUnit] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function onSubmit(event) {
    event.preventDefault();
    setMessage("");
    setError("");
    setLoading(true);
    try {
      await pantryApi.addIngredient({
        name: name.trim(),
        quantity: quantity === "" ? null : Number(quantity),
        unit: unit.trim() || null,
      });
      setName(""); setQuantity(""); setUnit("");
      setMessage("Ingredient saved.");
      onSaved?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }
  return (
    <form onSubmit={onSubmit} className="stack">
      <h2>Add Ingredient</h2>
      <label htmlFor="ingredientName">Ingredient</label>
      <input id="ingredientName" required value={name} onChange={(event) => setName(event.target.value)} placeholder="Sweet potatoes" />
      <label htmlFor="ingredientQuantity">Quantity</label>
      <input id="ingredientQuantity" type="number" min="0" step="any" value={quantity} onChange={(event) => setQuantity(event.target.value)} />
      <label htmlFor="ingredientUnit">Unit</label>
      <input id="ingredientUnit" value={unit} onChange={(event) => setUnit(event.target.value)} placeholder="lb, cups, bunches" />
      <button type="submit" disabled={loading}>{loading ? "Saving..." : "Save Ingredient"}</button>
      {message && <p className="status" role="status">{message}</p>}
      {error && <p className="error" role="alert">{error}</p>}
    </form>
  );
}
