// Compare the old country map with Mapshaper GeoJSON and TopoJSON exports.
// Run from web: npm run test:topojson-performance
import assert from "node:assert/strict";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { cpus, platform, release } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { performance } from "node:perf_hooks";
import { parseArgs } from "node:util";
import { gzipSync } from "node:zlib";
import { geoEqualEarth, geoPath } from "d3-geo";
import { feature as decodeFeature } from "topojson-client";
import { normalizeWinding } from "../src/components/map/normalizeWinding.js";

const root = fileURLToPath(new URL("../../", import.meta.url));
const { values } = parseArgs({ options: {
  baseline: { type: "string", default: "data/processed/countries.geojson" },
  geojson: { type: "string", default: "data/processed/countries-overview.geojson" },
  topojson: { type: "string", default: "data/processed/countries-overview.topojson" },
  object: { type: "string", default: "countries" },
  iterations: { type: "string", default: "5" },
  output: { type: "string", default: ".demo-checks/topojson-performance.json" },
} });
const iterations = Number(values.iterations);
assert(Number.isInteger(iterations) && iterations >= 3, "Use at least 3 measured iterations.");

function decode(parsed, topojson) {
  if (!topojson) return parsed;
  assert.equal(parsed.type, "Topology", "Expected a TopoJSON Topology.");
  const object = parsed.objects?.[values.object];
  assert(object, `Missing TopoJSON object '${values.object}'. Available: ${Object.keys(parsed.objects ?? {}).join(", ")}`);
  return decodeFeature(parsed, object);
}

function inspect(collection) {
  assert.equal(collection.type, "FeatureCollection");
  assert(collection.features?.length > 0, "Expected country features.");
  let vertices = 0;
  let polygonParts = 0;
  let holes = 0;
  const identities = [];
  for (const feature of collection.features) {
    const p = feature.properties;
    assert(typeof p?.country_code === "string" && p.country_code.trim(), "Missing country_code.");
    assert(typeof p?.name === "string" && p.name.trim(), "Missing country name.");
    // Compare a multiset: separate territories can share a country code.
    identities.push(JSON.stringify([p.country_code, p.name]));
    const geometry = feature.geometry;
    assert(["Polygon", "MultiPolygon"].includes(geometry?.type), "Expected non-null country polygons.");
    const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
    assert(polygons.length > 0, "Empty geometry.");
    polygonParts += polygons.length;
    for (const polygon of polygons) {
      assert(polygon.length > 0, "Empty polygon.");
      holes += polygon.length - 1;
      for (const ring of polygon) {
        assert(ring.length >= 4, "Ring must have at least four positions.");
        assert.deepEqual(ring[0], ring.at(-1), "Ring must be closed.");
        for (const position of ring) {
          assert(position.length >= 2 && position.every(Number.isFinite), "Invalid coordinate.");
        }
        vertices += ring.length;
      }
    }
  }
  return { features: collection.features.length, vertices, polygon_parts: polygonParts,
    holes, identities: identities.sort() };
}

function measure(dataset) {
  global.gc?.(); // Outside timed work; enabled by the npm command.
  const start = performance.now();
  const parsed = JSON.parse(dataset.text);
  const parsedAt = performance.now();
  const collection = decode(parsed, dataset.topojson);
  const decodedAt = performance.now();
  const features = collection.features.map((feature) => ({
    ...feature, geometry: normalizeWinding(feature.geometry),
  }));
  const normalizedAt = performance.now();
  const projection = geoEqualEarth().fitExtent([[10, 10], [950, 490]], { type: "Sphere" });
  const path = geoPath(projection);
  // Match WorldMap's initial world-view path work, without React or DOM work.
  const outlines = features.map((feature) => path(feature));
  const finished = performance.now();
  // Validate outside the timed section.
  for (const outline of outlines) {
    assert(outline && !/NaN|Infinity/.test(outline), "Country must produce a finite SVG path.");
  }
  return { parse_ms: parsedAt - start,
    decode_ms: dataset.topojson ? decodedAt - parsedAt : 0,
    winding_ms: normalizedAt - decodedAt, svg_path_ms: finished - normalizedAt,
    total_ms: finished - start,
    svg_path_characters: outlines.reduce((sum, outline) => sum + outline.length, 0) };
}

function median(numbers) {
  const sorted = [...numbers].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

const datasets = [
  { name: "Previous GeoJSON", key: "baseline", topojson: false },
  { name: "Simplified GeoJSON", key: "geojson", topojson: false },
  { name: "Simplified TopoJSON", key: "topojson", topojson: true },
];
for (const dataset of datasets) {
  dataset.path = resolve(root, values[dataset.key]);
  try {
    dataset.text = readFileSync(dataset.path, "utf8");
  } catch (error) {
    throw new Error(`Cannot read ${dataset.path}. Generate the Mapshaper exports or override --${dataset.key}.`, { cause: error });
  }
  dataset.metrics = inspect(decode(JSON.parse(dataset.text), dataset.topojson));
  dataset.bytes = Buffer.byteLength(dataset.text);
  dataset.gzip_bytes = gzipSync(dataset.text).length;
  dataset.samples = [];
}
for (const dataset of datasets.slice(1)) {
  assert.deepEqual(dataset.metrics.identities, datasets[0].metrics.identities,
    `${dataset.name} changed country codes, names, or feature counts.`);
}

console.log("Warming up each dataset once...");
for (const dataset of datasets) measure(dataset);
for (let iteration = 0; iteration < iterations; iteration++) {
  // Rotate and reverse order to distribute position effects across datasets.
  const offset = iteration % datasets.length;
  const order = [...datasets.slice(offset), ...datasets.slice(0, offset)];
  if (iteration % 2) order.reverse();
  for (const dataset of order) dataset.samples.push(measure(dataset));
  console.log(`Measured round ${iteration + 1}/${iterations}`);
}
const results = datasets.map(({ name, metrics, bytes, gzip_bytes, samples }) => {
  const { identities, ...geometry } = metrics;
  return { name, bytes, gzip_bytes, ...geometry, median: Object.fromEntries(
    Object.keys(samples[0]).map((key) => [key, median(samples.map((sample) => sample[key]))]),
  ), samples };
});
const compare = (before, after) => ({
  bytes_reduction_percent: 100 * (1 - after.bytes / before.bytes),
  gzip_reduction_percent: 100 * (1 - after.gzip_bytes / before.gzip_bytes),
  compute_speedup: before.median.total_ms / after.median.total_ms,
});
const report = {
  generated_at: new Date().toISOString(),
  environment: { node: process.version, os: `${platform()} ${release()}`, cpu: cpus()[0]?.model },
  inputs: Object.fromEntries(datasets.map((dataset) => [dataset.key, dataset.path])),
  method: { iterations, warmup_rounds: 1, statistic: "median", forced_gc: Boolean(global.gc),
    topojson_object: values.object, projection: "Equal Earth, 960x500, 10px padding, fitted to Sphere",
    scope: "Node JSON parsing, TopoJSON decoding, production winding normalization, and SVG path generation. Excludes disk I/O, network, React, DOM, browser painting, and country/region selection. Gzip sizes are estimates, not evidence of server compression.",
  },
  results,
  comparisons: {
    simplification: compare(results[0], results[1]),
    topojson_vs_simplified_geojson: compare(results[1], results[2]),
    combined: compare(results[0], results[2]),
  },
  checks: { country_codes_names_and_feature_counts_preserved: true,
    closed_rings_finite_coordinates_and_paths: true },
};
const output = resolve(root, values.output);
assert(!datasets.some((dataset) => dataset.path.toLowerCase() === output.toLowerCase()),
  "Report output must not overwrite an input map.");
mkdirSync(dirname(output), { recursive: true });
writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
console.table(results.map((r) => ({
  dataset: r.name, "size KiB": (r.bytes / 1024).toFixed(1),
  "gzip KiB": (r.gzip_bytes / 1024).toFixed(1), vertices: r.vertices,
  parts: r.polygon_parts, holes: r.holes,
  "parse ms": r.median.parse_ms.toFixed(1), "decode ms": r.median.decode_ms.toFixed(1),
  "winding ms": r.median.winding_ms.toFixed(1), "SVG ms": r.median.svg_path_ms.toFixed(1),
  "total ms": r.median.total_ms.toFixed(1),
})));
for (const [name, c] of Object.entries(report.comparisons)) {
  console.log(`${name}: ${c.bytes_reduction_percent.toFixed(1)}% smaller; ${c.gzip_reduction_percent.toFixed(1)}% smaller gzip; ${c.compute_speedup.toFixed(2)}x compute speedup`);
}
console.log("Country identities and basic geometry checks passed. Timings are observations, not pass/fail thresholds.");
console.log("Polygon parts and holes may be lost during simplification; compare their counts and check appearance separately.");
console.log("This measures world-map computation, not browser load time. TopoJSON can reduce transfer size without reducing render time.");
console.log(`Report: ${output}`);
