# IdentityHub

A web application for managing **Non-Human Identity (NHI)** security findings as Jira tickets.
Authenticate via email/password or Google OAuth, connect a Jira account through OAuth 2.0 (3LO),
create and track tickets, and expose a REST API for scanners and CI/CD pipelines.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 · APScheduler |
| **AI / LLM** | Ollama (local, OpenAI-compatible API) |
| **Database** | PostgreSQL 16 |
| **Frontend** | React 19 · TypeScript · Vite · Tailwind CSS · shadcn/ui |
| **Data Fetching** | TanStack Query v5 · Axios |
| **Forms** | React Hook Form · Zod |
| **Routing** | React Router v7 |
| **Testing** | pytest · Vitest · React Testing Library · MSW |
| **Infrastructure** | Docker · Docker Compose · nginx |

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Ollama](https://ollama.com/) (for Blog Digest) — install and pull the model: `ollama pull llama3.2`

### 1. Clone and configure

```bash
git clone <your-repo-url> && cd IdentityHub
cp .env.example .env
```

Edit `.env` and fill in the required values — see [Environment Variables](#environment-variables).

### 2. Start

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| DB Admin (Adminer) | http://localhost:8080 |
| PostgreSQL | `localhost:5433` |

> **DB Admin:** Open Adminer at http://localhost:8080 — log in with System **PostgreSQL**, Server `db`, Username `ihub`, Password from your `.env`, Database `identityhub`.

### 3. Verify

Open http://localhost:3000 in your browser.

---

## Environment Variables

Copy `.env.example` → `.env` and configure the values below.

### Database

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_PASSWORD` | PostgreSQL password for the `ihub` user | `changeme` |
| `DATABASE_URL` | Async connection string | `postgresql+asyncpg://ihub:<DB_PASSWORD>@db:5432/identityhub` |

### App Security

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | 64-char hex string for JWT signing. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |

### Jira OAuth 2.0 (3LO)

| Variable | Description | Default |
|----------|-------------|---------|
| `JIRA_ENCRYPTION_KEY` | Fernet key for encrypting Jira tokens at rest. Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` | — |
| `JIRA_CLIENT_ID` | OAuth client ID from your [Atlassian developer app](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/) | — |
| `JIRA_CLIENT_SECRET` | OAuth client secret | — |
| `JIRA_REDIRECT_URI` | Callback URL registered in the Atlassian app | `http://localhost:8000/jira/auth/callback` |

### Google OAuth 2.0

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `VITE_GOOGLE_CLIENT_ID` | Same value as `GOOGLE_CLIENT_ID` (used by the frontend) |

> **Note:** `GOOGLE_CLIENT_ID` and `VITE_GOOGLE_CLIENT_ID` must match — the frontend initiates the OAuth flow and the backend verifies the token.

<details>
<summary><strong>How to set up Google OAuth credentials</strong></summary>

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or select an existing one).
3. Navigate to **APIs & Services → OAuth consent screen**.
   - Choose **External** user type.
   - Fill in the required fields (app name, support email, developer contact).
   - Add scopes: `email`, `profile`, `openid`.
   - Under **Test users**, add the email addresses of anyone who needs to log in (required while the app is in "Testing" mode).
4. Navigate to **APIs & Services → Credentials**.
5. Click **+ CREATE CREDENTIALS → OAuth client ID**.
   - Application type: **Web application**
   - **Authorized JavaScript origins**: `http://localhost:5173`, `http://localhost:8000`
   - **Authorized redirect URIs**: `http://localhost:8000/auth/google/callback`
6. Copy the **Client ID** and **Client Secret** into your `.env`:

```
GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<your-client-secret>
VITE_GOOGLE_CLIENT_ID=<your-client-id>.apps.googleusercontent.com
```

7. Restart: `docker compose down && docker compose up --build`

</details>

### Blog Digest

Uses a local [Ollama](https://ollama.com/) instance via the OpenAI-compatible API — no external API key required.

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_BASE_URL` | Ollama API endpoint. **When running in Docker**, use `http://host.docker.internal:11434/v1` so the container can reach the host. | `http://localhost:11434/v1` |
| `LLM_MODEL` | Model for summarization | `llama3.2` |
| `BLOG_DIGEST_PROJECT_KEY` | Jira project key for digest tickets | `SEC` |
| `BLOG_DIGEST_USER_EMAIL` | Email of the user whose Jira connection is used by the **scheduled** job. Not needed for manual triggers from the UI. | — |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000` |

---

## Features

### Authentication
- Email/password registration and login (bcrypt).
- Google OAuth 2.0 social login.
- JWT sessions — access token (15 min) + refresh token (7 days, HttpOnly cookie) with silent refresh.

### Jira Integration
- Per-user Jira connection via OAuth 2.0 (3LO) with automatic token refresh.
- Jira tokens encrypted at rest with Fernet (AES-128-CBC + HMAC-SHA256).
- Browse projects and issue types.

### Ticket Management
- Create NHI finding tickets from the UI — select project, issue type, summary, and description.
- View recent tickets with project filtering.
- Tickets mirrored locally for fast retrieval.

### API Keys
- Generate API keys for programmatic access (`ihub_live_<hex>`).
- Raw key shown once at creation; stored as SHA-256 hash.
- List active keys (prefix only) and revoke.

### External REST API
- `POST /api/v1/tickets` — create tickets from scanners, CI/CD, or any external tool.
- Authenticated via `X-API-Key` header; rate limited to 20 req/min per key.

### Blog Digest
- **Manual trigger** from the UI — scrapes the latest [oasis.security blog](https://oasis.security/blog) post, generates an AI summary via Ollama, and creates a Jira ticket.
- **Scheduled job** — configurable cron schedule (default: daily 09:00 UTC), manageable from the Blog Digest settings page.
- Schedule can be updated at runtime (hour, minute, timezone, enable/disable) without restarting the backend.
- Uses a local Ollama LLM — no external API keys required.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Frontend (React SPA)                │
│        Vite · TypeScript · Tailwind · shadcn/ui      │
│              nginx reverse proxy (:3000)             │
└───────────────────────┬─────────────────────────────┘
                        │ REST / JSON
┌───────────────────────▼─────────────────────────────┐
│                   Backend (FastAPI)                   │
│    Routers ─► Services ─► Models / Schemas           │
│    Auth · Jira · API Keys · External · Blog Digest   │
│                 Rate Limiting · CORS                 │
│                       (:8000)                        │
└───────────────────────┬─────────────────────────────┘
                        │ SQLAlchemy (async)
┌───────────────────────▼─────────────────────────────┐
│                PostgreSQL 16 (:5432)                  │
│    users · jira_connections · api_keys · tickets     │
│    Fernet-encrypted tokens · bcrypt hashes           │
└─────────────────────────────────────────────────────┘
```

**Backend layers:** Routers (HTTP) → Services (business logic) → Models (ORM) → Schemas (Pydantic validation), wired together via FastAPI `Depends()`.

---

## API Endpoints

| Group | Endpoints |
|-------|-----------|
| **Auth** | `POST /auth/register` · `POST /auth/login` · `POST /auth/google` · `POST /auth/refresh` · `GET /auth/me` · `POST /auth/logout` |
| **Jira** | `GET /jira/auth/url` · `GET /jira/auth/callback` · `GET /jira/status` · `DELETE /jira/connection` · `GET /jira/projects` · `GET /jira/projects/{key}/issue-types` · `POST /jira/tickets` · `GET /jira/tickets` |
| **API Keys** | `POST /api-keys` · `GET /api-keys` · `DELETE /api-keys/{id}` |
| **Blog Digest** | `POST /blog-digest/trigger` · `GET /blog-digest/schedule` · `PUT /blog-digest/schedule` |
| **External** | `POST /api/v1/tickets` |
| **Health** | `GET /health` |

Full interactive docs: [Swagger UI](http://localhost:8000/docs) · [ReDoc](http://localhost:8000/redoc)

---

## Security

| Concern | Implementation |
|---------|---------------|
| Passwords | Bcrypt (12 rounds, unique salt) |
| Jira tokens | Fernet encryption at rest; decrypted in memory only |
| API keys | SHA-256 hashed; raw key shown once |
| JWT | HS256; access 15 min (in-memory), refresh 7 days (HttpOnly cookie) |
| OAuth CSRF | `state` parameter on Jira and Google callbacks |
| CORS | Restricted to the frontend origin |
| Rate limiting | 60 req/min per user; 20 req/min per API key |
| SQL injection | Parameterized queries via SQLAlchemy ORM |
| Secrets | `.env` file, excluded from version control |

---

## Running Tests

### Backend

```bash
docker compose exec backend pytest
```

Or locally:

```bash
cd backend && pip install -r requirements.txt && pytest
```

### Frontend

```bash
cd frontend && npm install && npm test
```

Coverage report:

```bash
npm run test:coverage
```

---

## Project Structure

```
IdentityHub/
├── backend/
│   ├── app/
│   │   ├── auth/          # JWT, bcrypt, Google OAuth
│   │   ├── jira/          # Jira OAuth 2.0, tickets, encryption
│   │   ├── api_keys/      # API key generation and hashing
│   │   ├── external/      # External REST API (X-API-Key)
│   │   ├── blog_digest/   # Blog scraping, LLM summary, scheduling, UI API
│   │   └── main.py        # FastAPI entry point
│   ├── alembic/           # Database migrations
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/           # Axios API modules
│   │   ├── components/    # shadcn/ui components
│   │   ├── features/      # Feature modules (auth, jira, api-keys, blog-digest)
│   │   │   └── */         #   components/, hooks/ per feature
│   │   ├── layouts/       # AppShell, AuthLayout
│   │   ├── pages/         # Route pages
│   │   ├── providers/     # AuthProvider, QueryProvider
│   │   ├── lib/           # Utilities, query keys, error helpers
│   │   └── test/          # Vitest setup, MSW mocks
│   ├── Dockerfile
│   └── package.json
├── docs/                  # Design documents (HLD)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Design Documents

| Document | Description |
|----------|-------------|
| [`docs/backend_hld.md`](docs/backend_hld.md) | Backend API contracts, service architecture, security model |
| [`docs/frontend_hld.md`](docs/frontend_hld.md) | Component hierarchy, state management, routing, UX flows |
| [`docs/db_hld.md`](docs/db_hld.md) | Database schema, relationships, encryption strategy |
| [`docs/blog_digest_ui_hld.md`](docs/blog_digest_ui_hld.md) | Blog Digest UI feature — API endpoints, frontend components, schedule management |
| [`docs/execution_plan.md`](docs/execution_plan.md) | Master execution plan — all tasks across 5 phases |
| [`docs/blog_digest_ui_execution_plan.md`](docs/blog_digest_ui_execution_plan.md) | Blog Digest UI execution plan — 11 tasks across 5 phases |
