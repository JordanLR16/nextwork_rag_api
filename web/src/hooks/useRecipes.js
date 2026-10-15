import { useEffect, useState } from "react";
import { listRecipes } from "../api/recipes";

export default function useRecipes() {
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    listRecipes()
      .then((data) => { if (active) setRecipes(data); })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [revision]);

  return { recipes, loading, error, reload: () => setRevision((value) => value + 1) };
}
