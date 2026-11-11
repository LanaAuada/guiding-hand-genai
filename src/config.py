"""Configuração central. Troque o modelo aqui se faltar VRAM (RTX 3050 Ti, 4 GB)."""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TRECHOS = RAIZ / "base" / "trechos.jsonl"
CASOS = RAIZ / "avaliacao" / "casos_teste.jsonl"
RESULTADOS = RAIZ / "avaliacao" / "resultados"
LIMIAR_JSON = RAIZ / "avaliacao" / "limiar.json"

# Mesmo modelo nas 3 configurações (A sem contexto, B RAG, C RAG + LoRA).
MODELO_LLM = "Qwen/Qwen2.5-1.5B-Instruct"   # fallback: "Qwen/Qwen2.5-0.5B-Instruct"
MODELO_EMBEDDING = "intfloat/multilingual-e5-small"

TOP_K = 3
SEED = 42


def carregar_limiar():
    """Limiar de similaridade escolhido no notebook 02 (avaliacao/limiar.json)."""
    if not LIMIAR_JSON.exists():
        raise FileNotFoundError("Rode primeiro o notebook 02_busca.ipynb para gerar o limiar.")
    return json.loads(LIMIAR_JSON.read_text(encoding="utf-8"))["limiar"]
