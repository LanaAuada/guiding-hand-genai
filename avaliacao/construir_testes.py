"""Gera avaliacao/casos_teste.jsonl e valida o gabarito contra a base.
Cada caso respondível aponta o trecho esperado e palavras-chave que DEVEM
aparecer no trecho (validação automática) e na resposta correta.
Casos 'nao_consta' não têm resposta na base: o assistente deve recusar.
Uso: python avaliacao/construir_testes.py
"""
import json, unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# (id, pergunta, trecho_esperado, [palavras-chave])
RESPONDIVEIS = [
("Q01", "O que a lei considera como pessoa com deficiência?", "T01", ["impedimento de longo prazo", "barreiras"]),
("Q02", "O que significa acessibilidade segundo a Lei Brasileira de Inclusão?", "T02", ["segurança e autonomia", "transportes"]),
("Q03", "O que é tecnologia assistiva?", "T03", ["funcionalidade", "autonomia"]),
("Q04", "O que são barreiras urbanísticas?", "T04", ["vias e nos espaços públicos"]),
("Q05", "Recusar uma adaptação razoável conta como discriminação?", "T05", ["adaptações razoáveis"]),
("Q06", "Quem comunica uma violação de direitos de pessoa com deficiência? Isso é dever de quem?", "T06", ["dever de todos"]),
("Q07", "A pessoa com deficiência tem direito a pontos de parada e terminais acessíveis no transporte coletivo?", "T07", ["pontos de parada", "terminais acessíveis"]),
("Q08", "O acompanhante da pessoa com deficiência também tem atendimento prioritário?", "T08", ["acompanhante", "extensivos"]),
("Q09", "Qual benefício mensal existe para pessoa com deficiência sem meios de subsistência?", "T09", ["1 (um) salário-mínimo"]),
("Q10", "Pode cobrar ingresso mais caro de pessoa com deficiência?", "T10", ["não poderá ser superior"]),
("Q11", "Quais elementos fazem parte do transporte coletivo para fins de acessibilidade?", "T12", ["terminais", "pontos de parada"]),
("Q12", "Que percentual das vagas de estacionamento deve ser reservado a veículos de pessoa com deficiência?", "T13", ["2%"]),
("Q13", "Os ônibus precisam informar todos os pontos do itinerário de forma acessível?", "T14", ["sistema de comunicação acessível", "itinerário"]),
("Q14", "Quanto da frota de táxi deve ser acessível?", "T15", ["10%"]),
("Q15", "O táxi pode cobrar tarifa diferente de pessoa com deficiência?", "T15", ["proibida a cobrança diferenciada"]),
("Q16", "Locadoras de veículos precisam ter carro adaptado?", "T16", ["veículo adaptado", "20 (vinte)"]),
("Q17", "As obras nas vias públicas devem garantir a livre circulação das pessoas?", "T19", ["livre circulação", "durante e após"]),
("Q18", "Sites de empresas e do governo precisam ser acessíveis?", "T20", ["sítios da internet", "acessibilidade"]),
("Q19", "Qual é a pena para quem discrimina uma pessoa por causa da deficiência?", "T22", ["1 (um) a 3 (três) anos"]),
("Q20", "Existe um cadastro nacional que registra as barreiras que impedem os direitos da pessoa com deficiência?", "T23", ["Cadastro-Inclusão", "barreiras"]),
("Q21", "Posso entrar com cão-guia em ônibus e metrô?", "T25", ["cão-guia", "todos os meios de transporte"]),
("Q22", "Quem tem direito a atendimento prioritário segundo a Lei 10.048?", "T26", ["idosos", "gestantes"]),
("Q23", "O que a lei diz sobre o passeio público, a calçada?", "T27", ["passeio público", "circulação de pedestres"]),
("Q24", "Semáforos para pedestres precisam ter sinal sonoro?", "T28", ["sinal sonoro"]),
("Q25", "Mobiliário urbano que oferece risco no caminho precisa de sinalização tátil?", "T29", ["sinalização tátil de alerta"]),
("Q26", "As cidades precisam ter plano de rotas acessíveis para os passeios públicos?", "T31", ["plano de rotas acessíveis"]),
("Q27", "Há reserva de vagas de táxi para motoristas com deficiência?", "T32", ["10% (dez por cento)", "condutores com deficiência"]),
]

# (id, pergunta, por que não consta)
NAO_CONSTA = [
("N01", "Qual o horário do ônibus 875P-10 hoje?", "dado em tempo real, fora da base"),
("N02", "Quanto custa a passagem de metrô para pessoa com deficiência visual em São Paulo?", "tarifa municipal, fora da base"),
("N03", "Qual o valor em reais da multa por estacionar em vaga reservada?", "quase-vizinha: a base fala das vagas, não do valor da multa"),
("N04", "Como solicito o passe livre interestadual?", "outra lei, fora da base"),
("N05", "Posso levar meu cachorro de estimação no metrô?", "quase-vizinha: a base só trata de cão-guia"),
("N06", "Qual o prazo para a prefeitura consertar uma calçada quebrada?", "quase-vizinha: a base fala de plano de rotas, não de prazo"),
("N07", "Qual a previsão do tempo para amanhã em São Paulo?", "fora do domínio"),
("N08", "O que a LGPD diz sobre dados de pessoas com deficiência?", "LGPD não está na base"),
]


def norm(s):
    return unicodedata.normalize("NFC", s).lower()


def main():
    trechos = {}
    for linha in open(RAIZ / "base" / "trechos.jsonl", encoding="utf-8"):
        t = json.loads(linha)
        trechos[t["id"]] = t
    casos, erros = [], []
    for id_, perg, tid, kws in RESPONDIVEIS:
        if tid not in trechos:
            erros.append(f"{id_}: trecho {tid} não existe")
            continue
        for kw in kws:
            if norm(kw) not in norm(trechos[tid]["texto"]):
                erros.append(f"{id_}: palavra-chave '{kw}' não está em {tid}")
        casos.append({"id": id_, "pergunta": perg, "tipo": "resposta",
                      "trecho_esperado": tid, "fonte_esperada": trechos[tid]["fonte"],
                      "palavras_chave": kws})
    for id_, perg, motivo in NAO_CONSTA:
        casos.append({"id": id_, "pergunta": perg, "tipo": "nao_consta",
                      "trecho_esperado": None, "fonte_esperada": None,
                      "palavras_chave": [], "motivo": motivo})
    if erros:
        print("ERROS DE GABARITO:")
        print("\n".join(erros))
        raise SystemExit(1)
    with open(RAIZ / "avaliacao" / "casos_teste.jsonl", "w", encoding="utf-8") as f:
        for c in casos:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"OK: {len(RESPONDIVEIS)} casos com resposta + {len(NAO_CONSTA)} 'não consta' = {len(casos)}")


if __name__ == "__main__":
    main()
