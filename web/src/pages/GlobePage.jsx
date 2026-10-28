import WorldMap from "../components/map/WorldMap";

export default function GlobePage() {
  return (
    <div className="page-stack">
      <h1>Explore the World</h1>
      <p>Select a country to explore its regions. Hover over a boundary to see its name.</p>
      <WorldMap />
    </div>
  );
}
