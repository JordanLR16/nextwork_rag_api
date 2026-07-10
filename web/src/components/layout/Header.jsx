export default function Header() {
  return (
    <header className="topbar">
      <span className="dateline">Jul 10, 2026</span>
      <div className="category-legend" aria-label="Recipe categories">
        {[
          { label: "Meat", color: "#9a3412" },
          { label: "Seafood", color: "#2563eb" },
          { label: "Starch", color: "#ca8a04" },
          { label: "Vegetable", color: "#16a34a" },
        ].map(({ label, color }) => (
          <div key={label} className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: color }} />
            <span>{label}</span>
          </div>
        ))}
      </div>
    </header>
  );
}
