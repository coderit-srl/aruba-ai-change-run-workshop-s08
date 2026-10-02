#!/usr/bin/env bash
# Una pagina del wiki NovaDC: intestazione e testo. Data e stato servono a riconoscere
# le pagine vecchie o ancora in revisione.   uso: leggi-pagina.sh <slug>
set -euo pipefail
: "${WIKI_URL:?WIKI_URL non impostata: esportare le variabili di .env}"
slug="${1:?uso: leggi-pagina.sh <slug>}"
uri=$(jq -rn --arg s "$slug" '$s|@uri')
risposta=$(curl -sS --fail-with-body "${WIKI_URL%/}/api/pages/$uri") \
  || { echo "ERRORE: pagina $slug non letta. $risposta" >&2; exit 2; }
jq -r '"slug: \(.slug)", "titolo: \(.title)", "aggiornata: \(.updated)",
  "stato: \(if .status == "" then "-" else .status end)", "autore: \(.author)",
  "", .body' <<<"$risposta"
