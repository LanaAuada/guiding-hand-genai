"""Geração fundamentada: JSON válido, citação da fonte e recusa ("não consta")."""
import json
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from config import MODELO_LLM

FORMATO = ('Responda SOMENTE com um objeto JSON, sem markdown e sem texto fora dele, no formato: '
           '{"resposta": "...", "fonte": "...", "status": "ok"}. '
           'A resposta deve ter no máximo 3 frases, em português simples.')

SYSTEM_A = ("Você é o assistente do Guiding Hand, que tira dúvidas de pessoas com deficiência visual "
            "sobre direitos, acessibilidade e transporte no Brasil. " + FORMATO +
            ' Em "fonte", cite a lei e o artigo. Se não souber, devolva '
            '{"resposta": "Não sei responder com segurança.", "fonte": null, "status": "nao_consta"}.')

SYSTEM_RAG = ("Você é o assistente do Guiding Hand, que tira dúvidas de pessoas com deficiência visual "
              "sobre direitos, acessibilidade e transporte no Brasil. Responda SOMENTE com base nos "
              "trechos de lei fornecidos. Nunca use conhecimento externo. " + FORMATO +
              ' Em "fonte", copie exatamente o nome da fonte do trecho usado (ex.: Lei 13.146/2015, art. 46, caput). '
              'Se os trechos NÃO responderem à pergunta, devolva '
              '{"resposta": "Não consta na base de conhecimento.", "fonte": null, "status": "nao_consta"}.')

RECUSA = {"resposta": "Não consta na base de conhecimento.", "fonte": None, "status": "nao_consta"}
CHAVES = {"resposta", "fonte", "status"}


class LLM:
    def __init__(self, modelo=MODELO_LLM, adaptador=None):
        self.tok = AutoTokenizer.from_pretrained(modelo)
        self.model = AutoModelForCausalLM.from_pretrained(modelo, dtype=torch.float16).to("cuda")
        if adaptador:
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.model, adaptador)
        self.model.eval()

    @torch.no_grad()
    def gerar(self, system, user, max_new_tokens=200):
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        ids = self.tok.apply_chat_template(msgs, add_generation_prompt=True,
                                           return_tensors="pt", return_dict=True).to("cuda")
        out = self.model.generate(**ids, max_new_tokens=max_new_tokens, do_sample=False)
        return self.tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()


def interpretar(texto):
    """Extrai o JSON da saída. Devolve dict válido ou None."""
    m = re.search(r"\{.*\}", texto or "", re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(d, dict) or not CHAVES <= d.keys() or d["status"] not in ("ok", "nao_consta"):
        return None
    return d


def formatar_trechos(achados):
    return "\n".join(f"[{t['id']}] {t['fonte']}: {t['texto']}" for t, _ in achados)


def montar_prompt_rag(pergunta, achados):
    return f"Trechos:\n{formatar_trechos(achados)}\n\nPergunta: {pergunta}"


def _resultado(raw, trechos_ids, top_score, gate=False):
    saida = interpretar(raw) if raw is not None else dict(RECUSA)
    return {"raw": raw, "saida": saida, "json_valido": saida is not None,
            "gate": gate, "top_score": top_score, "trechos": trechos_ids}


def responder_a(llm, pergunta):
    """Config A: o mesmo modelo, sem contexto."""
    return _resultado(llm.gerar(SYSTEM_A, pergunta), [], None)


def responder_rag(llm, buscador, pergunta, limiar=None, k=3):
    """Config B (e C, com adaptador LoRA no llm): busca + geração. Se o melhor trecho
    tiver similaridade abaixo do limiar, recusa sem chamar o modelo."""
    achados = buscador.buscar(pergunta, k=k)
    ids = [t["id"] for t, _ in achados]
    top = achados[0][1]
    if limiar is not None and top < limiar:
        return _resultado(None, ids, top, gate=True)
    return _resultado(llm.gerar(SYSTEM_RAG, montar_prompt_rag(pergunta, achados)), ids, top)
