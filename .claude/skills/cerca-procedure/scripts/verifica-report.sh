#!/usr/bin/env bash
# Controlla che ogni slug citato in un report esista: lo fa uno script, non il modello.
# uso: verifica-report.sh <slug> […]
# Esce con 0 se tutti esistono, 1 se qualcuno non esiste, 2 se la verifica non e' stata fatta.
set -uo pipefail
: "${WIKI_URL:?WIKI_URL non impostata: esportare le variabili di .env}"
(( $# )) || { echo "uso: verifica-report.sh <slug> [<slug> …]" >&2; exit 2; }
ko=0
for s in "$@"; do
  uri=$(jq -rn --arg s "$s" '$s|@uri')
  code=$(curl -s -o /dev/null -w '%{http_code}' "${WIKI_URL%/}/api/pages/$uri")
  case "$code" in
    200) echo "ok   $s" ;;
    404) echo "KO   $s (non esiste)"; ko=1 ;;
    *)   echo "ERRORE: verifica non eseguita, il wiki risponde $code" >&2; exit 2 ;;
  esac
done
exit $ko
