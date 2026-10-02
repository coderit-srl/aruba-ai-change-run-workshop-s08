# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""Costruisce il vault Obsidian dal wiki NovaDC (LAB 1.1 di S08).

    uv run vault/crawl.py

Scarica tutte le pagine via API — non dall'HTML — e scrive vault/<spazio>/<slug>.md con il
front-matter dello standard di documentazione. I riferimenti fra pagine del wiki sono in
prosa ("vedi \"Titolo\"", "Vedi anche: Titolo"): quelli che si risolvono diventano link
[[slug]], gli altri vengono elencati alla fine.

Il wiki resta la fonte: il vault ne è una copia rigenerata a ogni esecuzione.
- Le decisioni prese a mano (status, supersedes) stanno in vault/_decisioni.md e vengono
  riapplicate a ogni esecuzione: rilanciare il crawling non le perde.
- Una pagina che arriva dal wiki non si modifica nel vault: la modifica si propone in
  vault/_proposte/<slug>.md e si pubblica sul wiki. Lo script si ferma se trova una pagina
  generata modificata a mano (vault/.generato.json tiene l'impronta di ogni file scritto).
- Nessuna pagina è «valida» finché una persona non lo decide in _decisioni.md: lo stato di
  partenza è quello del wiki, oppure da-verificare.
"""

import hashlib
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import httpx

WIKI = os.environ.get("WIKI_URL", "").rstrip("/")
if not WIKI:
    sys.exit("WIKI_URL non impostata: esportare le variabili di .env")

VAULT = Path(__file__).parent
IMPRONTE = VAULT / ".generato.json"
RIFERIMENTO = re.compile(r'(?:[Vv]edi\s+"([^"]+)"|Vedi anche:\s*([^\n.]+))')


def tipo(p: dict) -> str:
    """Tipo di pagina secondo lo standard: runbook, riferimento, post-mortem, nota."""
    s, t, tag = p["slug"], p["title"].lower(), set(p.get("tags") or [])
    if p["space"] == "PM" or s.startswith("pm-"):
        return "post-mortem"
    if s.startswith(("note-", "appunti-")):
        return "nota"
    if {"runbook", "procedura"} & tag or t.startswith(("runbook", "procedura")):
        return "runbook"
    return "riferimento"


def decisioni() -> dict[str, dict]:
    """Legge vault/_decisioni.md: righe '- `slug`: status=..., supersedes=a,b'."""
    f = VAULT / "_decisioni.md"
    out: dict[str, dict] = {}
    if not f.exists():
        return out
    for m in re.finditer(r"^- `([a-z0-9-]+)`:\s*(.+)$", f.read_text(encoding="utf-8"), re.M):
        campi = dict(kv.split("=", 1) for kv in re.findall(r"(\w+=[^,;]+)", m.group(2)))
        out[m.group(1)] = {k.strip(): v.strip() for k, v in campi.items()}
    return out


def impronta(testo: str) -> str:
    return hashlib.sha256(testo.encode("utf-8")).hexdigest()


def modificate_a_mano() -> list[str]:
    """Pagine generate il cui contenuto non è più quello scritto dall'ultimo crawling."""
    if not IMPRONTE.exists():
        return []
    scritte = json.loads(IMPRONTE.read_text(encoding="utf-8"))
    return sorted(rel for rel, h in scritte.items()
                  if (VAULT / rel).exists() and impronta((VAULT / rel).read_text(encoding="utf-8")) != h)


def proposte_superate(aggiornate: dict[str, str]) -> list[str]:
    """Proposte in vault/_proposte/ scritte su una versione del wiki che nel frattempo è cambiata."""
    out = []
    for f in sorted((VAULT / "_proposte").glob("*.md")):
        testo = f.read_text(encoding="utf-8")
        fonte = re.search(r"^source: wiki/([a-z0-9-]+)$", testo, re.M)
        base = re.search(r"^updated: (\S+)$", testo, re.M)
        if fonte and base and aggiornate.get(fonte.group(1), base.group(1)) != base.group(1):
            out.append(f"{f.name}: il wiki è cambiato il {aggiornate[fonte.group(1)]}, la proposta parte dal {base.group(1)}")
    return out


def main() -> None:
    toccate = modificate_a_mano()
    if toccate:
        print("Pagine generate modificate a mano: il crawling le sovrascriverebbe.")
        for rel in toccate:
            print(f"  vault/{rel}")
        sys.exit("Spostare la modifica in vault/_proposte/ (o la decisione in vault/_decisioni.md), "
                 "ripristinare la pagina con git restore, poi rilanciare.")

    with httpx.Client(timeout=30) as c:
        elenco = c.get(f"{WIKI}/api/pages").raise_for_status().json()
        pagine = [c.get(f"{WIKI}/api/pages/{p['slug']}").raise_for_status().json() for p in elenco]

    per_titolo = {p["title"].strip().lower(): p["slug"] for p in pagine}
    oggi = max(date.fromisoformat(p["updated"]) for p in pagine)  # il "presente" del wiki
    dec = decisioni()
    non_risolti: list[tuple[str, str]] = []
    scritte: dict[str, str] = {}
    vecchie = 0

    for p in pagine:
        corpo = p["body"]

        def collega(m: re.Match) -> str:
            titolo = (m.group(1) or m.group(2)).strip()
            slug = per_titolo.get(titolo.lower())
            if slug:
                return f"{m.group(0)} → [[{slug}]]"
            non_risolti.append((p["slug"], titolo))
            return m.group(0)

        corpo = RIFERIMENTO.sub(collega, corpo)

        vecchie += (oggi - date.fromisoformat(p["updated"])).days > 365
        # «valida» la decide una persona: dal wiki arriva solo lo stato che ha già, o nessuno
        status = (p.get("status") or "da-verificare").strip().replace(" ", "-")
        d = dec.get(p["slug"], {})
        status = d.get("status", status)
        supersedes = [s for s in d.get("supersedes", "").split("|") if s]

        fm = [
            "---",
            f'title: "{p["title"]}"',
            f"type: {tipo(p)}",
            f"space: {p['space']}",
            f"updated: {p['updated']}",
            f"author: {p.get('author', '')}",
            f"status: {status}",
            f"supersedes: [{', '.join(supersedes)}]",
            f"source: wiki/{p['slug']}",
            f"tags: [{', '.join(p.get('tags') or [])}]",
            "---",
            "",
        ]
        if status == "superata":
            nota = d.get("nota", "vedi vault/_decisioni.md")
            fm += [f"> **Pagina superata.** {nota}", ""]
        dest = VAULT / p["space"] / f"{p['slug']}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        testo = "\n".join(fm) + corpo.strip() + "\n"
        dest.write_text(testo, encoding="utf-8")
        scritte[dest.relative_to(VAULT).as_posix()] = impronta(testo)

    IMPRONTE.write_text(json.dumps(scritte, indent=0, sort_keys=True) + "\n", encoding="utf-8")
    stati: dict[str, int] = {}
    for rel in scritte:
        st = re.search(r"^status: (.+)$", (VAULT / rel).read_text(encoding="utf-8"), re.M).group(1)
        stati[st] = stati.get(st, 0) + 1

    spazi = sorted({p["space"] for p in pagine})
    print(f"{len(pagine)} pagine · {len(spazi)} spazi ({', '.join(spazi)})")
    print("stato: " + " · ".join(f"{k} {v}" for k, v in sorted(stati.items()))
          + f"  (non aggiornate da più di un anno: {vecchie})")
    print(f"link non risolti: {len(non_risolti)}")
    for slug, titolo in non_risolti:
        print(f"  {slug}: \"{titolo}\"")
    for riga in proposte_superate({p["slug"]: p["updated"] for p in pagine}):
        print(f"proposta da rifare: {riga}")


if __name__ == "__main__":
    main()
