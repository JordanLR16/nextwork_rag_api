import PantryIngredientForm from "../components/pantry/PantryIngredientForm";
import PantryIngredientList from "../components/pantry/PantryIngredientList";

const ingredients = [
  { id: "pantry-1", name: "Eggs", category: "Refrigerated", quantity: "8" },
  { id: "pantry-2", name: "Jasmine rice", category: "Dry goods", quantity: "2 lb" },
  { id: "pantry-3", name: "Spinach", category: "Produce", quantity: "1 bunch" },
];

export default function PantryPage() {
  return (
    <div className="page-stack">
      <section>
        <div className="section-heading">
          <h1>Pantry</h1>
          <p>Ingredients currently owned by the user.</p>
        </div>
        <PantryIngredientList ingredients={ingredients} />
      </section>
      <PantryIngredientForm />
    </div>
  );
}
