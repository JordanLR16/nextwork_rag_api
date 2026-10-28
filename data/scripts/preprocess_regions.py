"""Simplify Admin 1 coverage and export one region collection per country."""

import argparse
import math
from pathlib import Path

import geopandas as gpd
import shapely

ROOT = Path(__file__).resolve().parents[2]


def preprocess_regions(source, output_dir, tolerance=0.02):
    # Match the country script's tolerance in EPSG:4326 degrees.
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("Tolerance must be a finite, non-negative number.")
    regions = gpd.read_file(source)
    if regions.crs is None:
        raise ValueError("Confirm the source coordinate reference system before continuing.")
    regions = regions.to_crs(epsg=4326).rename(columns={
        "ISO_A3": "country_code", "NAM_0": "country_name",
        "NAM_1": "region_name", "ADM1CD_c": "region_code",
    })
    regions = regions[[
        "country_code", "country_name", "region_code", "region_name", "geometry",
    ]].copy()
    regions["country_code"] = regions.country_code.astype("string").str.strip().str.upper()
    if not regions.country_code.str.fullmatch(r"[A-Z]{3}", na=False).all():
        raise ValueError("Every region must have a three-letter country code.")
    if regions.empty or regions.region_code.isna().any() or regions.region_code.duplicated().any():
        raise ValueError("Expected non-empty regions with unique, non-null region codes.")
    if (
        regions.geometry.isna().any() or regions.geometry.is_empty.any()
        or not regions.geometry.is_valid.all()
        or not regions.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).all()
    ):
        raise ValueError("Source regions contain missing, empty, invalid, or non-polygon geometry.")

    simplified = []
    for code, country in regions.groupby("country_code", sort=True):
        country = country.copy()
        if not shapely.coverage_is_valid(country.geometry.array):
            # The source has sub-nanodegree mismatches on some shared borders.
            # Snap only affected countries; substantial overlaps still fail validation.
            country.geometry = shapely.set_precision(country.geometry.array, 1e-9)
        if not shapely.coverage_is_valid(country.geometry.array):
            raise ValueError(f"{code} has overlaps or mismatched shared borders; repair the source before simplifying.")
        country.geometry = shapely.coverage_simplify(country.geometry.array, tolerance)
        if (
            country.geometry.isna().any() or country.geometry.is_empty.any()
            or not country.geometry.is_valid.all()
            or not shapely.coverage_is_valid(country.geometry.array)
        ):
            raise ValueError(f"Simplification produced invalid region coverage for {code}.")
        simplified.append((code, country))

    # Validate every country before writing any output.
    output_dir = Path(output_dir)
    for code, country in simplified:
        output_path = output_dir / code / "regions.geojson"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = output_path.with_suffix(".tmp.geojson")
        country.to_file(temporary_path, driver="GeoJSON", index=False)
        temporary_path.replace(output_path)

    original_vertices = int(regions.geometry.count_coordinates().sum())
    simplified_vertices = sum(int(country.geometry.count_coordinates().sum()) for _, country in simplified)
    print(f"Vertices: {original_vertices:,} -> {simplified_vertices:,}")
    print(f"Wrote {len(regions):,} regions for {len(simplified)} countries to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "data/raw/wbAdmin1.geojson")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed/regions")
    parser.add_argument("--tolerance", type=float, default=0.02)
    args = parser.parse_args()
    preprocess_regions(args.source, args.output_dir, args.tolerance)


if __name__ == "__main__":
    main()

