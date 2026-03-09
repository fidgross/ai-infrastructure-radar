# AI Infrastructure Radar — product requirements

## Product summary
AI Infrastructure Radar is a local-first strategy intelligence product for tracking important changes across the AI infrastructure stack and turning them into decision-ready outputs for strategy and CorpDev work.

## v1 goals
- Ingest and normalize signals from arXiv, GitHub, Hugging Face, and SEC EDGAR.
- Create canonical entities and typed events.
- Score events and entities across novelty, momentum, strategic importance, AWS relevance, CorpDev relevance, and confidence.
- Publish a daily brief with ranked items and compact reasoning.
- Provide searchable dashboards for events, entities, themes, and opportunities.
- Support watchlists and an opportunity queue.
- Run locally with Docker Compose, seeded data, and repeatable jobs.

## Non-goals
- Social firehose ingestion
- Multi-user permissions beyond a placeholder
- Full graph database stack
- Outreach or CRM automation
- Mobile app

## Product principles
- Optimize for signal, not coverage.
- Always preserve source attribution.
- Make scores explainable.
- Prefer deterministic parsing where possible.
- Use LLMs for synthesis and interpretation, not as the primary source of truth.
- Keep the first version narrow and stable.

## Source scope
Track the following in v1:
- arXiv
- GitHub repos, releases, stars, forks, issues velocity, and selected org activity
- Hugging Face models, datasets, spaces, and selected org activity
- SEC EDGAR filings for a configurable company watchlist

## Stack layers
- Compute and chips
- Cloud / AI factories / GPU clouds
- Training and inference systems
- Data and storage for AI workflows
- Developer workflow / orchestration / control plane
- Model routing / portability / gateway layer
- Commercial layer including pricing, contracts, partnerships, funding, acquisitions, and capex signals

## Event taxonomy
- `paper_published`
- `open_source_launch`
- `repo_acceleration`
- `major_release`
- `product_launch`
- `benchmark_claim`
- `pricing_change`
- `partnership`
- `funding_round`
- `acquisition`
- `public_filing_signal`
- `capex_signal`
- `commercialization_signal`
- `customer_reference`
- `executive_hire`
- `infrastructure_contract`

## Functional requirements

### FR-1 Ingestion
Each adapter must:
- be idempotent
- write raw payload snapshots
- normalize timestamps to UTC
- attach a source fingerprint to prevent duplicates
- log job run metadata

### FR-2 Normalization
Normalize all ingested material into:
- `SourceDocument`
- `Entity`
- `Event`
- `Theme`
- relationships between those objects

The normalization pipeline must:
- extract candidate entities from raw content
- resolve aliases to canonical entities
- assign a stack layer and one or more themes
- produce zero or more typed events from a source document

### FR-3 Entity resolution
Canonical entity types:
- company
- product
- repository
- paper
- person
- public_company
- theme

The system must maintain aliases and confidence scores and allow manual overrides.

### FR-4 Scoring
Every event must receive:
- `novelty_score`
- `momentum_score`
- `strategic_importance_score`
- `aws_relevance_score`
- `corpdev_score`
- `confidence_score`
- `radar_score`

Every entity must receive:
- `momentum_score`
- `aws_relevance_score`
- `corpdev_interest_score`
- `entity_priority_score`

Scoring must be explainable and reproducible.

### FR-5 Daily brief
Daily brief sections:
- Top 5 events
- Top 3 emerging entities
- Top 3 notable repos or papers
- Theme heat map summary
- Why this matters for AWS
- Possible actions
- Skeptical counterpoints

The daily brief must persist to the database and be viewable in the UI.

### FR-6 Search and filtering
Support:
- keyword search
- semantic search over source documents and summaries
- filters for time range, source family, event type, stack layer, theme, public/private, watchlist membership, and minimum score thresholds

### FR-7 Opportunity queue
Create opportunity candidates when rules are met, such as:
- high momentum plus high AWS relevance
- high CorpDev score plus repeated technical/commercial validation
- repeated watchlist presence across multiple weeks

Opportunity records must include rationale, linked events, candidate classification, risks, and an integration notes stub.

### FR-8 Watchlists
The UI must support watchlists for companies, themes, public companies, and AWS exposure areas.

### FR-9 Analyst controls
Support manual actions for:
- pinning an event
- marking an event as noise
- adjusting entity aliases
- overriding theme tags
- adding analyst notes to entities and opportunities

## Non-functional requirements
- Local-first development via Docker Compose
- P95 API latency under 500ms for common dashboard queries on seeded demo data
- Idempotent jobs with retries
- Structured logs for jobs and API
- Unit tests for adapters and scoring
- Integration tests for API and daily brief generation
- Strict TypeScript on frontend
- Typed request and response models on backend

## Technical architecture

### Backend
- Python 3.11
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Celery plus Redis
- Postgres plus pgvector
- Pydantic v2

### Frontend
- Next.js App Router
- TypeScript
- Tailwind
- React Query

### Infra
Local Docker Compose services:
- postgres
- redis
- backend
- worker
- frontend

### LLM abstraction
Implement a provider-agnostic summarization and classification interface with:
- `summarize_event(...)`
- `classify_themes(...)`
- `generate_aws_implication(...)`
- `generate_daily_brief_sections(...)`

For local development, include a deterministic stub provider and optional live provider hooks.

## Data model

### Core tables
- `source_documents`
- `source_payloads`
- `ingestion_runs`
- `entities`
- `entity_aliases`
- `themes`
- `entity_theme_links`
- `events`
- `event_entity_links`
- `event_scores`
- `entity_scores`
- `watchlists`
- `watchlist_items`
- `opportunities`
- `opportunity_event_links`
- `daily_briefs`
- `daily_brief_items`
- `analyst_notes`
- `embedding_chunks`

### Minimal schema notes
`source_documents`
- id
- source_type
- source_external_id
- title
- url
- published_at
- detected_at
- raw_text
- normalized_text
- fingerprint
- metadata_json

`entities`
- id
- entity_type
- canonical_name
- slug
- website
- description
- metadata_json
- created_at
- updated_at

`events`
- id
- event_type
- title
- summary
- why_it_matters
- skeptical_note
- occurred_at
- detected_at
- source_document_id
- stack_layer
- confidence
- status

`event_scores`
- event_id
- novelty_score
- momentum_score
- strategic_importance_score
- aws_relevance_score
- corpdev_score
- confidence_score
- radar_score
- scoring_version
- rationale_json

`entity_scores`
- entity_id
- momentum_score
- aws_relevance_score
- corpdev_interest_score
- entity_priority_score
- scoring_version
- rationale_json

`opportunities`
- id
- entity_id nullable
- theme_id nullable
- opportunity_type
- title
- rationale
- risks
- integration_notes
- priority_score
- status

## API requirements
- `GET /api/health`
- `GET /api/events`
- `GET /api/events/{id}`
- `GET /api/entities`
- `GET /api/entities/{slug}`
- `GET /api/themes`
- `GET /api/themes/{slug}`
- `GET /api/briefs/latest`
- `GET /api/opportunities`
- `GET /api/search`
- `POST /api/watchlists`
- `POST /api/watchlists/{id}/items`
- `POST /api/ingest/run/{source}`
- `POST /api/score/recompute`

List endpoints must support paging, sorting, and filters.

## Frontend requirements
Pages:
- `/`
- `/events`
- `/entities/[slug]`
- `/themes/[slug]`
- `/briefs/latest`
- `/opportunities`
- `/search`
- `/watchlists`

Dashboard widgets:
- top events
- emerging entities
- theme heat map
- watchlist changes
- opportunities
- AWS implications summary

## Ranking model
Use a deterministic weighted model for v1.

Event radar score:
- 20% novelty
- 20% momentum
- 25% strategic importance
- 20% AWS relevance
- 10% CorpDev
- 5% confidence

Entity priority score:
- weighted average of related event radar scores over 90 days
- plus acceleration bonus for recent momentum inflection
- plus manual analyst override if present

Rules:
- Deduplicate near-identical events
- Penalize repeated hype without fresh evidence
- Reward cross-source corroboration
- Reward technical plus commercial coincidence
- Reward control-point shifts

## Background job design
Queues:
- `ingest`
- `normalize`
- `score`
- `embed`
- `brief`

Jobs:
- `run_arxiv_ingest`
- `run_github_ingest`
- `run_hf_ingest`
- `run_edgar_ingest`
- `normalize_source_document`
- `resolve_entities`
- `extract_events`
- `score_events`
- `score_entities`
- `refresh_embeddings`
- `generate_daily_brief`

## Developer experience requirements
- One-command local start via `docker compose up --build`
- Seed script populates demo data and a sample daily brief
- Makefile or scripts for common commands
- Clear README with quickstart and architecture overview

## Success metrics
Engineering quality:
- adapters have fixture-driven tests
- scoring engine is deterministic under fixed input
- core API routes have integration coverage

## Milestones
### Milestone 1
- backend scaffold
- frontend scaffold
- Docker Compose
- Postgres and Redis wiring
- initial schema and migrations
- seed data

Exit criteria:
- app boots locally
- health endpoint works
- dashboard shell loads seeded data
