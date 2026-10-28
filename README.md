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
|-- embed.py               # Seed/import helper for recipe and pantry data
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
| `SEED_FILE` | Source file path for seed/import data | `./k8s.txt` |

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

Run the import helper from the project root:

```bash
python embed.py
```

`embed.py` supports JSON recipe/pantry objects and plain-text files. Plain text is imported as a recipe-style knowledge item.

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
