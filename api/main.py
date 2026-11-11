"""API do assistente Guiding Hand (FastAPI). Config final: RAG + LoRA v2 + limiar.

Rodar (na raiz do projeto, com o .venv ativo):
    uvicorn api.main:app --port 8000
Documentação interativa: http://127.0.0.1:8000/docs

LGPD (privacidade por desenho):
  * a base é só texto de lei (domínio público): nenhum dado pessoal é usado;
  * a pergunta NÃO é gravada em disco nem nos logs (o log guarda só status, similaridade e tempo);
  * perguntas com CPF, e-mail ou telefone são recusadas (minimização);
  * o modelo roda local: nada é enviado a serviços externos.
"""
import re
import sys
import threading
import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))   # módulos do projeto ficam em src/

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config import RAIZ, carregar_limiar
from prompts import RECUSA
from avaliacao import chave_fonte
from geracao import responder_rag

log = logging.getLogger("guiding_hand")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

ADAPTADOR = RAIZ / "modelo-lora_v2"
AVISO = "Informação jurídica geral, baseada só nos trechos citados. Não substitui orientação de um profissional."

# dados pessoais que a pergunta NÃO deve conter (minimização, LGPD art. 6º, III)
PADROES_PII = {
    "CPF": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    "e-mail": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "telefone": re.compile(r"(?:\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}\b"),
}


class Pergunta(BaseModel):
    pergunta: str = Field(..., min_length=5, max_length=300, examples=["Posso entrar com cão-guia no metrô?"])


class TrechoConsultado(BaseModel):
    id: str
    fonte: str
    similaridade: float


class Resposta(BaseModel):
    resposta: str
    fonte: str | None
    status: str                       # "ok" ou "nao_consta"
    trecho_citado: str | None         # texto do trecho da base que sustenta a resposta (explicabilidade)
    trechos_consultados: list[TrechoConsultado]
    aviso: str = AVISO


def detectar_pii(texto):
    return [nome for nome, rx in PADROES_PII.items() if rx.search(texto)]


def processar(estado, pergunta):
    """Lógica da rota, separada para poder ser testada sem GPU."""
    t0 = time.time()
    with estado["trava"]:                      # um pedido por vez na GPU
        r = responder_rag(estado["llm"], estado["buscador"], pergunta, limiar=estado["limiar"])
    por_id = {t["id"]: t for t in estado["trechos"]}
    consultados = [TrechoConsultado(id=i, fonte=por_id[i]["fonte"], similaridade=0.0) for i in r["trechos"]]
    saida, motivo = r["saida"], None
    if saida is None:                          # JSON inválido: recusa segura em vez de repassar lixo
        saida, motivo = dict(RECUSA), "json_invalido"
    elif saida["status"] == "ok" and chave_fonte(saida["fonte"]) not in estado["chaves_base"]:
        saida, motivo = dict(RECUSA), "fonte_inexistente"    # a fonte citada não existe na base
    elif r["gate"]:
        motivo = "abaixo_do_limiar"
    citado = None
    if saida["status"] == "ok":
        citado = next((t["texto"] for t in estado["trechos"]
                       if chave_fonte(t["fonte"]) == chave_fonte(saida["fonte"])), None)
    # log sem o texto da pergunta (LGPD)
    log.info("status=%s motivo=%s top1=%.3f tempo=%.1fs", saida["status"], motivo, r["top_score"], time.time() - t0)
    if consultados:
        consultados[0].similaridade = round(r["top_score"], 4)
    return Resposta(resposta=saida["resposta"], fonte=saida["fonte"], status=saida["status"],
                    trecho_citado=citado, trechos_consultados=consultados)


@asynccontextmanager
async def ciclo_de_vida(app):
    from busca import Buscador, carregar_trechos
    from geracao import LLM
    trechos = carregar_trechos()
    adaptador = str(ADAPTADOR) if ADAPTADOR.exists() else None
    log.info("adaptador LoRA: %s", adaptador or "NÃO encontrado (usando o modelo base)")
    app.state.g = {"trechos": trechos, "buscador": Buscador(trechos), "llm": LLM(adaptador=adaptador),
                   "limiar": carregar_limiar(), "chaves_base": {chave_fonte(t["fonte"]) for t in trechos},
                   "trava": threading.Lock()}
    yield


app = FastAPI(title="Guiding Hand · assistente de direitos e mobilidade", version="1.0", lifespan=ciclo_de_vida,
              description="RAG + LoRA sobre a Lei Brasileira de Inclusão e leis correlatas. Responde em JSON, cita a fonte e recusa o que não consta.")


@app.get("/saude")
def saude():
    return {"status": "ok"}


@app.get("/privacidade")
def privacidade():
    return {"dados_pessoais_na_base": False, "pergunta_gravada": False, "log_guarda": "status, similaridade e tempo",
            "perguntas_com_cpf_email_telefone": "recusadas", "processamento": "local, sem serviços externos"}


@app.post("/perguntar", response_model=Resposta)
def perguntar(corpo: Pergunta):
    pii = detectar_pii(corpo.pergunta)
    if pii:
        raise HTTPException(422, f"A pergunta parece conter dados pessoais ({', '.join(pii)}). Remova-os e tente de novo.")
    return processar(app.state.g, corpo.pergunta)
