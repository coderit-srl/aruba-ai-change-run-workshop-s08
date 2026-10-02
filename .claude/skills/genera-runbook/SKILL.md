---
name: genera-runbook
description: Genera o aggiorna un runbook nel formato dello standard di documentazione NovaDC a partire da una fonte leggibile (script, sequenza di comandi, pagina del vault). Usare quando si chiede di documentare una procedura operativa. Scrive solo proposte in vault/_proposte/, da pubblicare sul wiki: mai sui sistemi, mai sulle pagine generate dal wiki.
allowed-tools: Read, Write, Edit, Bash(git diff:*), Bash(cp vault/:*)
---

# genera-runbook

## Input

- la fonte: percorso di uno script, di una pagina del vault, o un blocco di comandi incollato
- facoltativo: lo slug di un runbook esistente da aggiornare

## Passi

1. Leggere la fonte per intero. Numerare mentalmente le righe: ogni passo del runbook dovrà
   indicarne una.
2. Compilare `template.md`: le tre sezioni obbligatorie dello standard (quando si usa, passi
   numerati, verifica finale) più prerequisiti e rollback se la fonte li prevede.
3. **Ogni passo cita la fonte** nella forma `[file:riga]` o `[[slug]]`. Un passo necessario
   che la fonte non contiene si scrive comunque, ma marcato `[DEDOTTO — da verificare]`.
4. Se esiste già un runbook nel vault: copiarlo in `vault/_proposte/<slug>.md` e modificare
   la copia, non riscriverla. Le pagine in `vault/<spazio>/` vengono dal wiki e il crawling
   le rigenera: una modifica fatta lì si perde. L'approvazione passa dal diff
   `git diff --no-index vault/<spazio>/<slug>.md vault/_proposte/<slug>.md`, quindi le righe
   non toccate devono restare identiche, compreso `updated`, che dice da quale versione del
   wiki parte la proposta.
5. Un runbook nuovo va in `vault/_proposte/<slug>.md` con il front-matter del vault
   (`type: runbook`, `status: da-verificare` finché una persona non lo ha provato).
6. Una proposta approvata si pubblica sul wiki da chi ne è responsabile. Al crawling
   successivo la pagina arriva nel vault dal wiki, e la proposta si cancella.

## Regole

- Nessun comando viene eseguito: la skill documenta, non interviene.
- Nessun passo inventato senza marcatore. Un runbook che sembra verificato e non lo è fa più
  danni di nessun runbook.
