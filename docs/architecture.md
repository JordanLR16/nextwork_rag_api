# Backend architecture

The backend is a layered FastAPI application in `backend/app`. Run commands from
the repository root. The frontend and geographic preprocessing scripts remain
in `web/` and `data/scripts/`.

## Responsibilities

```text
HTTP route -> service -> repository -> SQLAlchemy model/database
                 |
                 +-> injected Ollama generator
```

| Location | Responsibility |
| --- | --- |
| `main.py` | Build the app, register routers, manage startup and shutdown |
| `config.py` | Read environment settings at application construction |
| `dependencies.py` | Provide app settings, request sessions, authentication, and generation |
| `api/` | Validate HTTP requests, translate errors, return responses/files |
| `schemas/` | Pydantic input and import-result structures |
| `models/` | SQLAlchemy table definitions |
| `db/` | Lazy engine/session creation, connectivity retry, schema initialization |
| `repositories/` | SQL ranking, CRUD operations, JSON storage mapping |
| `services/` | Context selection/formatting, answer orchestration, write transactions |
| `integrations/` | External Ollama calls and Instagram content extraction |
| `cli/` | Command-line composition for demo data |

Services and repositories do not import FastAPI. The HTTP layer decides status
codes. Geography routes directly validate file paths and return file responses;
they do not need empty service/repository wrappers.

Recipe and pantry services accept Pydantic input schemas as application inputs.
There is no separate domain entity hierarchy for these simple CRUD workflows.

## App and database lifecycle

`create_app(settings=None, database=None)` creates an independent application.
Explicit settings and database objects can be supplied by tests or other callers.
Each app owns its settings and database resources; imports do not create engines,
directories, or database connections. Engines are created lazily on first use.

FastAPI lifespan initializes the database and disposes its engine on shutdown,
including failed startup. The request dependency opens and closes one session.
In-memory SQLite uses a shared connection pool so TestClient's request thread
sees the schema created during startup.

The table names, columns, JSON-in-text encoding, routes, response bodies, and
existing status codes are preserved. `create_all` creates missing tables; it
does not update columns in existing tables. Apply SQL changes from
`backend/migrations/` to existing deployments as documented in the README.
Introducing a migration framework is a separate schema-management change.

## Transactions

Repositories add records and run queries without committing. Recipe and pantry
write services own commit/rollback. If an operation grows to include several
writes, its service should coordinate them in one transaction. Avoid calling
several independently committing services when atomicity is required.

The seed command is a separate transaction coordinator. It reuses repository
mapping while inserting explicit demo IDs, commits the batch, and rolls back on
failure. Repeated runs preserve existing records and user edits.

## Retrieval and model generation

Retrieval currently uses SQL keyword matching, not embeddings. The query service
extracts terms, asks repositories for ranked recipes and remaining pantry slots,
formats context, and skips generation when nothing matches. SQL remains in the
repositories. A generator callable is injected through `get_generator`, allowing
tests to avoid model requests without patching the application module.

The Ollama integration owns SDK calls, model options, and host configuration.
The query route preserves the existing RuntimeError-to-503 behavior; other
unexpected query failures return a generic 500.

## Instagram imports

The former root `importer/` package now lives under
`backend/app/integrations/importers/`, with lowercase module names. Import result
models live in `schemas/imports.py`. Importers return candidates and metadata;
they do not commit database records or produce HTTP responses.

When adding an import endpoint, coordinate selection, extraction, and validation
in an import service. Keep saving a recipe as an explicit step so a future UI can
preview and edit candidates. Extract shared text parsing when a second importer
needs it; no import endpoint or new persistence behavior is introduced here.

## Development and verification

```powershell
uvicorn backend.app.main:app --env-file .env --reload
python -m backend.app.cli.seed_demo
python -m pytest -q
```

CLI commands read exported environment variables. The server command explicitly
loads `.env`. The root `app.py` remains a small compatibility entry point for
`uvicorn app:app`; application code should import `backend.app` modules directly.

Tests live in `backend/tests/`, discovered via `pyproject.toml`. Every API test
gets fresh settings, an in-memory database, and an overridden model dependency.
The real startup/shutdown lifecycle runs in tests. Existing API assertions cover
recipe/pantry persistence, authentication, retrieval, errors, and map responses.
Additional checks cover failed-write rollback, isolated app instances, relative
SQLite paths, repeatable seeding, and Ollama configuration without network calls.

CI runs backend tests, frontend tests, and the frontend build. The real-data map
benchmark stays opt-in because its large source inputs are not in Git. It still
uses the same data paths and production winding-normalization function.

For a new feature, add input schemas and routes, put orchestration in a service,
and add repository operations only where persistence is needed. Preserve public
API contracts in integration tests and exercise transaction boundaries against
a real test database. PostgreSQL deployment checks remain separate from the
fast SQLite suite.
