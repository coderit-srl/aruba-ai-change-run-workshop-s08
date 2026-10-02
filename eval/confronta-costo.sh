#!/usr/bin/env bash
# Confronta costo e tempo di due modi di rispondere alla stessa domanda:
# l'harness che cerca nel wiki con la skill cerca-procedure di S02, e rag/ask.py.
#   eval/confronta-costo.sh ["domanda" …]      (default: tre domande del golden set)
# Solo con Claude Code. Lanciarlo due volte: la prima esecuzione paga la scrittura della cache.
set -uo pipefail
cd "$(dirname "$0")/.."
: "${WIKI_URL:?WIKI_URL non impostata: esportare le variabili di .env}"
(( $# )) || set -- "Quali campi deve avere ogni pagina del wiki secondo lo standard di documentazione?" \
  "Quante connessioni contemporanee accetta la VPN, e da cosa dipende il limite?" \
  "Qual è la procedura valida per riavviare il servizio billing?"
for q in "$@"; do
  echo "### $q"
  claude -p --output-format json "$q Rispondi solo con quello che trovi nel wiki NovaDC, usando la skill cerca-procedure, e cita gli slug." </dev/null \
    | jq -r '"harness  costo: \(.total_cost_usd*10000|round/10000) USD · \(.duration_ms/1000|round) s · chiamate al modello \(.num_turns) · token letti dalla cache \(.usage.cache_read_input_tokens)"'
  uv run rag/ask.py --costo "$q" 2>/dev/null | grep '^costo:' | sed 's/^/rag      /'
done
