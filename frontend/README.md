# Bank AI Platform — React frontend

Single-page React app (Vite) for the Bank AI Platform: log in with the
banking API's local demo user, list and create accounts, view balances and
transaction history, deposit, withdraw, transfer, and ask the AI assistant.

## Run it

```bash
cd frontend
npm install
npm run dev        # serves on http://localhost:5173
```

The banking service must be running on `http://localhost:8080` and the AI
service on `http://localhost:8081` (see the project README). To point at
other URLs, set Vite env vars before starting:

```bash
VITE_BANKING_URL=http://localhost:8080 VITE_AI_URL=http://localhost:8081 npm run dev
```

Production build: `npm run build` (output in `dist/`), served with
`npm run preview` or the `Dockerfile` in this directory (nginx).

## Login

The login form is prefilled with the banking API's local demo user
(`demo` / `demo123`). This is a LOCAL DEMO ONLY — see the project README
section "Demo auth". Credentials are kept in the browser's localStorage so
the demo survives a page reload; log out clears them. Nothing here is a
real credential.
