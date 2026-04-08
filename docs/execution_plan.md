# IdentityHub — Master Execution Plan

> **Generated from:** `docs/db_hld.md`, `docs/backend_hld.md`, `docs/frontend_hld.md`
>
> **Usage:** Check off tasks (`- [x]`) as they are completed. Each task includes a ready-to-copy **Agent Prompt** for Cursor.

---

## Phase 1: Database Setup & Models

> **Source:** `docs/db_hld.md` — all tasks in this phase reference that document exclusively.
>
> **Goal:** Stand up PostgreSQL via Docker, define all SQLAlchemy models, configure Alembic, and run the initial migration.

---

### 1.1 — Project Scaffolding & Docker Compose

- [ ] **Task 1.1: Create root project scaffolding and Docker Compose file**

  **Target Files:**
  - `docker-compose.yml` (create)
  - `.env.example` (create)
  - `.env` (create — gitignored)
  - `.gitignore` (create)
  - `backend/` (create directory)
  - `frontend/` (create directory)

  **Agent Prompt:**
  > Create the root project scaffolding for IdentityHub. Refer to `docs/backend_hld.md` → Section 11 (Deployment & DevEx) for the Docker Compose structure.
  >
  > 1. Create a `docker-compose.yml` with three services:
  >    - `db`: PostgreSQL 16-alpine with `POSTGRES_DB=identityhub`, `POSTGRES_USER=ihub`, `POSTGRES_PASSWORD=${DB_PASSWORD}`, port 5432, and a named volume `pgdata`.
  >    - `backend`: builds from `./backend`, port 8000, depends on `db`, uses `env_file: .env`.
  >    - `frontend`: builds from `./frontend`, port 3000, depends on `backend`.
  > 2. Create `.env.example` with all environment variables referenced across the three HLD docs:
  >    ```
  >    DB_PASSWORD=changeme
  >    DATABASE_URL=postgresql+asyncpg://ihub:changeme@db:5432/identityhub
  >    SECRET_KEY=<generate-a-random-64-char-hex>
  >    JIRA_ENCRYPTION_KEY=<base64-encoded-32-bytes>
  >    JIRA_CLIENT_ID=
  >    JIRA_CLIENT_SECRET=
  >    JIRA_REDIRECT_URI=http://localhost:8000/jira/auth/callback
  >    GOOGLE_CLIENT_ID=
  >    GOOGLE_CLIENT_SECRET=
  >    LLM_BASE_URL=http://localhost:11434/v1
  >    LLM_MODEL=llama3.2
  >    BLOG_DIGEST_PROJECT_KEY=SEC
  >    BLOG_DIGEST_USER_EMAIL=
  >    VITE_API_BASE_URL=http://localhost:8000
  >    VITE_GOOGLE_CLIENT_ID=
  >    ```
  > 3. Copy `.env.example` to `.env`.
  > 4. Create `.gitignore` with entries for: `.env`, `__pycache__/`, `*.pyc`, `node_modules/`, `dist/`, `.venv/`, `pgdata/`, `.pytest_cache/`.
  > 5. Create empty `backend/` and `frontend/` directories (just a `.gitkeep` in each for now).

  **Acceptance Criteria:**
  - `docker-compose.yml` is valid YAML and defines all three services with correct dependencies.
  - `.env.example` contains every env var referenced in the HLDs.
  - `.gitignore` covers Python, Node, env files, and Postgres data.

---

### 1.2 — Backend Python Project Bootstrap

- [ ] **Task 1.2: Create backend Python project with requirements.txt and Dockerfile**

  **Target Files:**
  - `backend/requirements.txt` (create)
  - `backend/Dockerfile` (create)
  - `backend/app/__init__.py` (create)
  - `backend/app/config.py` (create)

  **Agent Prompt:**
  > Bootstrap the backend Python project for IdentityHub. Refer to `docs/backend_hld.md` → Section 3 (Technology Choices) and Section 4 (Backend Folder Structure) for dependencies and layout, and Section 11 for the Dockerfile.
  >
  > 1. Create `backend/requirements.txt` with latest stable versions of:
  >    - `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`
  >    - `python-jose[cryptography]`, `passlib[bcrypt]`, `bcrypt`
  >    - `cryptography` (for Fernet encryption)
  >    - `httpx` (async HTTP client)
  >    - `pydantic-settings` (for config)
  >    - `slowapi` (rate limiting)
  >    - `apscheduler` (blog digest scheduler)
  >    - `python-multipart` (form data support)
  >    - `openai` (Ollama-compatible LLM client)
  >    - `beautifulsoup4`, `lxml` (blog scraping)
  >    - `pytest`, `pytest-asyncio`, `httpx` (testing)
  >
  > 2. Create `backend/Dockerfile`:
  >    ```dockerfile
  >    FROM python:3.12-slim
  >    WORKDIR /app
  >    COPY requirements.txt .
  >    RUN pip install --no-cache-dir -r requirements.txt
  >    COPY . .
  >    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
  >    ```
  >
  > 3. Create `backend/app/__init__.py` (empty).
  >
  > 4. Create `backend/app/config.py` using Pydantic Settings per `docs/backend_hld.md` → Section 4:
  >    - `DATABASE_URL`, `SECRET_KEY`, `JIRA_ENCRYPTION_KEY`
  >    - `JIRA_CLIENT_ID`, `JIRA_CLIENT_SECRET`, `JIRA_REDIRECT_URI`
  >    - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
  >    - `LLM_BASE_URL` (default `http://localhost:11434/v1`), `LLM_MODEL` (default `llama3.2`)
  >    - `BLOG_DIGEST_PROJECT_KEY` (default "SEC"), `BLOG_DIGEST_USER_EMAIL` (optional)
  >    - `ACCESS_TOKEN_EXPIRE_MINUTES` (default 15), `REFRESH_TOKEN_EXPIRE_DAYS` (default 7)
  >    - Export a singleton `settings = Settings()`.

  **Acceptance Criteria:**
  - `requirements.txt` has all deps from the HLD with no version conflicts.
  - `Dockerfile` builds successfully.
  - `config.py` loads all env vars and provides sensible defaults.

---

### 1.3 — SQLAlchemy Base & `users` Model

- [ ] **Task 1.3: Create SQLAlchemy declarative base and `users` model**

  **Target Files:**
  - `backend/app/models/__init__.py` (create)
  - `backend/app/models/base.py` (create)
  - `backend/app/models/user.py` (create)

  **Agent Prompt:**
  > Create the SQLAlchemy model layer for IdentityHub. Refer to `docs/db_hld.md` → Section 3.1 (`users` table definition) for the exact schema, and Section 2 (ER Diagram) for relationships.
  >
  > 1. Create `backend/app/models/base.py`:
  >    - Define a `Base` using `DeclarativeBase` from SQLAlchemy 2.0.
  >    - Use `mapped_column` style (not legacy Column).
  >
  > 2. Create `backend/app/models/user.py`:
  >    - Table name: `users`
  >    - Columns exactly as specified in `docs/db_hld.md` → Section 3.1:
  >      - `id`: UUID PK with `server_default=text("gen_random_uuid()")`
  >      - `email`: VARCHAR(255), unique, not null
  >      - `password_hash`: VARCHAR(255), nullable (null for Google-only users)
  >      - `full_name`: VARCHAR(255), not null
  >      - `auth_provider`: VARCHAR(20), not null, server_default `'local'`
  >      - `google_sub`: VARCHAR(255), unique, nullable
  >      - `created_at`: TIMESTAMPTZ, not null, server_default `now()`
  >      - `updated_at`: TIMESTAMPTZ, not null, server_default `now()`
  >    - Indexes as specified: `ix_users_email` (unique on email), `ix_users_google_sub` (unique on google_sub where not null).
  >    - Relationships: `jira_connection` (one-to-one, back_populates), `api_keys` (one-to-many), `tickets` (one-to-many).
  >
  > 3. Create `backend/app/models/__init__.py` that imports and re-exports all models.

  **Acceptance Criteria:**
  - `User` model has all columns, types, constraints, and indexes matching `docs/db_hld.md` Section 3.1.
  - Relationships are declared (even though target models don't exist yet — use string references).

---

### 1.4 — `jira_connections` Model

- [ ] **Task 1.4: Create `jira_connections` SQLAlchemy model**

  **Target Files:**
  - `backend/app/models/jira_connection.py` (create)
  - `backend/app/models/__init__.py` (update import)

  **Agent Prompt:**
  > Create the `JiraConnection` SQLAlchemy model. Refer to `docs/db_hld.md` → Section 3.2 (`jira_connections` table definition) for the exact schema and Section 5.1 for encryption details.
  >
  > Columns exactly as specified:
  > - `id`: UUID PK
  > - `user_id`: UUID, FK → `users.id`, unique, not null (one connection per user)
  > - `cloud_id`: VARCHAR(255), not null
  > - `site_url`: VARCHAR(255), not null
  > - `access_token_enc`: LargeBinary (BYTEA), not null — Fernet-encrypted access token
  > - `refresh_token_enc`: LargeBinary (BYTEA), not null — Fernet-encrypted refresh token
  > - `token_expires_at`: TIMESTAMPTZ, not null
  > - `created_at`: TIMESTAMPTZ, not null, server_default `now()`
  > - `updated_at`: TIMESTAMPTZ, not null, server_default `now()`
  >
  > Index: `ix_jira_connections_user_id` — unique on `user_id`.
  >
  > Relationship: `user` back_populates `jira_connection`, `tickets` (one-to-many).
  >
  > Update `backend/app/models/__init__.py` to import and re-export `JiraConnection`.

  **Acceptance Criteria:**
  - `JiraConnection` model matches `docs/db_hld.md` Section 3.2 exactly.
  - `access_token_enc` and `refresh_token_enc` are `LargeBinary` (maps to BYTEA).
  - FK to `users.id` with unique constraint enforces one-to-one.

---

### 1.5 — `api_keys` Model

- [ ] **Task 1.5: Create `api_keys` SQLAlchemy model**

  **Target Files:**
  - `backend/app/models/api_key.py` (create)
  - `backend/app/models/__init__.py` (update import)

  **Agent Prompt:**
  > Create the `ApiKey` SQLAlchemy model. Refer to `docs/db_hld.md` → Section 3.3 (`api_keys` table definition) for the schema and Section 5.2 for the hashing model.
  >
  > Columns exactly as specified:
  > - `id`: UUID PK
  > - `user_id`: UUID, FK → `users.id`, not null
  > - `name`: VARCHAR(100), not null — user-provided label
  > - `key_hash`: VARCHAR(64), unique, not null — SHA-256 hex digest
  > - `key_prefix`: VARCHAR(16), not null — first 12 chars for display
  > - `is_active`: Boolean, not null, default True — set to False on revocation (soft-delete)
  > - `last_used_at`: TIMESTAMPTZ, nullable — updated on each API call
  > - `created_at`: TIMESTAMPTZ, not null, server_default `now()`
  >
  > Indexes: `ix_api_keys_key_hash` (unique on `key_hash`), `ix_api_keys_user_id` (on `user_id`).
  >
  > Relationship: `user` back_populates `api_keys`.
  >
  > Update `backend/app/models/__init__.py` to import and re-export `ApiKey`.

  **Acceptance Criteria:**
  - `ApiKey` model matches `docs/db_hld.md` Section 3.3 exactly.
  - `is_active` defaults to True for soft-delete pattern.
  - `key_hash` has unique index for O(1) lookup during API auth.

---

### 1.6 — `tickets` Model

- [ ] **Task 1.6: Create `tickets` SQLAlchemy model**

  **Target Files:**
  - `backend/app/models/ticket.py` (create)
  - `backend/app/models/__init__.py` (update import)

  **Agent Prompt:**
  > Create the `Ticket` SQLAlchemy model. Refer to `docs/db_hld.md` → Section 3.4 (`tickets` table definition) for the schema, including the composite index and query pattern.
  >
  > Columns exactly as specified:
  > - `id`: UUID PK
  > - `user_id`: UUID, FK → `users.id`, not null
  > - `jira_connection_id`: UUID, FK → `jira_connections.id`, not null
  > - `jira_ticket_key`: VARCHAR(50), not null — e.g. "SEC-42"
  > - `jira_ticket_url`: VARCHAR(500), not null
  > - `project_key`: VARCHAR(20), not null
  > - `summary`: VARCHAR(255), not null
  > - `description`: Text, nullable
  > - `issue_type`: VARCHAR(50), not null, server_default `'Task'`
  > - `source`: VARCHAR(20), not null — "ui", "api", or "blog_digest"
  > - `created_at`: TIMESTAMPTZ, not null, server_default `now()`
  >
  > Indexes:
  > - `ix_tickets_project_key_created` — composite on `(project_key, created_at DESC)` — powers the "recent 10 tickets" query.
  > - `ix_tickets_user_id` — on `user_id`.
  >
  > Relationships: `user` back_populates `tickets`, `jira_connection` back_populates `tickets`.
  >
  > Update `backend/app/models/__init__.py` to import and re-export `Ticket`.

  **Acceptance Criteria:**
  - `Ticket` model matches `docs/db_hld.md` Section 3.4 exactly.
  - Composite index on `(project_key, created_at.desc())` is defined.
  - Both FKs (`user_id`, `jira_connection_id`) are present.

---

### 1.7 — Database Session & Dependencies

- [ ] **Task 1.7: Create async database session factory and FastAPI dependency**

  **Target Files:**
  - `backend/app/database.py` (create)
  - `backend/app/dependencies.py` (create)

  **Agent Prompt:**
  > Create the database connection layer. Refer to `docs/backend_hld.md` → Section 4.1 (Layer Responsibilities) for the dependency injection pattern, and `docs/db_hld.md` → Section 7 (Capacity Notes) for pool settings.
  >
  > 1. Create `backend/app/database.py`:
  >    - Create an `async_engine` using `create_async_engine` with the `DATABASE_URL` from `config.py`.
  >    - Create an `async_session_factory` using `async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)`.
  >    - Create an async generator function `get_db()` that yields an `AsyncSession` and properly closes it.
  >
  > 2. Create `backend/app/dependencies.py`:
  >    - Import and re-export `get_db` as a FastAPI dependency.
  >    - Create a placeholder `get_current_user` dependency (will be implemented in Phase 2 Auth tasks). For now it can raise `NotImplementedError`.

  **Acceptance Criteria:**
  - `get_db` is an async generator suitable for FastAPI `Depends()`.
  - The engine uses `asyncpg` driver via the `DATABASE_URL`.
  - `expire_on_commit=False` is set per async best practices.

---

### 1.8 — Alembic Configuration & Initial Migration

- [ ] **Task 1.8: Configure Alembic and create the initial migration**

  **Target Files:**
  - `backend/alembic.ini` (create)
  - `backend/alembic/env.py` (create)
  - `backend/alembic/script.py.mako` (create)
  - `backend/alembic/versions/` (create directory)

  **Agent Prompt:**
  > Set up Alembic for database migrations. Refer to `docs/db_hld.md` → Section 6 (Migration Strategy) for the configuration and folder structure, and Section 6.3 for the initial migration content (including the `update_updated_at` trigger).
  >
  > 1. Create `backend/alembic.ini`:
  >    - Set `script_location = alembic`.
  >    - Leave `sqlalchemy.url` empty (it will be read from `config.py` in `env.py`).
  >
  > 2. Create `backend/alembic/env.py`:
  >    - Import `settings` from `app.config` to get `DATABASE_URL`.
  >    - Import `Base` from `app.models.base` and all models from `app.models` so Alembic sees them.
  >    - Set `target_metadata = Base.metadata`.
  >    - Configure both `run_migrations_offline` and `run_migrations_online` (async version using `asyncpg`).
  >
  > 3. Create `backend/alembic/script.py.mako` (standard Alembic template).
  >
  > 4. The initial migration will be auto-generated in a later step after Docker is running. But structure the `versions/` directory with a `.gitkeep`.
  >
  > **Important from `docs/db_hld.md` Section 6.3:** The initial migration must also create:
  > - The `update_updated_at()` trigger function (PL/pgSQL).
  > - Triggers on `users` and `jira_connections` tables that call this function `BEFORE UPDATE`.
  >
  > Include these as raw SQL in the migration template or in `env.py`'s `run_migrations_online`.

  **Acceptance Criteria:**
  - `alembic.ini` points to the correct script location.
  - `env.py` reads the DB URL from app config, imports all models, and supports async migrations.
  - The migration structure is ready for `alembic revision --autogenerate`.

---

### 1.9 — FastAPI App Entry Point (Minimal)

- [ ] **Task 1.9: Create minimal FastAPI app with health endpoint and startup migration**

  **Target Files:**
  - `backend/app/main.py` (create)

  **Agent Prompt:**
  > Create the FastAPI application entry point. Refer to `docs/backend_hld.md` → Section 6.6 (Health Endpoint) and Section 10.2 (Swagger Configuration) for the app setup, and Section 11 for auto-migration on startup.
  >
  > 1. Create `backend/app/main.py`:
  >    - Instantiate FastAPI with `title="IdentityHub API"`, `description`, `version="1.0.0"`, `docs_url="/docs"`, `redoc_url="/redoc"`.
  >    - Add a lifespan context manager that:
  >      a. Runs `alembic upgrade head` on startup (via subprocess or alembic programmatic API).
  >      b. Yields (app runs).
  >      c. Disposes the engine on shutdown.
  >    - Add CORS middleware configured per `docs/backend_hld.md` → Section 7 (Security Design): allow origins = `["http://localhost:3000"]`, allow credentials, allow all methods and headers.
  >    - Implement `GET /health` that returns `{"status": "healthy", "version": "1.0.0", "database": "connected"}` after pinging the DB.
  >
  > Do NOT include any routers yet — those will be added in Phase 2.

  **Acceptance Criteria:**
  - `GET /health` returns 200 with the expected JSON.
  - CORS is configured for the frontend origin.
  - Alembic migrations run automatically on startup.
  - Swagger UI is available at `/docs`.

---

### 1.10 — Verify Database Setup End-to-End

- [ ] **Task 1.10: Boot Docker Compose and verify all 4 tables are created**

  **Target Files:**
  - No new files — validation only.

  **Agent Prompt:**
  > Verify the entire Phase 1 database setup works end-to-end.
  >
  > 1. Run `docker compose up --build` from the project root.
  > 2. Wait for the backend to start and Alembic migrations to run.
  > 3. Connect to the PostgreSQL container and verify:
  >    - All 4 tables exist: `users`, `jira_connections`, `api_keys`, `tickets`.
  >    - The `update_updated_at` trigger function exists.
  >    - Triggers are attached to `users` and `jira_connections`.
  >    - All indexes from `docs/db_hld.md` Sections 3.1–3.4 are present.
  > 4. Hit `GET http://localhost:8000/health` and verify it returns `{"status": "healthy", "version": "1.0.0", "database": "connected"}`.
  > 5. Hit `http://localhost:8000/docs` and verify Swagger UI loads.
  >
  > Fix any issues found.

  **Acceptance Criteria:**
  - Docker Compose starts all services without errors.
  - All 4 tables, their indexes, and triggers exist in PostgreSQL.
  - Health endpoint and Swagger UI both respond correctly.

---

## Phase 2: Python Backend API

> **Source:** `docs/backend_hld.md` — all tasks reference this document plus `docs/db_hld.md` for encryption/security details.
>
> **Goal:** Implement all API endpoints, services, and middleware described in the backend HLD.

---

### 2.1 — Auth Utilities (JWT & Password Hashing)

- [ ] **Task 2.1: Implement JWT creation/verification and password hashing utilities**

  **Target Files:**
  - `backend/app/auth/__init__.py` (create)
  - `backend/app/auth/utils.py` (create)

  **Agent Prompt:**
  > Implement the auth utility layer. Refer to `docs/backend_hld.md` → Section 5.1 (App Authentication) for the token strategy, and `docs/db_hld.md` → Section 5.3 (Passwords — Bcrypt) for hashing.
  >
  > Create `backend/app/auth/utils.py` with:
  >
  > 1. **Password hashing** (per `docs/db_hld.md` Section 5.3):
  >    - `hash_password(password: str) -> str` — uses bcrypt with rounds=12.
  >    - `verify_password(plain: str, hashed: str) -> bool` — uses `passlib` CryptContext with bcrypt.
  >
  > 2. **JWT token creation** (per `docs/backend_hld.md` Section 5.1):
  >    - `create_access_token(user_id: str, email: str) -> str` — HS256, expires in 15 min (from `settings.ACCESS_TOKEN_EXPIRE_MINUTES`). Include `sub` (user_id), `email`, `exp`, `type: "access"`.
  >    - `create_refresh_token(user_id: str) -> str` — HS256, expires in 7 days (from `settings.REFRESH_TOKEN_EXPIRE_DAYS`). Include `sub` (user_id), `exp`, `type: "refresh"`.
  >    - `decode_token(token: str) -> dict` — decodes and validates. Raises appropriate exceptions on expiry or invalid tokens.

  **Acceptance Criteria:**
  - bcrypt hashing uses 12 rounds per the HLD.
  - Access token expires in 15 min, refresh token in 7 days.
  - `decode_token` raises clear exceptions for expired/invalid tokens.
  - All functions use `settings.SECRET_KEY` for signing.

---

### 2.2 — Auth Schemas (Pydantic Models)

- [ ] **Task 2.2: Create Pydantic request/response schemas for auth endpoints**

  **Target Files:**
  - `backend/app/auth/schemas.py` (create)

  **Agent Prompt:**
  > Create all Pydantic schemas for the auth domain. Refer to `docs/backend_hld.md` → Section 6.2 (Auth Endpoints) for the exact request/response shapes.
  >
  > Define the following schemas in `backend/app/auth/schemas.py`:
  >
  > 1. **`RegisterRequest`** — `email` (EmailStr), `password` (str, min_length=8), `full_name` (str, min_length=1, max_length=255).
  > 2. **`LoginRequest`** — `email` (EmailStr), `password` (str).
  > 3. **`GoogleAuthRequest`** — `code` (str), `redirect_uri` (str).
  > 4. **`UserResponse`** — `id` (UUID), `email` (str), `full_name` (str), `auth_provider` (str). Use `model_config = ConfigDict(from_attributes=True)`.
  > 5. **`AuthResponse`** — `access_token` (str), `token_type` (str, default "bearer"), `user` (UserResponse).
  > 6. **`MessageResponse`** — `detail` (str).
  > 7. **`ErrorResponse`** — `detail` (str), `code` (str).
  >
  > Each schema must match the exact JSON shapes shown in `docs/backend_hld.md` Section 6.2.

  **Acceptance Criteria:**
  - All schemas match the API contract in the HLD.
  - Validation constraints (min_length, max_length, EmailStr) are applied.
  - `UserResponse` has `from_attributes=True` for ORM compatibility.

---

### 2.3 — Auth Service (Register, Login, Google)

- [ ] **Task 2.3: Implement AuthService and GoogleAuthService**

  **Target Files:**
  - `backend/app/auth/service.py` (create)

  **Agent Prompt:**
  > Implement the auth business logic. Refer to `docs/backend_hld.md` → Section 5.1 (App Authentication) for all three auth flows and Section 6.2 for the exact error codes/responses.
  >
  > Create `backend/app/auth/service.py` with two classes:
  >
  > **1. `AuthService`:**
  > - `async register(db, email, password, full_name) -> (User, access_token, refresh_token)`:
  >   - Normalize email to lowercase.
  >   - Check for duplicate email → raise `HTTPException(409)` with code `EMAIL_EXISTS`.
  >   - Hash password with bcrypt, create User with `auth_provider="local"`.
  >   - Return user + tokens.
  >
  > - `async login(db, email, password) -> (User, access_token, refresh_token)`:
  >   - Look up user by email, verify password.
  >   - On failure → raise `HTTPException(401)` with code `INVALID_CREDENTIALS`.
  >   - Return user + tokens.
  >
  > - `async refresh(db, refresh_token_str) -> (User, new_access_token, new_refresh_token)`:
  >   - Decode the refresh token, verify `type == "refresh"`.
  >   - Load the user from DB.
  >   - Return user + new token pair.
  >
  > **2. `GoogleAuthService`:**
  > - `async authenticate(db, code, redirect_uri) -> (User, access_token, refresh_token)`:
  >   - Exchange `code` for Google `id_token` via `httpx` (POST to `https://oauth2.googleapis.com/token`).
  >   - Extract `sub`, `email`, `name` from the id_token.
  >   - Find user by `google_sub` or by `email`:
  >     - If found by email but no `google_sub` → link accounts (set `google_sub`). Per `docs/db_hld.md` Section 3.1 design notes.
  >     - If not found → create new user with `auth_provider="google"`, `password_hash=None`.
  >   - Return user + tokens.

  **Acceptance Criteria:**
  - Registration rejects duplicate emails with `EMAIL_EXISTS`.
  - Login returns `INVALID_CREDENTIALS` on wrong password.
  - Google auth handles: new user, existing Google user, and account linking (existing email user adds Google).
  - All functions return both access and refresh tokens.

---

### 2.4 — Auth Router (All Endpoints)

- [ ] **Task 2.4: Create the auth router with all 6 endpoints**

  **Target Files:**
  - `backend/app/auth/router.py` (create)
  - `backend/app/main.py` (update — include router)
  - `backend/app/dependencies.py` (update — implement `get_current_user`)

  **Agent Prompt:**
  > Create the auth router with all endpoints. Refer to `docs/backend_hld.md` → Section 6.2 (Auth Endpoints) for all 6 endpoints and their exact contracts, and Section 10.2 for the Swagger tag `"Auth"`.
  >
  > 1. Create `backend/app/auth/router.py` with `APIRouter(prefix="/auth", tags=["Auth"])`:
  >
  >    - `POST /auth/register` → 201, returns `AuthResponse`. Set refresh token as HttpOnly cookie.
  >    - `POST /auth/login` → 200, returns `AuthResponse`. Set refresh token as HttpOnly cookie.
  >    - `POST /auth/google` → 200, returns `AuthResponse`. Set refresh token as HttpOnly cookie.
  >    - `POST /auth/refresh` → 200, returns `AuthResponse`. Read refresh token from HttpOnly cookie. Returns full user object per HLD.
  >    - `GET /auth/me` → 200, returns `UserResponse`. Requires `get_current_user` dependency.
  >    - `POST /auth/logout` → 200, returns `MessageResponse`. Clears the refresh token cookie.
  >
  > 2. Update `backend/app/dependencies.py`:
  >    - Implement `get_current_user`: extract Bearer token from `Authorization` header, decode it, load user from DB. Raise 401 with `NOT_AUTHENTICATED` on failure.
  >
  > 3. Update `backend/app/main.py`: include the auth router.
  >
  > **HttpOnly cookie settings for refresh token:**
  > - `httponly=True`, `secure=False` (dev), `samesite="lax"`, `path="/auth"`, `max_age=7*24*60*60`.

  **Acceptance Criteria:**
  - All 6 auth endpoints work per the HLD contract.
  - Refresh token is stored in HttpOnly cookie (not returned in JSON body).
  - Access token is returned in JSON body.
  - `GET /auth/me` requires and validates the Bearer token.
  - All endpoints appear under the "Auth" tag in Swagger.

---

### 2.5 — Jira Encryption Utility

- [ ] **Task 2.5: Implement Fernet encryption/decryption for Jira tokens**

  **Target Files:**
  - `backend/app/jira/__init__.py` (create)
  - `backend/app/jira/encryption.py` (create)

  **Agent Prompt:**
  > Implement the Fernet encryption utility for Jira tokens. Refer to `docs/db_hld.md` → Section 5.1 (Jira Tokens — Fernet Encryption) for the encryption design.
  >
  > Create `backend/app/jira/encryption.py`:
  > - `encrypt_token(plaintext: str) -> bytes` — encrypts using Fernet with key from `settings.JIRA_ENCRYPTION_KEY`.
  > - `decrypt_token(ciphertext: bytes) -> str` — decrypts and returns the plaintext string.
  >
  > The `JIRA_ENCRYPTION_KEY` is a base64-encoded 32-byte key. `cryptography.fernet.Fernet(key)` handles the rest.
  >
  > Tokens are decrypted in-memory only when making Jira API calls — they must never be logged or returned to the client.

  **Acceptance Criteria:**
  - `encrypt_token` produces bytes suitable for storing in a BYTEA column.
  - `decrypt_token` recovers the original plaintext.
  - Round-trip test: `decrypt_token(encrypt_token("test")) == "test"`.
  - Key is read from `settings.JIRA_ENCRYPTION_KEY`.

---

### 2.6 — Jira Schemas

- [ ] **Task 2.6: Create Pydantic schemas for Jira endpoints**

  **Target Files:**
  - `backend/app/jira/schemas.py` (create)

  **Agent Prompt:**
  > Create all Pydantic schemas for the Jira domain. Refer to `docs/backend_hld.md` → Section 6.3 (Jira Integration Endpoints) for the exact request/response shapes.
  >
  > Define in `backend/app/jira/schemas.py`:
  >
  > 1. **`AuthUrlResponse`** — `authorization_url` (str), `state` (str).
  > 2. **`JiraStatusResponse`** — `connected` (bool), `cloud_id` (str | None), `jira_site_url` (str | None).
  > 3. **`JiraProject`** — `id` (str), `key` (str), `name` (str), `avatar_url` (str | None).
  > 4. **`ProjectsResponse`** — `projects` (list[JiraProject]).
  > 5. **`JiraIssueType`** — `id` (str), `name` (str), `is_default` (bool).
  > 6. **`IssueTypesResponse`** — `issue_types` (list[JiraIssueType]).
  > 7. **`CreateTicketRequest`** — `project_key` (str), `summary` (str, max_length=255), `description` (str | None, max_length=32000), `issue_type` (str, default="Task").
  > 8. **`TicketCreatedBy`** — `id` (UUID), `full_name` (str).
  > 9. **`TicketResponse`** — `id` (UUID), `jira_ticket_key` (str), `jira_ticket_url` (str), `summary` (str), `issue_type` (str), `source` (str), `created_at` (datetime), `created_by` (TicketCreatedBy).
  > 10. **`TicketsListResponse`** — `tickets` (list[TicketResponse]).
  >
  > Note from `docs/backend_hld.md` Section 6.3 `POST /jira/tickets`: The response shape matches `GET /jira/tickets` exactly, enabling optimistic cache prepend on the frontend.

  **Acceptance Criteria:**
  - All schemas match the API contract in the HLD.
  - `CreateTicketRequest` validates `summary` max 255, `description` max 32000.
  - `TicketResponse` includes `created_by` with user info.
  - `POST` and `GET` ticket responses share the same `TicketResponse` schema.

---

### 2.7 — Jira Service (OAuth Flow, Token Refresh, API Calls)

- [ ] **Task 2.7: Implement JiraService with OAuth flow, token refresh, and Jira API calls**

  **Target Files:**
  - `backend/app/jira/service.py` (create)

  **Agent Prompt:**
  > Implement the JiraService. Refer to `docs/backend_hld.md` → Section 5.2 (Jira OAuth 2.0 3LO Flow) for the complete OAuth flow, Section 6.3 for endpoint behaviors, and `docs/db_hld.md` Section 5.1 for token encryption.
  >
  > Create `backend/app/jira/service.py` with class `JiraService`:
  >
  > 1. **`generate_auth_url(user_id: str) -> (authorization_url, state)`**:
  >    - Generate `state` = HMAC-sign(`user_id` + random nonce) using `settings.SECRET_KEY`.
  >    - Build Atlassian OAuth URL: `https://auth.atlassian.com/authorize` with params: `audience=api.atlassian.com`, `client_id`, `scope=read:jira-work write:jira-work offline_access`, `redirect_uri`, `state`, `response_type=code`, `prompt=consent`.
  >
  > 2. **`handle_callback(code: str, state: str, db: AsyncSession)`**:
  >    - Verify HMAC signature of `state`, extract `user_id`. Per Section 5.2: "The backend encodes the user_id and a random nonce into the OAuth state parameter using HMAC signing."
  >    - Exchange `code` for tokens via POST to `https://auth.atlassian.com/oauth/token`.
  >    - Fetch `cloud_id` from `https://api.atlassian.com/oauth/token/accessible-resources`.
  >    - Encrypt tokens using `encryption.encrypt_token()`.
  >    - Upsert into `jira_connections`.
  >
  > 3. **`get_status(user_id: str, db) -> JiraStatusResponse`**:
  >    - Per Section 6.3: always returns 200. `connected: true/false`.
  >
  > 4. **`get_projects(user_id: str, db) -> list[JiraProject]`**:
  >    - Decrypt token, call `GET /rest/api/3/project` on Jira Cloud.
  >    - Handle 401 → token refresh → retry (single retry pattern from Section 5.2).
  >
  > 5. **`get_issue_types(user_id: str, project_key: str, db) -> list[JiraIssueType]`**:
  >    - Call Jira API for project metadata, return issue types.
  >
  > 6. **`create_ticket(user_id: str, payload: CreateTicketRequest, source: str, db) -> TicketResponse`**:
  >    - Decrypt token, POST to Jira Cloud API to create the issue.
  >    - Record the ticket in the local `tickets` table with `source` = "ui" | "api" | "blog_digest".
  >    - Return the full `TicketResponse` shape.
  >
  > 7. **`get_recent_tickets(project_key: str, limit: int, db) -> list[TicketResponse]`**:
  >    - Query local `tickets` table per `docs/db_hld.md` Section 3.4 query pattern.
  >
  > 8. **`disconnect(user_id: str, db)`**:
  >    - Delete the `jira_connections` row for this user.
  >
  > 9. **`_refresh_token(connection: JiraConnection, db) -> str`** (private):
  >    - POST to `https://auth.atlassian.com/oauth/token` with `grant_type=refresh_token`.
  >    - Re-encrypt and persist new tokens.
  >
  > 10. **`_make_jira_request(method, url, connection, db, **kwargs)`** (private):
  >     - Makes an authenticated request. On 401 → calls `_refresh_token` → retries once.

  **Acceptance Criteria:**
  - OAuth state uses HMAC signing with user_id + nonce.
  - Token refresh is automatic on 401 with a single retry.
  - Tokens are encrypted before storage and decrypted only in-memory.
  - Tickets are recorded in the local DB with the correct `source` value.
  - `get_recent_tickets` queries by `project_key` ordered by `created_at DESC` with `LIMIT`.

---

### 2.8 — Jira Router

- [ ] **Task 2.8: Create the Jira router with all endpoints**

  **Target Files:**
  - `backend/app/jira/router.py` (create)
  - `backend/app/main.py` (update — include router)

  **Agent Prompt:**
  > Create the Jira router. Refer to `docs/backend_hld.md` → Section 6.3 (Jira Integration Endpoints) for all endpoints and Section 10.2 for the Swagger tag `"Jira"`.
  >
  > Create `backend/app/jira/router.py` with `APIRouter(prefix="/jira", tags=["Jira"])`:
  >
  > 1. `GET /jira/auth/url` → 200, returns `AuthUrlResponse`. Requires `get_current_user`.
  > 2. `GET /jira/auth/callback?code=...&state=...` → 302 redirect to `http://localhost:3000/jira/connected?status=success` or `?status=error&message=...`. This is called by Atlassian's redirect — NO auth header available. User is identified from the HMAC-signed `state` parameter.
  > 3. `GET /jira/status` → 200, returns `JiraStatusResponse`. Always 200 — `connected: true/false`.
  > 4. `DELETE /jira/connection` → 200, returns `MessageResponse`.
  > 5. `GET /jira/projects` → 200, returns `ProjectsResponse`. 403 if no Jira connection (`JIRA_NOT_CONNECTED`).
  > 6. `GET /jira/projects/{project_key}/issue-types` → 200, returns `IssueTypesResponse`.
  > 7. `POST /jira/tickets` → 201, returns `TicketResponse`. Sets `source="ui"`.
  > 8. `GET /jira/tickets?project_key=...&limit=10` → 200, returns `TicketsListResponse`.
  >
  > Update `backend/app/main.py` to include this router.
  >
  > **Error handling per Section 6.3:**
  > - 403 `JIRA_NOT_CONNECTED` when user has no Jira connection.
  > - 400 `JIRA_PROJECT_NOT_FOUND` for invalid project key.
  > - 502 `JIRA_API_ERROR` for upstream Jira failures.

  **Acceptance Criteria:**
  - All 8 Jira endpoints match the HLD contract.
  - `/jira/auth/callback` does NOT require Bearer auth (identifies user from state).
  - All other Jira endpoints require `get_current_user`.
  - Error codes match the HLD exactly.

---

### 2.9 — API Key Schemas & Service

- [ ] **Task 2.9: Implement API key schemas and service (generate, list, revoke)**

  **Target Files:**
  - `backend/app/api_keys/__init__.py` (create)
  - `backend/app/api_keys/schemas.py` (create)
  - `backend/app/api_keys/service.py` (create)

  **Agent Prompt:**
  > Implement the API key management domain. Refer to `docs/backend_hld.md` → Section 6.4 (API Key Management Endpoints) for the contract, and `docs/db_hld.md` → Section 3.3 (api_keys) and Section 5.2 (API Keys — One-Way Hashing) for the security model.
  >
  > 1. Create `backend/app/api_keys/schemas.py`:
  >    - `CreateApiKeyRequest` — `name` (str, min_length=1, max_length=100).
  >    - `ApiKeyCreatedResponse` — `id` (UUID), `name` (str), `key` (str), `created_at` (datetime). Note: raw key is returned ONLY here.
  >    - `ApiKeyListItem` — `id` (UUID), `name` (str), `key_prefix` (str), `created_at` (datetime), `last_used_at` (datetime | None).
  >    - `ApiKeysListResponse` — `api_keys` (list[ApiKeyListItem]).
  >
  > 2. Create `backend/app/api_keys/service.py` with class `ApiKeyService`:
  >    - `generate_key(user_id, name, db)`:
  >      - Generate raw key: `"ihub_live_" + 48 random hex chars` (per `docs/db_hld.md` Section 5.2).
  >      - Store SHA-256 hash in `key_hash`, first 12 chars in `key_prefix`.
  >      - Return the raw key exactly once.
  >    - `list_keys(user_id, db)`:
  >      - Return all keys where `is_active = True` (per `docs/db_hld.md` Section 3.3 soft-delete).
  >    - `revoke_key(user_id, key_id, db)`:
  >      - Set `is_active = False` (soft-delete, per `docs/db_hld.md` Section 3.3).
  >      - Verify the key belongs to the user.
  >    - `validate_api_key(raw_key, db) -> (ApiKey, User)`:
  >      - Hash the provided key, look up by `key_hash`.
  >      - If not found → raise with `INVALID_API_KEY`.
  >      - If found but `is_active = False` → raise with `API_KEY_REVOKED` (distinct error per Section 3.3).
  >      - Update `last_used_at`.
  >      - Return the key and its owning user.

  **Acceptance Criteria:**
  - Raw key format: `ihub_live_` + 48 hex chars.
  - Key is returned only once at creation time.
  - `validate_api_key` distinguishes between `INVALID_API_KEY` and `API_KEY_REVOKED`.
  - `list_keys` only returns active keys.
  - `revoke_key` does soft-delete (sets `is_active = False`).

---

### 2.10 — API Key Router

- [ ] **Task 2.10: Create the API key management router**

  **Target Files:**
  - `backend/app/api_keys/router.py` (create)
  - `backend/app/main.py` (update — include router)

  **Agent Prompt:**
  > Create the API key CRUD router. Refer to `docs/backend_hld.md` → Section 6.4 (API Key Management Endpoints) and Section 10.2 for the Swagger tag `"API Keys"`.
  >
  > Create `backend/app/api_keys/router.py` with `APIRouter(prefix="/api-keys", tags=["API Keys"])`:
  >
  > 1. `POST /api-keys` → 201, returns `ApiKeyCreatedResponse`. Requires `get_current_user`.
  > 2. `GET /api-keys` → 200, returns `ApiKeysListResponse`. Requires `get_current_user`.
  > 3. `DELETE /api-keys/{key_id}` → 200, returns `MessageResponse` `"API key revoked"`. Requires `get_current_user`.
  >
  > Update `backend/app/main.py` to include this router.

  **Acceptance Criteria:**
  - All 3 endpoints match the HLD contract.
  - All require Bearer auth.
  - POST returns the raw key only once.
  - DELETE performs soft-delete.

---

### 2.11 — External API Router (Programmatic Ticket Creation)

- [ ] **Task 2.11: Create the external API endpoint for programmatic ticket creation**

  **Target Files:**
  - `backend/app/external/__init__.py` (create)
  - `backend/app/external/schemas.py` (create)
  - `backend/app/external/router.py` (create)
  - `backend/app/main.py` (update — include router)

  **Agent Prompt:**
  > Implement the external-facing API for scanners and CI/CD systems. Refer to `docs/backend_hld.md` → Section 5.3 (External API Key Authentication) for the auth flow, Section 6.5 (External API Endpoint) for the contract, and Section 10.3 for the Swagger `X-API-Key` header configuration.
  >
  > 1. Create `backend/app/external/schemas.py`:
  >    - `ExternalCreateTicketRequest` — `project_key` (str), `summary` (str, max_length=255), `description` (str | None, max_length=32000), `issue_type` (str, default="Task").
  >    - `ExternalTicketResponse` — `jira_ticket_key` (str), `jira_ticket_url` (str), `summary` (str), `created_at` (datetime).
  >
  > 2. Create `backend/app/external/router.py` with `APIRouter(prefix="/api/v1", tags=["External API"])`:
  >    - `POST /api/v1/tickets` → 201, returns `ExternalTicketResponse`.
  >    - Auth: `X-API-Key` header → validate via `ApiKeyService.validate_api_key()`.
  >    - Load the key owner's Jira connection.
  >    - If no Jira connection → 403 `JIRA_NOT_CONNECTED`.
  >    - Create ticket via `JiraService.create_ticket()` with `source="api"`.
  >
  > 3. Configure the `APIKeyHeader` security scheme per Section 10.3:
  >    ```python
  >    external_api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
  >    ```
  >
  > 4. Update `backend/app/main.py` to include this router.
  >
  > **Error codes (per Section 6.5):**
  > - 401 `INVALID_API_KEY`, 401 `API_KEY_REVOKED`, 403 `JIRA_NOT_CONNECTED`, 422 `VALIDATION_ERROR`, 502 `JIRA_API_ERROR`.

  **Acceptance Criteria:**
  - `POST /api/v1/tickets` creates a ticket under the API key owner's Jira identity.
  - `X-API-Key` header is properly validated.
  - Distinct error codes for invalid vs. revoked keys.
  - Response includes `jira_ticket_key` and `jira_ticket_url`.

---

### 2.12 — Rate Limiting

- [ ] **Task 2.12: Add rate limiting with slowapi**

  **Target Files:**
  - `backend/app/main.py` (update)
  - `backend/app/external/router.py` (update)

  **Agent Prompt:**
  > Add rate limiting per `docs/backend_hld.md` → Section 7 (Security Design): "slowapi — 60 req/min per user on authenticated endpoints; 20 req/min per key on external API."
  >
  > 1. In `backend/app/main.py`:
  >    - Initialize `slowapi` Limiter with a key function based on user identity.
  >    - Add the `SlowAPIMiddleware` to the app.
  >    - Set default limit: 60/minute for authenticated endpoints.
  >
  > 2. In `backend/app/external/router.py`:
  >    - Apply a tighter limit of 20/minute per API key on `POST /api/v1/tickets`.
  >
  > 3. Ensure rate limit errors return `429` with `{"detail": "Rate limit exceeded. Try again later.", "code": "RATE_LIMITED"}` per Section 6.5.

  **Acceptance Criteria:**
  - Authenticated endpoints: 60 req/min per user.
  - External API: 20 req/min per API key.
  - 429 responses include the `RATE_LIMITED` code.

---

### 2.13 — Global Exception Handlers

- [ ] **Task 2.13: Implement global exception handlers**

  **Target Files:**
  - `backend/app/main.py` (update)

  **Agent Prompt:**
  > Implement the global exception handling strategy. Refer to `docs/backend_hld.md` → Section 8 (Error Handling Strategy) for the complete list.
  >
  > Add exception handlers in `backend/app/main.py` for:
  > 1. Pydantic `ValidationError` → 422 with field-level details, code `VALIDATION_ERROR`.
  > 2. Custom `JiraApiError` → 502 with upstream error message, code `JIRA_API_ERROR`.
  > 3. Custom `JiraNotConnectedError` → 403, code `JIRA_NOT_CONNECTED`.
  > 4. Custom `AuthenticationError` → 401.
  > 5. `RateLimitExceeded` (slowapi) → 429 with `RATE_LIMITED` code.
  > 6. Unhandled exceptions → 500 with generic "Internal server error" message (log details, never expose).
  >
  > Create a custom exceptions module at `backend/app/exceptions.py` with: `JiraApiError`, `JiraNotConnectedError`, `AuthenticationError`.
  >
  > All errors must return the consistent envelope: `{"detail": "...", "code": "..."}`.

  **Acceptance Criteria:**
  - All error responses follow the `{detail, code}` envelope.
  - Internal errors (500) never expose stack traces.
  - Each custom exception maps to its correct HTTP status code.

---

### 2.14 — Blog Digest Service (Bonus)

- [ ] **Task 2.14: Implement the NHI Blog Digest automation**

  **Target Files:**
  - `backend/app/blog_digest/__init__.py` (create)
  - `backend/app/blog_digest/service.py` (create)
  - `backend/app/blog_digest/scheduler.py` (create)
  - `backend/app/main.py` (update — start scheduler on lifespan)

  **Agent Prompt:**
  > Implement the Blog Digest bonus feature. Refer to `docs/backend_hld.md` → Section 9 (Bonus: NHI Blog Digest) for the complete flow.
  >
  > 1. Create `backend/app/blog_digest/service.py` with class `BlogDigestService`:
  >    - `scrape_latest_post()` → scrape `https://oasis.security/blog` for the most recent post URL and title using `httpx` + `beautifulsoup4`.
  >    - `generate_summary(post_content: str) -> str` → call the local Ollama LLM via the `openai` client (Ollama exposes an OpenAI-compatible API) with a prompt to produce a concise NHI-focused summary. Configuration:
  >      - `LLM_BASE_URL` (default `http://localhost:11434/v1`)
  >      - `LLM_MODEL` (default `llama3.2`)
  >      Use `openai.AsyncOpenAI(base_url=settings.LLM_BASE_URL, api_key="ollama")`.
  >    - `run_digest(db)`:
  >      a. Scrape latest post.
  >      b. Fetch post content and extract main text.
  >      c. Generate AI summary.
  >      d. Use the system user (configured via `BLOG_DIGEST_USER_EMAIL`) to create a Jira ticket:
  >         - Project: `settings.BLOG_DIGEST_PROJECT_KEY`.
  >         - Summary: `[NHI Blog Digest] {blog post title}`.
  >         - Description: AI-generated summary + link to original post.
  >         - Issue type: Task.
  >         - Source: `blog_digest`.
  >
  > 2. Create `backend/app/blog_digest/scheduler.py`:
  >    - Configure APScheduler with a cron job (default: daily at 09:00 UTC).
  >    - The job calls `BlogDigestService.run_digest()`.
  >
  > 3. Update `backend/app/main.py` lifespan:
  >    - Start the scheduler on startup.
  >    - Shut down the scheduler on shutdown.

  **Acceptance Criteria:**
  - Blog scraping fetches the latest post from oasis.security/blog.
  - LLM summary is generated via Ollama using the configured model (`llama3.2` by default).
  - Ticket is created under the system user's Jira connection.
  - Scheduler runs daily at 09:00 UTC by default.
  - Failures are logged but don't crash the app.

---

### 2.15 — Backend Test Infrastructure Setup

- [ ] **Task 2.15: Set up pytest test infrastructure with async test database**

  **Target Files:**
  - `backend/tests/__init__.py` (create)
  - `backend/tests/conftest.py` (create)
  - `backend/pytest.ini` (create)

  **Agent Prompt:**
  > Set up the foundational test infrastructure for the backend. Refer to `docs/backend_hld.md` → Section 4 (tests/ directory) and `docs/db_hld.md` for the schema.
  >
  > 1. Create `backend/pytest.ini`:
  >    - Set `asyncio_mode = auto`.
  >    - Set `testpaths = tests`.
  >
  > 2. Create `backend/tests/conftest.py` with:
  >    - A `test_engine` fixture using `create_async_engine` pointed at a **test** PostgreSQL database (`identityhub_test`). Use `DATABASE_URL` from env with `_test` suffix, or an in-memory SQLite fallback for CI.
  >    - A `db_session` fixture that:
  >      a. Creates all tables via `Base.metadata.create_all`.
  >      b. Yields an `AsyncSession`.
  >      c. Drops all tables on teardown for full isolation.
  >    - An `async_client` fixture using `httpx.AsyncClient` with the FastAPI `app` under `ASGITransport`, overriding the `get_db` dependency with the test session.
  >    - A `test_user` factory fixture that creates a user with hashed password in the test DB and returns the User object.
  >    - A `auth_headers` fixture that generates a valid JWT access token for the test user and returns `{"Authorization": "Bearer <token>"}`.
  >    - A `test_settings` fixture that patches `app.config.settings` with test-safe values (e.g., a test `SECRET_KEY`, a test `JIRA_ENCRYPTION_KEY`).
  >
  > 3. Add `pytest`, `pytest-asyncio`, `httpx`, `factory-boy` to `backend/requirements.txt` if not already present.

  **Acceptance Criteria:**
  - `pytest` discovers and runs async test functions.
  - Each test gets a clean database with fresh tables.
  - `async_client` can make HTTP requests against the FastAPI app.
  - `test_user` and `auth_headers` fixtures enable authenticated test requests.
  - Tests do not affect the production database.

---

### 2.16 — Backend Smoke Test

- [ ] **Task 2.16: Verify all backend endpoints via Swagger UI**

  **Target Files:**
  - No new files — validation only.

  **Agent Prompt:**
  > Perform end-to-end smoke testing of the backend API.
  >
  > 1. Run `docker compose up --build`.
  > 2. Open `http://localhost:8000/docs` — verify all endpoint groups appear: Auth, Jira, API Keys, External API, Health.
  > 3. Test the following flow manually in Swagger or via `curl`:
  >    a. `POST /auth/register` — create a user.
  >    b. `GET /auth/me` — verify the returned user data.
  >    c. `POST /auth/login` — login with the same user.
  >    d. `POST /auth/refresh` — refresh the token.
  >    e. `POST /api-keys` — create an API key, note the raw key.
  >    f. `GET /api-keys` — verify the key appears with prefix only.
  >    g. `DELETE /api-keys/{id}` — revoke the key.
  >    h. `GET /health` — verify healthy status.
  > 4. Verify all error responses follow the `{detail, code}` envelope.
  > 5. Run `pytest -v` in the `backend/` directory to verify the test infrastructure from Task 2.15 is working (even if no domain tests exist yet).
  >
  > Fix any issues found.

  **Acceptance Criteria:**
  - All endpoints respond with correct status codes and shapes.
  - Auth flow works: register → login → me → refresh → logout.
  - API key flow works: create → list → revoke.
  - Error responses are consistent.
  - `pytest` runs without import errors or configuration issues.

---

## Phase 3: React Frontend — Setup, Routing & State

> **Source:** `docs/frontend_hld.md` — all tasks reference this document.
>
> **Goal:** Scaffold the React app, implement routing, auth context, API layer, and all pages/components.
>
> **Gate:** Phase 2 must be complete (including Task 2.16 smoke test passing).

---

### 3.1 — Vite + React + TypeScript Scaffolding

- [ ] **Task 3.1: Create the React project with Vite and install all dependencies**

  **Target Files:**
  - `frontend/package.json` (create via `npm create vite`)
  - `frontend/tsconfig.json` (create)
  - `frontend/vite.config.ts` (create)
  - `frontend/tailwind.config.ts` (create)
  - `frontend/postcss.config.js` (create)
  - `frontend/src/index.css` (create)
  - `frontend/src/main.tsx` (create)
  - `frontend/.env.example` (create)
  - `frontend/Dockerfile` (create)

  **Agent Prompt:**
  > Scaffold the React frontend. Refer to `docs/frontend_hld.md` → Section 1.1 (Technology Choices) for the tech stack, Section 7 (Folder Structure) for the project layout, Section 11 (Environment Variables), and Section 12 (Deployment) for the Dockerfile.
  >
  > 1. Initialize a Vite + React + TypeScript project in the `frontend/` directory.
  > 2. Install all dependencies from Section 1.1:
  >    - `react-router-dom` (v6)
  >    - `@tanstack/react-query` (v5)
  >    - `axios`
  >    - `react-hook-form`, `@hookform/resolvers`, `zod`
  >    - `sonner` (toast notifications)
  >    - `lucide-react` (icons)
  >    - `tailwindcss`, `postcss`, `autoprefixer` (dev deps)
  >    - `clsx`, `tailwind-merge` (for `cn()` utility)
  > 3. Configure Tailwind CSS with the standard setup.
  > 4. Create `frontend/src/index.css` with Tailwind directives.
  > 5. Create `frontend/.env.example` per Section 11: `VITE_API_BASE_URL=http://localhost:8000`, `VITE_GOOGLE_CLIENT_ID=...`.
  > 6. Create `frontend/Dockerfile` per Section 12 (multi-stage build with nginx).
  > 7. Create `frontend/nginx.conf` per Section 12 — with the exact proxy rules and SPA fallback as specified.
  > 8. Set up the directory structure from Section 7 (create empty directories/files): `src/api/`, `src/components/ui/`, `src/features/`, `src/hooks/`, `src/layouts/`, `src/lib/`, `src/pages/`, `src/providers/`, `src/types/`.

  **Acceptance Criteria:**
  - `npm run dev` starts the Vite dev server on port 3000.
  - TypeScript compiles without errors.
  - Tailwind CSS is working (utility classes apply styles).
  - Folder structure matches `docs/frontend_hld.md` Section 7.

---

### 3.2 — shadcn/ui Setup & Base Components

- [ ] **Task 3.2: Initialize shadcn/ui and install required components**

  **Target Files:**
  - `frontend/components.json` (create via shadcn init)
  - `frontend/src/components/ui/*.tsx` (created by shadcn)
  - `frontend/src/lib/utils.ts` (create)

  **Agent Prompt:**
  > Set up shadcn/ui components. Refer to `docs/frontend_hld.md` → Section 1.1 (shadcn/ui: "Radix primitives + Tailwind — copy-paste ownership") and Section 4.2 for the component inventory.
  >
  > 1. Initialize shadcn/ui in the `frontend/` directory with the default configuration.
  > 2. Install the following shadcn components needed across the app:
  >    - `button`, `input`, `label`, `textarea`, `select`, `dialog`, `card`, `badge`
  >    - `dropdown-menu`, `command` (for combobox), `popover`, `separator`
  >    - `skeleton`, `table`, `toast` (sonner), `tooltip`, `avatar`
  > 3. Create `frontend/src/lib/utils.ts` with the `cn()` helper:
  >    ```typescript
  >    import { clsx, type ClassValue } from "clsx";
  >    import { twMerge } from "tailwind-merge";
  >    export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }
  >    ```

  **Acceptance Criteria:**
  - All shadcn components are installed and importable.
  - `cn()` utility works for conditional class merging.
  - No TypeScript errors.

---

### 3.3 — Shared Types

- [ ] **Task 3.3: Define shared TypeScript types**

  **Target Files:**
  - `frontend/src/types/index.ts` (create)

  **Agent Prompt:**
  > Define all shared TypeScript types. Refer to `docs/frontend_hld.md` → Section 7 (`types/` — "User, Ticket, ApiKey, JiraProject, etc.") and `docs/backend_hld.md` → Section 6 for the exact response shapes.
  >
  > Create `frontend/src/types/index.ts` with:
  >
  > ```typescript
  > export interface User {
  >   id: string;
  >   email: string;
  >   full_name: string;
  >   auth_provider: 'local' | 'google';
  > }
  >
  > export interface AuthResponse {
  >   access_token: string;
  >   token_type: string;
  >   user: User;
  > }
  >
  > export interface JiraStatus {
  >   connected: boolean;
  >   cloud_id?: string;
  >   jira_site_url?: string;
  > }
  >
  > export interface JiraProject {
  >   id: string;
  >   key: string;
  >   name: string;
  >   avatar_url?: string;
  > }
  >
  > export interface JiraIssueType {
  >   id: string;
  >   name: string;
  >   is_default: boolean;
  > }
  >
  > export interface TicketCreatedBy {
  >   id: string;
  >   full_name: string;
  > }
  >
  > export interface Ticket {
  >   id: string;
  >   jira_ticket_key: string;
  >   jira_ticket_url: string;
  >   summary: string;
  >   issue_type: string;
  >   source: 'ui' | 'api' | 'blog_digest';
  >   created_at: string;
  >   created_by: TicketCreatedBy;
  > }
  >
  > export interface ApiKey {
  >   id: string;
  >   name: string;
  >   key_prefix: string;
  >   created_at: string;
  >   last_used_at: string | null;
  > }
  >
  > export interface ApiKeyCreated {
  >   id: string;
  >   name: string;
  >   key: string;
  >   created_at: string;
  > }
  > ```

  **Acceptance Criteria:**
  - All types match the backend API response shapes from `docs/backend_hld.md` Section 6.
  - Types are exported and importable from `@/types`.

---

### 3.4 — Axios Client & Interceptors

- [ ] **Task 3.4: Create the Axios instance with auth interceptors**

  **Target Files:**
  - `frontend/src/api/client.ts` (create)

  **Agent Prompt:**
  > Create the configured Axios instance. Refer to `docs/frontend_hld.md` → Section 6.1 (Axios Instance) for the exact implementation including request and response interceptors.
  >
  > Create `frontend/src/api/client.ts` with:
  > 1. An Axios instance with `baseURL` from `import.meta.env.VITE_API_BASE_URL` and `withCredentials: true`.
  > 2. A **request interceptor** that attaches the access token from a module-level ref (not localStorage — per Section 5.2: "stored in memory, not localStorage for security").
  > 3. A **response interceptor** that on 401:
  >    - Attempts `POST /auth/refresh` (uses the HttpOnly cookie).
  >    - On success: updates the access token and user, retries the original request.
  >    - On failure: clears auth state, redirects to `/login`.
  >    - Prevents infinite loops with `_retry` flag.
  > 4. Export helper functions: `setAccessToken(token)`, `getAccessToken()`, `setUser(user)`, `clearAuth()` — these will be wired to AuthContext later.
  >
  > Implement exactly as shown in `docs/frontend_hld.md` Section 6.1.

  **Acceptance Criteria:**
  - Access token is stored in memory, NOT localStorage.
  - 401 triggers silent refresh using HttpOnly cookie.
  - Refresh failure redirects to `/login`.
  - No infinite retry loops.

---

### 3.5 — API Modules (Auth, Jira, API Keys)

- [ ] **Task 3.5: Create typed API modules for all backend domains**

  **Target Files:**
  - `frontend/src/api/authApi.ts` (create)
  - `frontend/src/api/jiraApi.ts` (create)
  - `frontend/src/api/apiKeysApi.ts` (create)

  **Agent Prompt:**
  > Create the API function modules. Refer to `docs/frontend_hld.md` → Section 6.2 (API Module Organization) for the file layout, and `docs/backend_hld.md` → Section 6 for all endpoint contracts.
  >
  > 1. `frontend/src/api/authApi.ts`:
  >    - `register(data: {email, password, full_name}) → AuthResponse`
  >    - `login(data: {email, password}) → AuthResponse`
  >    - `googleAuth(data: {code, redirect_uri}) → AuthResponse`
  >    - `refresh() → AuthResponse`
  >    - `getMe() → User`
  >    - `logout() → void`
  >
  > 2. `frontend/src/api/jiraApi.ts`:
  >    - `getAuthUrl() → {authorization_url, state}`
  >    - `getStatus() → JiraStatus`
  >    - `getProjects() → {projects: JiraProject[]}`
  >    - `getIssueTypes(projectKey) → {issue_types: JiraIssueType[]}`
  >    - `createTicket(payload) → Ticket`
  >    - `getRecentTickets(projectKey, limit?) → {tickets: Ticket[]}`
  >    - `disconnect() → {detail: string}`
  >
  > 3. `frontend/src/api/apiKeysApi.ts`:
  >    - `createKey(data: {name}) → ApiKeyCreated`
  >    - `listKeys() → {api_keys: ApiKey[]}`
  >    - `deleteKey(keyId) → {detail: string}`
  >
  > Each function uses the configured Axios instance from `client.ts` and is fully typed with the types from `src/types/`.

  **Acceptance Criteria:**
  - All API functions are typed with request and response types.
  - All functions use the shared Axios instance.
  - Endpoints match `docs/backend_hld.md` Section 6 exactly.

---

### 3.6 — Query Keys & Error Utilities

- [ ] **Task 3.6: Create query key factory and error handling utilities**

  **Target Files:**
  - `frontend/src/lib/queryKeys.ts` (create)
  - `frontend/src/lib/errors.ts` (create)

  **Agent Prompt:**
  > Create shared utilities. Refer to `docs/frontend_hld.md` → Section 5.4 (Query Keys Convention) and Section 6.4 (Error Handling) for the exact implementations.
  >
  > 1. Create `frontend/src/lib/queryKeys.ts` — implement the query key factory exactly as shown in Section 5.4:
  >    ```typescript
  >    export const queryKeys = {
  >      auth: { user: ['auth', 'user'] as const },
  >      jira: {
  >        status: ['jira', 'status'] as const,
  >        projects: ['jira', 'projects'] as const,
  >        issueTypes: (projectKey: string) => ['jira', 'issueTypes', projectKey] as const,
  >        tickets: (projectKey: string) => ['jira', 'tickets', projectKey] as const,
  >      },
  >      apiKeys: { list: ['apiKeys'] as const },
  >    } as const;
  >    ```
  >
  > 2. Create `frontend/src/lib/errors.ts` — implement `getErrorMessage()` and `getErrorCode()` exactly as shown in Section 6.4, handling: 429 (rate limit), `data.detail` (string or array), 502 (Jira unavailable), and fallback.

  **Acceptance Criteria:**
  - Query keys follow the factory pattern from the HLD.
  - `getErrorMessage` handles all error shapes from the backend.
  - `getErrorCode` extracts the machine-readable code for programmatic branching.

---

### 3.7 — Auth Provider (Context)

- [ ] **Task 3.7: Create AuthProvider and useAuth hook**

  **Target Files:**
  - `frontend/src/providers/AuthProvider.tsx` (create)

  **Agent Prompt:**
  > Create the AuthProvider. Refer to `docs/frontend_hld.md` → Section 5.2 (Auth Context) for the exact interface and behavior, and Section 6.1 for how it wires to the Axios interceptors.
  >
  > Create `frontend/src/providers/AuthProvider.tsx`:
  >
  > 1. Implement the `AuthContextValue` interface from Section 5.2:
  >    ```typescript
  >    interface AuthContextValue {
  >      user: User | null;
  >      accessToken: string | null;
  >      isLoading: boolean;
  >      login: (accessToken: string, user: User) => void;
  >      logout: () => Promise<void>;
  >    }
  >    ```
  >
  > 2. On mount, attempt silent refresh via `POST /auth/refresh` (HttpOnly cookie). Per Section 5.2: "The refresh response includes the full user object, so the frontend can restore both accessToken and user without a separate API call." If refresh fails, set `isLoading = false` and user remains null.
  >
  > 3. `login(token, user)` — stores token in memory (via `setAccessToken` from `client.ts`), sets `user` state.
  > 4. `logout()` — calls `POST /auth/logout`, clears state (via `clearAuth` from `client.ts`), redirects to `/login`.
  > 5. Wire `setAccessToken`, `setUser`, `clearAuth` from `client.ts` so the Axios interceptor stays in sync.
  >
  > Export `useAuth()` hook that reads from this context.

  **Acceptance Criteria:**
  - Silent refresh on mount restores both `accessToken` and `user`.
  - Access token is stored in memory only (not localStorage).
  - `logout` clears all state and redirects.
  - `isLoading` is true while checking initial auth state.

---

### 3.8 — Query Provider

- [ ] **Task 3.8: Create QueryClientProvider wrapper**

  **Target Files:**
  - `frontend/src/providers/QueryProvider.tsx` (create)

  **Agent Prompt:**
  > Create the TanStack Query provider. Refer to `docs/frontend_hld.md` → Section 5.3 (TanStack Query Configuration) for the exact settings.
  >
  > Create `frontend/src/providers/QueryProvider.tsx`:
  > - Instantiate `QueryClient` with the exact defaults from Section 5.3:
  >   ```typescript
  >   staleTime: 30_000,
  >   retry: 1,
  >   refetchOnWindowFocus: true,
  >   ```
  > - Wrap children in `<QueryClientProvider>`.

  **Acceptance Criteria:**
  - Query client uses 30s stale time, 1 retry, refetch on window focus.
  - Provider wraps the app correctly.

---

### 3.9 — Layouts (AppShell & AuthLayout)

- [ ] **Task 3.9: Create AppShell and AuthLayout layout components**

  **Target Files:**
  - `frontend/src/layouts/AppShell.tsx` (create)
  - `frontend/src/layouts/AuthLayout.tsx` (create)
  - `frontend/src/components/FullPageSpinner.tsx` (create)

  **Agent Prompt:**
  > Create the two layout components. Refer to `docs/frontend_hld.md` → Section 4.2 (Layout Components) for responsibilities and Section 9 (Wireframes) for the visual structure.
  >
  > 1. `frontend/src/layouts/AuthLayout.tsx`:
  >    - Centered card on a clean branded background. Wraps login/register pages.
  >    - Show the app logo/name at the top.
  >    - Renders `<Outlet />` for nested routes.
  >    - Per Section 4.2: "Centered card on a branded background."
  >
  > 2. `frontend/src/layouts/AppShell.tsx`:
  >    - Sidebar + topbar + content area. Wraps all protected pages.
  >    - Per Section 9.1 wireframe:
  >      - **Sidebar**: Navigation links for Dashboard, Settings > Jira, Settings > API Keys. Include a `JiraStatusBadge` showing connection status.
  >      - **Topbar**: App name "IdentityHub" on the left, user avatar/name + dropdown menu with logout on the right.
  >    - Renders `<Outlet />` for the page content area.
  >    - The sidebar should be collapsible per Section 4.2.
  >
  > 3. `frontend/src/components/FullPageSpinner.tsx`:
  >    - A centered loading spinner used during auth state resolution (referenced in Section 3.2 Route Guards).
  >
  > Use shadcn/ui components and Tailwind for styling. Make it look modern and polished.

  **Acceptance Criteria:**
  - `AuthLayout` centers content in a card with a professional look.
  - `AppShell` has a functional sidebar with nav links, topbar with user menu, and an outlet for pages.
  - `FullPageSpinner` renders a centered spinner.
  - Both layouts use `<Outlet />` for child routes.

---

### 3.10 — Router Setup & Route Guards

- [ ] **Task 3.10: Set up React Router with route guards**

  **Target Files:**
  - `frontend/src/App.tsx` (create/update)

  **Agent Prompt:**
  > Set up the router. Refer to `docs/frontend_hld.md` → Section 3 (Routing Map) for all routes, Section 3.1 (Route Table) for the exact path→component mapping, and Section 3.2 (Route Guards) for the `ProtectedRoute` and `PublicOnlyRoute` implementations.
  >
  > Create/update `frontend/src/App.tsx`:
  >
  > 1. Wrap the app in providers: `QueryProvider` → `AuthProvider` → `RouterProvider`.
  > 2. Define routes per Section 3.1:
  >
  >    | Path | Component | Layout | Guard |
  >    |------|-----------|--------|-------|
  >    | `/` | Redirect to `/dashboard` | — | — |
  >    | `/login` | `LoginPage` | `AuthLayout` | `PublicOnlyRoute` |
  >    | `/register` | `RegisterPage` | `AuthLayout` | `PublicOnlyRoute` |
  >    | `/auth/google/callback` | `GoogleCallbackPage` | `AuthLayout` | `PublicOnlyRoute` |
  >    | `/dashboard` | `DashboardPage` | `AppShell` | `ProtectedRoute` |
  >    | `/jira/connected` | `JiraCallbackPage` | `AppShell` | `ProtectedRoute` |
  >    | `/settings/jira` | `JiraSettingsPage` | `AppShell` | `ProtectedRoute` |
  >    | `/settings/api-keys` | `ApiKeysPage` | `AppShell` | `ProtectedRoute` |
  >
  > 3. Implement route guards per Section 3.2:
  >    - `ProtectedRoute`: if `isLoading` show `FullPageSpinner`, if no user redirect to `/login`.
  >    - `PublicOnlyRoute`: if `isLoading` show `FullPageSpinner`, if user redirect to `/dashboard`.
  >
  > Create placeholder page components (just returning the page name as text) so the router compiles.

  **Acceptance Criteria:**
  - All 8 routes from the HLD are configured.
  - Protected routes redirect unauthenticated users to `/login`.
  - Public routes redirect authenticated users to `/dashboard`.
  - `/` redirects to `/dashboard`.
  - `FullPageSpinner` shows while auth is loading.

---

### 3.11 — Login Page & Form

- [ ] **Task 3.11: Implement LoginPage with email/password and Google sign-in**

  **Target Files:**
  - `frontend/src/pages/LoginPage.tsx` (create/update)
  - `frontend/src/features/auth/components/LoginForm.tsx` (create)
  - `frontend/src/features/auth/components/GoogleSignInButton.tsx` (create)
  - `frontend/src/features/auth/hooks/useLogin.ts` (create)
  - `frontend/src/features/auth/hooks/useGoogleAuth.ts` (create)

  **Agent Prompt:**
  > Implement the login page. Refer to `docs/frontend_hld.md` → Section 8.1 (Login / Register UX flow) for the interaction flow, Section 10.1 for the form validation schema, and Section 6.4 for error code handling.
  >
  > 1. `LoginForm.tsx`:
  >    - Use React Hook Form + Zod with the `loginSchema` from Section 10.1.
  >    - Fields: email (input), password (input).
  >    - On submit: call `POST /auth/login`, then `auth.login(token, user)`, navigate to `/dashboard`.
  >    - On `INVALID_CREDENTIALS` error: show inline form error "Invalid email or password" (per Section 6.4 error handling table).
  >    - Link to `/register` at the bottom.
  >
  > 2. `GoogleSignInButton.tsx`:
  >    - Renders a "Sign in with Google" button.
  >    - On click: redirect to Google OAuth consent screen with `VITE_GOOGLE_CLIENT_ID`, scope `openid email profile`, `redirect_uri = origin + /auth/google/callback`.
  >
  > 3. `useLogin.ts`: TanStack Query mutation wrapping `authApi.login()`.
  >
  > 4. `LoginPage.tsx`: Composes `LoginForm` + `GoogleSignInButton` inside the `AuthLayout`.

  **Acceptance Criteria:**
  - Login form validates with Zod schema.
  - Successful login stores token, sets user, and navigates to dashboard.
  - `INVALID_CREDENTIALS` shows inline error.
  - Google sign-in button redirects to Google.

---

### 3.12 — Register Page & Form

- [ ] **Task 3.12: Implement RegisterPage with form validation**

  **Target Files:**
  - `frontend/src/pages/RegisterPage.tsx` (create/update)
  - `frontend/src/features/auth/components/RegisterForm.tsx` (create)
  - `frontend/src/features/auth/hooks/useRegister.ts` (create)

  **Agent Prompt:**
  > Implement the register page. Refer to `docs/frontend_hld.md` → Section 10.1 for the `registerSchema`, Section 8.1 for the flow, and Section 6.4 for error handling.
  >
  > 1. `RegisterForm.tsx`:
  >    - Use React Hook Form + Zod with the `registerSchema` from Section 10.1:
  >      - `email`: valid email
  >      - `password`: min 8 characters
  >      - `full_name`: min 1, max 255 characters
  >    - On submit: call `POST /auth/register`, then `auth.login(token, user)`, navigate to `/dashboard`.
  >    - On `EMAIL_EXISTS` error: show inline error "This email is already registered" on the email field (per Section 6.4).
  >    - Link to `/login` at the bottom.
  >
  > 2. `useRegister.ts`: TanStack Query mutation wrapping `authApi.register()`.
  >
  > 3. `RegisterPage.tsx`: Composes `RegisterForm` + `GoogleSignInButton` inside the `AuthLayout`.

  **Acceptance Criteria:**
  - All three fields validate per Zod schema.
  - `EMAIL_EXISTS` error shows inline on the email field.
  - Successful registration logs user in and redirects to dashboard.

---

### 3.13 — Google Callback Page

- [ ] **Task 3.13: Implement GoogleCallbackPage**

  **Target Files:**
  - `frontend/src/pages/GoogleCallbackPage.tsx` (create/update)

  **Agent Prompt:**
  > Implement the Google OAuth callback page. Refer to `docs/frontend_hld.md` → Section 4.2 (GoogleCallbackPage) and Section 8.1 for the flow.
  >
  > Create `frontend/src/pages/GoogleCallbackPage.tsx`:
  > 1. On mount, extract the `code` parameter from the URL query string.
  > 2. Call `POST /auth/google` with `{code, redirect_uri: window.location.origin + '/auth/google/callback'}`.
  > 3. On success: `auth.login(token, user)`, navigate to `/dashboard`.
  > 4. If the response includes an `ACCOUNT_LINKED` code, show an info toast: "Your Google account has been linked to your existing account" (per Section 6.4).
  > 5. On error: show an error toast and redirect to `/login`.
  > 6. While loading, show a spinner with "Signing in with Google...".

  **Acceptance Criteria:**
  - Extracts code from URL, exchanges it for a session.
  - Shows `ACCOUNT_LINKED` toast when applicable.
  - Redirects to dashboard on success, login on failure.

---

### 3.14 — Jira Hooks (Status, Projects, Issue Types, Tickets)

- [ ] **Task 3.14: Create all Jira-related TanStack Query hooks**

  **Target Files:**
  - `frontend/src/features/jira/hooks/useJiraStatus.ts` (create)
  - `frontend/src/features/jira/hooks/useProjects.ts` (create)
  - `frontend/src/features/jira/hooks/useIssueTypes.ts` (create)
  - `frontend/src/features/jira/hooks/useRecentTickets.ts` (create)
  - `frontend/src/features/jira/hooks/useCreateTicket.ts` (create)
  - `frontend/src/features/jira/types.ts` (create)

  **Agent Prompt:**
  > Create all Jira query/mutation hooks. Refer to `docs/frontend_hld.md` → Section 5.1 (State Management Strategy) for the hook list, Section 6.3 for the `useCreateTicket` implementation with optimistic updates, and Section 5.4 for query keys.
  >
  > 1. `useJiraStatus()` — `useQuery` wrapping `jiraApi.getStatus()`, key: `queryKeys.jira.status`.
  > 2. `useProjects()` — `useQuery` wrapping `jiraApi.getProjects()`, key: `queryKeys.jira.projects`. Only enabled when Jira is connected.
  > 3. `useIssueTypes(projectKey)` — `useQuery` wrapping `jiraApi.getIssueTypes(projectKey)`, key: `queryKeys.jira.issueTypes(projectKey)`. Only enabled when `projectKey` is truthy.
  > 4. `useRecentTickets(projectKey)` — `useQuery` wrapping `jiraApi.getRecentTickets(projectKey)`, key: `queryKeys.jira.tickets(projectKey)`. Only enabled when `projectKey` is truthy.
  > 5. `useCreateTicket(projectKey)` — `useMutation` wrapping `jiraApi.createTicket()` with the exact optimistic update logic from Section 6.3:
  >    - `onSuccess`: prepend new ticket to cache, show success toast.
  >    - `onError`: if `JIRA_PROJECT_NOT_FOUND`, invalidate projects query. Show error toast.

  **Acceptance Criteria:**
  - All hooks use the correct query keys from the factory.
  - `useCreateTicket` performs optimistic cache updates on success.
  - Queries are conditionally enabled based on prerequisites.
  - Error handling matches Section 6.4.

---

### 3.15 — Dashboard Page (Project Selector, Ticket Form, Recent Tickets)

- [ ] **Task 3.15: Implement the DashboardPage with all feature components**

  **Target Files:**
  - `frontend/src/pages/DashboardPage.tsx` (create/update)
  - `frontend/src/features/jira/components/ProjectCombobox.tsx` (create)
  - `frontend/src/features/jira/components/CreateTicketForm.tsx` (create)
  - `frontend/src/features/jira/components/IssueTypeSelect.tsx` (create)
  - `frontend/src/features/jira/components/RecentTicketsList.tsx` (create)
  - `frontend/src/features/jira/components/TicketCard.tsx` (create)

  **Agent Prompt:**
  > Implement the dashboard page — the main screen of the app. Refer to `docs/frontend_hld.md` → Section 9.1 (Dashboard Wireframe) for the layout, Section 4.2 (Feature Components) for each component's behavior, Section 8.3 (Create Ticket flow) for the interaction sequence, Section 10.2 for form validation, and Section 6.5 for loading/empty states.
  >
  > 1. **`DashboardPage.tsx`**:
  >    - If Jira is not connected (from `useJiraStatus`), show a "Connect Jira" CTA instead of the form (per Section 6.4 `JIRA_NOT_CONNECTED` handling).
  >    - If connected: show `ProjectCombobox` at top, `CreateTicketForm` below it, `RecentTicketsList` at the bottom.
  >    - Track `selectedProjectKey` in local state.
  >
  > 2. **`ProjectCombobox.tsx`**:
  >    - Per Section 4.2: "Searchable dropdown populated from `GET /jira/projects`. Emits `onSelect(projectKey)`."
  >    - Use shadcn `Command` + `Popover` for the combobox pattern.
  >    - Show project key and name. Show avatar if available.
  >
  > 3. **`CreateTicketForm.tsx`**:
  >    - Per Section 4.2: React Hook Form with fields: summary, description, issue type dropdown.
  >    - Validation schema from Section 10.2: summary required (max 255), description optional (max 32000), issue_type defaults to "Task".
  >    - Submit via `useCreateTicket` mutation.
  >    - Per Section 8.3: show loading spinner on button, reset form on success, show toast.
  >
  > 4. **`IssueTypeSelect.tsx`**:
  >    - Per Section 4.2: "Dropdown fetched per selected project. Pre-selects the `is_default: true` option."
  >
  > 5. **`RecentTicketsList.tsx`**:
  >    - Per Section 4.2: "Renders up to 10 tickets. Each ticket is a clickable card that opens `jira_ticket_url` in a new tab."
  >    - Show a subtle `source` badge when `source !== "ui"` (e.g., "via API").
  >    - Handle loading (skeletons), error (retry button), and empty states per Section 6.5.
  >
  > 6. **`TicketCard.tsx`**:
  >    - Show ticket key, summary, creation time, source badge.
  >    - Clickable → opens `jira_ticket_url` in new tab.

  **Acceptance Criteria:**
  - Dashboard matches the wireframe from Section 9.1.
  - Project selector is searchable.
  - Ticket form validates, submits, resets, and shows toast.
  - Recent tickets list shows up to 10 items with correct source badges.
  - Loading/error/empty states are handled per Section 6.5.

---

### 3.16 — Jira Settings Page

- [ ] **Task 3.16: Implement JiraSettingsPage (connect/disconnect Jira)**

  **Target Files:**
  - `frontend/src/pages/JiraSettingsPage.tsx` (create/update)
  - `frontend/src/features/jira/components/JiraStatusCard.tsx` (create)
  - `frontend/src/features/jira/components/ConnectJiraButton.tsx` (create)
  - `frontend/src/features/jira/components/DisconnectJiraButton.tsx` (create)

  **Agent Prompt:**
  > Implement the Jira settings page. Refer to `docs/frontend_hld.md` → Section 4.2 (JiraSettingsPage, JiraStatusCard, ConnectJiraButton, DisconnectJiraButton) and Section 8.2 (Jira OAuth Connection flow).
  >
  > 1. **`JiraSettingsPage.tsx`**: Composes `JiraStatusCard`, `ConnectJiraButton` (when disconnected), `DisconnectJiraButton` (when connected).
  >
  > 2. **`JiraStatusCard.tsx`**: Per Section 4.2: "Shows connected site URL or 'Not connected' with connect CTA." Display `jira_site_url` when connected.
  >
  > 3. **`ConnectJiraButton.tsx`**: Per Section 4.2: "Calls `GET /jira/auth/url`, redirects browser to Atlassian consent." Use `window.location.href = authorization_url` per Section 8.2.
  >
  > 4. **`DisconnectJiraButton.tsx`**: Per Section 4.2: "Confirmation dialog, then `DELETE /jira/connection`. Invalidates Jira queries." Use a shadcn `Dialog` for confirmation.

  **Acceptance Criteria:**
  - Connected state shows site URL + disconnect button.
  - Disconnected state shows connect button.
  - Connect redirects to Atlassian OAuth.
  - Disconnect confirms before deleting, then invalidates all Jira query caches.

---

### 3.17 — Jira Callback Page

- [ ] **Task 3.17: Implement JiraCallbackPage**

  **Target Files:**
  - `frontend/src/pages/JiraCallbackPage.tsx` (create/update)

  **Agent Prompt:**
  > Implement the Jira OAuth callback page. Refer to `docs/frontend_hld.md` → Section 3.1 (Route Table — `/jira/connected`) and Section 8.2 (Jira OAuth Connection flow).
  >
  > Create `frontend/src/pages/JiraCallbackPage.tsx`:
  > 1. Per Section 3.1: "Reads `?status=` from Jira OAuth redirect, shows success/error, redirects to dashboard."
  > 2. Read `status` and `message` from URL query params.
  > 3. If `status=success`: show success toast "Jira connected successfully", invalidate `jiraStatus` query, navigate to `/dashboard`.
  > 4. If `status=error`: show error toast with the `message` param, navigate to `/settings/jira`.

  **Acceptance Criteria:**
  - Reads status from URL params set by the backend redirect.
  - Shows appropriate toast for success/error.
  - Navigates to dashboard on success, Jira settings on error.

---

### 3.18 — API Keys Page

- [ ] **Task 3.18: Implement ApiKeysPage (create, list, revoke)**

  **Target Files:**
  - `frontend/src/pages/ApiKeysPage.tsx` (create/update)
  - `frontend/src/features/api-keys/components/ApiKeyTable.tsx` (create)
  - `frontend/src/features/api-keys/components/ApiKeyRow.tsx` (create)
  - `frontend/src/features/api-keys/components/CreateKeyDialog.tsx` (create)
  - `frontend/src/features/api-keys/components/KeyRevealCard.tsx` (create)
  - `frontend/src/features/api-keys/hooks/useApiKeys.ts` (create)
  - `frontend/src/features/api-keys/hooks/useCreateApiKey.ts` (create)
  - `frontend/src/features/api-keys/hooks/useDeleteApiKey.ts` (create)

  **Agent Prompt:**
  > Implement the API keys page. Refer to `docs/frontend_hld.md` → Section 9.2 (API Keys Wireframe) for the layout, Section 4.2 for component behaviors, Section 8.4 (API Key Creation Show-Once Pattern) for the creation flow, and Section 10.3 for form validation.
  >
  > 1. **`ApiKeysPage.tsx`**: Header "API Keys" + "Generate API Key" button + `ApiKeyTable`.
  >
  > 2. **`ApiKeyTable.tsx`**: Per Section 9.2 wireframe: columns for Name, Key (prefix), Last Used, and delete action. Per Section 4.2: "Lists keys with name, prefix, created date, last used date, and a delete button."
  >
  > 3. **`ApiKeyRow.tsx`**: Single row with delete button that opens a confirmation dialog.
  >
  > 4. **`CreateKeyDialog.tsx`**: Per Section 8.4 flow:
  >    - Modal with a "name" field (validated with Section 10.3 schema).
  >    - On success: transition to `KeyRevealCard` showing the raw key.
  >    - On close/done: invalidate `apiKeys` query.
  >
  > 5. **`KeyRevealCard.tsx`**: Per Section 4.2: "Shows the API key once with a copy-to-clipboard button and a warning that it won't be shown again."
  >    - Monospace font for the key.
  >    - Copy button with clipboard feedback.
  >    - Warning banner: "This key will not be shown again."
  >
  > 6. **Hooks**: `useApiKeys()`, `useCreateApiKey()`, `useDeleteApiKey()` — TanStack Query wrappers with cache invalidation.

  **Acceptance Criteria:**
  - API keys page matches the wireframe from Section 9.2.
  - Create flow shows raw key exactly once in the reveal card.
  - Copy to clipboard works with toast confirmation.
  - Delete shows confirmation dialog, then soft-deletes.
  - Table refreshes after create/delete.

---

### 3.19 — Sidebar Jira Status Badge

- [ ] **Task 3.19: Add JiraStatusBadge to the sidebar**

  **Target Files:**
  - `frontend/src/layouts/AppShell.tsx` (update)

  **Agent Prompt:**
  > Add the Jira connection status indicator to the sidebar. Refer to `docs/frontend_hld.md` → Section 4.1 (Component Hierarchy) which shows `Sidebar → JiraStatusBadge`, and Section 4.2 which describes the sidebar: "Navigation links, Jira connection status badge."
  >
  > Update the sidebar in `AppShell.tsx`:
  > 1. Use `useJiraStatus()` to get the connection status.
  > 2. Show a green badge/dot with "Connected" when `connected: true`.
  > 3. Show a yellow/gray badge with "Not Connected" when `connected: false`.
  > 4. Position it near the Jira settings nav link.

  **Acceptance Criteria:**
  - Sidebar shows a visual indicator of Jira connection status.
  - Status updates when Jira is connected/disconnected (via query invalidation).

---

### 3.20 — useClipboard Hook

- [ ] **Task 3.20: Create the useClipboard shared hook**

  **Target Files:**
  - `frontend/src/hooks/useClipboard.ts` (create)

  **Agent Prompt:**
  > Create the shared `useClipboard` hook. Refer to `docs/frontend_hld.md` → Section 7 (Folder Structure) which lists `src/hooks/useClipboard.ts`.
  >
  > Implement `useClipboard()`:
  > - `copy(text: string)` — copies text to clipboard using the Clipboard API.
  > - Returns `{copy, hasCopied}` where `hasCopied` resets after 2 seconds.
  > - Shows a toast "Copied to clipboard" on success.
  > - This is used by `KeyRevealCard` for the copy-to-clipboard button (Section 8.4).

  **Acceptance Criteria:**
  - Clipboard API is used for copy.
  - `hasCopied` auto-resets after 2 seconds.
  - Toast notification on copy.

---

## Phase 4: Integration & Testing

> **Goal:** Wire everything together, polish the UI, and verify all flows end-to-end.

---

### 4.1 — Frontend ↔ Backend Integration Test

- [ ] **Task 4.1: Full integration test — auth flow**

  **Target Files:**
  - No new files — testing only.

  **Agent Prompt:**
  > Test the complete auth flow end-to-end.
  >
  > 1. `docker compose up --build` — ensure all three services start.
  > 2. Open `http://localhost:3000` — should redirect to `/login`.
  > 3. Navigate to `/register` — register a new user. Verify redirect to `/dashboard`.
  > 4. Refresh the page — verify silent refresh works (user stays logged in).
  > 5. Click logout — verify redirect to `/login`.
  > 6. Login with the same credentials — verify access to dashboard.
  > 7. Verify protected routes redirect to `/login` when unauthenticated.
  > 8. Verify public routes redirect to `/dashboard` when authenticated.
  >
  > Fix any issues found.

  **Acceptance Criteria:**
  - Registration → login → refresh → logout flow works seamlessly.
  - Route guards work correctly in both directions.
  - No console errors.

---

### 4.2 — Jira Integration Test

- [ ] **Task 4.2: Test Jira OAuth flow and ticket creation**

  **Target Files:**
  - No new files — testing only.

  **Agent Prompt:**
  > Test the Jira integration end-to-end (requires a real Jira account).
  >
  > 1. Log in to the app.
  > 2. Navigate to `/settings/jira` — verify "Not Connected" state.
  > 3. Click "Connect Jira" — verify redirect to Atlassian consent screen.
  > 4. Authorize — verify redirect back to `/jira/connected?status=success`.
  > 5. Verify success toast and redirect to dashboard.
  > 6. Verify sidebar badge shows "Connected".
  > 7. On dashboard: select a project from the combobox.
  > 8. Create a ticket with summary, description, and issue type.
  > 9. Verify the ticket appears in the Recent Tickets list.
  > 10. Click the ticket — verify it opens in Jira in a new tab.
  > 11. Navigate to `/settings/jira` — verify connected state with site URL.
  > 12. Disconnect Jira — verify it switches back to "Not Connected".
  >
  > Fix any issues found.

  **Acceptance Criteria:**
  - Full Jira OAuth cycle works.
  - Tickets are created in Jira and recorded locally.
  - Recent tickets list updates with optimistic cache.
  - Disconnect clears the connection cleanly.

---

### 4.3 — API Key & External API Test

- [ ] **Task 4.3: Test API key management and external ticket creation**

  **Target Files:**
  - No new files — testing only.

  **Agent Prompt:**
  > Test the API key and external API flows end-to-end.
  >
  > 1. Navigate to `/settings/api-keys`.
  > 2. Create a new API key with name "Test Key".
  > 3. Verify the raw key is displayed in the reveal card.
  > 4. Copy the key — verify clipboard works.
  > 5. Close the dialog — verify the key appears in the table with prefix only.
  > 6. Use `curl` to test the external API:
  >    ```bash
  >    curl -X POST http://localhost:8000/api/v1/tickets \
  >      -H "X-API-Key: <your-key>" \
  >      -H "Content-Type: application/json" \
  >      -d '{"project_key": "SEC", "summary": "Test from API", "issue_type": "Task"}'
  >    ```
  > 7. Verify 201 response with `jira_ticket_key` and `jira_ticket_url`.
  > 8. In the app dashboard, verify the API-created ticket appears with a "via API" badge.
  > 9. Revoke the API key in the UI.
  > 10. Retry the `curl` — verify 401 with `API_KEY_REVOKED` error.
  > 11. Try with a random key — verify 401 with `INVALID_API_KEY` error.
  >
  > Fix any issues found.

  **Acceptance Criteria:**
  - API key create → use → revoke lifecycle works.
  - External API creates tickets under the key owner's Jira identity.
  - Revoked keys return a distinct error from invalid keys.
  - API-created tickets show "via API" badge in the UI.

---

### 4.4 — Error Handling & Edge Cases

- [ ] **Task 4.4: Verify error handling and edge cases across the app**

  **Target Files:**
  - Various files — fixes only.

  **Agent Prompt:**
  > Verify error handling across all flows. Refer to `docs/frontend_hld.md` → Section 6.4 (Error Handling) for the complete error code → UI behavior mapping, and Section 6.5 for loading/empty states.
  >
  > Test each scenario:
  > 1. **Register with existing email** → "This email is already registered" inline error.
  > 2. **Login with wrong password** → "Invalid email or password" inline error.
  > 3. **Access dashboard without Jira connection** → "Connect Jira" CTA.
  > 4. **Submit ticket form with invalid data** → validation errors on fields.
  > 5. **Empty states**: No tickets yet → contextual empty state message.
  > 6. **No API keys** → empty state with CTA to create first key.
  > 7. **Rate limiting** → "Too many requests" toast on 429.
  > 8. **Backend down** → error state with retry button.
  > 9. **Token expiry** → silent refresh, user stays logged in.
  > 10. **Concurrent sessions** → verify no data interference between users.
  >
  > Fix any issues found.

  **Acceptance Criteria:**
  - Every error code from Section 6.4 maps to the correct UI behavior.
  - Loading states show skeleton placeholders.
  - Empty states show contextual messages with action CTAs.
  - No unhandled promise rejections or console errors.

---

### 4.5 — UI Polish & Responsive Design

- [ ] **Task 4.5: Polish UI styling and ensure responsive behavior**

  **Target Files:**
  - Various component files — style updates.

  **Agent Prompt:**
  > Polish the UI for a production-grade look. Refer to `docs/frontend_hld.md` → Section 9 (Wireframes) for the intended visual layout.
  >
  > 1. Ensure the app looks professional and modern using shadcn/ui + Tailwind.
  > 2. Verify the sidebar collapses cleanly on smaller screens.
  > 3. Ensure forms are well-spaced with clear labels and error messages.
  > 4. Verify toast notifications appear and disappear properly.
  > 5. Check that the `KeyRevealCard` has a prominent warning about the key being shown only once.
  > 6. Verify ticket cards are visually distinct with clear hierarchy (key, summary, date, badge).
  > 7. Ensure consistent spacing, typography, and color usage across all pages.
  > 8. Add hover states, focus rings, and transitions where appropriate.

  **Acceptance Criteria:**
  - UI matches the wireframes in spirit — professional and polished.
  - All interactive elements have clear hover/focus states.
  - No visual overflow or layout breaks.
  - Consistent design language across all pages.

---

### 4.6 — Frontend Test Infrastructure Setup

- [ ] **Task 4.6: Set up Vitest, React Testing Library, and MSW for frontend testing**

  **Target Files:**
  - `frontend/vitest.config.ts` (create)
  - `frontend/src/test/setup.ts` (create)
  - `frontend/src/test/mocks/server.ts` (create)
  - `frontend/src/test/mocks/handlers.ts` (create)
  - `frontend/src/test/test-utils.tsx` (create)
  - `frontend/package.json` (update — add dev deps and test script)

  **Agent Prompt:**
  > Set up the frontend test infrastructure. Refer to `docs/frontend_hld.md` → Section 1.1 for the tech stack and Section 6 for the API layer that tests must mock.
  >
  > 1. Install dev dependencies:
  >    - `vitest` (test runner — Vite-native, faster than Jest for Vite projects)
  >    - `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`
  >    - `@vitest/coverage-v8` (coverage provider)
  >    - `msw` (Mock Service Worker — for intercepting API calls in tests)
  >    - `jsdom` (DOM environment for Vitest)
  >
  > 2. Create `frontend/vitest.config.ts`:
  >    - Extend from `vite.config.ts`.
  >    - Set `environment: 'jsdom'`, `globals: true`, `setupFiles: ['./src/test/setup.ts']`.
  >    - Configure coverage: `provider: 'v8'`, `reporter: ['text', 'lcov']`, `include: ['src/**/*.{ts,tsx}']`, `exclude: ['src/test/**', 'src/components/ui/**']`.
  >
  > 3. Create `frontend/src/test/setup.ts`:
  >    - Import `@testing-library/jest-dom/vitest`.
  >    - Set up MSW server: `beforeAll(() => server.listen())`, `afterEach(() => server.resetHandlers())`, `afterAll(() => server.close())`.
  >
  > 4. Create `frontend/src/test/mocks/handlers.ts`:
  >    - Define MSW request handlers for all backend endpoints from `docs/backend_hld.md` Section 6:
  >      - `POST /auth/register` → 201 with mock `AuthResponse`.
  >      - `POST /auth/login` → 200 with mock `AuthResponse`.
  >      - `POST /auth/google` → 200 with mock `AuthResponse`.
  >      - `POST /auth/refresh` → 200 with mock `AuthResponse`.
  >      - `GET /auth/me` → 200 with mock `User`.
  >      - `POST /auth/logout` → 200.
  >      - `GET /jira/status` → 200 with `{connected: true, cloud_id: "test", jira_site_url: "https://test.atlassian.net"}`.
  >      - `GET /jira/projects` → 200 with mock projects.
  >      - `GET /jira/projects/:key/issue-types` → 200 with mock issue types.
  >      - `POST /jira/tickets` → 201 with mock `TicketResponse`.
  >      - `GET /jira/tickets` → 200 with mock `TicketsListResponse`.
  >      - `GET /api-keys` → 200 with mock `ApiKeysListResponse`.
  >      - `POST /api-keys` → 201 with mock `ApiKeyCreatedResponse`.
  >      - `DELETE /api-keys/:id` → 200.
  >    - Each handler should return realistic data matching the exact shapes from `docs/backend_hld.md` Section 6.
  >
  > 5. Create `frontend/src/test/mocks/server.ts`:
  >    - `export const server = setupServer(...handlers)`.
  >
  > 6. Create `frontend/src/test/test-utils.tsx`:
  >    - A custom `render` function that wraps components in required providers:
  >      - `QueryClientProvider` (with a test QueryClient: `retry: false`, `staleTime: 0`).
  >      - `AuthProvider` (or a mock auth context).
  >      - `MemoryRouter` (for routing tests).
  >    - Re-export everything from `@testing-library/react`.
  >
  > 7. Add script to `package.json`: `"test": "vitest"`, `"test:coverage": "vitest run --coverage"`.

  **Acceptance Criteria:**
  - `npm test` runs Vitest in watch mode.
  - `npm run test:coverage` produces a coverage report.
  - MSW intercepts all backend API calls in test environment.
  - Custom `render` wraps components in all necessary providers.
  - Mock data matches the exact API contract shapes from the HLDs.

---

### 4.7 — README & Setup Documentation

- [ ] **Task 4.7: Create comprehensive README with setup instructions**

  **Target Files:**
  - `README.md` (create)

  **Agent Prompt:**
  > Create a comprehensive README for the IdentityHub project. Refer to the original assignment requirements (documented submission expectations) and all three HLD docs for the feature list.
  >
  > Include:
  > 1. **Project Overview** — what IdentityHub does (NHI finding management with Jira integration).
  > 2. **Tech Stack** — Python/FastAPI, PostgreSQL, React/TypeScript/Vite, Docker.
  > 3. **Quick Start**:
  >    - Prerequisites: Docker, Docker Compose, Jira account, Google OAuth credentials (optional).
  >    - `cp .env.example .env` and fill in secrets.
  >    - `docker compose up --build` — single command startup.
  > 4. **Environment Variables** — explain each one from `.env.example`.
  > 5. **Architecture** — brief description of the 3-tier architecture.
  > 6. **Features**:
  >    - User auth (email/password + Google OAuth)
  >    - Jira OAuth 2.0 (3LO) connection
  >    - Ticket creation (UI + API)
  >    - Recent tickets view
  >    - API key management
  >    - External REST API for scanners/CI-CD
  >    - Blog Digest automation (bonus)
  > 7. **API Documentation** — Swagger at `/docs`.
  > 8. **Design Decisions** — reference the HLD docs in `docs/`.
  > 9. **Security** — Fernet encryption, bcrypt, JWT, CORS, rate limiting.
  > 10. **Running Tests** — `cd backend && pytest`, `cd frontend && npm test`, `npm run test:coverage`.

  **Acceptance Criteria:**
  - README provides clear setup instructions.
  - A new developer can get the app running with `docker compose up --build`.
  - All features and design decisions are documented.
  - Test commands are documented.

---

## Phase 5: Automated Testing

> **Source:** `docs/backend_hld.md`, `docs/frontend_hld.md`, `docs/db_hld.md` — all tests are derived from the contracts, schemas, and behaviors defined in these documents.
>
> **Goal:** Achieve robust automated test coverage for the Python backend (unit + integration tests with pytest) and the React frontend (unit + integration tests with Vitest + React Testing Library). Every API endpoint, service method, and complex UI component must have explicit test coverage.

---

### 5.1 — Backend Unit Tests: Auth Utilities

- [ ] **Task 5.1: Write unit tests for JWT and password hashing utilities**

  **Target Files:**
  - `backend/tests/unit/__init__.py` (create)
  - `backend/tests/unit/test_auth_utils.py` (create)

  **Agent Prompt:**
  > Write comprehensive unit tests for `app/auth/utils.py`. Refer to `docs/backend_hld.md` → Section 5.1 (Token Strategy) and `docs/db_hld.md` → Section 5.3 (Passwords — Bcrypt) for the exact specifications. Use `pytest` and `pytest-asyncio`.
  >
  > Test the following in `backend/tests/unit/test_auth_utils.py`:
  >
  > **Password Hashing (per `docs/db_hld.md` Section 5.3):**
  > 1. `test_hash_password_returns_bcrypt_hash` — verify the result starts with `$2b$` (bcrypt prefix).
  > 2. `test_hash_password_uses_12_rounds` — verify the hash uses rounds=12 (check the `$2b$12$` prefix).
  > 3. `test_verify_password_correct` — hash a password, verify with the same input returns True.
  > 4. `test_verify_password_incorrect` — verify with a wrong password returns False.
  > 5. `test_hash_password_unique_salts` — hash the same password twice, verify the hashes differ (per-user salt).
  >
  > **JWT Access Token (per `docs/backend_hld.md` Section 5.1):**
  > 6. `test_create_access_token_contains_correct_claims` — verify `sub`, `email`, `type: "access"`, and `exp` are present.
  > 7. `test_access_token_expires_in_15_minutes` — verify `exp` is approximately `now + 15 minutes` (with 5s tolerance).
  > 8. `test_decode_valid_access_token` — create and decode a token, verify claims round-trip.
  > 9. `test_decode_expired_token_raises` — create a token with -1 min expiry, verify `decode_token` raises.
  > 10. `test_decode_invalid_token_raises` — pass garbage string, verify it raises.
  > 11. `test_decode_token_wrong_secret_raises` — sign with one key, decode with another.
  >
  > **JWT Refresh Token (per `docs/backend_hld.md` Section 5.1):**
  > 12. `test_create_refresh_token_contains_correct_claims` — verify `sub`, `type: "refresh"`, and `exp`.
  > 13. `test_refresh_token_expires_in_7_days` — verify `exp` is approximately `now + 7 days`.
  > 14. `test_access_and_refresh_tokens_have_different_type_claims` — create both, verify `type` field differs.

  **Acceptance Criteria:**
  - All 14 tests pass.
  - Tests verify bcrypt uses 12 rounds per HLD.
  - Tests verify access token = 15 min, refresh token = 7 days per HLD.
  - Tests cover expired, invalid, and wrong-secret token scenarios.

---

### 5.2 — Backend Unit Tests: Jira Encryption

- [ ] **Task 5.2: Write unit tests for Fernet encryption/decryption**

  **Target Files:**
  - `backend/tests/unit/test_encryption.py` (create)

  **Agent Prompt:**
  > Write unit tests for `app/jira/encryption.py`. Refer to `docs/db_hld.md` → Section 5.1 (Jira Tokens — Fernet Encryption) for the specification.
  >
  > Test the following in `backend/tests/unit/test_encryption.py`:
  >
  > 1. `test_encrypt_returns_bytes` — verify `encrypt_token("test")` returns `bytes`.
  > 2. `test_decrypt_recovers_plaintext` — round-trip: `decrypt_token(encrypt_token("my_token")) == "my_token"`.
  > 3. `test_encrypt_produces_different_ciphertext_each_time` — encrypt the same string twice, verify ciphertexts differ (Fernet uses random IV).
  > 4. `test_decrypt_with_wrong_key_raises` — encrypt with one Fernet key, attempt decrypt with a different key, verify it raises `InvalidToken`.
  > 5. `test_decrypt_corrupted_ciphertext_raises` — pass garbage bytes, verify it raises.
  > 6. `test_encrypt_empty_string` — verify empty string encrypts/decrypts without error.
  > 7. `test_encrypt_long_token` — verify a 2000-char token (realistic OAuth token length) round-trips correctly.
  >
  > Use `unittest.mock.patch` to override `settings.JIRA_ENCRYPTION_KEY` with a test key generated via `Fernet.generate_key()`.

  **Acceptance Criteria:**
  - All 7 tests pass.
  - Tests confirm round-trip integrity for various token lengths.
  - Tests confirm wrong-key and corrupted-data scenarios raise errors.
  - Tests use a test encryption key, not production.

---

### 5.3 — Backend Unit Tests: API Key Service

- [ ] **Task 5.3: Write unit tests for API key generation, validation, and revocation**

  **Target Files:**
  - `backend/tests/unit/test_api_key_service.py` (create)

  **Agent Prompt:**
  > Write unit tests for `app/api_keys/service.py`. Refer to `docs/db_hld.md` → Section 3.3 (`api_keys` table) and Section 5.2 (API Keys — One-Way Hashing) for the security model, and `docs/backend_hld.md` → Section 6.4 and 6.5 for the error codes.
  >
  > Test the following in `backend/tests/unit/test_api_key_service.py`:
  >
  > **Key Generation (per `docs/db_hld.md` Section 5.2):**
  > 1. `test_generate_key_format` — verify the raw key matches `ihub_live_` + 48 hex chars (total length = 58).
  > 2. `test_generate_key_prefix_is_first_12_chars` — verify `key_prefix` matches `raw_key[:12]`.
  > 3. `test_generate_key_hash_is_sha256` — verify `key_hash` equals `hashlib.sha256(raw_key.encode()).hexdigest()`.
  > 4. `test_generate_key_unique_each_call` — generate two keys, verify raw keys differ.
  > 5. `test_generate_key_stored_in_db` — verify the key record is persisted with `is_active=True`.
  >
  > **Key Validation (per `docs/backend_hld.md` Section 6.5):**
  > 6. `test_validate_valid_key_returns_key_and_user` — create a key, validate it, verify it returns the key and owning user.
  > 7. `test_validate_key_updates_last_used_at` — validate a key, verify `last_used_at` is updated.
  > 8. `test_validate_invalid_key_raises_INVALID_API_KEY` — pass a random string, verify HTTP 401 with code `INVALID_API_KEY`.
  > 9. `test_validate_revoked_key_raises_API_KEY_REVOKED` — revoke a key, then validate it, verify HTTP 401 with code `API_KEY_REVOKED` (distinct from `INVALID_API_KEY`).
  >
  > **Key Revocation (per `docs/db_hld.md` Section 3.3 soft-delete):**
  > 10. `test_revoke_key_sets_is_active_false` — revoke a key, verify `is_active == False` in DB.
  > 11. `test_revoke_key_not_owned_by_user_raises` — attempt to revoke another user's key, verify 404 or 403.
  >
  > **Key Listing (per `docs/db_hld.md` Section 3.3):**
  > 12. `test_list_keys_only_returns_active` — create 2 keys, revoke 1, verify `list_keys` returns only the active one.
  > 13. `test_list_keys_returns_prefix_not_hash` — verify returned items have `key_prefix` but not raw key or hash.
  >
  > These tests require the `db_session` and `test_user` fixtures from `conftest.py`.

  **Acceptance Criteria:**
  - All 13 tests pass.
  - Key format matches `ihub_live_` + 48 hex chars per HLD.
  - `INVALID_API_KEY` and `API_KEY_REVOKED` are distinct error codes per HLD.
  - Soft-delete is verified (row persists, `is_active` flips).
  - `list_keys` filters out revoked keys.

---

### 5.4 — Backend Unit Tests: Auth Service

- [ ] **Task 5.4: Write unit tests for AuthService and GoogleAuthService**

  **Target Files:**
  - `backend/tests/unit/test_auth_service.py` (create)

  **Agent Prompt:**
  > Write unit tests for `app/auth/service.py`. Refer to `docs/backend_hld.md` → Section 5.1 (App Authentication) for all auth flows and Section 6.2 for error codes, and `docs/db_hld.md` → Section 3.1 for user schema and the account-linking design note.
  >
  > Test the following in `backend/tests/unit/test_auth_service.py`:
  >
  > **AuthService.register:**
  > 1. `test_register_creates_user_with_hashed_password` — verify user is created, `password_hash` is not plaintext, `auth_provider == "local"`.
  > 2. `test_register_normalizes_email_to_lowercase` — register with "User@EXAMPLE.com", verify stored as "user@example.com".
  > 3. `test_register_returns_access_and_refresh_tokens` — verify both tokens are returned.
  > 4. `test_register_duplicate_email_raises_409_EMAIL_EXISTS` — register twice with the same email, verify 409 with `EMAIL_EXISTS`.
  >
  > **AuthService.login:**
  > 5. `test_login_success_returns_tokens` — register then login, verify tokens returned.
  > 6. `test_login_wrong_email_raises_401_INVALID_CREDENTIALS` — login with non-existent email.
  > 7. `test_login_wrong_password_raises_401_INVALID_CREDENTIALS` — register, then login with wrong password.
  > 8. `test_login_google_only_user_no_password_raises_401` — create a Google-only user (password_hash=None), attempt email/password login.
  >
  > **AuthService.refresh:**
  > 9. `test_refresh_valid_token_returns_new_tokens_and_user` — create a refresh token, call refresh, verify new tokens and full user object returned.
  > 10. `test_refresh_expired_token_raises_401` — pass an expired refresh token.
  > 11. `test_refresh_access_token_as_refresh_raises_401` — pass an access token (type="access") where a refresh token is expected.
  >
  > **GoogleAuthService.authenticate (mock Google API with `httpx` mock):**
  > 12. `test_google_auth_new_user_creates_account` — mock Google token exchange, verify new user is created with `auth_provider="google"`, `password_hash=None`.
  > 13. `test_google_auth_existing_google_user_returns_tokens` — create a Google user, authenticate again, verify same user returned.
  > 14. `test_google_auth_existing_email_links_account` — register a local user, then Google auth with same email. Verify `google_sub` is set on the existing user per `docs/db_hld.md` Section 3.1 design notes: "A user who registers locally and later signs in with Google (same email) will have their account linked."
  >
  > Use `unittest.mock.patch` to mock `httpx.AsyncClient.post` for Google API calls.

  **Acceptance Criteria:**
  - All 14 tests pass.
  - Email normalization to lowercase is verified.
  - Duplicate email returns `EMAIL_EXISTS` (409).
  - Wrong credentials return `INVALID_CREDENTIALS` (401).
  - Google account linking is tested per the DB HLD design note.
  - Refresh token validation rejects access tokens.

---

### 5.5 — Backend Unit Tests: Jira Service

- [ ] **Task 5.5: Write unit tests for JiraService core logic**

  **Target Files:**
  - `backend/tests/unit/test_jira_service.py` (create)

  **Agent Prompt:**
  > Write unit tests for `app/jira/service.py`. Refer to `docs/backend_hld.md` → Section 5.2 (Jira OAuth 2.0 3LO Flow) for the HMAC state mechanism and token refresh pattern, Section 6.3 for endpoint behaviors, and `docs/db_hld.md` → Sections 3.2 and 3.4 for data models.
  >
  > Test the following in `backend/tests/unit/test_jira_service.py`:
  >
  > **OAuth State (per Section 5.2: "state = HMAC-sign(user_id + nonce)"):**
  > 1. `test_generate_auth_url_includes_state_with_hmac` — verify `generate_auth_url` returns a URL with a `state` param.
  > 2. `test_state_hmac_verifies_on_callback` — generate a state, verify `handle_callback` can extract `user_id` from it.
  > 3. `test_state_hmac_rejects_tampered_state` — modify the state string, verify callback raises.
  > 4. `test_generate_auth_url_contains_correct_scopes` — verify the URL includes `read:jira-work write:jira-work offline_access`.
  >
  > **Jira Status (per Section 6.3 — always 200):**
  > 5. `test_get_status_connected_returns_true` — user with a `jira_connection` → `{connected: true, cloud_id, jira_site_url}`.
  > 6. `test_get_status_not_connected_returns_false` — user without connection → `{connected: false}`.
  >
  > **Token Refresh (per Section 5.2 — single retry on 401):**
  > 7. `test_make_jira_request_retries_on_401` — mock a 401 response, then 200 on retry. Verify `_refresh_token` is called and the request is retried exactly once.
  > 8. `test_make_jira_request_fails_after_retry_exhausted` — mock 401 on both attempts, verify it raises `JiraApiError`.
  >
  > **Ticket Creation (per Section 6.3 — records in local DB):**
  > 9. `test_create_ticket_records_in_local_db` — mock Jira API success, verify a row is inserted into the `tickets` table with correct `source`, `project_key`, `jira_ticket_key`, and `jira_ticket_url`.
  > 10. `test_create_ticket_sets_source_correctly` — call with `source="ui"`, verify. Call with `source="api"`, verify. Call with `source="blog_digest"`, verify.
  >
  > **Recent Tickets (per `docs/db_hld.md` Section 3.4 query pattern):**
  > 11. `test_get_recent_tickets_orders_by_created_at_desc` — create 3 tickets, verify returned in descending order.
  > 12. `test_get_recent_tickets_filters_by_project_key` — create tickets in 2 projects, query one, verify only that project's tickets returned.
  > 13. `test_get_recent_tickets_respects_limit` — create 15 tickets, request limit=10, verify 10 returned.
  >
  > **Disconnect:**
  > 14. `test_disconnect_deletes_jira_connection` — connect then disconnect, verify row is removed.
  >
  > Mock external HTTP calls (`httpx.AsyncClient`) for all Jira/Atlassian API interactions.

  **Acceptance Criteria:**
  - All 14 tests pass.
  - HMAC state generation and verification are tested.
  - Token refresh retry logic (single retry on 401) is verified.
  - Ticket recording in the local DB is tested with correct source values.
  - Recent tickets query ordering and filtering match the DB HLD.

---

### 5.6 — Backend Unit Tests: SQLAlchemy Models

- [ ] **Task 5.6: Write unit tests for SQLAlchemy model constraints and relationships**

  **Target Files:**
  - `backend/tests/unit/test_models.py` (create)

  **Agent Prompt:**
  > Write unit tests verifying SQLAlchemy model constraints and relationships. Refer to `docs/db_hld.md` → Sections 3.1–3.4 for all table definitions, constraints, and indexes.
  >
  > Test the following in `backend/tests/unit/test_models.py`:
  >
  > **Users Model (Section 3.1):**
  > 1. `test_user_email_unique_constraint` — attempt to create two users with the same email, verify `IntegrityError`.
  > 2. `test_user_google_sub_unique_constraint` — two users with the same `google_sub`, verify `IntegrityError`.
  > 3. `test_user_password_hash_nullable` — create a user with `password_hash=None` (Google-only user), verify it persists.
  > 4. `test_user_auth_provider_defaults_to_local` — create a user without setting `auth_provider`, verify it defaults to `"local"`.
  > 5. `test_user_created_at_auto_set` — create a user, verify `created_at` is populated.
  >
  > **JiraConnections Model (Section 3.2):**
  > 6. `test_jira_connection_user_id_unique` — one connection per user. Try to create two for the same user, verify `IntegrityError`.
  > 7. `test_jira_connection_fk_to_users` — create a connection with invalid `user_id`, verify FK violation.
  > 8. `test_jira_connection_stores_bytea_tokens` — verify `access_token_enc` and `refresh_token_enc` can store `bytes`.
  >
  > **ApiKeys Model (Section 3.3):**
  > 9. `test_api_key_hash_unique` — two keys with same `key_hash`, verify `IntegrityError`.
  > 10. `test_api_key_is_active_defaults_true` — create a key without setting `is_active`, verify it defaults to `True`.
  > 11. `test_api_key_last_used_at_nullable` — create a key, verify `last_used_at` is `None`.
  >
  > **Tickets Model (Section 3.4):**
  > 12. `test_ticket_issue_type_defaults_to_task` — create a ticket without `issue_type`, verify default is `"Task"`.
  > 13. `test_ticket_fk_to_users` — verify FK relationship with users table.
  > 14. `test_ticket_fk_to_jira_connections` — verify FK relationship with jira_connections table.
  >
  > **Relationships:**
  > 15. `test_user_has_jira_connection_relationship` — create user + connection, verify `user.jira_connection` navigates to the connection.
  > 16. `test_user_has_api_keys_relationship` — create user + 2 keys, verify `user.api_keys` returns both.
  > 17. `test_user_has_tickets_relationship` — create user + ticket, verify `user.tickets` returns the ticket.
  >
  > Use the `db_session` fixture from `conftest.py`.

  **Acceptance Criteria:**
  - All 17 tests pass.
  - Unique constraints on `email`, `google_sub`, `user_id` (jira), `key_hash` are verified.
  - Default values (`auth_provider`, `is_active`, `issue_type`) are verified.
  - Nullable columns (`password_hash`, `last_used_at`) are verified.
  - All FK relationships and ORM navigation properties work.

---

### 5.7 — Backend Integration Tests: Auth Endpoints

- [ ] **Task 5.7: Write integration tests for all 6 auth API endpoints**

  **Target Files:**
  - `backend/tests/integration/__init__.py` (create)
  - `backend/tests/integration/test_auth_endpoints.py` (create)

  **Agent Prompt:**
  > Write integration tests for every auth endpoint. Use `httpx.AsyncClient` with the FastAPI app (via `ASGITransport`). Refer to `docs/backend_hld.md` → Section 6.2 for all request/response contracts and error codes.
  >
  > Test the following in `backend/tests/integration/test_auth_endpoints.py`:
  >
  > **POST /auth/register (Section 6.2):**
  > 1. `test_register_201_returns_token_and_user` — valid payload → 201, response has `access_token`, `token_type: "bearer"`, `user` with `id`, `email`, `full_name`, `auth_provider: "local"`.
  > 2. `test_register_sets_refresh_token_cookie` — verify response has `Set-Cookie` with `httponly`, `samesite=lax`, `path=/auth`.
  > 3. `test_register_409_duplicate_email` — register twice → 409 with `{"detail": "Email already registered", "code": "EMAIL_EXISTS"}`.
  > 4. `test_register_422_invalid_email` — payload with `email: "notanemail"` → 422 with `VALIDATION_ERROR`.
  > 5. `test_register_422_short_password` — password < 8 chars → 422.
  > 6. `test_register_422_missing_full_name` — omit `full_name` → 422.
  >
  > **POST /auth/login (Section 6.2):**
  > 7. `test_login_200_valid_credentials` — register then login → 200, same response shape.
  > 8. `test_login_401_wrong_password` — → `{"detail": "Invalid email or password", "code": "INVALID_CREDENTIALS"}`.
  > 9. `test_login_401_nonexistent_email` — → same 401 `INVALID_CREDENTIALS`.
  >
  > **POST /auth/refresh (Section 6.2):**
  > 10. `test_refresh_200_with_valid_cookie` — register (get cookie), send refresh request with cookie → 200 with new `access_token` and full `user` object.
  > 11. `test_refresh_401_no_cookie` — → `{"detail": "Invalid or expired refresh token", "code": "INVALID_REFRESH_TOKEN"}`.
  > 12. `test_refresh_401_invalid_cookie` — garbage cookie → 401.
  >
  > **GET /auth/me (Section 6.2):**
  > 13. `test_me_200_with_valid_token` — pass valid Bearer token → 200 with user data.
  > 14. `test_me_401_no_token` — → `{"detail": "Not authenticated", "code": "NOT_AUTHENTICATED"}`.
  > 15. `test_me_401_expired_token` — pass expired token → 401.
  >
  > **POST /auth/logout (Section 6.2):**
  > 16. `test_logout_200_clears_cookie` — → 200 with `{"detail": "Logged out successfully"}`, verify cookie is cleared.
  >
  > **POST /auth/google (Section 6.2 — mock Google API):**
  > 17. `test_google_auth_200_new_user` — mock Google token exchange, verify 200 with `auth_provider: "google"`.
  > 18. `test_google_auth_200_existing_user_links_account` — register local user, then Google auth with same email → verify account linking.
  >
  > All tests use the `async_client` and `db_session` fixtures. Verify all error responses follow the `{"detail": "...", "code": "..."}` envelope per Section 8.

  **Acceptance Criteria:**
  - All 18 tests pass against the actual FastAPI app with a test database.
  - Every status code (201, 200, 401, 409, 422) is tested.
  - Every error `code` string matches the HLD exactly.
  - HttpOnly cookie behavior is verified for register, login, refresh, and logout.
  - All responses follow the `{detail, code}` error envelope.

---

### 5.8 — Backend Integration Tests: API Key Endpoints

- [ ] **Task 5.8: Write integration tests for API key CRUD endpoints**

  **Target Files:**
  - `backend/tests/integration/test_api_key_endpoints.py` (create)

  **Agent Prompt:**
  > Write integration tests for all API key endpoints. Refer to `docs/backend_hld.md` → Section 6.4 (API Key Management Endpoints) and `docs/db_hld.md` → Section 3.3 for the soft-delete model.
  >
  > Test the following in `backend/tests/integration/test_api_key_endpoints.py`:
  >
  > **POST /api-keys (Section 6.4):**
  > 1. `test_create_api_key_201_returns_raw_key` — valid request → 201 with `id`, `name`, `key` (raw), `created_at`. Verify `key` starts with `ihub_live_`.
  > 2. `test_create_api_key_requires_auth` — no Bearer token → 401.
  > 3. `test_create_api_key_422_empty_name` — empty name → 422.
  > 4. `test_create_api_key_422_name_too_long` — name > 100 chars → 422.
  >
  > **GET /api-keys (Section 6.4):**
  > 5. `test_list_api_keys_200_returns_masked_keys` — create 2 keys, list → 200 with `api_keys` array. Verify each has `key_prefix` but NOT the raw `key`.
  > 6. `test_list_api_keys_excludes_revoked` — create 2 keys, revoke 1, list → only 1 returned.
  > 7. `test_list_api_keys_requires_auth` — no token → 401.
  > 8. `test_list_api_keys_only_own_keys` — create keys for 2 different users, each user's list only shows their own.
  >
  > **DELETE /api-keys/{key_id} (Section 6.4):**
  > 9. `test_revoke_api_key_200` — revoke → 200 with `{"detail": "API key revoked"}`.
  > 10. `test_revoke_api_key_is_soft_delete` — revoke, then query DB directly → `is_active == False`, row still exists.
  > 11. `test_revoke_other_users_key_404` — user A tries to revoke user B's key → 404.
  > 12. `test_revoke_nonexistent_key_404` — random UUID → 404.
  > 13. `test_revoke_requires_auth` — no token → 401.
  >
  > All tests use `async_client` with `auth_headers` fixture.

  **Acceptance Criteria:**
  - All 13 tests pass.
  - Raw key is returned only in the creation response.
  - Listed keys show `key_prefix`, not the full key or hash.
  - Soft-delete is verified at the DB level.
  - User isolation: users can only see/revoke their own keys.

---

### 5.9 — Backend Integration Tests: External API Endpoint

- [ ] **Task 5.9: Write integration tests for the external ticket creation API**

  **Target Files:**
  - `backend/tests/integration/test_external_endpoint.py` (create)

  **Agent Prompt:**
  > Write integration tests for `POST /api/v1/tickets`. Refer to `docs/backend_hld.md` → Section 5.3 (External API Key Authentication), Section 6.5 (External API Endpoint) for the contract and all error codes.
  >
  > Test the following in `backend/tests/integration/test_external_endpoint.py`:
  >
  > **Happy Path:**
  > 1. `test_create_ticket_via_api_key_201` — create a user, connect Jira (mocked), create API key, POST ticket with `X-API-Key` → 201 with `jira_ticket_key`, `jira_ticket_url`, `summary`, `created_at`. Mock the Jira Cloud API call.
  > 2. `test_ticket_source_is_api` — verify the ticket stored in the DB has `source == "api"`.
  > 3. `test_ticket_created_under_key_owner_jira_identity` — verify the Jira API call uses the key owner's Jira token (mock check).
  >
  > **Error Paths (per Section 6.5 — verify exact error codes):**
  > 4. `test_missing_api_key_401_INVALID_API_KEY` — no `X-API-Key` header → 401 `{"code": "INVALID_API_KEY"}`.
  > 5. `test_invalid_api_key_401_INVALID_API_KEY` — random key value → 401 `{"code": "INVALID_API_KEY"}`.
  > 6. `test_revoked_api_key_401_API_KEY_REVOKED` — revoked key → 401 `{"code": "API_KEY_REVOKED"}`. Per Section 6.5: distinct from `INVALID_API_KEY`.
  > 7. `test_key_owner_no_jira_connection_403_JIRA_NOT_CONNECTED` — valid key, but owner has no Jira connection → 403 `{"code": "JIRA_NOT_CONNECTED"}`.
  > 8. `test_validation_error_422` — missing `project_key` → 422 `{"code": "VALIDATION_ERROR"}`.
  > 9. `test_summary_too_long_422` — summary > 255 chars → 422.
  > 10. `test_jira_api_failure_502_JIRA_API_ERROR` — mock Jira API returning 500 → 502 `{"code": "JIRA_API_ERROR"}`.
  >
  > **Rate Limiting (per Section 7 — 20 req/min per key):**
  > 11. `test_rate_limit_429_RATE_LIMITED` — send 21 requests rapidly → verify 429 `{"detail": "Rate limit exceeded. Try again later.", "code": "RATE_LIMITED"}` on the 21st.
  >
  > Mock Jira API calls with `httpx` mocking. Use `async_client`.

  **Acceptance Criteria:**
  - All 11 tests pass.
  - Every error code from Section 6.5 is tested: `INVALID_API_KEY`, `API_KEY_REVOKED`, `JIRA_NOT_CONNECTED`, `VALIDATION_ERROR`, `JIRA_API_ERROR`, `RATE_LIMITED`.
  - `source == "api"` is verified for API-created tickets.
  - Rate limiting at 20 req/min is verified.

---

### 5.10 — Backend Integration Tests: Jira Endpoints

- [ ] **Task 5.10: Write integration tests for all Jira API endpoints**

  **Target Files:**
  - `backend/tests/integration/test_jira_endpoints.py` (create)

  **Agent Prompt:**
  > Write integration tests for all Jira endpoints. Refer to `docs/backend_hld.md` → Section 6.3 (Jira Integration Endpoints) for all contracts and error codes. Mock all external Atlassian/Jira API calls.
  >
  > Test the following in `backend/tests/integration/test_jira_endpoints.py`:
  >
  > **GET /jira/auth/url (Section 6.3):**
  > 1. `test_get_auth_url_200` — authenticated request → 200 with `authorization_url` and `state`.
  > 2. `test_get_auth_url_requires_auth` — no token → 401.
  >
  > **GET /jira/auth/callback (Section 6.3):**
  > 3. `test_callback_success_redirects_with_status_success` — valid code + state → 302 redirect to `http://localhost:3000/jira/connected?status=success`.
  > 4. `test_callback_invalid_state_redirects_with_error` — tampered state → redirect with `?status=error`.
  > 5. `test_callback_no_auth_required` — per HLD: "This endpoint is called by Atlassian's redirect — NO auth header available."
  >
  > **GET /jira/status (Section 6.3):**
  > 6. `test_status_connected_200` — user has Jira connection → `{connected: true, cloud_id, jira_site_url}`.
  > 7. `test_status_not_connected_200` — no connection → `{connected: false}`. Per HLD: "Always returns 200."
  >
  > **GET /jira/projects (Section 6.3):**
  > 8. `test_projects_200_returns_list` — mock Jira API → 200 with `{projects: [...]}` with `id`, `key`, `name`.
  > 9. `test_projects_403_no_jira_connection` — no connection → 403 `JIRA_NOT_CONNECTED`.
  >
  > **GET /jira/projects/{project_key}/issue-types (Section 6.3):**
  > 10. `test_issue_types_200` — mock Jira API → 200 with `{issue_types: [{id, name, is_default}]}`.
  >
  > **POST /jira/tickets (Section 6.3):**
  > 11. `test_create_ticket_201` — valid payload → 201 with full `TicketResponse` shape including `created_by`.
  > 12. `test_create_ticket_source_is_ui` — verify `source == "ui"`.
  > 13. `test_create_ticket_403_no_jira` — no connection → 403 `JIRA_NOT_CONNECTED`.
  > 14. `test_create_ticket_400_invalid_project` — mock Jira returning project not found → 400 `JIRA_PROJECT_NOT_FOUND`.
  > 15. `test_create_ticket_502_jira_api_error` — mock Jira 500 → 502 `JIRA_API_ERROR`.
  > 16. `test_create_ticket_422_summary_too_long` — summary > 255 chars → 422.
  >
  > **GET /jira/tickets (Section 6.3):**
  > 17. `test_get_tickets_200` — create 3 tickets, GET → 200 with `{tickets: [...]}`.
  > 18. `test_get_tickets_filters_by_project_key` — query with `project_key` param, verify filtering.
  > 19. `test_get_tickets_default_limit_10` — create 15 tickets, verify only 10 returned by default.
  > 20. `test_get_tickets_custom_limit` — `?limit=5` → 5 tickets.
  >
  > **DELETE /jira/connection (Section 6.3):**
  > 21. `test_disconnect_200` — → `{"detail": "Jira connection removed"}`.
  > 22. `test_disconnect_requires_auth` — no token → 401.

  **Acceptance Criteria:**
  - All 22 tests pass.
  - All error codes match the HLD: `JIRA_NOT_CONNECTED`, `JIRA_PROJECT_NOT_FOUND`, `JIRA_API_ERROR`.
  - `/jira/status` always returns 200 per HLD.
  - `/jira/auth/callback` does NOT require Bearer auth.
  - Ticket creation response shape matches GET response shape (per HLD note about optimistic cache).
  - Query parameters (`project_key`, `limit`) are verified.

---

### 5.11 — Backend Integration Tests: Health & Error Handling

- [ ] **Task 5.11: Write integration tests for health endpoint and global error handlers**

  **Target Files:**
  - `backend/tests/integration/test_health_and_errors.py` (create)

  **Agent Prompt:**
  > Write integration tests for the health endpoint and global exception handlers. Refer to `docs/backend_hld.md` → Section 6.6 (Health Endpoint) and Section 8 (Error Handling Strategy).
  >
  > Test the following in `backend/tests/integration/test_health_and_errors.py`:
  >
  > **GET /health (Section 6.6):**
  > 1. `test_health_200` — → `{"status": "healthy", "version": "1.0.0", "database": "connected"}`.
  > 2. `test_health_no_auth_required` — health endpoint should not require authentication.
  >
  > **Error Envelope (Section 8):**
  > 3. `test_422_validation_error_envelope` — send malformed JSON to any endpoint → 422 with `{"detail": [...], "code": "VALIDATION_ERROR"}`.
  > 4. `test_401_error_has_code_field` — hit a protected endpoint without auth → 401 with `{"detail": "...", "code": "NOT_AUTHENTICATED"}`.
  > 5. `test_500_hides_internal_details` — trigger an unhandled exception (e.g., mock a service to raise), verify 500 response has generic message and does NOT contain stack trace or internal details.
  >
  > **Content Type:**
  > 6. `test_all_errors_return_json` — verify `Content-Type: application/json` on error responses.

  **Acceptance Criteria:**
  - All 6 tests pass.
  - Health endpoint returns exact shape from HLD.
  - All errors follow `{detail, code}` envelope.
  - 500 errors never expose internal details.

---

### 5.12 — Frontend Unit Tests: Auth Components

- [ ] **Task 5.12: Write unit tests for LoginForm and RegisterForm components**

  **Target Files:**
  - `frontend/src/features/auth/components/__tests__/LoginForm.test.tsx` (create)
  - `frontend/src/features/auth/components/__tests__/RegisterForm.test.tsx` (create)

  **Agent Prompt:**
  > Write unit tests for the auth form components. Use Vitest + React Testing Library + MSW. Refer to `docs/frontend_hld.md` → Section 10.1 (Form Validation schemas), Section 8.1 (Login/Register flow), and Section 6.4 (Error Handling) for expected behaviors.
  >
  > **LoginForm tests (`LoginForm.test.tsx`):**
  >
  > 1. `test_renders_email_and_password_fields` — verify both input fields are present.
  > 2. `test_renders_submit_button` — verify "Login" or "Sign in" button exists.
  > 3. `test_renders_link_to_register` — verify link to `/register` exists.
  > 4. `test_shows_validation_error_on_empty_submit` — click submit without filling fields → validation errors appear.
  > 5. `test_shows_validation_error_for_invalid_email` — enter "notanemail", submit → email validation error.
  > 6. `test_submits_with_valid_data` — fill valid email + password, submit → verify `POST /auth/login` is called (MSW handler).
  > 7. `test_shows_INVALID_CREDENTIALS_error_inline` — override MSW handler to return 401 `INVALID_CREDENTIALS` → verify inline error "Invalid email or password" appears (per Section 6.4 error table).
  > 8. `test_navigates_to_dashboard_on_success` — verify navigation occurs after successful login.
  > 9. `test_disables_button_during_submission` — verify button is disabled while mutation is pending.
  >
  > **RegisterForm tests (`RegisterForm.test.tsx`):**
  >
  > 10. `test_renders_email_password_and_name_fields` — verify all 3 fields.
  > 11. `test_validates_password_min_8_chars` — enter 5-char password → error "Password must be at least 8 characters" (per Section 10.1).
  > 12. `test_validates_full_name_required` — empty name → error.
  > 13. `test_validates_full_name_max_255` — name > 255 chars → error.
  > 14. `test_shows_EMAIL_EXISTS_error_on_email_field` — override MSW to return 409 `EMAIL_EXISTS` → verify inline error "This email is already registered" on the email field (per Section 6.4).
  > 15. `test_submits_valid_data` — fill valid data → verify `POST /auth/register` is called.
  > 16. `test_navigates_to_dashboard_on_success` — verify redirect.
  > 17. `test_renders_link_to_login` — verify link to `/login`.
  >
  > Use the custom `render` from `test-utils.tsx`. Use `userEvent` for typing and clicking.

  **Acceptance Criteria:**
  - All 17 tests pass.
  - Zod validation rules from Section 10.1 are tested (email format, password min 8, name required/max 255).
  - Error code → inline error mapping matches Section 6.4.
  - Navigation on success is verified.
  - Button disabled state during submission is verified.

---

### 5.13 — Frontend Unit Tests: CreateTicketForm

- [ ] **Task 5.13: Write unit tests for CreateTicketForm component**

  **Target Files:**
  - `frontend/src/features/jira/components/__tests__/CreateTicketForm.test.tsx` (create)

  **Agent Prompt:**
  > Write unit tests for the `CreateTicketForm` component. Use Vitest + React Testing Library + MSW. Refer to `docs/frontend_hld.md` → Section 10.2 (Create Ticket validation schema), Section 8.3 (Create Ticket flow), Section 4.2 (CreateTicketForm behavior), and Section 6.4 (error code handling).
  >
  > Test the following in `CreateTicketForm.test.tsx`:
  >
  > 1. `test_renders_summary_description_and_issue_type_fields` — verify all form fields are present.
  > 2. `test_summary_required_validation` — submit without summary → "Summary is required" error.
  > 3. `test_summary_max_255_validation` — enter > 255 chars → "Summary must be under 255 characters" error.
  > 4. `test_description_max_32000_validation` — enter > 32000 chars → error.
  > 5. `test_description_is_optional` — submit without description → no error on description field.
  > 6. `test_issue_type_defaults_to_task` — verify issue type dropdown defaults to "Task" per `docs/backend_hld.md` Section 6.3.
  > 7. `test_submits_valid_ticket` — fill valid data, submit → verify `POST /jira/tickets` called with correct payload.
  > 8. `test_resets_form_on_success` — per Section 8.3: "Reset form fields" after successful creation.
  > 9. `test_shows_success_toast` — per Section 8.3: shows toast "Ticket SEC-42 created".
  > 10. `test_shows_loading_spinner_on_button` — per Section 8.3: "Show loading spinner on button" during submission.
  > 11. `test_handles_JIRA_PROJECT_NOT_FOUND_error` — override MSW to return 400 `JIRA_PROJECT_NOT_FOUND` → verify toast error appears (per Section 6.4: "Toast error + invalidate projects query cache").
  > 12. `test_handles_JIRA_API_ERROR` — override MSW to return 502 → verify "Jira is temporarily unavailable" toast (per Section 6.4).
  >
  > Use the custom `render` from `test-utils.tsx`. Provide mock `projectKey` prop.

  **Acceptance Criteria:**
  - All 12 tests pass.
  - Validation rules match Section 10.2 schema exactly.
  - Form reset on success is verified (per Section 8.3).
  - Success toast and error toasts match Section 6.4.
  - Loading state on submit button is verified.

---

### 5.14 — Frontend Unit Tests: API Key Components

- [ ] **Task 5.14: Write unit tests for CreateKeyDialog, KeyRevealCard, and ApiKeyTable**

  **Target Files:**
  - `frontend/src/features/api-keys/components/__tests__/CreateKeyDialog.test.tsx` (create)
  - `frontend/src/features/api-keys/components/__tests__/KeyRevealCard.test.tsx` (create)
  - `frontend/src/features/api-keys/components/__tests__/ApiKeyTable.test.tsx` (create)

  **Agent Prompt:**
  > Write unit tests for the API key management components. Use Vitest + React Testing Library + MSW. Refer to `docs/frontend_hld.md` → Section 8.4 (API Key Creation Show-Once Pattern), Section 4.2 (component behaviors), Section 9.2 (API Keys Wireframe), and Section 10.3 (validation schema).
  >
  > **CreateKeyDialog tests (`CreateKeyDialog.test.tsx`):**
  >
  > 1. `test_renders_name_input_and_create_button` — verify dialog content.
  > 2. `test_validates_name_required` — empty name → error "Name is required" (per Section 10.3).
  > 3. `test_validates_name_max_100` — > 100 chars → error "Name must be under 100 characters".
  > 4. `test_submits_and_shows_key_reveal_card` — fill name, submit → verify `KeyRevealCard` appears with the raw key.
  > 5. `test_shows_loading_state_during_creation` — verify loading indicator during mutation.
  >
  > **KeyRevealCard tests (`KeyRevealCard.test.tsx`):**
  >
  > 6. `test_displays_raw_key_in_monospace` — verify the raw key text is displayed.
  > 7. `test_shows_warning_never_shown_again` — verify warning message "This key will not be shown again" (per Section 4.2).
  > 8. `test_copy_button_copies_to_clipboard` — click copy → verify `navigator.clipboard.writeText` is called with the key.
  > 9. `test_done_button_closes_dialog` — click "Done" → verify dialog closes.
  >
  > **ApiKeyTable tests (`ApiKeyTable.test.tsx`):**
  >
  > 10. `test_renders_table_with_columns` — verify columns: Name, Key, Last Used, delete action (per Section 9.2 wireframe).
  > 11. `test_displays_key_prefix_not_full_key` — verify `key_prefix` is shown, not the raw key.
  > 12. `test_shows_last_used_relative_time` — verify "2h ago" or "never" format.
  > 13. `test_delete_button_shows_confirmation` — click delete → verify confirmation dialog appears.
  > 14. `test_empty_state_when_no_keys` — no keys → empty state message per Section 6.5.
  >
  > Mock `navigator.clipboard.writeText` for clipboard tests.

  **Acceptance Criteria:**
  - All 14 tests pass.
  - Show-once pattern verified: raw key appears only in `KeyRevealCard`.
  - Warning message about key visibility is present.
  - Copy-to-clipboard functionality is verified.
  - Validation rules match Section 10.3.
  - Empty state is tested per Section 6.5.

---

### 5.15 — Frontend Unit Tests: Route Guards & AuthProvider

- [ ] **Task 5.15: Write unit tests for ProtectedRoute, PublicOnlyRoute, and AuthProvider**

  **Target Files:**
  - `frontend/src/providers/__tests__/AuthProvider.test.tsx` (create)
  - `frontend/src/test/__tests__/RouteGuards.test.tsx` (create)

  **Agent Prompt:**
  > Write unit tests for auth state management and route guards. Use Vitest + React Testing Library + MSW. Refer to `docs/frontend_hld.md` → Section 5.2 (Auth Context) for the `AuthContextValue` interface and behavior, and Section 3.2 (Route Guards) for `ProtectedRoute` and `PublicOnlyRoute` implementations.
  >
  > **AuthProvider tests (`AuthProvider.test.tsx`):**
  >
  > 1. `test_initial_state_is_loading` — on mount, `isLoading` is true.
  > 2. `test_attempts_silent_refresh_on_mount` — verify `POST /auth/refresh` is called on mount (per Section 5.2: "On app mount, attempts a silent refresh").
  > 3. `test_restores_user_from_refresh_response` — mock refresh success → verify `user` is populated from the response (per Section 5.2: "The refresh response includes the full user object").
  > 4. `test_sets_loading_false_on_refresh_failure` — mock refresh failure → `isLoading` becomes false, `user` remains null.
  > 5. `test_login_stores_token_and_user` — call `login(token, user)` → verify `user` state is updated.
  > 6. `test_logout_clears_state_and_calls_api` — call `logout()` → verify `POST /auth/logout` is called and `user` becomes null.
  > 7. `test_access_token_in_memory_not_localstorage` — after login, verify `localStorage` does NOT contain the token (per Section 5.2: "stored in memory, not localStorage for security").
  >
  > **Route Guards tests (`RouteGuards.test.tsx`):**
  >
  > 8. `test_protected_route_shows_spinner_while_loading` — `isLoading=true` → renders `FullPageSpinner` (per Section 3.2).
  > 9. `test_protected_route_redirects_to_login_when_unauthenticated` — `user=null, isLoading=false` → navigate to `/login`.
  > 10. `test_protected_route_renders_children_when_authenticated` — `user=validUser` → renders children.
  > 11. `test_public_route_shows_spinner_while_loading` — `isLoading=true` → renders `FullPageSpinner`.
  > 12. `test_public_route_redirects_to_dashboard_when_authenticated` — `user=validUser` → navigate to `/dashboard`.
  > 13. `test_public_route_renders_children_when_unauthenticated` — `user=null` → renders children.

  **Acceptance Criteria:**
  - All 13 tests pass.
  - Silent refresh on mount is verified.
  - Token stored in memory (not localStorage) per security requirement.
  - Route guards redirect correctly in all 4 states (loading, authenticated, unauthenticated) for both protected and public routes.
  - Logout calls the API and clears state.

---

### 5.16 — Frontend Unit Tests: Error Utilities & Query Keys

- [ ] **Task 5.16: Write unit tests for getErrorMessage, getErrorCode, and queryKeys**

  **Target Files:**
  - `frontend/src/lib/__tests__/errors.test.ts` (create)
  - `frontend/src/lib/__tests__/queryKeys.test.ts` (create)

  **Agent Prompt:**
  > Write unit tests for the shared utility functions. Use Vitest. Refer to `docs/frontend_hld.md` → Section 6.4 (Error Handling) for `getErrorMessage` and `getErrorCode`, and Section 5.4 (Query Keys Convention) for the key factory.
  >
  > **Error Utilities tests (`errors.test.ts`):**
  >
  > Test `getErrorMessage()` with all cases from Section 6.4:
  > 1. `test_429_returns_rate_limit_message` — 429 response → "Too many requests. Please wait a moment and try again."
  > 2. `test_502_returns_jira_unavailable_message` — 502 response → "Jira is temporarily unavailable. Please try again."
  > 3. `test_string_detail_returns_detail` — `{detail: "Email already registered"}` → returns that string.
  > 4. `test_array_detail_returns_validation_message` — `{detail: [...]}` → "Validation error. Please check your input."
  > 5. `test_unknown_error_returns_fallback` — non-Axios error → "An unexpected error occurred."
  > 6. `test_no_response_data_returns_fallback` — Axios error with no response body → fallback message.
  >
  > Test `getErrorCode()`:
  > 7. `test_extracts_code_from_response` — `{code: "EMAIL_EXISTS"}` → returns `"EMAIL_EXISTS"`.
  > 8. `test_returns_null_for_missing_code` — no `code` field → returns `null`.
  > 9. `test_returns_null_for_non_axios_error` — plain Error → returns `null`.
  >
  > **Query Keys tests (`queryKeys.test.ts`):**
  >
  > 10. `test_auth_user_key` — `queryKeys.auth.user` → `['auth', 'user']`.
  > 11. `test_jira_status_key` — `queryKeys.jira.status` → `['jira', 'status']`.
  > 12. `test_jira_issue_types_key_includes_project` — `queryKeys.jira.issueTypes('SEC')` → `['jira', 'issueTypes', 'SEC']`.
  > 13. `test_jira_tickets_key_includes_project` — `queryKeys.jira.tickets('SEC')` → `['jira', 'tickets', 'SEC']`.
  >
  > Create mock Axios errors using `AxiosError` constructor or factory for testing.

  **Acceptance Criteria:**
  - All 13 tests pass.
  - Every error scenario from Section 6.4 is covered.
  - Query key factory returns the exact structures from Section 5.4.
  - Both `getErrorMessage` and `getErrorCode` handle non-Axios errors gracefully.

---

### 5.17 — Frontend Integration Tests: API Contract Compliance

- [ ] **Task 5.17: Write integration tests verifying frontend handles all API states correctly**

  **Target Files:**
  - `frontend/src/features/jira/components/__tests__/DashboardPage.integration.test.tsx` (create)
  - `frontend/src/pages/__tests__/ApiKeysPage.integration.test.tsx` (create)

  **Agent Prompt:**
  > Write integration tests that verify the frontend correctly handles all API response states. Use Vitest + React Testing Library + MSW to simulate backend responses. Refer to `docs/frontend_hld.md` → Section 6.5 (Loading & Empty States) and Section 6.4 (Error Handling table) for the exact UI behaviors expected.
  >
  > **DashboardPage Integration (`DashboardPage.integration.test.tsx`):**
  >
  > 1. `test_loading_state_shows_skeletons` — while API calls are in-flight → verify skeleton components render (per Section 6.5: "Skeleton placeholders matching the shape of the expected content").
  > 2. `test_jira_not_connected_shows_connect_cta` — MSW returns `{connected: false}` → verify "Connect Jira" CTA appears instead of the form (per Section 6.4 `JIRA_NOT_CONNECTED` handling).
  > 3. `test_empty_tickets_shows_empty_state` — MSW returns `{tickets: []}` → verify empty state with CTA "No tickets yet — create your first finding" (per Section 6.5).
  > 4. `test_error_state_shows_retry_button` — MSW returns 500 → verify inline error message with "Retry" button (per Section 6.5).
  > 5. `test_retry_button_refetches` — click retry → verify the query is refetched.
  > 6. `test_tickets_display_source_badge_for_non_ui` — MSW returns tickets with `source: "api"` → verify "via API" badge appears (per Section 4.2 RecentTicketsList: "Shows a subtle source badge when source !== 'ui'").
  > 7. `test_ticket_card_opens_jira_url_in_new_tab` — click ticket → verify `window.open` called with `jira_ticket_url` and `_blank`.
  > 8. `test_project_selector_populates_from_api` — MSW returns projects → verify dropdown options appear.
  > 9. `test_issue_type_preselects_default` — MSW returns issue types with one having `is_default: true` → verify it's preselected (per Section 4.2 IssueTypeSelect: "Pre-selects the is_default: true option").
  >
  > **ApiKeysPage Integration (`ApiKeysPage.integration.test.tsx`):**
  >
  > 10. `test_loading_state_shows_skeletons` — while loading → skeleton UI.
  > 11. `test_empty_state_shows_create_cta` — no keys → empty state with "Generate API Key" CTA.
  > 12. `test_displays_keys_from_api` — MSW returns 2 keys → verify both appear in table.
  > 13. `test_create_key_flow_end_to_end` — click Generate → fill name → submit → verify key reveal card appears → click Done → verify table refreshes.
  > 14. `test_delete_key_flow_end_to_end` — click delete → confirm → verify key disappears from table.
  > 15. `test_rate_limit_shows_toast` — override MSW to return 429 → verify "Too many requests" toast (per Section 6.4).

  **Acceptance Criteria:**
  - All 15 tests pass.
  - Loading states use skeleton placeholders per Section 6.5.
  - Empty states show contextual messages with action CTAs per Section 6.5.
  - Error states show inline error with retry button per Section 6.5.
  - Source badges, default selections, and toast messages match the HLD.
  - Full create/delete flows are tested end-to-end within the component tree.

---

### 5.18 — Frontend Unit Tests: useClipboard Hook

- [ ] **Task 5.18: Write unit tests for the useClipboard hook**

  **Target Files:**
  - `frontend/src/hooks/__tests__/useClipboard.test.ts` (create)

  **Agent Prompt:**
  > Write unit tests for the `useClipboard` hook. Use Vitest + `@testing-library/react` `renderHook`. Refer to `docs/frontend_hld.md` → Section 7 (`src/hooks/useClipboard.ts`) and the usage context in Section 8.4 (API Key Creation).
  >
  > Test the following in `useClipboard.test.ts`:
  >
  > 1. `test_copy_calls_clipboard_api` — call `copy("test")` → verify `navigator.clipboard.writeText("test")` is called.
  > 2. `test_hasCopied_is_true_after_copy` — call `copy()` → `hasCopied` becomes true.
  > 3. `test_hasCopied_resets_after_2_seconds` — call `copy()` → wait 2s → `hasCopied` becomes false (use `vi.useFakeTimers()`).
  > 4. `test_copy_shows_toast` — call `copy()` → verify toast "Copied to clipboard" is shown.
  > 5. `test_handles_clipboard_api_failure_gracefully` — mock `writeText` to reject → verify no unhandled error.
  >
  > Mock `navigator.clipboard.writeText` with `vi.fn()`.

  **Acceptance Criteria:**
  - All 5 tests pass.
  - Clipboard API call is verified.
  - 2-second auto-reset of `hasCopied` is verified with fake timers.
  - Toast on copy is verified.
  - Graceful error handling for clipboard API failures.

---

### 5.19 — Run All Tests & Coverage Report

- [ ] **Task 5.19: Run full test suites and verify coverage thresholds**

  **Target Files:**
  - No new files — validation and potential fixture fixes.

  **Agent Prompt:**
  > Run the complete backend and frontend test suites and verify coverage.
  >
  > **Backend:**
  > 1. Run `cd backend && pytest -v --tb=short` — all tests must pass.
  > 2. Run `cd backend && pytest --cov=app --cov-report=term-missing` — generate coverage report.
  > 3. Verify minimum coverage thresholds:
  >    - `app/auth/utils.py` — ≥ 95%
  >    - `app/auth/service.py` — ≥ 90%
  >    - `app/api_keys/service.py` — ≥ 90%
  >    - `app/jira/encryption.py` — ≥ 95%
  >    - `app/jira/service.py` — ≥ 85%
  >    - `app/models/` — ≥ 90%
  >    - Overall `app/` — ≥ 80%
  >
  > **Frontend:**
  > 1. Run `cd frontend && npm test -- --run` — all tests must pass.
  > 2. Run `cd frontend && npm run test:coverage` — generate coverage report.
  > 3. Verify minimum coverage thresholds:
  >    - `src/features/auth/components/` — ≥ 90%
  >    - `src/features/jira/components/` — ≥ 85%
  >    - `src/features/api-keys/components/` — ≥ 85%
  >    - `src/providers/AuthProvider.tsx` — ≥ 90%
  >    - `src/lib/errors.ts` — ≥ 95%
  >    - Overall `src/` — ≥ 75% (excluding `src/components/ui/` which are shadcn vendor files)
  >
  > Fix any failing tests. If coverage is below thresholds, identify and fill the gaps.

  **Acceptance Criteria:**
  - All backend tests pass (`pytest` exit code 0).
  - All frontend tests pass (`vitest` exit code 0).
  - Backend coverage: ≥ 80% overall, ≥ 90% on core services.
  - Frontend coverage: ≥ 75% overall (excluding shadcn/ui), ≥ 85% on feature components.
  - Coverage reports are generated and readable.
  - No test isolation issues (each test runs independently).

---

## Dependency Graph Summary

```
Phase 1 (DB)          Phase 2 (Backend)          Phase 3 (Frontend)        Phase 4 (Integration)    Phase 5 (Automated Tests)
─────────────         ──────────────────         ──────────────────        ─────────────────────    ────────────────────────
1.1 Scaffolding ──┐
1.2 Python Setup ─┤
1.3 users model ──┤
1.4 jira model ───┤── 2.1 Auth utils ────┐
1.5 api_keys ─────┤   2.2 Auth schemas ──┤
1.6 tickets ──────┤   2.3 Auth service ───┤── 3.1 React scaffold ──┐
1.7 DB session ───┤   2.4 Auth router ────┤   3.2 shadcn/ui ───────┤
1.8 Alembic ──────┤   2.5 Encryption ─────┤   3.3 Types ───────────┤
1.9 FastAPI app ──┤   2.6 Jira schemas ───┤   3.4 Axios client ────┤── 4.1 Auth test ──────┐
1.10 Verify DB ───┘   2.7 Jira service ───┤   3.5 API modules ─────┤   4.2 Jira test ──────┤
                       2.8 Jira router ────┤   3.6 Query keys ──────┤   4.3 API key test ───┤
                       2.9 API key svc ────┤   3.7 AuthProvider ────┤   4.4 Error test ─────┤
                       2.10 API key rtr ───┤   3.8 QueryProvider ───┤   4.5 UI polish ──────┤
                       2.11 External API ──┤   3.9 Layouts ─────────┤   4.6 FE test infra ──┤
                       2.12 Rate limit ────┤   3.10 Router ─────────┤   4.7 README ─────────┘
                       2.13 Error hdlrs ───┤   3.11 Login page ─────┤       │
                       2.14 Blog digest ───┤   3.12 Register page ──┤       ├── 5.1 Auth utils tests
                       2.15 BE test infra ─┤   3.13 Google callback ┤       ├── 5.2 Encryption tests
                       2.16 Smoke test ────┘   3.14 Jira hooks ─────┤       ├── 5.3 API key svc tests
                                               3.15 Dashboard ──────┤       ├── 5.4 Auth svc tests
                                               3.16 Jira settings ──┤       ├── 5.5 Jira svc tests
                                               3.17 Jira callback ──┤       ├── 5.6 Model tests
                                               3.18 API keys page ──┤       ├── 5.7 Auth endpoint tests
                                               3.19 Status badge ───┤       ├── 5.8 API key endpoint tests
                                               3.20 useClipboard ───┘       ├── 5.9 External API tests
                                                                             ├── 5.10 Jira endpoint tests
                                                                             ├── 5.11 Health/error tests
                                                                             ├── 5.12 Auth component tests
                                                                             ├── 5.13 Ticket form tests
                                                                             ├── 5.14 API key component tests
                                                                             ├── 5.15 Route guard tests
                                                                             ├── 5.16 Utility tests
                                                                             ├── 5.17 FE integration tests
                                                                             ├── 5.18 useClipboard tests
                                                                             └── 5.19 Coverage report
```

---

## Execution Notes

1. **Sequential within phases**: Tasks within each phase should be executed in order — later tasks depend on earlier ones.
2. **Phase gates**: Do not start Phase 2 until Phase 1 Task 1.10 passes. Do not start Phase 3 until Phase 2 Task 2.16 passes. Do not start Phase 4 until all Phase 3 tasks are complete. Do not start Phase 5 until Phase 4 Tasks 4.6 and 4.7 are complete (test infrastructure + README).
3. **Test infrastructure first**: Tasks 2.15 (backend test infra) and 4.6 (frontend test infra) set up the test frameworks and must be completed before any Phase 5 test-writing tasks.
4. **Phase 5 parallelism**: Backend tests (5.1–5.11) and frontend tests (5.12–5.18) can be executed in parallel by different developers. Within each group, tasks are independent except 5.19 which runs last.
5. **Each task = one Cursor prompt**: Every task is scoped to be completable in a single Cursor Agent session by copying the Agent Prompt verbatim.
6. **Commit after each task**: Create a git commit after each successful task for easy rollback.
7. **Total tasks**: 72 tasks across 5 phases (10 in Phase 1 + 16 in Phase 2 + 20 in Phase 3 + 7 in Phase 4 + 19 in Phase 5). The 19 Phase 5 testing tasks and 2 test infrastructure tasks (2.15, 4.6) were added during the testing audit.
