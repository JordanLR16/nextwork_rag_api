import { useEffect, useMemo, useState } from "react";
import { geoEqualEarth, geoPath } from "d3-geo";
import "./WorldMap.css";

const WIDTH = 960;
const HEIGHT = 500;

export default function WorldMap() {
  const [countries, setCountries] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadCountries() {
      try {
        const response = await fetch("/maps/countries.geojson", {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Map request failed: ${response.status}`);
        }

        const data = await response.json();

        if (
          data.type !== "FeatureCollection" ||
          !Array.isArray(data.features)
        ) {
          throw new Error("Expected a GeoJSON FeatureCollection.");
        }

        setCountries(data);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      }
    }

    loadCountries();
    return () => controller.abort();
  }, []);

  const shapes = useMemo(() => {
    if (!countries) return [];

    const projection = geoEqualEarth().fitExtent(
      [[10, 10], [WIDTH - 10, HEIGHT - 10]],
      { type: "Sphere" }
    );

    const path = geoPath(projection);

    return countries.features.map((feature, index) => ({
      // Temporary rendering key; choose validated IDs before linking recipes.
      key: index,
      name: feature.properties?.NAM_0 ?? "Unnamed area",
      outline: path(feature),
    }));
  }, [countries]);

  if (error) return <p role="alert">{error}</p>;
  if (!countries) return <p role="status">Loading world map…</p>;

  return (
    <div className="world-map">
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-labelledby="world-map-title"
      >
        <title id="world-map-title">World country boundaries</title>

        {shapes.map((shape) => (
          <path
            key={shape.key}
            d={shape.outline}
            className="world-map-country"
          >
            <title>{shape.name}</title>
          </path>
        ))}
      </svg>
    </div>
  );
}