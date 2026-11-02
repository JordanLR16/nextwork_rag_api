# Nextwork RAG API

A full-stack recipe knowledge base built with FastAPI, SQLAlchemy, Ollama, and a React/Vite frontend. The backend stores structured recipe and pantry data, retrieves matching context, and uses a local Ollama model to answer questions from the knowledge base.

## Features

- FastAPI backend with health, query, recipe, and pantry endpoints
- SQLAlchemy models with SQLite by default and PostgreSQL support for Docker/local deployments
- Ollama integration for local LLM responses
- React/Vite frontend with recipe, pantry, and question-answering views
- Optional API-key protection for write endpoints
- Docker Compose setup for API, web, and PostgreSQL services
- Pytest coverage for core backend routes

## Tech Stack

- Backend: Python, FastAPI, Pydantic, SQLAlchemy
- Database: SQLite or PostgreSQL
- LLM runtime: Ollama
- Frontend: React, Vite, CSS
- DevOps: Docker, Docker Compose
- Testing: Pytest, FastAPI TestClient

## Project Structure

```text
.
|-- app.py                 # FastAPI routes and RAG query flow
|-- database.py            # SQLAlchemy engine, models, and session handling
|-- seed_demo.py           # Repeatable recipe and pantry demo data
|-- importer/              # Instagram extraction and recipe parsing
|-- data/scripts/          # Geographic data preprocessing
|-- tests/                 # Backend API tests
|-- web/                   # React/Vite frontend
|-- Dockerfile             # Backend container
`-- docker-compose.yml     # API, web, and PostgreSQL services
```

## API Overview

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Returns service status and active runtime configuration |
| `POST` | `/query` | Searches stored context and generates an answer with Ollama |
| `GET` | `/recipes` | Lists saved recipes |
| `POST` | `/recipes` | Adds a structured recipe |
| `GET` | `/pantry` | Lists pantry items |
| `POST` | `/pantry` | Adds a pantry item |
| `POST` | `/add` | Legacy endpoint that now directs callers to structured routes |

## Local Setup

Use Python `3.11` for the smoothest setup.

1. Create and activate a Python virtual environment.
2. Install backend dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy the backend environment example:

   ```powershell
   copy .env.example .env
   ```

4. Start the backend:

   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

5. Start the frontend:

   ```bash
   cd web
   npm install
   copy .env.example .env
   npm run dev
   ```

The API runs on `http://localhost:8000` and the frontend runs on `http://localhost:5173`.

## Environment Variables

### Backend

| Variable | Description | Default |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./db/app.db` |
| `MODEL_NAME` | Ollama model name | `tinyllama` |
| `OLLAMA_HOST` | Optional custom Ollama host | unset |
| `ADD_API_KEY` | Optional API key for write endpoints | unset |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | local Vite origins |

### Frontend

| Variable | Description | Default |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_ADD_API_KEY` | Optional API key sent with write requests | unset |

## Database Setup

### SQLite

SQLite is used automatically when `DATABASE_URL` is not set. The local database is created at `db/app.db`.

### PostgreSQL

Set `DATABASE_URL` in `.env` or your shell:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nextwork
```

Docker Compose includes a PostgreSQL service configured with the same default credentials.

## Seed Data

Populate example recipes and pantry items from the project root:

```bash
python seed_demo.py
```

The demo seed can run repeatedly without replacing existing records. Add your
own data through the recipe and pantry API endpoints. The `importer/` package
extracts Instagram content for future import workflows; it does not save recipes
to the database automatically.

## Local and generated files

Raw map inputs in `data/raw/` and generated maps in `data/processed/` are ignored
by Git. Keep them locally for preprocessing, map endpoints, and benchmarks.
The API reads countries from `data/processed/countries.geojson`; the frontend
fetches them through `/api/countries` rather than bundling a second map copy.
Generate country boundaries with `python data/scripts/preprocess_boundaries.py`
using the script's configured PostGIS connection. Region generation is described
below. Missing country data returns HTTP 503; missing country regions return 404.

Database files, `*.dump` backups, benchmark reports in `.demo-checks/`, frontend
builds, and installed dependencies stay outside version control. Preserve local
backups separately when needed. The API Docker build excludes raw map inputs,
local databases, backups, and reports, but includes generated maps, so generate
them before building an image that needs to serve map data.

## Map region preprocessing

Install the optional geospatial dependencies, then generate the region files:

```powershell
python -m pip install -r requirements-geospatial.txt
python data/scripts/preprocess_regions.py
```

The script reads `data/raw/wbAdmin1.geojson` and writes
`data/processed/regions/<ISO_A3>/regions.geojson` for each country in that source.
Each collection retains country codes/names and region codes/names. Like the
country boundary script, it simplifies polygon coverage with a default tolerance
of `0.02` degrees in EPSG:4326, preserving matching shared region borders.
This uses Shapely directly (Shapely 2.1+ with GEOS 3.12+), so region preprocessing
does not require PostgreSQL. Tiny source border mismatches are snapped to a
`1e-9` degree precision grid where needed; invalid coverage stops the run before
any files are written. Input files are never modified.

Optional arguments: `--source <path>`, `--output-dir <path>`, and `--tolerance <degrees>`.
Defaults resolve relative to the repository, so the script can run from any directory.

The API serves these files at `GET /api/countries/{country_code}/regions`.
The world map fetches regions only after a country is selected, focuses on that
country, and clears the region layer when returning to the world view. Countries
without region files display a message. Rebuild/restart the API container after
generating data when using Docker, since processed files are copied into its image.

## World map preprocessing benchmark

Compare the local country source with the generated country dataset:

```powershell
cd web
npm run test:map-performance
```

This opt-in test requires `data/raw/wbAdmin0.geojson`,
`data/processed/countries.geojson`, and installed frontend dependencies. It reads
existing files without running preprocessing or connecting to PostgreSQL. Paths
resolve from the repository root, regardless of the working directory.

The table compares three datasets: the original source, an unsimplified source
with the same fields as the processed output, and the processed output. The
matched-fields baseline helps separate geometry simplification from metadata
removal and JSON formatting. Both inputs must use EPSG:4326 coordinates.

It measures UTF-8 and estimated gzip sizes, coordinate counts, JSON parsing,
the production winding-normalization function, and D3 SVG path generation with
the world map's Equal Earth projection and dimensions. One warmup per dataset
precedes five measured rounds; dataset order alternates, and reported timings
are medians. The JSON report retains individual samples and machine details.

```powershell
npm run test:map-performance -- --iterations 9 --output .demo-checks/map-comparison.json
```

Override inputs with `--raw <path>` and `--processed <path>`. The default report
is `.demo-checks/world-map-performance.json` (ignored by Git). The test fails if
country codes/names or feature counts change, or if preprocessing fails to reduce
vertices, matched-field payload sizes, and generated SVG path characters. It
does not enforce timing thresholds, which vary by machine and background load.

These are Node computation measurements, not browser load times or FPS. Disk
reads, network transfer, React updates, DOM insertion, and browser painting are
excluded. Gzip size does not imply that the API currently enables compression.
The benchmark checks closed rings and finite coordinates/paths; visual fidelity
and topological validity still require separate checks. It covers the initial
world view; region loading after country selection is a separate workload.

## Tests

Run backend tests from the project root:

```bash
pytest
```

If `pytest` is not available, reinstall dependencies in the active environment:

```bash
pip install -r requirements.txt
```

## Docker

Start Docker Desktop and ensure Ollama is running on Windows. In PowerShell from the project root:

```powershell
ollama pull tinyllama
docker compose up --build -d
Get-Content migrations/001_recipe_metadata.sql | docker compose exec -T db psql -U postgres -d nextwork -v ON_ERROR_STOP=1
docker compose exec -T api python seed_demo.py
docker compose ps
```

If Ollama is not already running, start `ollama serve` in a separate terminal.
The API container connects to it at `http://host.docker.internal:11434`.
The demo seed can be run repeatedly; it preserves existing records.
The migration adds recipe metadata columns for older PostgreSQL volumes and is safe to repeat.

Services:

- `db`: PostgreSQL database on `localhost:5432`
- `api`: FastAPI backend on `http://localhost:8000`
- `web`: React frontend on `http://localhost:5173`

Open the frontend, inspect Recipe Book and Pantry, then ask "How do I make spinach rice?" in Ask.
Recipes and pantry entries saved in the frontend persist in PostgreSQL.
API documentation is available at `http://localhost:8000/docs`.

```powershell
# Follow logs
docker compose logs -f api web
# Stop the demo, keeping PostgreSQL data
docker compose stop
# Start it again
docker compose up -d
```

## Current Status

The frontend reads and saves recipes and pantry entries through the API. The Docker demo uses PostgreSQL for persistent data and host Ollama for question answering.
