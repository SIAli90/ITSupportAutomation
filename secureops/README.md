# SecureOps — IT Asset & Incident Management System

A full-stack computer science portfolio project for an IT operations team. Track hardware assets, report and resolve incidents, review an audit trail, and control access using defined roles.

**Stack:** Python · FastAPI · SQLAlchemy · PostgreSQL / SQLite · TypeScript · React · Vite · Docker · GitHub Actions

> **Purpose:** An educational capstone-style project. It is not a formally assessed university capstone or production-ready incident response platform.

## Features

- **Authentication:** password-based sign-in, PBKDF2-HMAC-SHA256 hashing, short-lived JWTs stored only in browser memory.
- **Role-based access:** admin, analyst, and read-only viewer roles are enforced on the **server**, not merely hidden in the UI.
- **Asset inventory:** asset tags, device types, assignments, locations and lifecycle status.
- **Incident workflow:** severity levels, reporting, link to asset, assignments and open/investigating/resolved status.
- **Dashboard:** counters, recent incidents and activity feed.
- **Audit log:** who created or edited which record, plus the changed fields (no passwords or access tokens).
- **Automated tests:** API integration tests for authentication, RBAC, validation, user creation, incidents, inventory and auditing.
- **Responsive interface:** mobile-friendly React dashboard; no mock API data.
- **Deployment:** Docker Compose for PostgreSQL, FastAPI and Nginx serving the built React UI.

## Running with Docker (recommended)

**Requirements:** Docker Desktop / Docker Engine and Docker Compose.

1. Copy `.env.example` to `.env`.
2. Replace every `CHANGE_ME` placeholder with a unique secret. Generate a random JWT signing key using:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
   Use a real email address format and a strong password of at least 12 characters for the administrator. `DB_PASSWORD` should use URL-safe characters because it is embedded into the DB connection URL.
3. Start:
   ```bash
   docker compose up --build -d
   ```
4. Open **http://localhost:8080** and sign in with `ADMIN_EMAIL` and `ADMIN_PASSWORD`.
5. Optional: populate *fictional* demonstration data after the API starts:
   ```bash
   docker compose exec backend python -m app.seed_demo
   ```
6. Shut down (retains PostgreSQL volume): `docker compose down`.

**Please note:** In Docker Compose, the UI is deliberately available only on your own computer (`127.0.0.1:8080`). Do not publish this to the internet without additional hardening (see [architecture and security notes](docs/ARCHITECTURE.md)).

## Running locally without Docker

Use Python 3.11+ and Node.js 20+.

**Terminal 1 — API:**

```bash
cd backend
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Set the following environment variables in your terminal (PowerShell shown; replace values):

```powershell
$env:JWT_SECRET="use-a-long-unique-random-secret-with-at-least-32-characters"
$env:ADMIN_EMAIL="admin@example.com"
$env:ADMIN_PASSWORD="replace-with-a-strong-admin-password"
$env:DATABASE_URL="sqlite:///./secure_it_ops.db"
python -m uvicorn app.main:app --reload
```

**Terminal 2 — UI:**

```bash
cd frontend
npm install
npm run dev
```

Browse to **http://localhost:5173**. The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

Open API docs at **http://localhost:8000/docs**.

## API summary

| Method | Route | Permissions |
|---|---|---|
| `GET` | `/api/health` | Public |
| `POST` | `/api/auth/login` | Public |
| `GET` | `/api/auth/me` | Signed in |
| `GET` | `/api/dashboard` | Signed in |
| `GET` / `POST` | `/api/assets` | Everyone signed in / admin & analyst |
| `PATCH` | `/api/assets/{id}` | Admin & analyst |
| `GET` / `POST` | `/api/incidents` | Everyone signed in / admin & analyst |
| `PATCH` | `/api/incidents/{id}` | Admin & analyst |
| `GET` | `/api/audit` | Signed in |
| `GET` / `POST` | `/api/users` | Admin |

## Run the tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q tests
```

Tests use a new isolated in-memory SQLite database. CI also attempts a frontend production build on each push and pull request.

## Suggested demonstration

1. Sign in as the administrator; add an analyst and a viewer from **Team**.
2. Add a laptop and a server in **Assets**.
3. Report a high-severity incident linked to the laptop.
4. Update its status to **Investigating**, then **Resolved**.
5. Inspect the live dashboard and immutable-through-the-API audit history.
6. Sign in as a viewer and demonstrate that the UI hides edit actions and the API returns HTTP 403 for modifications.

## Project structure

```text
secure-it-ops/
├── backend/
│   ├── app/            # FastAPI application, RBAC, data models, optional demo seed
│   ├── tests/          # Integration and security tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/            # React + TypeScript interface
│   ├── nginx.conf
│   └── Dockerfile
├── docs/ARCHITECTURE.md
├── .github/workflows/ci.yml
├── docker-compose.yml
├── .env.example
└── README.md
```

## Skills demonstrated

**Software engineering:** layered application architecture, REST APIs, strict validation, automated testing, responsive design.

**Computer science:** relational modelling, transactions, security controls, state transitions, indexing, filtering, authentication flows.

**DevOps:** containerisation, CI, environment configuration and reproducible deployment.

## Future improvements

- PostgreSQL migrations with Alembic, CLI database restore and backup tasks.
- SSO + MFA, password reset, lockout and login throttling.
- More robust audit storage, correlation IDs, richer incident history and attachments.
- Exportable reports, extended filters, accessibility audits and end-to-end tests.
- Real system observability and structured logs with OpenTelemetry.

## Licence

MIT — see [LICENSE](LICENSE).
