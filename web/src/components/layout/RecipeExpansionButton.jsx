import { useState } from "react";

export default function RecipeExpansionButton({
  children,
  closedLabel = "Add Recipe",
  openLabel = "Close",
  title = "Add Recipe",
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="floating-recipe-form">
      {expanded && (
        <section className="floating-panel" aria-label={title}>
          <div className="floating-panel-header">
            <h2>{title}</h2>
            <button
              type="button"
              className="secondary-button"
              onClick={() => setExpanded(false)}
            >
              {openLabel}
            </button>
          </div>
          {children}
        </section>
      )}

      <button
        type="button"
        className="floating-action-button"
        aria-expanded={expanded}
        onClick={() => setExpanded((current) => !current)}
      >
        {expanded ? openLabel : closedLabel}
      </button>
    </div>
  );
}
