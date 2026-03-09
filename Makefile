PROJECT=ai-infrastructure-radar
LOCAL_DATABASE_URL=sqlite+pysqlite:///./.data/radar-dev.db
VENV_PYTHON=.venv/bin/python
VENV_PIP=.venv/bin/pip
VENV_UVICORN=.venv/bin/uvicorn

.PHONY: up down logs migrate seed backend-test frontend-lint frontend-typecheck prod-build prod-up prod-down prod-logs local-venv local-bootstrap local-seed local-backend local-pipeline local-test-sources local-test-normalization local-test-scoring frontend-install frontend-dev

up:
	docker compose up --build -d

down:
	docker compose down --remove-orphans

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python /app/scripts/seed_demo_data.py

backend-test:
	docker compose exec backend pytest /app/backend/tests -q

frontend-lint:
	docker compose exec frontend npm run lint

frontend-typecheck:
	docker compose exec frontend npm run typecheck

prod-build:
	docker compose -f docker-compose.prod.yml build

prod-up:
	docker compose -f docker-compose.prod.yml up --build -d

prod-down:
	docker compose -f docker-compose.prod.yml down --remove-orphans

prod-logs:
	docker compose -f docker-compose.prod.yml logs -f --tail=200

local-venv:
	python3 -m venv .venv
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r backend/requirements.txt

local-bootstrap:
	mkdir -p .data
	PYTHONPATH=backend DATABASE_URL=$(LOCAL_DATABASE_URL) $(VENV_PYTHON) scripts/bootstrap_local_db.py

local-seed:
	mkdir -p .data
	PYTHONPATH=backend DATABASE_URL=$(LOCAL_DATABASE_URL) $(VENV_PYTHON) scripts/seed_demo_data.py

local-backend:
	mkdir -p .data
	PYTHONPATH=backend DATABASE_URL=$(LOCAL_DATABASE_URL) BACKEND_CORS_ORIGINS='["http://localhost:3000"]' $(VENV_UVICORN) app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000

local-pipeline:
	mkdir -p .data
	PYTHONPATH=backend DATABASE_URL=$(LOCAL_DATABASE_URL) $(VENV_PYTHON) scripts/run_pipeline.py

local-test-sources:
	PYTHONPATH=backend DATABASE_URL=$(LOCAL_DATABASE_URL) $(VENV_PYTHON) -m pytest backend/tests/sources -q

local-test-normalization:
	PYTHONPATH=backend DATABASE_URL=$(LOCAL_DATABASE_URL) $(VENV_PYTHON) -m pytest backend/tests/normalization -q

local-test-scoring:
	PYTHONPATH=backend DATABASE_URL=$(LOCAL_DATABASE_URL) $(VENV_PYTHON) -m pytest backend/tests/scoring -q

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && INTERNAL_API_URL=http://localhost:8000 NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
