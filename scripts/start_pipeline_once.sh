#!/bin/sh
set -eu

exec python /app/scripts/run_pipeline.py --manifest /app/config/source_manifest.json
