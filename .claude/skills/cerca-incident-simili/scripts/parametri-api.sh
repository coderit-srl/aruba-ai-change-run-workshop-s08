#!/usr/bin/env bash
# I filtri di GET /api/issues, letti dalla spec OpenAPI del ticketing: nome e descrizione.
#   parametri-api.sh
# Legge la documentazione dell'API invece di copiarla nella skill.
set -euo pipefail
: "${TICKETS_URL:?TICKETS_URL non impostata: esportare le variabili di .env}"
curl -sS --fail-with-body "${TICKETS_URL%/}/api/openapi.json" \
  | jq -r '.paths["/api/issues"].get.parameters[] | "\(.name)\t\(.description // "")"'
