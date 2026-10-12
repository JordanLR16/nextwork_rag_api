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

Start the full stack with Docker Compose:

```bash
docker compose up --build
```

Services:

- `db`: PostgreSQL database on `localhost:5432`
- `api`: FastAPI backend on `http://localhost:8000`
- `web`: React frontend on `http://localhost:5173`

## Current Status

The backend API, database models, Docker setup, and core tests are in place. The frontend includes the main application views and is being connected to the structured recipe and pantry endpoints. The next polish pass is to replace remaining sample frontend data with live API calls.
