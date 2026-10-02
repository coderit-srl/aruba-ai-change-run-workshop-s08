"""Indicizza il vault (LAB 2.1 di S08).

    uv run rag/index.py                       # chunking per titolo (##)
    uv run rag/index.py --strategia fissa     # chunk da 400 caratteri, per il confronto del LAB 2.2

Legge le pagine del vault, esclude quelle indicate in rag/corpus.md, divide in chunk, calcola
gli embedding in locale e scrive una tabella LanceDB per strategia in rag/indice/.
"""

import argparse
import re

import lancedb

from comune import INDICE, RADICE, VAULT, embed


def front_matter(testo: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n", testo, re.S)
    if not m:
        return {}, testo
    campi = dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M))
    return {k: v.strip().strip('"') for k, v in campi.items()}, testo[m.end():]


def per_titolo(corpo: str) -> list[str]:
    """Un chunk per sezione ##; il titolo # della pagina resta attaccato alla prima."""
    parti = re.split(r"(?m)^(?=## )", corpo)
    return [p.strip() for p in parti if p.strip()]


def fissa(corpo: str, n: int = 400) -> list[str]:
    """Dimensione fissa, senza overlap: taglia dove capita, anche a metà di una procedura."""
    corpo = corpo.strip()
    return [corpo[i:i + n] for i in range(0, len(corpo), n)]


def esclusi() -> list[str]:
    testo = (RADICE / "rag" / "corpus.md").read_text(encoding="utf-8")
    return re.findall(r"^- escludi:\s*(\S+)", testo, re.M)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategia", choices=["titolo", "fissa"], default="titolo")
    args = ap.parse_args()
    dividi = per_titolo if args.strategia == "titolo" else fissa

    prefissi = esclusi()
    righe = []
    pagine = 0
    for f in sorted(f for f in VAULT.glob("*/*.md") if not f.parent.name.startswith("_")):  # _proposte/ non risponde
        if f.stem.startswith(tuple(prefissi)):
            continue
        fm, corpo = front_matter(f.read_text(encoding="utf-8"))
        pagine += 1
        for n, testo in enumerate(dividi(corpo), start=1):
            righe.append({
                "id": f"{f.stem}#{n}", "slug": f.stem, "n": n,
                "title": fm.get("title", f.stem), "space": fm.get("space", ""),
                "status": fm.get("status", "da-verificare"), "updated": fm.get("updated", ""),
                # il titolo della pagina entra nel testo indicizzato: da solo un chunk
                # "## Passi" non dice di quale procedura sono i passi
                "text": testo, "_indicizzato": f"{fm.get('title', '')}\n{testo}",
            })

    vettori = embed([r.pop("_indicizzato") for r in righe], "passage")
    for r, v in zip(righe, vettori):
        r["vector"] = v.tolist()

    INDICE.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(INDICE))
    db.create_table(args.strategia, data=righe, mode="overwrite")
    print(f"{pagine} pagine · {len(righe)} chunk · {len(righe[0]['vector'])} dimensioni "
          f"· strategia {args.strategia}")


if __name__ == "__main__":
    main()
