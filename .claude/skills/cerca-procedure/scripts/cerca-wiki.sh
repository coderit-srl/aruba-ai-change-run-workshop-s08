#!/usr/bin/env bash
# Ricerca nel wiki NovaDC: solo slug, data e titolo, per consumare meno contesto.
# Il wiki cerca il testo esatto: una parola per volta.   uso: cerca-wiki.sh <parola> [limite]
set -euo pipefail
: "${WIKI_URL:?WIKI_URL non impostata: esportare le variabili di .env}"
termine="${1:?uso: cerca-wiki.sh <parola> [limite]}"
risposta=$(curl -sS --fail-with-body -G "${WIKI_URL%/}/api/search" \
  --data-urlencode "q=$termine" --data-urlencode "limit=${2:-10}") \
  || { echo "ERRORE: il wiki non risponde. $risposta" >&2; exit 2; }
if [[ $(jq length <<<"$risposta") -eq 0 ]]; then
  echo "nessun risultato per: $termine (il wiki cerca il testo esatto: una parola per volta)"
  exit 0
fi
jq -r '.[] | "\(.slug)\t\(.updated)\t\(.title)"' <<<"$risposta"
