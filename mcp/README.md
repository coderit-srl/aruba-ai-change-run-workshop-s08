# Server MCP NovaDC — copia locale

È lo stesso server che il docente fa girare per l'aula, copiato qui per poterlo estendere nel
LAB 4.2 di S02 (il tool `search_applied_changes`).

```bash
set -a; . ../.env; set +a        # WIKI_URL e TICKETS_URL puntano al sandbox del docente
uv run uvicorn app:app --port 8083
```

Poi in `.env` impostare `MCP_URL=http://localhost:8083`, riesportare le variabili e
riavviare l'harness: `/mcp` deve mostrare il tool nuovo.

`NOVADC_MCP_READONLY=true` avvia il server senza i tool di scrittura.
