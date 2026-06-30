# nextwork_rag_api

FastAPI + Postgres + Ollama RAG backend with a React/Vite frontend.

## Project Structure

- `app.py`: FastAPI API (`/health`, `/query`, `/recipes`, `/pantry`)
- `database.py`: SQLAlchemy models and database session management
- `embed.py`: seed helper to add example data into the database
- `web/`: React frontend
- `tests/`: backend API tests

## Local Setup

Use Python `3.11` for the smoothest setup.

1. Create and activate a Python virtual environment.
2. Install backend dependencies:
   `pip install -r requirements.txt`
3. Copy backend env file:
   `copy .env.example .env`
4. Start the backend:
   `uvicorn app:app --reload --host 0.0.0.0 --port 8000`

Frontend:

1. `cd web`
2. `npm install`
3. `copy .env.example .env`
4. `npm run dev`

## Environment Variables (Backend)

- `DATABASE_URL`: SQLAlchemy database URL (default `sqlite:///./db/app.db`)
- `MODEL_NAME`: Ollama model (default `tinyllama`)
- `OLLAMA_HOST`: Optional Ollama host URL
- `ADD_API_KEY`: Optional key to protect write endpoints
- `CORS_ORIGINS`: comma-separated origins
- `SEED_FILE`: source file path for `embed.py`

## Database Setup

### Option 1: Local SQLite (default)

The backend will use SQLite by default when `DATABASE_URL` is unset.

### Option 2: PostgreSQL

Set `DATABASE_URL` in your `.env` or environment:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nextwork
```

If you want to use Docker Compose, the package includes a Postgres service.

## Seed Data

Run `python embed.py` to import recipes or pantry items from the file configured by `SEED_FILE`.

## Tests

Run `pytest` from the project root.

## Docker

Use Docker Compose:

```bash
docker compose up --build
```

Services:

- `db`: PostgreSQL database
- `api`: FastAPI backend on `http://localhost:8000`
- `web`: frontend on `http://localhost:5173`
