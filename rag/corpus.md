# Corpus del RAG

Criterio del gruppo, LAB 2.1 di S08. `rag/index.py` legge questo file: indicizza le pagine
del vault il cui slug **non** corrisponde a nessuno dei prefissi esclusi.

## Esclusi

Pagine senza contenuto operativo: verbali, stati di avanzamento, procedure amministrative,
valutazioni fornitore, note di riunioni di progetto. Nessuna risponde a una domanda del team
Run o Change, e occupano posti nel top-k.

- escludi: avanzamento-progetto-
- escludi: verbale-riunione-
- escludi: note-riunione-tecnica-
- escludi: procedura-amministrativa-
- escludi: valutazione-fornitore-

Il verbale del CAB settimanale resta dentro: parla di change reali sui sistemi.

## Inclusi, ma filtrati a ogni domanda

Le pagine con `status: superata` restano nell'indice ma sono escluse dal retrieval (filtro
`status != 'superata'` in `rag/ask.py`): così un cambio di decisione non richiede di
reindicizzare.
