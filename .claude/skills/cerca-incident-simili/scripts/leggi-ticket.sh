#!/usr/bin/env bash
# Un ticket NovaDC per intero: campi, descrizione, commenti, collegamenti.
# Esce con 1 se il ticket non esiste: serve anche a verificare le chiavi di un report.
#   uso: leggi-ticket.sh <KEY>
set -euo pipefail
: "${TICKETS_URL:?TICKETS_URL non impostata: esportare le variabili di .env}"
key="${1:?uso: leggi-ticket.sh <KEY>}"
uri=$(jq -rn --arg s "$key" '$s|@uri')
risposta=$(curl -s -w '\n%{http_code}' "${TICKETS_URL%/}/api/issues/$uri") || risposta=$'\n000'
case "${risposta##*$'\n'}" in
  200) ;;
  404) echo "KO   $key (non esiste)"; exit 1 ;;
  *)   echo "ERRORE: il ticketing risponde ${risposta##*$'\n'}" >&2; exit 2 ;;
esac
jq -r '"\(.key)  \(.type)  \(.status)  \(.severity // "")",
  "servizi: \(.services | join(", "))   host: \(.hosts | join(", "))",
  "aperto: \(.created)   chiuso: \(.resolved // "-")",
  "titolo: \(.summary)", "", .description,
  "", "commenti:", (.comments[] | "- \(.created[0:16]) \(.author): \(.body)"),
  "collegamenti: \(.links | map("\(.type) \(.key)") | join(", ") | if . == "" then "nessuno" else . end)"
' <<<"${risposta%$'\n'*}"
