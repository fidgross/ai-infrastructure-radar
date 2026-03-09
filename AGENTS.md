# AI Infrastructure Radar — agent instructions

## Mission
Build a focused v1 of AI Infrastructure Radar according to `docs/prd/ai-infrastructure-radar-prd.md`.

## Read before doing any work
1. `docs/prd/ai-infrastructure-radar-prd.md`
2. `plans/phase1.md`
3. `docs/status.md`

## Execution rules
- For any task larger than a small bugfix, start by reviewing the milestone plan and keep changes scoped to the requested milestone.
- Do not silently expand scope.
- Prefer deterministic parsing, explicit schemas, and simple architecture.
- Optimize for a reliable local Docker Compose setup.
- Use Python 3.11 on the backend and strict TypeScript on the frontend.
- Do not introduce extra infrastructure beyond Postgres, Redis, FastAPI, Next.js, and Celery unless explicitly requested.
- Treat the app as single-user internal software in v1.
- All source adapters must be idempotent.
- All background jobs must be retry-safe.
- Every new API route must use typed request/response models.
- Every source adapter must have fixture-based tests.
- Every scoring change must be documented in code comments and `docs/status.md`.
- Update `docs/status.md` after each milestone with:
  - what changed
  - validation commands run
  - known issues / follow-ups

## Validation rules
After each milestone, run the smallest reliable validation set for the files you changed. Before declaring completion, run all relevant checks.

Backend minimum:
- formatter/lint
- unit tests for changed modules
- integration smoke tests if API surface changed

Frontend minimum:
- lint
- typecheck
- tests for changed components if present

End-to-end before milestone completion:
- bring the local stack up if infra changed
- verify the relevant page or endpoint manually

## Coding style
- Keep functions small and composable.
- Prefer clear naming over clever abstractions.
- Keep comments useful and sparse.
- Do not leave dead code.
- If you add a TODO, explain why it is deferred.

## File ownership guidance for parallel Codex tasks
To avoid thread collisions:
- Backend source adapters: `backend/app/sources/**`, `backend/tests/sources/**`
- Backend scoring/brief logic: `backend/app/scoring/**`, `backend/app/brief/**`, `backend/tests/scoring/**`
- Frontend UI: `frontend/**`
- Shared schema changes must be handled in a dedicated task and merged before parallel work starts.

## Definition of done
A task is done only when:
- code is implemented
- tests/validation pass for the requested scope
- docs/status.md is updated
- the task stops at the requested boundary
