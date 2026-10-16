# Cortex XDR AI-Powered SOC Dashboard



A full-stack Security Operations Center (SOC) dashboard that ingests, correlates, and analyzes alerts and incidents from **Palo Alto Networks Cortex XDR**, with AI-powered analysis, role-based authentication, and a modern React frontend.



> **Status:** Active development — v1.0.0

> **Backend:** FastAPI (Python) · **Frontend:** React 18 + TypeScript + Vite · **Database:** PostgreSQL + pgvector · **Orchestration:** Docker Compose



---



## Table of Contents



[Project Overview](#project-overview)
[Tech Stack](#tech-stack)
[Architecture & Services](#architecture--services)
[Directory Structure](#directory-structure)
[Prerequisites](#prerequisites)
[Quick Start (Docker Compose)](#quick-start-docker-compose)
[Manual Backend Setup](#manual-backend-setup)
[Manual Frontend Setup](#manual-frontend-setup)
[Environment Variables](#environment-variables)
[GitHub Upload — What Is / Isn't Included](#github-upload---what-is--isnt-included)
[API Endpoints](#api-endpoints)
[Frontend Routes](#frontend-routes)
[Available Scripts](#available-scripts)
[Security Notes](#security-notes)
[License](#license)


---



## Project Overview



The Cortex XDR AI-Powered SOC Dashboard is a SOC analyst workspace that:



Synchronizes alerts and incidents from **Cortex XDR** via its REST API
Provides AI-powered analysis (OpenAI-compatible provider) of alerts and incidents
Displays dashboards with key metrics and visualizations
Supports JWT-based authentication with role-based access (admin/user)
Includes rate limiting and secure password hashing (bcrypt)
Runs entirely with Docker Compose (PostgreSQL + backend API + background worker + frontend)


---



## Tech Stack



| Layer | Technology | Version / Notes |

|-------|-----------|-----------------|

| Backend API | FastAPI | Python 3.10+ |

| Backend language | Python | 3.10 (`.venv`) |

| Database | PostgreSQL | 16-alpine (Docker), SQLAlchemy 2.0, Alembic migrations, pgvector |

| Frontend | React 18 + TypeScript | Vite, Tailwind CSS |

| State / routing | React Router DOM | Lazy-loaded routes |

| Charts | Recharts | Dashboard visualizations |

| Icons | Lucide React | UI icons |

| HTTP client | Axios | API calls from frontend |

| Auth | JWT (python-jose) + bcrypt | Password hashing, access tokens |

| Rate limiting | slowapi | Per-minute request limits |

| AI / LLM | OpenAI-compatible API | Provider-agnostic (`openai`, `anthropic`, `local`, `mock`) |

| Testing | pytest | Backend tests under `backend/tests/` |

| Containerization | Docker + Docker Compose | Multi-service orchestration |



## Architecture & Services



`docker-compose.yml` defines four services:



| Service | Role | Port |

|---------|------|------|

| `db` | PostgreSQL database (with pgdata volume) | 5432 |

| `backend` | FastAPI API; runs `alembic upgrade head` then `uvicorn` | 8000 |

| `worker` | Background sync worker for Cortex XDR data | — |

| `frontend` | Vite-built React app served via nginx | 5173 |



The backend bootstraps a default admin user on startup (dev mode only) if no users exist.



---



## Directory Structure



```

cortex_dashboard/

├── .gitignore # Files excluded from Git (see GitHub Upload section)

├── .env.example # Template — copy to .env and fill real values

├── .env # Local secrets (created by you; NOT committed)

├── docker-compose.yml # Multi-service orchestration

│

├── backend/ # FastAPI application

│ ├── app/

│ │ ├── main.py # FastAPI entry point, CORS, rate limiting, routers

│ │ ├── core/

│ │ │ ├── config.py # Pydantic settings from .env

│ │ │ ├── database.py # SQLAlchemy engine/session + init_db

│ │ │ └── security.py # Password hashing / JWT helpers

│ │ ├── api/

│ │ │ ├── deps.py # Dependency injection (DB session, current user)

│ │ │ └── endpoints/ # health, auth, dashboard, alerts, incidents,

│ │ │ │ # sync, settings, analysis

│ │ ├── models/ # SQLAlchemy models (user, alert, incident, etc.)

│ │ ├── schemas/ # Pydantic request/response schemas

│ │ └── services/ # AI service, Cortex client, normalization, sync

│ ├── alembic/ # DB migration scripts

│ ├── alembic.ini

│ ├── Dockerfile

│ ├── requirements.txt # Pinned Python dependencies

│ └── tests/ # pytest test suite

│

└── frontend/ # React SPA

├── index.html

├── package.json

├── vite.config.ts

├── tailwind.config.js

├── postcss.config.js

├── tsconfig.json

├── Dockerfile

├── src/

│ ├── main.tsx

│ ├── App.tsx # Route definitions + Protected wrapper

│ ├── index.css

│ ├── i18n.ts # Internationalization strings

│ ├── contexts/

│ │ └── LanguageContext.tsx

│ ├── lib/api.ts # Axios instance + token helpers

│ ├── components/

│ │ ├── layout/ # AppLayout, Header, Sidebar

│ │ └── ui/ # Button, Card, Input, Badge, Skeleton

│ ├── pages/ # Login, Dashboard, Alerts, AlertDetail,

│ │ # Incidents, IncidentDetail, Settings

│ └── ...

```





## Prerequisites



**Docker** + **Docker Compose** (recommended path)
**Python 3.10+** and **pip** (for manual backend)
**Node.js 18+** and **npm** (for manual frontend)
A Cortex XDR tenant with API credentials (optional — dashboard works in demo mode without them)


---



## Quick Start (Docker Compose)



```bash

# 1. Open the project folder

cd /home/jetson/Desktop/visual_studio/cortex_dashboard



# 2. Create your environment file from the example

cp .env.example .env

# Edit .env and add your Cortex XDR / AI credentials (see .env.example comments)



# 3. Build and start all services

docker-compose up --build



# 4. Access the services

# Frontend: http://localhost:5173

# Backend API: http://localhost:8000

# API docs: http://localhost:8000/docs

# PostgreSQL: localhost:5432

```



Default admin (dev, bootstrapped on first start): `admin` / `admin123` — **change these in production.**



---



## Manual Backend Setup



```bash

cd backend



# Create virtual environment

python -m venv .venv

source .venv/bin/activate



# Install dependencies

pip install -r requirements.txt



# Copy environment config

cp ../.env.example ../.env # then edit ../.env with your values



# Run migrations

alembic upgrade head



# Start the API

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

```



Run tests:

```bash

cd backend

pytest

```



---



## Manual Frontend Setup



```bash

cd frontend



# Install dependencies

npm install



# Start dev server

npm run dev # http://localhost:5173



# Production build

npm run build # outputs to dist/



# Lint

npm run lint

```





## Environment Variables



Create `.env` at the project root by copying `.env.example`. Never commit `.env` — it may contain API keys and secrets.



| Variable | Purpose | Example |

|----------|---------|---------|

| `SECRET_KEY` | JWT signing secret | strong random string |

| `DATABASE_URL` | SQLAlchemy DB URL | `postgresql+psycopg2://soc:socpassword@db:5432/socdb` |

| `CORTEX_TENANT_FQDN` | Cortex XDR tenant endpoint | `https://<tenant>.api.cortexdata.panw.io` |

| `CORTEX_API_KEY_ID` / `CORTEX_API_KEY` | Cortex XDR API credentials | from Cortex XDR console |

| `AI_PROVIDER` / `AI_MODEL` / `AI_API_KEY` | LLM provider & key | `openai`, `gpt-4o-mini` |

| `CORTEX_DEMO_MODE` / `AI_DEMO_MODE` | Use synthetic demo data | `false` |

| `FRONTEND_ORIGIN` / `BACKEND_CORS_ORIGINS` | CORS allowed origins | `http://localhost:5173` |



Full documented list is inside `.env.example`.



---



## GitHub Upload — What Is / Isn't Included



### ⚠️ Important: Before uploading to GitHub



This repository **did not have a root `.gitignore`**. I have added one (`/.gitignore`) so that secrets, local caches, and dependency folders are **not** uploaded.



### ✅ Files that WILL be uploaded to GitHub



All source code and project configuration, including:



`docker-compose.yml`
`.env.example` (template only — safe to commit)
`.gitignore`
`README.md`
`backend/` source code: `app/`, `alembic/`, `requirements.txt`, `Dockerfile`, `tests/`
`frontend/` source code: `src/`, `package.json`, `vite.config.ts`, `tailwind.config.js`, `Dockerfile`, etc.


### ❌ Files that will NOT be uploaded (ignored by `.gitignore`)



| Path | Reason |

|------|--------|

| `.env` | Contains real secrets / API keys — must stay local |

| `.venv/` | Python virtual environment (machine-specific, hundreds of MB) |

| `backend/__pycache__/` | Python bytecode cache |

| `backend/.pytest_cache/` | Pytest cache |

| `frontend/node_modules/` | npm dependencies (installed via `npm install`) |

| `frontend/dist/` / `frontend/build/` | Production build output |

| `.vscode/`, `.idea/` | IDE settings |

| `*.pyc`, `*.pyo` | Compiled Python files |

| `docker-compose.override.yml` | Local Docker overrides |

| `.DS_Store`, `Thumbs.db` | OS metadata files |



If you upload without the provided `.gitignore`, files such as `.env`, `.venv/`, `__pycache__/`, and `node_modules/` **would** be pushed to GitHub — including potentially sensitive credentials. Always review `git status --short` before your first `git add`.





## API Endpoints



All backend routes are mounted under `/api`:



| Method | Path | Description |

|--------|------|-------------|

| `GET` | `/api/health` | Health check |

| `POST` | `/api/auth/...` | Authentication (login, token) |

| `GET` | `/api/dashboard` | Dashboard metrics |

| `GET` | `/api/alerts` | List alerts |

| `GET` | `/api/alerts/{id}` | Alert detail |

| `GET` | `/api/incidents` | List incidents |

| `GET` | `/api/incidents/{id}` | Incident detail |

| `POST` | `/api/sync` | Trigger Cortex XDR sync |

| `GET` | `/api/settings` | Application settings |

| `POST` | `/api/analysis/...` | AI-powered alert/incident analysis |

| `GET` | `/api/docs` | Interactive Swagger UI (dev only) |



---



## Frontend Routes



| Path | Page | Access |

|------|------|--------|

| `/login` | Login | Public |

| `/` | Dashboard | Protected |

| `/alerts` | Alerts list | Protected |

| `/alerts/:alertId` | Alert detail | Protected |

| `/incidents` | Incidents list | Protected |

| `/incidents/:incidentId` | Incident detail | Protected |

| `/settings` | Settings | Protected |



---



## Available Scripts



**Backend** (`backend/`):

`pip install -r requirements.txt` — install dependencies
`alembic upgrade head` — apply DB migrations
`uvicorn app.main:app --reload` — run dev server
`pytest` — run test suite


**Frontend** (`frontend/`):

`npm run dev` — start dev server (Vite)
`npm run build` — TypeScript check + production build
`npm run preview` — preview production build
`npm run test` — run vitest tests
`npm run lint` — ESLint


**Docker**:

`docker-compose up --build` — build & start all services
`docker-compose down` — stop & remove containers


---



## Security Notes



**Never commit `.env`** — it may contain `SECRET_KEY`, `CORTEX_API_KEY`, `AI_API_KEY`, and database credentials. Only `.env.example` is safe to commit.
Change the default admin credentials (`admin` / `admin123`) before any production deployment.
`SECRET_KEY` should be a strong, randomly generated value in production.
API docs (`/docs`) are disabled in production via `ENVIRONMENT=production`.
Secrets in `config.py` are marked `exclude=True` so they never appear in logs or settings dumps.


---



## License



Internal / proprietary — Cortex XDR AI-Powered SOC Dashboard. 