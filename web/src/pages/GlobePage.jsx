import WorldMap from "../components/map/WorldMap";

export default function GlobePage() {
  return (
    <div className="page-stack">
      <h1>Explore the World</h1>
      <p>Hover over a country to see its name.</p>
      <WorldMap />
    </div>
  );
}