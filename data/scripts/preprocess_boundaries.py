import os
from pathlib import Path

import geopandas as gpd
from sqlalchemy import create_engine, text


# The default connects from this local script to the Docker database.
# Override it when using a different PostgreSQL server.
database_url = os.getenv(
    "BOUNDARIES_DATABASE_URL",
    "postgresql+psycopg2://postgres:Idontcare!1@localhost:5432/nextwork",
)

# EPSG:4326 uses degrees. This is a starting point to compare visually,
# not a uniform distance in meters.
simplification_tolerance = 0.02

path_to_wbAdmin0 = "data/raw/wbAdmin0.geojson"
wbAdmin0 = gpd.read_file(path_to_wbAdmin0)

wbAdmin0["country_code"] = (
    wbAdmin0["ISO_A3"].astype("string").str.strip().str.upper()
)
wbAdmin0["name"] = wbAdmin0["NAM_0"]

wbAdmin0 = wbAdmin0[["country_code", "name", "geometry"]].copy()

if wbAdmin0.crs is None:
    raise ValueError("Confirm the source coordinate reference system before continuing.")

wbAdmin0 = wbAdmin0.to_crs(epsg=4326)

engine = create_engine(database_url)
try:
    with engine.begin() as connection:
        # PostGIS must already be installed and enabled in this database.
        postgis_version = connection.execute(
            text("SELECT PostGIS_Full_Version()")
        ).scalar_one()
        print(postgis_version)

        # Dedicated working table, replaced on each successful run.
        # A failed transaction rolls back changes to this table.
        wbAdmin0.to_postgis(
            "countries_preprocess_input",
            connection,
            if_exists="replace",
            index=False,
        )

        invalid_edges = connection.execute(text("""
            SELECT COUNT(*)
            FROM (
                SELECT ST_CoverageInvalidEdges(geometry) OVER () AS edges
                FROM countries_preprocess_input
            ) AS checked
            WHERE NOT ST_IsEmpty(edges)
        """)).scalar_one()

        if invalid_edges:
            raise ValueError(
                f"{invalid_edges} country features have invalid coverage edges. "
                "Inspect overlaps and mismatched shared borders before simplifying."
            )

        simplified = gpd.read_postgis(
            text("""
                SELECT
                    country_code,
                    name,
                    ST_CoverageSimplify(
                        geometry, :tolerance
                    ) OVER () AS geometry
                FROM countries_preprocess_input
            """),
            connection,
            geom_col="geometry",
            params={"tolerance": simplification_tolerance},
        )
finally:
    engine.dispose()

if (
    len(simplified) != len(wbAdmin0)
    or simplified.geometry.isna().any()
    or simplified.geometry.is_empty.any()
    or not simplified.geometry.is_valid.all()
):
    raise ValueError("Simplification produced missing, empty, or invalid country features.")

original_vertices = int(wbAdmin0.geometry.count_coordinates().sum())
simplified_vertices = int(simplified.geometry.count_coordinates().sum())
print(f"Vertices: {original_vertices:,} -> {simplified_vertices:,}")

output_path = Path("data/processed/countries.geojson")
output_path.parent.mkdir(parents=True, exist_ok=True)

simplified.to_file(output_path, driver="GeoJSON", index=False)
print(f"Wrote {len(simplified)} countries to {output_path} ({output_path.stat().st_size:,} bytes)")
