---
name: modulo-formativo
description: Genera un modulo formativo interno con quiz verificabile a partire dal vault NovaDC. Usare quando si chiede materiale di formazione o un quiz su un argomento operativo. Ogni risposta del quiz deve puntare a una frase esatta del vault.
allowed-tools: Read, Grep, Glob, Write, Bash(uv run formazione/verifica_quiz.py:*)
---

# modulo-formativo

## Input

- `argomento` — per esempio «gestione delle severità e dell'escalation»
- `domande` — numero di domande del quiz, default 5

## Passi

1. Cercare nel vault le pagine sull'argomento. **Escludere** quelle con `status: superata`
   e segnalare quelle `da-verificare`: la formazione non si costruisce su pagine obsolete.
2. Scrivere `formazione/<argomento>/modulo.md`: obiettivi (tre al massimo), contenuto
   diviso per sezioni, e per ogni sezione le pagine del vault da cui viene.
3. Scrivere `formazione/<argomento>/quiz.json`, una lista di domande:

   ```json
   {"domanda": "...", "opzioni": ["a) ...", "b) ...", "c) ..."], "corretta": "b",
    "fonte": "<slug>", "citazione": "<frase copiata esattamente dal vault>"}
   ```

   Le opzioni sbagliate sono errori che un operatore farebbe davvero, non assurdità.
4. Eseguire `uv run formazione/verifica_quiz.py formazione/<argomento>/quiz.json` e
   correggere finché ogni citazione è trovata.

## Regole

- Nessuna domanda su contenuti marcati superati.
- La citazione è copiata, non parafrasata: è ciò che lo script controlla.
