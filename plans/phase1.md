# Phase 1 plan — AI Infrastructure Radar v1

## Goal
Ship a local-first v1 that ingests four source families, normalizes them into entities and events, scores them, and renders a daily brief plus dashboard.

## Milestone 0 — docs and guardrails
- Add PRD
- Add AGENTS.md
- Add status log

## Milestone 1 — scaffold and schema
### Deliverables
- Docker Compose
- backend + frontend scaffold
- Postgres + Redis wiring
- initial database models and migrations
- seed data and health endpoint

### Validation
- `docker compose up --build`
- health endpoint returns OK
- seeded dashboard shell renders

## Milestone 2 — ingestion adapters
### Deliverables
- arXiv adapter
- GitHub adapter
- Hugging Face adapter
- EDGAR adapter
- ingestion run logging
- raw payload persistence

### Validation
- adapter unit tests pass
- manual run persists source documents for sample queries/watchlists

## Milestone 3 — normalization and scoring
### Deliverables
- entity extraction
- alias resolution
- theme tagging
- event extraction
- score computation

### Validation
- sample source docs normalize into entities + events
- ranking output looks reasonable on seeded dataset

## Milestone 4 — API and dashboard
### Deliverables
- list/detail/search API endpoints
- dashboard widgets
- entity pages
- theme pages
- filters

### Validation
- user can browse ranked events and entity detail pages end-to-end

## Milestone 5 — briefs, watchlists, opportunities
### Deliverables
- daily brief generator
- watchlists
- opportunity queue
- analyst notes

### Validation
- latest daily brief page renders
- watchlist changes visible
- opportunity candidates present on seeded/live sample data

## Milestone 6 — hardening
### Deliverables
- integration tests
- README cleanup
- stable seed/demo flow
- lint/type/test clean run

### Validation
- fresh clone setup works
- all core commands documented
