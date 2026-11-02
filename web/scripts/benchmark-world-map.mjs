// Opt-in benchmark using local datasets and the same D3 operations as WorldMap.
import assert from "node:assert/strict";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { cpus, platform, release } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { performance } from "node:perf_hooks";
import { parseArgs } from "node:util";
import { gzipSync } from "node:zlib";
import { geoEqualEarth, geoPath } from "d3-geo";
import { normalizeWinding } from "../src/components/map/normalizeWinding.js";

const root = fileURLToPath(new URL("../../", import.meta.url));
const { values } = parseArgs({ options: {
  raw: { type: "string", default: "data/raw/wbAdmin0.geojson" },
  processed: { type: "string", default: "data/processed/countries.geojson" },
  iterations: { type: "string", default: "5" },
  output: { type: "string", default: ".demo-checks/world-map-performance.json" },
} });
const iterations = Number(values.iterations);
assert(Number.isInteger(iterations) && iterations >= 3, "Use at least 3 measured iterations.");

function load(path) {
  const absolute = resolve(root, path);
  try {
    return readFileSync(absolute, "utf8");
  } catch (error) {
    throw new Error(`Cannot read ${absolute}. Supply local raw and processed country GeoJSON files.`, { cause: error });
  }
}

function validate(collection) {
  assert.equal(collection.type, "FeatureCollection");
  assert(collection.features.length > 0, "The collection must contain countries.");
  for (const feature of collection.features) {
    assert(["Polygon", "MultiPolygon"].includes(feature.geometry?.type), "Expected country polygons.");
    assert(feature.geometry.coordinates.length > 0, "Empty country geometry.");
  }
}

function countVertices(collection) {
  let count = 0;
  for (const feature of collection.features) {
    const polygons = feature.geometry.type === "Polygon"
      ? [feature.geometry.coordinates] : feature.geometry.coordinates;
    for (const polygon of polygons) {
      for (const ring of polygon) {
        assert(ring.length >= 4, "Polygon rings must contain at least four positions.");
        assert.deepEqual(ring[0], ring.at(-1), "Polygon rings must be closed.");
        for (const position of ring) {
          assert(position.length >= 2 && position.every(Number.isFinite), "Invalid coordinate.");
        }
        count += ring.length;
      }
    }
  }
  return count;
}

function countryIdentities(collection) {
  // Retain duplicate codes: territories can have separate features.
  return collection.features.map(({ properties: p }) => JSON.stringify([
    String(p.country_code ?? p.ISO_A3).trim().toUpperCase(), p.name ?? p.NAM_0,
  ])).sort();
}

function matchedSchema(text) {
  const collection = JSON.parse(text);
  validate(collection);
  return JSON.stringify({ type: "FeatureCollection", features: collection.features.map((feature) => ({
    type: "Feature",
    properties: {
      country_code: String(feature.properties.ISO_A3).trim().toUpperCase(),
      name: feature.properties.NAM_0,
    },
    geometry: feature.geometry,
  })) });
}

function describe(text) {
  const collection = JSON.parse(text);
  validate(collection);
  return {
    bytes: Buffer.byteLength(text), gzip_bytes: gzipSync(text).length,
    features: collection.features.length, vertices: countVertices(collection),
    identities: countryIdentities(collection),
  };
}

function measure(text) {
  // GC runs outside the timed work when started with --expose-gc (npm default).
  global.gc?.();
  const start = performance.now();
  const collection = JSON.parse(text);
  const parsed = performance.now();
  const features = collection.features.map((feature) => ({
    ...feature, geometry: normalizeWinding(feature.geometry),
  }));
  const normalized = performance.now();
  const projection = geoEqualEarth().fitExtent([[10, 10], [950, 490]], { type: "Sphere" });
  const path = geoPath(projection);
  let pathCharacters = 0;
  for (const feature of features) {
    const outline = path(feature);
    assert(outline && !/NaN|Infinity/.test(outline), "Country must produce a finite SVG path.");
    pathCharacters += outline.length;
  }
  const finished = performance.now();
  return {
    parse_ms: parsed - start, winding_ms: normalized - parsed,
    svg_path_ms: finished - normalized, total_ms: finished - start,
    svg_path_characters: pathCharacters,
  };
}

function median(numbers) {
  const sorted = [...numbers].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

const datasets = [
  { name: "Raw source", text: load(values.raw) },
  { name: "Unsimplified, matched fields", text: null },
  { name: "Preprocessed", text: load(values.processed) },
];
datasets[1].text = matchedSchema(datasets[0].text);
for (const dataset of datasets) {
  console.log(`Inspecting ${dataset.name}...`);
  dataset.metrics = describe(dataset.text);
  dataset.samples = [];
}
assert.deepEqual(datasets[0].metrics.identities, datasets[2].metrics.identities,
  "Preprocessing changed country codes, names, or feature counts; compare matching source/output datasets.");

console.log("Warming up each dataset once...");
for (const dataset of datasets) measure(dataset.text);
for (let iteration = 0; iteration < iterations; iteration++) {
  // Reverse order each round to reduce consistent first/last-run bias.
  const order = iteration % 2 ? [...datasets].reverse() : datasets;
  for (const dataset of order) dataset.samples.push(measure(dataset.text));
  console.log(`Measured round ${iteration + 1}/${iterations}`);
}

const results = datasets.map(({ name, metrics, samples }) => {
  const { identities, ...sizes } = metrics;
  return { name, ...sizes, median: Object.fromEntries(
    Object.keys(samples[0]).map((key) => [key, median(samples.map((sample) => sample[key]))]),
  ), samples };
});
const before = results[0];
const matched = results[1];
const after = results[2];
const reduction = (a, b) => 100 * (1 - b / a);
const comparison = {
  raw_bytes_reduction_percent: reduction(before.bytes, after.bytes),
  matched_fields_bytes_reduction_percent: reduction(matched.bytes, after.bytes),
  gzip_bytes_reduction_percent: reduction(before.gzip_bytes, after.gzip_bytes),
  vertices_reduction_percent: reduction(before.vertices, after.vertices),
  raw_compute_speedup: before.median.total_ms / after.median.total_ms,
  matched_fields_compute_speedup: matched.median.total_ms / after.median.total_ms,
};

// Deterministic regression checks, rather than flaky wall-clock thresholds.
const checks = {
  country_features_preserved: true, // Checked above, including identities and duplicates.
  fewer_vertices: after.vertices < before.vertices,
  smaller_than_matched_fields: after.bytes < matched.bytes,
  smaller_gzip_than_matched_fields: after.gzip_bytes < matched.gzip_bytes,
  fewer_svg_path_characters: after.median.svg_path_characters < matched.median.svg_path_characters,
};
const report = {
  generated_at: new Date().toISOString(),
  environment: { node: process.version, os: `${platform()} ${release()}`, cpu: cpus()[0]?.model },
  inputs: { raw: resolve(root, values.raw), processed: resolve(root, values.processed) },
  method: {
    iterations, warmup_rounds: 1, statistic: "median", forced_gc: Boolean(global.gc),
    projection: "Equal Earth, 960x500, 10px padding, fitted to Sphere",
    scope: "JSON parsing, production winding normalization, D3 SVG path generation in Node; excludes disk I/O, network, React, DOM and browser paint. Gzip is a size estimate, not a claim about server compression.",
    baseline: "Matched-fields baseline keeps raw coordinates, selects the same country fields as preprocessing and uses compact JSON. Input coordinates must already be EPSG:4326.",
  },
  results, comparison, checks,
};
const output = resolve(root, values.output);
mkdirSync(dirname(output), { recursive: true });
writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
console.table(results.map((result) => ({
  dataset: result.name, MiB: (result.bytes / 1024 ** 2).toFixed(2),
  "gzip MiB": (result.gzip_bytes / 1024 ** 2).toFixed(2), vertices: result.vertices,
  "parse ms": result.median.parse_ms.toFixed(1), "winding ms": result.median.winding_ms.toFixed(1),
  "SVG ms": result.median.svg_path_ms.toFixed(1), "total ms": result.median.total_ms.toFixed(1),
})));
console.log(`Vertex reduction: ${comparison.vertices_reduction_percent.toFixed(1)}%`);
console.log(`Compute speedup: ${comparison.raw_compute_speedup.toFixed(2)}x vs raw; ${comparison.matched_fields_compute_speedup.toFixed(2)}x vs matched fields`);
console.log(`Report: ${output}`);
for (const [check, passed] of Object.entries(checks)) assert(passed, `Preprocessing regression: ${check}`);
console.log("All preprocessing regression checks passed. Timings are observations, not pass/fail thresholds.");
