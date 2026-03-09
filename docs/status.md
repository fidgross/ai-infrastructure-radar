# AI Infrastructure Radar — status log

## Current milestone
- active: Production hardening / scheduled pipeline / generated briefs
- goal: Add production deployment assets, run the full ingest->normalize->score->brief pipeline every 6 hours, and expose operational freshness status.
- owner: Codex
- started: 2026-03-08

## Last completed work
- Added production deployment assets under `deploy/` for backend/frontend systemd services, a 6-hour systemd timer for the pipeline, and an Nginx reverse-proxy template for same-origin routing.
- Added a checked-in `config/source_manifest.json` plus `scripts/run_pipeline.py` to sequentially ingest enabled sources, normalize pending documents, recompute scores, generate the current UTC brief, and emit a JSON run summary.
- Added deterministic daily brief generation from scored events and ranked entities, with same-day upsert semantics and brief-item regeneration.
- Added operational bookkeeping columns for normalization, scoring, and brief freshness, plus `GET /api/operations/status` for latest ingest runs, normalization backlog, score freshness, brief freshness, and derived overall status.
- Added backend tests for brief generation, pipeline orchestration, and operational status, plus freshness assertions in normalization/scoring tests.
- Materialized `AGENTS.md`, the PRD, and the Phase 1 plan from the prompt pack into a new repo.
- Added Docker Compose, backend and frontend Dockerfiles, a Makefile, and quickstart README.
- Implemented the FastAPI scaffold, Celery app, SQLAlchemy models, Alembic migrations, seed script, health route, and seeded dashboard summary route.
- Implemented the Next.js App Router dashboard shell wired to seeded backend data.
- Added a non-Docker host-run path using local SQLite plus bootstrap and run commands so the app can keep moving while Docker access is blocked.
- Implemented arXiv, GitHub, Hugging Face, and EDGAR adapters, a shared ingestion contract, ingestion run persistence, Celery task wrappers, a manual `run_ingest.py` CLI, and fixture-based source tests.
- Implemented deterministic normalization and scoring pipelines, including entity extraction, alias resolution, theme tagging, event extraction, scoring rationale persistence, and `run_normalize.py` / `run_score.py` host-run scripts.
- Implemented Milestone 4 browse/search APIs for events, entities, themes, briefs, opportunities, search, watchlists, and local operations routes for ingest and score recompute.
- Added frontend browse pages for events, entities, themes, event detail, latest brief, opportunities, search, and watchlists, plus navigation linking across the normalized graph.
- Validated the host-run path end to end on this machine by installing backend/frontend dependencies, bootstrapping and seeding SQLite, fixing Python 3.9 compatibility issues, passing the backend test suite, and passing frontend typecheck, lint, and production build.
- Smoke-tested the live backend over HTTP and confirmed `GET /api/health`, `GET /api/dashboard/summary`, and `GET /api/events` return seeded responses from the local SQLite app.
- Upgraded the frontend from Next.js 14.2.x to the patched 15.5.10 line, adapted the App Router page signatures for Next 15, and cleared the frontend audit to `0` vulnerabilities.

## Validation commands run
- `PYTHONPYCACHEPREFIX=/tmp/air_pycache python3 -m compileall backend scripts`
- `PYTHONPATH=backend DATABASE_URL=sqlite+pysqlite:///./.data/radar-dev.db .venv/bin/pytest backend/tests -q`
- `PYTHONPATH=backend DATABASE_URL=sqlite+pysqlite:////tmp/air-radar-dev.db .venv/bin/python scripts/bootstrap_local_db.py`
- `PYTHONPATH=backend DATABASE_URL=sqlite+pysqlite:////tmp/air-radar-dev.db .venv/bin/python scripts/run_pipeline.py --manifest /tmp/air_radar_fixture_manifest.json`
- `curl -fsS http://127.0.0.1:8001/api/operations/status`
- `PYTHONPYCACHEPREFIX=/tmp/air_pycache python3 -m compileall backend scripts`
- `docker compose config`
- `docker compose up --build -d` (blocked by Docker Desktop organization sign-in policy)
- `PYTHONPYCACHEPREFIX=/tmp/air_pycache python3 -m compileall backend scripts` after the SQLite host-run pivot
- `PYTHONPATH=backend python3 -m pytest backend/tests/sources -q` (blocked because `pytest` is not installed in the system Python environment)
- `PYTHONPYCACHEPREFIX=/tmp/air_pycache python3 -m compileall backend scripts` after Milestone 3 normalization/scoring changes
- `PYTHONPATH=backend python3 -m pytest backend/tests/normalization backend/tests/scoring -q` (blocked because `pytest` is not installed in the system Python environment)
- `PYTHONPYCACHEPREFIX=/tmp/air_pycache python3 -m compileall backend scripts` after Milestone 4 API and browse-page changes
- `make local-venv`
- `make local-bootstrap`
- `make local-seed`
- `PYTHONPATH=backend DATABASE_URL=sqlite+pysqlite:///./.data/radar-dev.db .venv/bin/pytest backend/tests -q`
- `cd frontend && npm install`
- `cd frontend && npm audit --json`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- `curl -fsS http://127.0.0.1:8000/api/health`
- `curl -fsS http://127.0.0.1:8000/api/dashboard/summary`
- `curl -fsS http://127.0.0.1:8000/api/events`

## Known issues / follow-ups
- Docker-based validation is currently blocked by Docker Desktop returning: `Sign in to continue using Docker Desktop. Membership in the [amazonians] organization is required.`
- Because the Docker stack could not start, `alembic upgrade head`, seed execution inside the container, the health curl check, and frontend page verification are still pending.
- The host-run path relies on ORM-driven table creation for SQLite and is intentionally less production-like than the Docker/Postgres flow.
- Local compatibility fixes were required because this machine only has Python 3.9 available; the repo now works there, but Docker/Postgres validation should still happen on the intended 3.11 path once Docker is available.
- `next lint` still passes, but Next.js 15 warns that the command is deprecated and should eventually be migrated to plain ESLint CLI before moving to Next 16.
- The checked-in source manifest uses live watch targets intended for production; automated tests inject fixture-based manifests to avoid network access.

## Decisions made
- Production v1 targets a single-VM deployment with managed Postgres, no Redis/Celery in the request path, same-origin routing, and a 6-hour UTC pipeline timer.
- Daily briefs are now generated deterministically from scored data and rewritten for the current UTC date on every scheduled run.
- Operational freshness is tracked with first-class timestamps on source normalization, event/entity scoring, and brief updates instead of metadata-only markers.
- The prompt pack under `/Users/gdan/Downloads/ai_infrastructure_radar_prd_codex_prompt_pack.md` is the source of truth until the repo acquires its own files.
- Milestone 1 includes a provisional `GET /api/dashboard/summary` endpoint so the seeded dashboard shell can render real database-backed content without pulling Milestone 4 API scope forward.
- Local developer velocity takes precedence over runtime parity until Docker is usable, so SQLite host-run support is now a first-class fallback path.
- Milestone 2 validation is fixture-first: adapter parsing and idempotent persistence are verified without requiring live network calls.
- Milestone 3 stays deterministic and rule-based: one primary event per source document, theme inference from keyword rules, and versioned score rationale JSON for explainability.
- Milestone 4 keeps the UI browse-first and server-rendered: read paths are exposed in the frontend now, while watchlist mutation remains API-first until interactive forms are worth the complexity.
- Local host-run support must work on Python 3.9 in this workspace, so the repo now avoids Python 3.10/3.11-only constructs in runtime-critical paths such as ORM annotations, dataclass decorators, and `datetime.UTC`.
