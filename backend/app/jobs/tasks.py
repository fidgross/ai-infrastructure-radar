from __future__ import annotations

from app.core.celery_app import celery_app
from app.jobs.ingest import run_source_ingest
from app.jobs.normalize import run_normalize_pipeline
from app.jobs.score import run_entity_scoring, run_event_scoring, run_scoring_pipeline


@celery_app.task(name="jobs.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="jobs.run_arxiv_ingest")
def run_arxiv_ingest(**kwargs):
    return run_source_ingest(source_type="arxiv", **kwargs).__dict__


@celery_app.task(name="jobs.run_github_ingest")
def run_github_ingest(**kwargs):
    return run_source_ingest(source_type="github", **kwargs).__dict__


@celery_app.task(name="jobs.run_hf_ingest")
def run_hf_ingest(**kwargs):
    return run_source_ingest(source_type="huggingface", **kwargs).__dict__


@celery_app.task(name="jobs.run_edgar_ingest")
def run_edgar_ingest(**kwargs):
    return run_source_ingest(source_type="edgar", **kwargs).__dict__


@celery_app.task(name="jobs.normalize_source_document")
def normalize_source_document_task(**kwargs):
    return run_normalize_pipeline(**kwargs)


@celery_app.task(name="jobs.score_events")
def score_events_task(**kwargs):
    return run_event_scoring(**kwargs)


@celery_app.task(name="jobs.score_entities")
def score_entities_task(**kwargs):
    return run_entity_scoring(**kwargs)


@celery_app.task(name="jobs.score_pipeline")
def score_pipeline_task(**kwargs):
    return run_scoring_pipeline(**kwargs)
