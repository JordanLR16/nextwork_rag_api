import { useEffect, useState } from "react";
import PantryIngredientForm from "../components/pantry/PantryIngredientForm";
import PantryIngredientList from "../components/pantry/PantryIngredientList";
import { pantryApi } from "../api/pantry";

export default function PantryPage() {
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    pantryApi.listIngredients()
      .then((items) => { if (active) setIngredients(items); })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [revision]);
  return (
    <div className="page-stack">
      <section>
        <div className="section-heading">
          <h1>Pantry</h1>
        </div>
        {loading && <p role="status">Loading pantry...</p>}
        {error && <p className="error" role="alert">{error}</p>}
        {!loading && !error && !ingredients.length && <p>Your pantry is empty.</p>}
        <PantryIngredientList ingredients={ingredients} />
      </section>
      <PantryIngredientForm onSaved={() => setRevision((value) => value + 1)} />
    </div>
  );
}
