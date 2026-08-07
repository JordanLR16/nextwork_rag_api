import { useState } from "react";

export default function RecipeExpansionButton({
  children,
  closedLabel = "Add Recipe",
  openLabel = "Close",
  title = "Add Recipe",
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={expanded ? "floating-recipe-form expanded" : "floating-recipe-form"}>
      <section
        className="floating-panel"
        aria-label={title}
        aria-hidden={!expanded}
        inert={expanded ? undefined : true}
      >
        <div className="floating-panel-header">
          <h2>{title}</h2>
        </div>
        {children}
      </section>

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
