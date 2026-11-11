"""Busca semântica nos trechos da base (embeddings multilingual-e5-small)."""
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from config import TRECHOS, MODELO_EMBEDDING


def carregar_trechos():
    with open(TRECHOS, encoding="utf-8") as f:
        return [json.loads(l) for l in f]


class Buscador:
    def __init__(self, trechos=None, modelo=MODELO_EMBEDDING):
        self.trechos = trechos or carregar_trechos()
        # CPU: só 32 trechos, e a VRAM fica toda para o LLM.
        self.modelo = SentenceTransformer(modelo, device="cpu")
        docs = [f"passage: {t['fonte']}. {t['texto']}" for t in self.trechos]
        self.emb = self.modelo.encode(docs, normalize_embeddings=True)

    def buscar(self, pergunta, k=3):
        """Devolve [(trecho, similaridade_cosseno), ...] do mais ao menos parecido."""
        q = self.modelo.encode([f"query: {pergunta}"], normalize_embeddings=True)[0]
        sims = self.emb @ q
        idx = np.argsort(-sims)[:k]
        return [(self.trechos[i], float(sims[i])) for i in idx]
