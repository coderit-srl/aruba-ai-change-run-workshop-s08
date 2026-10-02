# Risultati del retrieval test

Golden set: `eval/golden-set.jsonl`, 11 domande con risposta nel corpus e 1 senza.
Corpus: 24 pagine del vault (criterio in `rag/corpus.md`). Embedding: `multilingual-e5-small`,
in locale. Misura: `uv run eval/hit_rate.py --k <k>`.

## Chunking

| Strategia | k | Pagina giusta nel top-k | Chunk con la risposta nel top-k |
|-----------|---|-------------------------|----------------------------------|
| Per titolo (`##`) | 1 | 11/11 | 10/11 |
| Dimensione fissa, 400 caratteri | 1 | 11/11 | 9/11 |
| Per titolo (`##`) | 3 | 11/11 | 11/11 |
| Dimensione fissa, 400 caratteri | 3 | 11/11 | 10/11 |
| Per titolo (`##`) | 5 | 11/11 | 11/11 |
| Dimensione fissa, 400 caratteri | 5 | 11/11 | 10/11 |

Trovare la pagina giusta è facile su questo corpus: escluso il rumore, le pagine sono poche e
con un lessico distintivo. La differenza fra strategie si vede solo chiedendo se il chunk
recuperato **contiene** la risposta: a dimensione fissa, una frase finisce a cavallo di due
chunk e nessuno dei due la contiene intera.

Scelta: chunking per titolo, k=5. Con 11 domande la differenza fra le due strategie è una
domanda sola: indica una tendenza, non la dimostra.

## Domanda fuori corpus

«Qual è la retention dei log in OpenSearch?» non ha risposta nel wiki.

| Strategia | Score della domanda fuori corpus | Minimo delle domande vere | Margine |
|-----------|----------------------------------|---------------------------|---------|
| Per titolo | 0,854 | 0,855 | +0,001 |
| Dimensione fissa | 0,860 | 0,855 | −0,005 |

Con i modelli e5 gli score sono compressi (0,85–0,92). Per titolo la domanda fuori corpus
resta sotto quella vera più bassa di un millesimo: basta una domanda nuova per invertirlo. A
dimensione fissa è sopra. Una soglia sullo score non è una difesa affidabile.

Difesa adottata: la regola «Non trovato nel corpus» nelle istruzioni di `rag/ask.py`, e la
verifica in codice che ogni citazione sia fra i chunk recuperati. Con la regola, il modello
risponde «Non trovato nel corpus.» e non cita nulla.

Da provare: un reranker multilingue sui primi 20 chunk, per vedere se i suoi score separano.

## RAG o harness che cerca nel wiki (01/10)

La critica attesa in aula: «l'harness può cercare nel wiki da solo, e il wiki non va mai
fuori data». Misurato con `eval/confronta-costo.sh` su tre domande del golden set, con
Claude Code (`claude -p`, modello claude-opus-5-5) da entrambe le parti: da una parte l'harness
con la skill `cerca-procedure` di S02, dall'altra `rag/ask.py --costo`. Cache già calda.

| Domanda | Harness: costo · tempo · chiamate | RAG: costo · tempo · chiamate |
|---------|-----------------------------------|-------------------------------|
| Campi obbligatori dello standard | 0,10 USD · 27 s · 7 | 0,016 USD · 6 s · 1 |
| Connessioni della VPN | 0,15 USD · 34 s · 8 | 0,013 USD · 5 s · 1 |
| Procedura di riavvio del billing | 0,17 USD · 42 s · 6 | 0,030 USD · 12 s · 1 |

- L'harness arriva alla pagina giusta: cercando una parola per volta, ogni domanda del golden
  set ha almeno una parola che la trova. La domanda intera, invece, non trova mai nulla: il
  wiki cerca il testo esatto. Circa metà delle parole di ciascuna domanda non porta alla pagina.
- Il costo dell'harness viene dai giri: 6-8 chiamate al modello, e ogni chiamata rilegge
  tutto il contesto (200-285 mila token letti dalla cache, contro 39 mila del RAG).
- A cache fredda la differenza si riduce: la prima chiamata paga la scrittura della cache
  (harness 0,31-0,37 USD, RAG 0,22-0,24 USD).
- I 39 mila token del RAG sono quasi tutti il contesto di Claude Code: i pezzi trovati sono
  circa 250 token. Con una chiamata diretta all'API il costo del RAG scende di un ordine di
  grandezza; quello dell'harness no, perché i giri restano.
- Aggiornare il RAG non costa token: crawling e embedding girano in locale.
- Su NovaDC le pagine sono piccole (in media circa 220 token). Su un wiki reale, con pagine
  da 5-20 mila token, ogni pagina letta dall'harness pesa su tutti i giri successivi.

