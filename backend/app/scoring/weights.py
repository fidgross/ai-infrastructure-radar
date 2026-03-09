EVENT_SCORE_WEIGHTS = {
    "novelty_score": 0.20,
    "momentum_score": 0.20,
    "strategic_importance_score": 0.25,
    "aws_relevance_score": 0.20,
    "corpdev_score": 0.10,
    "confidence_score": 0.05,
}

EVENT_TYPE_WEIGHTS = {
    "paper_published": 6.6,
    "open_source_launch": 7.0,
    "repo_acceleration": 7.4,
    "major_release": 7.8,
    "product_launch": 8.0,
    "benchmark_claim": 6.2,
    "pricing_change": 6.8,
    "partnership": 8.2,
    "funding_round": 7.0,
    "acquisition": 9.0,
    "public_filing_signal": 7.1,
    "capex_signal": 8.5,
    "commercialization_signal": 7.4,
    "customer_reference": 6.9,
    "executive_hire": 5.8,
    "infrastructure_contract": 8.1,
}

STACK_LAYER_WEIGHTS = {
    "Compute and chips": 8.8,
    "Cloud / AI factories / GPU clouds": 8.7,
    "Training and inference systems": 8.4,
    "Data and storage for AI workflows": 7.3,
    "Developer workflow / orchestration / control plane": 7.8,
    "Model routing / portability / gateway layer": 8.6,
    "Commercial layer": 8.0,
}

AWS_LAYER_WEIGHTS = {
    "Compute and chips": 8.6,
    "Cloud / AI factories / GPU clouds": 8.8,
    "Training and inference systems": 8.5,
    "Data and storage for AI workflows": 7.4,
    "Developer workflow / orchestration / control plane": 8.0,
    "Model routing / portability / gateway layer": 8.7,
    "Commercial layer": 7.9,
}

THEME_AWS_BONUS = {
    "inference-economics": 0.9,
    "model-portability": 1.2,
    "ai-capex-signals": 1.0,
    "developer-workflow-control-plane": 0.8,
}

THEME_CORPDEV_BONUS = {
    "inference-economics": 0.8,
    "model-portability": 1.1,
    "ai-capex-signals": 1.0,
    "developer-workflow-control-plane": 0.6,
}

ENTITY_TYPE_CORPDEV_BONUS = {
    "company": 1.0,
    "public_company": 1.2,
    "product": 0.8,
    "repository": 0.7,
    "paper": 0.4,
    "person": 0.1,
    "theme": 0.2,
}
