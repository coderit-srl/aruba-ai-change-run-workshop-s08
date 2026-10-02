# Costruire o adottare: i sistemi NovaDC

Decisione del gruppo, LAB 4.3 di S02. Le tre domande, in ordine: esiste un server MCP
mantenuto? Il modello conosce già il linguaggio di query e c'è una spec? Serve vincolare le
chiamate, incapsulare query difficili o nascondere una credenziale?

| Sistema | Scelta | Motivo |
|---------|--------|--------|
| Wiki | MCP custom | Sistema interno, nessun server esistente. Tre tool per intenzione: cercare, leggere, elencare. Senza MCP funziona comunque via HTTP |
| Ticketing | MCP custom | Il token di scrittura deve restare fuori dal modello; il workflow delle transizioni e la differenza fra data di apertura e di applicazione sono conoscenza da incapsulare (`search_applied_changes`) |
| Log (OpenSearch) | Server esistente o API diretta | Esistono server MCP mantenuti per OpenSearch ed Elastic, e il modello conosce la Query DSL. La pagina wiki `accesso-log-e-metriche` basta come documentazione |
| Metriche (VictoriaMetrics, Grafana) | Server esistente o API diretta | Server MCP per Grafana disponibili; l'API di VictoriaMetrics è compatibile Prometheus e il modello conosce PromQL |

## Stessa domanda, due strade

Domanda: quali change sono stati applicati su `novadc-portal` nell'ultima settimana?

- **Via OpenAPI.** L'agent legge `/api/openapi.json`, trova `resolved_after` nella
  descrizione di `/api/issues` e chiama con `curl`. Può chiamare qualsiasi endpoint. Per una
  scrittura il token dovrebbe stare nel suo ambiente.
- **Via MCP.** L'agent vede solo i tool esposti e usa `search_applied_changes`. Il token resta
  nel server; con `NOVADC_MCP_READONLY=true` i tool di scrittura non esistono.

La differenza non è la capacità, è il controllo.
