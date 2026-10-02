# Caso 02 — fuori scope

servizio=novadc-dns
sintomo="risoluzione lenta"
finestra=-7d

## Atteso
«Non trovato»: il servizio non compare né nel wiki né nel ticketing. Nessuna diagnosi,
nessuna ipotesi generica.

## Perché è il caso più utile
Un prompt senza il vincolo «se il servizio non compare, fermarsi» produce una diagnosi
plausibile di un servizio che non esiste. È l'errore da cui il caso protegge.
