import { useEffect, useMemo, useState } from "react";
import { geoCentroid, geoEqualEarth, geoMercator, geoPath } from "d3-geo";
import { normalizeWinding } from "./normalizeWinding";
import "./WorldMap.css";

const WIDTH = 960;
const HEIGHT = 500;
const SELECTED_COUNTRY_ZOOM = 1.1;
const SELECTED_COUNTRY_LEFT_PADDING = 24;
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function validateCollection(data) {
  if (data.type !== "FeatureCollection" || !Array.isArray(data.features)) {
    throw new Error("Expected a GeoJSON FeatureCollection.");
  }
  return data;
}

function renderFeature(feature) {
  return { ...feature, geometry: normalizeWinding(feature.geometry) };
}

export default function WorldMap() {
  const [countries, setCountries] = useState(null);
  const [error, setError] = useState("");
  const [selectedCode, setSelectedCode] = useState("");
  const [regionState, setRegionState] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadCountries() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/countries`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Map request failed: ${response.status}`);
        }

        const data = await response.json();

        if (!controller.signal.aborted) setCountries(validateCollection(data));
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      }
    }

    loadCountries();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!selectedCode) return;
    const controller = new AbortController();
    setRegionState({ code: selectedCode, loading: true });

    async function loadRegions() {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/countries/${encodeURIComponent(selectedCode)}/regions`,
          { signal: controller.signal }
        );
        if (controller.signal.aborted) return;
        if (response.status === 404) {
          setRegionState({ code: selectedCode, data: { type: "FeatureCollection", features: [] } });
          return;
        }
        if (!response.ok) throw new Error(`Region request failed: ${response.status}`);
        const data = validateCollection(await response.json());
        if (!controller.signal.aborted) setRegionState({ code: selectedCode, data });
      } catch (err) {
        if (!controller.signal.aborted) setRegionState({ code: selectedCode, error: err.message });
      }
    }
    loadRegions();
    return () => controller.abort();
  }, [selectedCode]);

  const selectedFeatures = useMemo(() => countries?.features.filter(
    (feature) => feature.properties?.country_code === selectedCode
  ) ?? [], [countries, selectedCode]);
  const selectedCountry = selectedFeatures[0];
  // Gate rendering by country code as well as aborting old requests.
  const activeRegions = selectedCode && regionState?.code === selectedCode ? regionState : null;

  const { shapes, regionShapes } = useMemo(() => {
    if (!countries) return { shapes: [], regionShapes: [] };

    const focus = selectedFeatures.length
      ? { type: "FeatureCollection", features: selectedFeatures.map(renderFeature) }
      : { type: "Sphere" };
    // Center Mercator on the selected longitude while keeping north upright.
    // This also keeps countries near the date line together in the detail view.
    const projection = (selectedFeatures.length
      ? geoMercator().rotate([-geoCentroid(focus)[0], 0])
      : geoEqualEarth()).fitExtent(
      [[10, 10], [WIDTH - 10, HEIGHT - 10]],
      focus
    );

    if (selectedFeatures.length) {
      projection.scale(projection.scale() * SELECTED_COUNTRY_ZOOM);
      const [[left, top], [, bottom]] = geoPath(projection).bounds(focus);
      const [x, y] = projection.translate();
      // Anchor the country's left edge and keep its vertical center in view.
      projection.translate([
        x + SELECTED_COUNTRY_LEFT_PADDING - left,
        y + HEIGHT / 2 - (top + bottom) / 2,
      ]);
    }

    const path = geoPath(projection);

    const shapes = countries.features.map((feature, index) => ({
      key: `${feature.properties?.country_code ?? "area"}-${index}`,
      code: feature.properties?.country_code,
      name: feature.properties?.name ?? "Unnamed area",
      outline: path(renderFeature(feature)),
    }));
    const regionShapes = (activeRegions?.data?.features ?? []).map((feature) => ({
      key: feature.properties.region_code,
      name: feature.properties.region_name ?? "Unnamed region",
      outline: path(renderFeature(feature)),
    }));
    return { shapes, regionShapes };
  }, [countries, selectedFeatures, activeRegions]);

  // Some countries have separate territory features sharing the same code.
  const countryOptions = shapes.filter((shape, index) => shape.code &&
    shapes.findIndex((candidate) => candidate.code === shape.code) === index)
    .sort((a, b) => a.name.localeCompare(b.name));

  if (error) return <p role="alert">{error}</p>;
  if (!countries) return <p role="status">Loading world map…</p>;

  return (
    <div className="world-map">
      <div className="world-map-controls">
        <label>
          Country{" "}
          <select value={selectedCode} onChange={(event) => setSelectedCode(event.target.value)}>
            <option value="">World view</option>
            {countryOptions.map((shape) => (
              <option key={shape.code} value={shape.code}>{shape.name}</option>
            ))}
          </select>
        </label>
        {selectedCode && <button type="button" onClick={() => setSelectedCode("")}>Back to world</button>}
      </div>
      {selectedCountry && (
        <div className="world-map-status" aria-live="polite">
          <strong>{selectedCountry.properties.name}</strong>
          {(!activeRegions || activeRegions.loading) && <p role="status">Loading regions…</p>}
          {activeRegions?.error && <p role="alert">{activeRegions.error}</p>}
          {activeRegions?.data && <p>{regionShapes.length ? `${regionShapes.length} regions. Hover over a region to see its name.` : "No region data available for this country."}</p>}
        </div>
      )}
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="group"
        aria-labelledby="world-map-title"
      >
        <title id="world-map-title">{selectedCountry ? `${selectedCountry.properties.name} regions` : "World country boundaries"}</title>

        {shapes.map((shape) => (
          <path
            key={shape.key}
            d={shape.outline}
            className={`world-map-country${shape.code === selectedCode ? " is-selected" : ""}`}
            role={shape.code ? "button" : undefined}
            tabIndex={shape.code ? 0 : undefined}
            aria-label={shape.name}
            aria-pressed={shape.code ? shape.code === selectedCode : undefined}
            onClick={() => shape.code && setSelectedCode(shape.code)}
            onKeyDown={(event) => {
              if (shape.code && (event.key === "Enter" || event.key === " ")) {
                event.preventDefault();
                setSelectedCode(shape.code);
              }
            }}
          >
            <title>{shape.name}</title>
          </path>
        ))}
        {regionShapes.map((shape) => (
          <path key={shape.key} d={shape.outline} className="world-map-region" aria-label={shape.name}>
            <title>{shape.name}</title>
          </path>
        ))}
      </svg>
    </div>
  );
}
