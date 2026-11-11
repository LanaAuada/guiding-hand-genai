"""Métricas do placar. Funciona para qualquer configuração (A, B, C)."""
import re
import unicodedata
import pandas as pd


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def tokens(s):
    return re.findall(r"[a-z0-9%]+", sem_acento(s.lower()))


def chave_fonte(fonte):
    """('13146', '2015', '46') a partir de 'Lei 13.146/2015, art. 46, caput'. None se não achar."""
    if not fonte:
        return None
    s = sem_acento(str(fonte).lower())
    lei = re.search(r"(\d{1,2})\.?(\d{3})\s*/\s*(\d{4})", s)
    art = re.search(r"art\.?\s*(\d+)\s*[o°]?\s*(?:-\s*([a-z]))?", s)
    if not lei or not art:
        return None
    return (lei.group(1) + lei.group(2), lei.group(3), art.group(1) + (art.group(2) or ""))


def cobertura(palavras, resposta):
    """Fração das palavras-chave presentes na resposta (>=70% dos tokens da palavra-chave)."""
    if not palavras:
        return 1.0
    tr = set(tokens(resposta or ""))
    achou = 0
    for p in palavras:
        tp = tokens(p)
        if tp and sum(t in tr for t in tp) / len(tp) >= 0.7:
            achou += 1
    return achou / len(palavras)


def avaliar_caso(caso, res, chaves_base):
    saida = res["saida"]
    ok = bool(saida) and saida["status"] == "ok"
    e_resp = caso["tipo"] == "resposta"
    chave = chave_fonte(saida["fonte"]) if saida else None
    linha = {"id": caso["id"], "tipo": caso["tipo"], "json_valido": res["json_valido"]}
    linha["acerto"] = (e_resp and ok and cobertura(caso["palavras_chave"], saida["resposta"]) >= 0.5)
    linha["citacao_correta"] = (e_resp and ok and chave is not None
                                and chave == chave_fonte(caso["fonte_esperada"]))
    linha["recusa_correta"] = (not e_resp) and bool(saida) and saida["status"] == "nao_consta"
    linha["recusa_indevida"] = e_resp and bool(saida) and saida["status"] == "nao_consta"
    # alucinação: respondeu o que não consta, OU deu uma fonte que não existe na base
    linha["alucinacao"] = ((not e_resp and ok) or (e_resp and ok and chave not in chaves_base))
    return linha


def placar(resultados_por_config, casos, trechos):
    chaves_base = {chave_fonte(t["fonte"]) for t in trechos}
    n_resp = sum(c["tipo"] == "resposta" for c in casos)
    n_nc = len(casos) - n_resp
    linhas, detalhes = [], {}
    for nome, resultados in resultados_por_config.items():
        det = pd.DataFrame([avaliar_caso(c, resultados[c["id"]], chaves_base) for c in casos])
        detalhes[nome] = det
        linhas.append({
            "config": nome,
            f"acerto (/{n_resp})": int(det.acerto.sum()),
            f"citação correta (/{n_resp})": int(det.citacao_correta.sum()),
            f"recusa correta (/{n_nc})": int(det.recusa_correta.sum()),
            f"recusa indevida (/{n_resp})": int(det.recusa_indevida.sum()),
            f"JSON válido (/{len(casos)})": int(det.json_valido.sum()),
            f"alucinação (/{len(casos)})": int(det.alucinacao.sum()),
            "taxa de alucinação": f"{det.alucinacao.mean():.0%}",
        })
    return pd.DataFrame(linhas).set_index("config"), detalhes
