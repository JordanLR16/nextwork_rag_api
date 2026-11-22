# Web UI

## Run

1. Install dependencies:
   `npm install`
2. Copy env file:
   `copy .env.example .env`
3. Start dev server:
   `npm run dev`

## Environment

- `VITE_API_BASE_URL`: Backend URL, default `http://localhost:8000`
- `VITE_COGNITO_REGION`: Cognito region
- `VITE_COGNITO_USER_POOL_ID`: User pool ID
- `VITE_COGNITO_CLIENT_ID`: Public SPA app client ID (no client secret)
- `VITE_COGNITO_DOMAIN`: Managed-login domain URL

The supplied example uses the Recidex development pool. Register
`http://localhost:5173/auth/callback` as a Cognito callback and
`http://localhost:5173/` as a sign-out URL. See
[the authentication guide](../docs/authentication.md) for backend configuration,
fresh database setup, and full setup. Private pages require sign-in. Tokens
stay in memory, so refreshing the page requires choosing Sign in again.
