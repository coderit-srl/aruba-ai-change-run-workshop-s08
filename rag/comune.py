"""Pezzi condivisi da index.py, ask.py ed eval/hit_rate.py: modello, percorsi, retrieval."""

from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
VAULT = RADICE / "vault"
INDICE = RADICE / "rag" / "indice"
MODELLI = RADICE / "rag" / "modelli"
MODELLO = "intfloat/multilingual-e5-small"

_modello = None


def modello():
    """Caricato una volta sola: sono qualche secondo, e hit_rate.py fa molte domande."""
    global _modello
    if _modello is None:
        from sentence_transformers import SentenceTransformer
        _modello = SentenceTransformer(MODELLO, cache_folder=str(MODELLI))
    return _modello


def embed(testi: list[str], tipo: str):
    """I modelli e5 vogliono un prefisso: 'passage: ' per i chunk, 'query: ' per le domande."""
    return modello().encode([f"{tipo}: {t}" for t in testi], normalize_embeddings=True)


def cerca(domanda: str, k: int = 5, strategia: str = "titolo", filtra_superate: bool = True):
    """Top-k chunk per la domanda. Restituisce dizionari con slug, n, score, testo."""
    import lancedb
    tabella = lancedb.connect(str(INDICE)).open_table(strategia)
    q = tabella.search(embed([domanda], "query")[0]).distance_type("cosine").limit(k)
    if filtra_superate:
        q = q.where("status != 'superata'", prefilter=True)
    righe = q.to_list()
    for r in righe:
        r["score"] = 1 - r.pop("_distance")
    return righe
