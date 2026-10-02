# Decisioni sul corpus

Decisioni del gruppo nel LAB 1.2 di S08. `vault/crawl.py` le riapplica a ogni esecuzione:
le righe che iniziano con `` - `slug`: `` sono lette dallo script, il resto è per le persone.

Nessuna pagina è stata cancellata: lo standard chiede di marcare, non di rimuovere.

## Riavvio del servizio billing: tre procedure divergenti

Tre pagine descrivono il riavvio in modo incompatibile. Nessuna vale ovunque:

- `runbook-restart-billing` (runbook ufficiale): un server alla volta, togliendolo prima dal
  bilanciatore. È la più vecchia, ma è l'unica applicabile su tutti e quattro gli app server.
- `note-turno-notte-riavvii` (nota personale): tutti i server insieme con un ciclo `for`.
  Contraddice il «mai tutti insieme» del runbook ufficiale e non va seguita.
- `procedura-riavvio-servizi-applicativi` (in revisione): dichiara superate le altre, ma usa
  `novadc-ctl`, che su `app-03` e `app-04` non è installato.

Decisione: vale il runbook ufficiale finché `novadc-ctl` non è installato ovunque. La nota
personale è superata; la procedura nuova resta in revisione.

- `note-turno-notte-riavvii`: status=superata, nota=Contraddice runbook-restart-billing (mai tutti i server insieme). Vale runbook-restart-billing.
- `procedura-riavvio-servizi-applicativi`: status=in-revisione
- `runbook-restart-billing`: status=valida, supersedes=note-turno-notte-riavvii

## Pagine obsolete

- `test-di-carico-portale` (PROJ, aggiornata più di un anno e mezzo prima delle altre): le
  conclusioni sul dimensionamento vengono da un test di progetto mai ripetuto.

- `test-di-carico-portale`: status=superata, nota=Test di progetto mai ripetuto: le conclusioni sul dimensionamento non descrivono l'infrastruttura attuale.

## Link rotti

- `appunti-onboarding` rimanda a «Dimensionamento risorse database», che non esiste nel
  wiki. Link lasciato com'è, segnalato qui: non c'è una pagina con cui sostituirlo.
