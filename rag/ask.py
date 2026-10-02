"""Risponde a una domanda sul vault, con citazioni verificate (LAB 2.1 e 2.3 di S08).

    uv run rag/ask.py "Quali campi deve avere ogni pagina del wiki?"
    uv run rag/ask.py --solo-retrieval "..."      # mostra i chunk, senza generare
    uv run rag/ask.py --costo "..."               # anche token e costo (solo con claude -p)

La generazione la fa l'harness in modalità non interattiva: RAG_LLM sceglie quale
(default "claude -p"; per esempio "codex exec" o "opencode run").

Controlli deterministici, fatti da codice e non dal modello:
- sotto la soglia di score (RAG_SOGLIA, disattivata) la domanda non arriva al modello;
- ogni citazione [slug#n] della risposta deve essere fra i chunk recuperati;
- per ogni pagina citata: lo stato nel vault, e se sul wiki è cambiata dopo l'indicizzazione.
  Il wiki è la fonte: prima di agire, la pagina si rilegge lì.

Cosa esce dalla macchina: gli embedding e la ricerca sono locali; la domanda e i pezzi
trovati vanno al modello scelto con RAG_LLM.
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import urllib.parse
import urllib.request

from comune import cerca

# Soglia sullo score del retrieval. Misurata sul golden set (eval/risultati.md): con i
# modelli e5 gli score sono compressi (0,85-0,92) e la domanda fuori corpus sta a un
# millesimo dalla domanda vera piu' bassa, o sopra: nessuna soglia e' affidabile. Resta disattivata; la difesa vera e' la regola
# "Non trovato nel corpus" nelle istruzioni piu' la verifica delle citazioni qui sotto.
SOGLIA = float(os.environ.get("RAG_SOGLIA", "0"))

ISTRUZIONI = """Rispondere in italiano usando SOLO i passaggi forniti sotto.
Ogni frase termina con la citazione del passaggio da cui viene, nella forma [slug#n].
Se i passaggi non contengono la risposta, scrivere esattamente: Non trovato nel corpus.
Se due passaggi si contraddicono, dirlo e citarli entrambi. Nessuna altra fonte.
Ogni passaggio ha uno stato. Se un passaggio citato non è «valida», scriverlo nella frase
che lo usa: per esempio «(pagina da verificare)» o «(pagina in revisione)»."""


def aggiornata_sul_wiki(slug: str) -> str | None:
    """Data di aggiornamento della pagina sul wiki, o None se il wiki non risponde."""
    wiki = os.environ.get("WIKI_URL", "").rstrip("/")
    if not wiki:
        return None
    try:
        with urllib.request.urlopen(f"{wiki}/api/pages/{urllib.parse.quote(slug)}", timeout=10) as r:
            return json.load(r).get("updated")
    except OSError:
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("domanda")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--strategia", default="titolo")
    ap.add_argument("--solo-retrieval", action="store_true")
    ap.add_argument("--costo", action="store_true", help="token e costo della chiamata (claude -p)")
    args = ap.parse_args()

    chunk = cerca(args.domanda, k=args.k, strategia=args.strategia)
    if args.solo_retrieval:
        for c in chunk:
            print(f"{c['score']:.3f}  {c['id']:45s} {c['status']}")
        return

    if not chunk or chunk[0]["score"] < SOGLIA:
        vicino = f"{chunk[0]['slug']} (score {chunk[0]['score']:.2f})" if chunk else "nessuna"
        print(f"Non trovato nel corpus. Pagina più vicina: {vicino}")
        return

    passaggi = "\n\n".join(f"[{c['id']}] {c['title']} (aggiornata {c['updated']}, stato {c['status']})\n{c['text']}"
                           for c in chunk)
    prompt = f"{ISTRUZIONI}\n\nDomanda: {args.domanda}\n\nPassaggi:\n\n{passaggi}"
    comando = shlex.split(os.environ.get("RAG_LLM", "claude -p"))
    if args.costo:
        comando += ["--output-format", "json"]
    uscita = subprocess.run(comando + [prompt], capture_output=True, text=True, check=True).stdout.strip()
    costo = None
    if args.costo:
        dati = json.loads(uscita)
        uscita, costo = dati["result"].strip(), dati
    risposta = uscita
    print(risposta)

    recuperati = {c["id"] for c in chunk}
    citate = set(re.findall(r"\[([a-z0-9-]+#\d+)\]", risposta))
    inventate = citate - recuperati
    print()
    print(f"citazioni: {len(citate)} · fuori dalla ricerca: {len(inventate)}")
    for c in sorted(inventate):
        print(f"  NON VALIDA  [{c}]")

    pagine = {c["slug"]: c for c in chunk if c["id"] in citate}
    if pagine:
        print("pagine citate (stato nel vault · confronto con il wiki):")
    for slug, c in sorted(pagine.items()):
        sul_wiki = aggiornata_sul_wiki(slug)
        if sul_wiki is None:
            confronto = "wiki non raggiungibile: confronto non fatto"
        elif sul_wiki != c["updated"]:
            confronto = f"CAMBIATA SUL WIKI il {sul_wiki}: rifare rag/reindex.sh"
        else:
            confronto = "uguale al wiki"
        print(f"  {slug:40s} {c['status']:14s} {confronto}")
    non_valide = [s for s, c in pagine.items() if c["status"] != "valida"]
    if non_valide:
        print(f"ATTENZIONE: {len(non_valide)} pagine citate non sono state approvate da nessuno. "
              "Prima di agire, rileggerle sul wiki.")
    if costo:
        u = costo.get("usage", {})
        modelli = ", ".join(costo.get("modelUsage", {})) or "?"
        print(f"costo: {costo.get('total_cost_usd', 0):.4f} USD · {costo.get('duration_ms', 0) / 1000:.0f} s · "
              f"modello {modelli} · chiamate al modello {costo.get('num_turns')} · "
              f"token in {u.get('input_tokens', 0)} + cache {u.get('cache_read_input_tokens', 0) + u.get('cache_creation_input_tokens', 0)}"
              f" · token out {u.get('output_tokens', 0)}")
    sys.exit(1 if inventate else 0)


if __name__ == "__main__":
    main()
