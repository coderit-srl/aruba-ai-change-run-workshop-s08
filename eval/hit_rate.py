"""Retrieval test sul golden set (LAB 2.2 e 2.3 di S08).

    uv run eval/hit_rate.py            # entrambe le strategie, k=5
    uv run eval/hit_rate.py --k 3 -v   # dettaglio per domanda

Per le domande con fonte, due misure:
- pagina: almeno uno slug di `context` è fra i primi k chunk
- chunk: almeno uno dei primi k chunk contiene il testo in additional_metadata.evidenza,
  cioè il pezzo che risponde davvero. È questa la misura che il chunking sposta.
Per le domande senza fonte (context vuoto) si riporta lo score del chunk migliore accanto al
minimo delle domande vere. Il margine fra i due dice se una soglia ha senso: se è negativo o
di pochi millesimi, basta una domanda nuova per invertirlo.

Misura il retrieval, non la risposta: le metriche sulla risposta (faithfulness, answer
relevancy) le calcola S07 con deepeval, su questo stesso file.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "rag"))
from comune import cerca  # noqa: E402

GOLDEN = Path(__file__).parent / "golden-set.jsonl"


def misura(strategia: str, k: int, verbose: bool):
    righe = [json.loads(l) for l in GOLDEN.read_text(encoding="utf-8").splitlines() if l.strip()]
    hit = hit_chunk = tot = 0
    score_vere: list[float] = []
    score_fuori: list[float] = []
    for g in righe:
        chunk = cerca(g["input"], k=k, strategia=strategia)
        slug = [c["slug"] for c in chunk]
        top = chunk[0]["score"] if chunk else 0.0
        if g["context"]:
            tot += 1
            score_vere.append(top)
            ok = any(s in slug for s in g["context"])
            hit += ok
            evidenza = (g.get("additional_metadata") or {}).get("evidenza", "")
            ok_chunk = bool(evidenza) and any(evidenza in c["text"] for c in chunk)
            hit_chunk += ok_chunk
            ok = ok and ok_chunk
        else:
            score_fuori.append(top)
            ok = None
        if verbose:
            esito = "--" if ok is None else ("ok" if ok else "KO")
            print(f"  {esito}  top={top:.3f}  {g['input'][:60]}")
            if ok is False:
                print(f"        attese {g['context'] or 'nessuna fonte'} · trovate {slug}")
    return hit, hit_chunk, tot, score_vere, score_fuori


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--strategia", choices=["titolo", "fissa"])
    args = ap.parse_args()
    for s in [args.strategia] if args.strategia else ["titolo", "fissa"]:
        if args.verbose:
            print(f"strategia {s}")
        hit, hit_chunk, tot, vere, fuori = misura(s, args.k, args.verbose)
        print(f"{s:8s}  k={args.k}  pagina {hit}/{tot}  ·  chunk con la risposta {hit_chunk}/{tot}")
        if fuori and vere:
            margine = min(vere) - max(fuori)
            print(f"          fuori corpus: score max {max(fuori):.3f}  ·  domande vere: min {min(vere):.3f}"
                  f"  ·  margine {margine:+.3f}")


if __name__ == "__main__":
    main()
