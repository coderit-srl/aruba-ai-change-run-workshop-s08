#!/usr/bin/env bash
# Incident di un servizio che contengono una parola, dal piu' recente.
# Il ticketing cerca il testo esatto: una parola per volta.
#   uso: cerca-incident.sh <servizio> <parola> [finestra, default -180d]
set -euo pipefail
: "${TICKETS_URL:?TICKETS_URL non impostata: esportare le variabili di .env}"
(( $# >= 2 )) || { echo "uso: cerca-incident.sh <servizio> <parola> [finestra]" >&2; exit 2; }
risposta=$(curl -sS --fail-with-body -G "${TICKETS_URL%/}/api/issues" \
  --data-urlencode "type=Incident" --data-urlencode "service=$1" \
  --data-urlencode "q=$2" --data-urlencode "created_after=${3:--180d}" \
  --data-urlencode "limit=20") \
  || { echo "ERRORE: il ticketing non risponde. $risposta" >&2; exit 2; }
jq -r '"totale: \(.total)",
  (.issues[] | "\(.key)\t\(.created[0:10])\t\(.status)\t\(.summary)")' <<<"$risposta"
