# AI Infrastructure Radar

Local-first AI infrastructure intelligence tooling for tracking important technical and commercial signals, scoring them, and presenting a seeded dashboard and brief workflow.

## Milestone 1 scope
- Docker Compose stack for Postgres, Redis, FastAPI, Celery, and Next.js
- Initial SQLAlchemy schema and Alembic migrations
- Seeded demo data covering entities, events, scores, opportunities, and a daily brief
- Health endpoint plus a seeded dashboard shell

## Quickstart
1. Copy `.env.example` to `.env` if you want local overrides.
2. Run `docker compose up --build -d`.
3. Run `docker compose exec backend python /app/scripts/seed_demo_data.py`.
4. Open `http://localhost:3000`.
5. Check `http://localhost:8000/api/health`.

## Non-Docker local mode
If Docker Desktop is unavailable, you can run a usable local app against SQLite.

1. Run `make local-venv`.
2. Run `make local-bootstrap` (this recreates the local SQLite DB).
3. Run `make local-seed`.
4. In one terminal, run `make local-backend`.
5. In a second terminal, run `make frontend-install`.
6. In a third terminal, run `make frontend-dev`.
7. Open `http://localhost:3000` and `http://localhost:8000/api/health`.

## Production deployment shape
The intended v1 deployment is:
- one Linux VM
- managed Postgres
- backend and frontend as separate systemd services
- one same-origin reverse proxy routing `/api/*` to FastAPI and all other routes to Next.js
- no Redis/Celery in the production critical path yet

Production deploy assets live under `deploy/`.

Typical production flow:
1. Provision Postgres and set `DATABASE_URL`.
2. Create the backend virtualenv and install `backend/requirements.txt`.
3. Run `alembic upgrade head` from `backend/`.
4. Build the frontend with `npm ci && npm run build`.
5. Install the systemd units from `deploy/systemd/`.
6. Install the reverse-proxy config from `deploy/caddy/` or `deploy/nginx/`.
7. Start `ai-radar-backend`, `ai-radar-frontend`, and `ai-radar-pipeline.timer`.

Production env split:
- backend env: `APP_ENV=production`, `DATABASE_URL`, `BACKEND_CORS_ORIGINS=["https://app.example.com"]`
- backend env: `BACKEND_TRUSTED_HOSTS=["app.example.com","127.0.0.1","localhost","backend"]`
- frontend env: `INTERNAL_API_URL=http://127.0.0.1:8000`, `NEXT_PUBLIC_API_URL=https://app.example.com`

Do not use SQLite in production.

## Fastest hosted path
If you do not have a VM yet, the easiest path is Render Blueprint deploy:
- one `render.yaml` creates the database, backend, frontend, and pipeline
- the frontend exposes a public HTTPS URL immediately
- the backend stays private
- the frontend now proxies `/api/*` to the backend

Use the runbook in `deploy/render/README.md`.

Railway is still supported and documented in `deploy/railway/README.md`.

## Docker deployment
The current `docker-compose.yml` is for local/dev. For deployment, use `docker-compose.prod.yml`.

Production Docker stack:
- `postgres`
- `backend`
- `frontend`
- `pipeline`
- `caddy`

For a public VM:
1. Point DNS for your hostname to the VM IP.
2. Open inbound `80/tcp` and `443/tcp`.
3. Set `.env` with:
   - `APP_ENV=production`
   - `PUBLIC_BASE_URL=https://app.example.com`
   - `SITE_ADDRESS=app.example.com`
   - `BACKEND_CORS_ORIGINS=["https://app.example.com"]`
   - `BACKEND_TRUSTED_HOSTS=["app.example.com","127.0.0.1","localhost","backend"]`
   - `DATABASE_URL=...` if you are using managed Postgres instead of the bundled container
4. Run `make prod-up`

Caddy will terminate TLS automatically when `SITE_ADDRESS` is a real public hostname.

Bring it up:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Smoke checks:

```bash
curl -fsS http://127.0.0.1/api/health
curl -fsS http://127.0.0.1/api/dashboard/summary
curl -fsS http://127.0.0.1/api/operations/status
```

If the host is internet-facing, also verify:

```bash
curl -I https://app.example.com/
curl -fsS https://app.example.com/api/health
```

Useful targets:
- `make prod-build`
- `make prod-up`
- `make prod-down`
- `make prod-logs`

## Test the app without Docker
From the repo root:

```bash
make local-venv
make local-bootstrap
make local-seed
PYTHONPATH=backend DATABASE_URL=sqlite+pysqlite:///./.data/radar-dev.db .venv/bin/pytest backend/tests -q
cd frontend && npm install && npm run typecheck && npm run lint && npm run build
```

Then run the app:

```bash
make local-backend
```

In a second terminal:

```bash
make frontend-dev
```

Quick HTTP checks:

```bash
curl -fsS http://127.0.0.1:8000/api/health
curl -fsS http://127.0.0.1:8000/api/dashboard/summary
curl -fsS http://127.0.0.1:8000/api/events
```

Manual UI checks:
- Open `http://localhost:3000/`
- Open `http://localhost:3000/events`
- Open `http://localhost:3000/entities`
- Open `http://localhost:3000/themes`
- Open `http://localhost:3000/search?q=FluxRouter`
- Open `http://localhost:3000/briefs/latest`

Frontend dependency status:
- `cd frontend && npm audit --json` now returns `0` vulnerabilities after upgrading to the patched Next.js 15.5 line.

Tradeoffs of this mode:
- It is intended for app development velocity, not production-parity validation.
- SQLite is good enough for Milestones 2-5 logic work, but final verification should still happen against Docker/Postgres.
- Alembic migrations remain the source of truth for the Docker/Postgres path; the local bootstrap script creates tables directly from the ORM models.

## Manual ingestion in local mode
Once the local DB is bootstrapped, you can persist fixture-backed source documents without Docker:

```bash
PYTHONPATH=backend DATABASE_URL=sqlite+pysqlite:///./.data/radar-dev.db .venv/bin/python scripts/run_ingest.py --source arxiv --fixture backend/tests/fixtures/sources/arxiv_feed.xml
PYTHONPATH=backend DATABASE_URL=sqlite+pysqlite:///./.data/radar-dev.db .venv/bin/python scripts/run_ingest.py --source github --fixture backend/tests/fixtures/sources/github_releases.json
PYTHONPATH=backend DATABASE_URL=sqlite+pysqlite:///./.data/radar-dev.db .venv/bin/python scripts/run_ingest.py --source huggingface --fixture backend/tests/fixtures/sources/huggingface_models.json
PYTHONPATH=backend DATABASE_URL=sqlite+pysqlite:///./.data/radar-dev.db .venv/bin/python scripts/run_ingest.py --source edgar --fixture backend/tests/fixtures/sources/edgar_submissions.json
```

When external network access is available, the same script can use live queries such as:
- `--source arxiv --query "cat:cs.LG AND llm inference"`
- `--source github --repo example/fluxrouter`
- `--source huggingface --org tensorforge`
- `--source edgar --ticker NVDA`

## Normalization and scoring in local mode
After source documents exist in the database, run:

```bash
PYTHONPATH=backend DATABASE_URL=sqlite+pysqlite:///./.data/radar-dev.db .venv/bin/python scripts/run_normalize.py --limit 20
PYTHONPATH=backend DATABASE_URL=sqlite+pysqlite:///./.data/radar-dev.db .venv/bin/python scripts/run_score.py --reprocess
```

Useful local test targets:
- `make local-test-sources`
- `make local-test-normalization`
- `make local-test-scoring`
- `make local-pipeline`

## Scheduled pipeline
The checked-in production watch manifest is `config/source_manifest.json`.

Run the full sequential pipeline manually:

```bash
PYTHONPATH=backend DATABASE_URL=sqlite+pysqlite:///./.data/radar-dev.db .venv/bin/python scripts/run_pipeline.py
```

The pipeline:
1. ingests all enabled source manifest entries
2. normalizes all pending source documents
3. recomputes event and entity scores
4. upserts the current UTC daily brief
5. prints a JSON summary for scheduler logs

To inspect freshness and backlog:

```bash
curl -fsS http://127.0.0.1:8000/api/operations/status
```

## Browse surface in local mode
Once the local DB is seeded and the backend/frontend are running, the app exposes:
- `/`
- `/events`
- `/events/{event_id}`
- `/entities`
- `/entities/{slug}`
- `/themes`
- `/themes/{slug}`
- `/search`
- `/briefs/latest`
- `/opportunities`
- `/watchlists`

## Services
- `postgres`: primary data store with `pgvector`
- `redis`: Celery broker/result backend
- `backend`: FastAPI application and Alembic runner
- `worker`: Celery worker with milestone queue names preconfigured
- `frontend`: Next.js App Router app

For production, only `backend` and `frontend` are required in the request path; the scheduled pipeline runs through `scripts/run_pipeline.py` and systemd.

## Useful commands
- `make up`
- `make down`
- `make migrate`
- `make seed`
- `make backend-test`
- `make frontend-lint`
- `make frontend-typecheck`
- `make local-venv`
- `make local-bootstrap`
- `make local-backend`
- `make local-pipeline`
- `make local-test-sources`
- `make local-test-normalization`
- `make local-test-scoring`
- `make frontend-install`
- `make frontend-dev`

## Architecture
- Backend: Python 3.11, FastAPI, SQLAlchemy 2.x, Alembic, Celery
- Frontend: Next.js App Router, TypeScript, Tailwind
- Local infra: Docker Compose, Postgres, Redis

## Repository layout
- `docs/`: PRD and milestone status
- `backend/`: FastAPI app, models, migrations, and tests
- `frontend/`: Next.js dashboard shell
- `scripts/`: local helper scripts
