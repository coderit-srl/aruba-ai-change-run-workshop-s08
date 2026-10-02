"""Verifica che ogni citazione di un quiz esista nel vault (LAB 3.2 di S08).

    uv run formazione/verifica_quiz.py formazione/<argomento>/quiz.json

Controllo deterministico: la citazione deve comparire nella pagina indicata come fonte,
a meno di spazi e a capo. Esce con codice 1 se almeno una citazione non si trova.
"""

import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent / "vault"


def normalizza(t: str) -> str:
    return re.sub(r"\s+", " ", t.replace("**", "")).strip().lower()


def main() -> None:
    quiz = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    trovate = 0
    for i, d in enumerate(quiz, start=1):
        pagine = list(VAULT.glob(f"*/{d['fonte']}.md"))
        if not pagine:
            print(f"KO  {i}. fonte inesistente: {d['fonte']}")
            continue
        testo = normalizza(pagine[0].read_text(encoding="utf-8"))
        if "status: superata" in testo:
            print(f"KO  {i}. fonte superata: {d['fonte']}")
        elif normalizza(d["citazione"]) in testo:
            trovate += 1
            print(f"ok  {i}. {d['fonte']}")
        else:
            print(f"KO  {i}. citazione non trovata in {d['fonte']}: \"{d['citazione'][:60]}\"")
    print(f"{trovate}/{len(quiz)} citazioni trovate nel vault")
    sys.exit(0 if trovate == len(quiz) else 1)


if __name__ == "__main__":
    main()
