const NAV_ITEMS = [
  { id: "home", label: "Home" },
  { id: "recipes", label: "Recipe Book" },
  { id: "pantry", label: "Pantry" },
  { id: "ask", label: "Ask" },
];

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="brand-mark">NR</div>
      <nav className="sidebar-nav" aria-label="Primary navigation">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={activePage === item.id ? "nav-button active" : "nav-button"}
            onClick={() => onNavigate(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
