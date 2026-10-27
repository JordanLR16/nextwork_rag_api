import { geoArea } from "d3-geo";

function normalizePolygon(rings) {
  return rings.map((ring, index) => {
    // Country rings enclose less than a hemisphere. D3 interprets a
    // clockwise ring as the small interior and the reverse as its complement.
    const clockwise = geoArea({ type: "Polygon", coordinates: [ring] }) <= 2 * Math.PI;
    const shouldBeClockwise = index === 0; // Holes use the opposite winding.

    return clockwise === shouldBeClockwise ? ring : [...ring].reverse();
  });
}

export function normalizeWinding(geometry) {
  if (geometry?.type === "Polygon") {
    return { ...geometry, coordinates: normalizePolygon(geometry.coordinates) };
  }

  if (geometry?.type === "MultiPolygon") {
    return {
      ...geometry,
      coordinates: geometry.coordinates.map(normalizePolygon),
    };
  }

  return geometry;
}
