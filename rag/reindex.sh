#!/usr/bin/env bash
# Ricostruisce vault e indice dopo un cambio del wiki o delle decisioni, poi rimisura.
#   rag/reindex.sh
set -euo pipefail
cd "$(dirname "$0")/.."
uv run vault/crawl.py
uv run rag/index.py --strategia titolo
uv run rag/index.py --strategia fissa
uv run eval/hit_rate.py
