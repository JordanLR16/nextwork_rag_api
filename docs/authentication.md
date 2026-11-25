# Cognito authentication and personal knowledge bases

The development pool is `recidex-users-dev` (`us-east-1_hD6WcEfVv`). Its public
app client ID is `7fkm3q2c1aas8ol6dctvpjnaji` and its login domain is
`https://us-east-1hd6wcefvv.auth.us-east-1.amazoncognito.com`.
These are public identifiers, not AWS credentials. Use a separate pool for production.

## Cognito console settings

Configure the app client as a single-page application/public client with no secret:

- Identity provider: Cognito user pool.
- OAuth flow: authorization code grant only; the frontend library adds PKCE and state validation.
- Scopes: `openid`, `email`. The app does not request the optional `profile` scope.
- Allowed callback URL: `http://localhost:5173/auth/callback`.
- Allowed sign-out URL: `http://localhost:5173/`.
- Email sign-in, self-service registration, and email verification enabled.
- Configure a domain and managed-login branding for the app client.
- Recommended initial access token validity: 15 minutes.

Use `http://localhost:5173` consistently. If you use another origin, register its
exact callback and sign-out URLs in Cognito and allow the origin in backend CORS.
Production URLs must use HTTPS. AWS IAM keys are not needed to verify tokens.

## Start locally

From the repository root, install dependencies in your virtual environment:

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
Copy-Item web/.env.example web/.env
```

Only copy the examples if those local files do not exist; preserve existing
database/model settings otherwise. The examples contain the development identifiers.

Start the API against an empty database. Startup creates the current user, recipe,
and pantry tables from the SQLAlchemy models:

```powershell
uvicorn backend.app.main:app --env-file .env --reload --host 0.0.0.0 --port 8000
```

This pre-production project recreates outdated development databases instead of
upgrading them. There are no schema migration scripts or Alembic dependency.
Existing tables are not modified by `create_all`; deleting rows alone does not
update their schema. See the reset instructions below if you have an old database.

In another terminal:

```powershell
cd web
npm install
npm run dev
```

Open `http://localhost:5173`, choose Sign in, register, verify your email, and sign in.
The callback exchanges the authorization code once and removes it from the URL.
Private pages require login; the map and health endpoint remain public.

## Start with Docker

```powershell
docker compose up --build -d
```

The API creates its tables in an empty PostgreSQL database. If an existing volume
has an outdated schema, stop the stack and follow the reset instructions below.

## Reset an outdated development database

These optional commands discard local development data. Run them only when you
intend to start over. Resetting the application database does not delete Cognito
accounts; after signing in again, the API recreates the local user record.

For default SQLite, stop the API and run from the repository root:

```powershell
Remove-Item -LiteralPath .\db\app.db
```

This path applies to the default `sqlite:///./db/app.db` configuration. If you use
a different `DATABASE_URL`, reset only that selected development database. Restart
the API to create empty tables with the current schema.

For the Compose PostgreSQL database, run from the repository root:

```powershell
docker compose down --volumes
docker compose up --build -d
```

`down --volumes` removes this Compose project's volumes, including `postgres_data`
and all database contents. The next startup creates a fresh database. If you also
keep other data in that volume, it is discarded too. No reset runs automatically.

## Ownership and demo data

FastAPI verifies access-token signatures with cached Cognito JWKS keys, pins RS256,
and checks issuer, expiration, issued-at time, client ID, subject, and `token_use=access`.
It rejects ID tokens. Missing configuration fails closed; the old shared API key no
longer authenticates any user endpoint.

The first authenticated API request creates a local user from the verified issuer
and subject. The local ID is stable and independent of email or recipe author name.
`GET /auth/me` returns this local ID; it is also available from a signed-in browser
request using the shared API client. The API does not store passwords or tokens.

Every recipe/pantry write sets ownership on the server. Lists and RAG searches filter
by owner before ordering and limiting. The supplied owner field in JSON is ignored;
the authenticated user always owns the new record. Imported candidates must go
through the same owned save workflow if an import endpoint is added later.

Each user starts with an empty knowledge base. Add recipes and pantry entries
through the UI, or seed examples after signing in and obtaining your local user ID:

```powershell
python -m backend.app.cli.seed_demo --owner-id YOUR_LOCAL_USER_ID
```

Use the same database environment for the API and these commands. In Docker, run
the commands through `docker compose exec api`. Seeding creates separate IDs per
owner, can be repeated, and preserves existing edits.

## Sessions and limits

Tokens stay in browser memory. Session storage holds only the pending login
transaction. Reloading the page requires choosing Sign in again; Cognito may reuse
its existing login cookie. The client renews tokens while the page remains open.
Sign-out clears private React state, attempts refresh-token revocation, and redirects
through Cognito logout to clear the managed-login session.

JWT signature validation does not detect Cognito revocation immediately. A copied
access token can work until expiration. Use short access-token lifetimes; immediate
revocation would require an additional server-side session/revocation design.
Setting the local user's `is_active` to false blocks subsequent API requests immediately.

This integration does not add API rate limiting. Configure rate limits and production
email delivery (typically SES) before opening registration broadly.

## Verification

Backend tests exercise signed RSA JWTs, invalid tokens, disabled users, two-user
list/retrieval isolation, ownership spoofing, and repeatable per-user demo seeding.
Frontend tests cover callback handling, token attachment, and authentication failures.
They do not contact AWS. Manually verify signup, email confirmation, login, token
renewal, and logout against the configured pool, then repeat with a second user.
