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
- `VITE_ADD_API_KEY`: Optional API key sent as `X-API-Key` for `/add`
