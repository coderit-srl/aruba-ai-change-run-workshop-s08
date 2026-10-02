---
name: cerca-incident-simili
description: Cerca nel ticketing NovaDC gli incident passati simili a un sintomo su un servizio, in sola lettura. Usare quando si chiede se un problema è già successo, con che frequenza, e come era stato chiuso. Non usare per aprire, commentare o modificare ticket.
allowed-tools: Bash(.claude/skills/cerca-incident-simili/scripts/parametri-api.sh:*), Bash(.claude/skills/cerca-incident-simili/scripts/cerca-incident.sh:*), Bash(.claude/skills/cerca-incident-simili/scripts/leggi-ticket.sh:*), Read
---

# cerca-incident-simili

Skill di **diagnosi** sul ticketing. Il ticketing si interroga solo con i tre script in
`scripts/`, che leggono l'indirizzo da `$TICKETS_URL`. Le letture non richiedono token:
**non** usare né chiedere `TICKETS_API_TOKEN`.

I percorsi qui sotto partono dalla radice del repo. Con un harness che legge le skill da
un'altra cartella (Codex: `.agents/skills/`), sono relativi alla cartella di questa skill.

## Prima di tutto: la spec

I filtri disponibili e il loro significato sono nella spec OpenAPI del ticketing:
`.claude/skills/cerca-incident-simili/scripts/parametri-api.sh` li elenca con la
descrizione. Leggerli prima di costruire una ricerca: in particolare la differenza fra
`created_after` (quando il ticket è stato aperto) e `resolved_after` (quando è stato chiuso).

## Input

- `servizio` — per esempio `novadc-billing`
- `sintomo` — due o tre parole chiave
- `finestra` — facoltativa, default `-180d`

## Passi

1. Incident sul servizio che contengono una parola del sintomo, **una parola per
   ricerca**: il ticketing cerca il testo esatto.
   `.claude/skills/cerca-incident-simili/scripts/cerca-incident.sh <servizio> <parola> [finestra]`.
   Ripetere con due o tre sinonimi: il testo dei ticket è scritto da persone diverse.
   Se lo script risponde `ERRORE`, il ticketing non è raggiungibile: dirlo e fermarsi.
2. Leggere per intero i ticket più pertinenti, al massimo cinque:
   `.claude/skills/cerca-incident-simili/scripts/leggi-ticket.sh <KEY>`. I commenti sono
   testimonianze scritte durante l'emergenza: riportarli come tali, non come conclusioni.
3. Restituire una tabella: chiave, data di apertura, sintomo, causa dichiarata alla chiusura
   (o `non dichiarata`), collegamenti ad altri ticket. Sopra la tabella, i termini cercati.
4. **Verifica prima di rispondere**: ogni chiave in tabella deve essere stata letta con
   `leggi-ticket.sh` in questo lavoro. Una chiave per cui lo script risponde `KO` si toglie.

## Regole

- Nessuna scrittura sul ticketing.
- Se non si trova nulla, dirlo: «nessun incident simile nella finestra», con i termini usati.
- Contare le ricorrenze: la riga `totale` di `cerca-incident.sh` dice quanti incident
  corrispondono, anche oltre i 20 mostrati.
