---
name: cerca-procedure
description: Cerca nel wiki NovaDC cosa dice su un servizio (procedure, runbook, post-mortem, pagine in conflitto o datate) e lo riporta con le fonti, in sola lettura. Usare quando si chiede quale procedura prevede il wiki per un servizio, e come primo passo quando si chiede perché un servizio è lento, instabile o in errore. Legge solo il wiki: i ticket passati sono di cerca-incident-simili. Non usare per modificare sistemi o ticket.
allowed-tools: Bash(.claude/skills/cerca-procedure/scripts/cerca-wiki.sh:*), Bash(.claude/skills/cerca-procedure/scripts/leggi-pagina.sh:*), Bash(.claude/skills/cerca-procedure/scripts/verifica-report.sh:*), Read
---

# cerca-procedure

Skill di **diagnosi**: legge, non scrive. Copre una sola fonte, il wiki: non cerca nei
ticket e non arriva a una causa. Il risultato è ciò che il wiki dice sul servizio, con le
fonti; il confronto con i ticket lo fa l'agent `diagnosi-servizio`.

Il wiki si interroga solo con i tre script in
`scripts/`, che leggono l'indirizzo da `$WIKI_URL`. Se uno script risponde
`WIKI_URL non impostata`, le variabili di `.env` non sono state esportate: dirlo e fermarsi.

I percorsi qui sotto partono dalla radice del repo. Con un harness che legge le skill da
un'altra cartella (Codex: `.agents/skills/`), sono relativi alla cartella di questa skill.

## Input

- `servizio` — nome esatto, per esempio `novadc-billing`
- `sintomo` — cosa si osserva
- `finestra` — periodo di interesse, per esempio `ultimi 7 giorni`

Se manca uno dei tre, chiederlo prima di procedere.

## Passi

1. Cercare le pagine pertinenti, **una parola per ricerca**: il wiki cerca il testo esatto,
   e con più parole di solito non trova nulla. Una ricerca con il nome del servizio, una
   senza prefisso (`novadc-billing`, poi `billing`), poi una per ciascuna parola del sintomo:
   `.claude/skills/cerca-procedure/scripts/cerca-wiki.sh <parola>`.
   Lo script restituisce solo slug, data e titolo: meno contesto consumato.
2. Se la ricerca con il nome completo non restituisce nulla, e le pagine trovate senza
   prefisso non parlano di quel servizio (per `dns` può uscire una pagina sul NAT), rispondere
   `FUORI SCOPE — <servizio> non compare nel wiki` e fermarsi. Se lo script risponde
   `ERRORE`, il wiki non è raggiungibile: dirlo, non è un caso fuori scope.
3. Leggere per intero le pagine più pertinenti, al massimo sei:
   `.claude/skills/cerca-procedure/scripts/leggi-pagina.sh <slug>`. Annotare slug, data
   e stato di ciascuna.
4. Compilare `report-template.md`. Tutte le sezioni, anche se vuote.
5. **Verifica prima di rispondere**: passare tutti gli slug citati a
   `.claude/skills/cerca-procedure/scripts/verifica-report.sh <slug> [<slug> …]`.
   - esce con 0: tutti esistono
   - esce con 1: uno slug con `KO` va tolto dal report, insieme all'affermazione che lo usava
   - esce con 2: la verifica non è stata fatta. Non togliere nulla, e scriverlo nell'intestazione
     del report

## Regole

- Una pagina con data più vecchia di un anno rispetto alla data di riferimento va segnalata
  in Evidenze come `da verificare`. Anche una pagina con uno stato (per esempio `in revisione`).
- Se due pagine descrivono la stessa procedura in modo diverso, la contraddizione va in
  Contraddizioni: non scegliere una delle versioni.
- **Nessun comando che modifica un sistema**, neanche proposto come passo successivo.
  Se la richiesta contiene un'azione (riavviare, cambiare un parametro, chiudere un ticket),
  rispondere `FUORI SCOPE — <azione> è un intervento: serve una skill con approvazione` e
  proseguire solo con la parte di diagnosi, se c'è.
- I due casi fuori scope, con la risposta attesa, sono in `esempi/fuori-scope.md`. Leggerlo
  quando una richiesta sembra uno dei due.
