# /// script
# requires-python = ">=3.11"
# dependencies = ["sentence-transformers>=3"]
# ///
"""Scarica in anticipo il modello di embedding usato nel LAB 2.1 di S08.

    uv run rag/scarica_modello.py

Il download è di qualche centinaio di MB: con quindici macchine sulla stessa rete conviene
avviarlo durante il LAB 1.1, non quando serve. Il modello resta in rag/modelli/, fuori da git.

Modello multilingue e piccolo, perché il wiki è in italiano con termini tecnici inglesi e
l'indice gira in locale. Con i modelli della famiglia e5 i testi si prefissano con
"passage: " in indicizzazione e con "query: " nelle domande.
"""

from pathlib import Path

from sentence_transformers import SentenceTransformer

MODELLO = "intfloat/multilingual-e5-small"
CARTELLA = Path(__file__).parent / "modelli"

modello = SentenceTransformer(MODELLO, cache_folder=str(CARTELLA))
prova = modello.encode(["query: procedura di riavvio del servizio billing"], normalize_embeddings=True)
print(f"{MODELLO} pronto in {CARTELLA} — {prova.shape[1]} dimensioni")
