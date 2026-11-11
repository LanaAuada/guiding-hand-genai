"""Gera base/treino_lora.jsonl para o LoRA (Parte 5).

Regras para não contaminar o teste:
 1. Nenhuma pergunta de treino é igual a uma pergunta de teste (conferido no fim).
 2. 8 trechos ficam FORA do treino (nem como resposta, nem como contexto distrator).
    Assim dá para medir se o LoRA aprendeu o COMPORTAMENTO (JSON, citação, recusa)
    ou só decorou a base.
A resposta-alvo é extrativa: um resumo fiel do próprio trecho, citando a fonte dele.

Uso: python src/gerar_dados_treino.py
"""
import json
import random
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import RAIZ, CASOS, SEED
from prompts import SYSTEM_RAG, RECUSA, montar_prompt_rag
from respostas_treino import RESPOSTAS

FORA_DO_TREINO = ["T03", "T09", "T10", "T12", "T16", "T20", "T28", "T31"]
VERSAO = sys.argv[1] if len(sys.argv) > 1 else "v1"   # v1: alvo extrativo | v2: respostas diretas
SUFIXO = "" if VERSAO == "v1" else "_" + VERSAO
SAIDA = RAIZ / "base" / f"treino_lora{SUFIXO}.jsonl"

PERGUNTAS = {
    "T01": ["Como a lei define uma pessoa com deficiência?", "Quem é considerado pessoa com deficiência segundo o Estatuto?"],
    "T02": ["Qual é a definição legal de acessibilidade?", "Acessibilidade abrange quais espaços e serviços?"],
    "T04": ["Como a lei classifica as barreiras nos transportes?", "O que a lei entende por barreira?"],
    "T05": ["O que é considerado discriminação por deficiência?", "A pessoa com deficiência pode sofrer algum tipo de discriminação?"],
    "T06": ["Se eu presenciar uma violação de direitos de pessoa com deficiência, o que devo fazer?", "Denunciar ameaça a pessoa com deficiência é obrigação de quem?"],
    "T07": ["O atendimento prioritário vale para proteção e socorro em qualquer circunstância?", "O atendimento prioritário abrange terminais e estações acessíveis?"],
    "T08": ["O atendente pessoal também recebe os direitos de atendimento prioritário?", "Quem acompanha a pessoa com deficiência tem os mesmos direitos de prioridade?"],
    "T11": ["Como é assegurado o direito ao transporte e à mobilidade da pessoa com deficiência?", "O direito ao transporte da pessoa com deficiência é em igualdade com os demais?"],
    "T13": ["Onde devem ser reservadas vagas de estacionamento para pessoa com deficiência?", "Quantas vagas devem ser reservadas nos estacionamentos para veículos que transportam pessoa com deficiência?"],
    "T14": ["Os veículos de transporte coletivo precisam ser acessíveis?", "Há prioridade para a pessoa com deficiência no embarque e no desembarque?"],
    "T15": ["Táxis precisam ter veículos acessíveis?", "Pode haver cobrança adicional no táxi para pessoa com deficiência?"],
    "T17": ["A acessibilidade é um direito? O que ela garante?", "Para que serve a acessibilidade na vida da pessoa com deficiência?"],
    "T18": ["Quais projetos devem seguir os princípios do desenho universal?", "Quando se pode adotar adaptação razoável no lugar do desenho universal?"],
    "T19": ["Obras em calçadas e ruas podem prejudicar a acessibilidade?", "Quem deve garantir a circulação segura das pessoas durante obras nas vias públicas?"],
    "T21": ["A pessoa com deficiência tem direito a produtos de tecnologia assistiva?", "A lei garante acesso a recursos que aumentem a autonomia e a mobilidade pessoal?"],
    "T22": ["Discriminar alguém por causa da deficiência é crime?", "Incitar discriminação contra pessoa com deficiência tem punição prevista?"],
    "T23": ["O que é o Cadastro-Inclusão?", "Existe um registro público de informações sobre pessoas com deficiência e barreiras?"],
    "T24": ["A pessoa com deficiência pode ser obrigada a ir pessoalmente a órgãos públicos?", "Quando é proibido exigir o comparecimento presencial de pessoa com deficiência?"],
    "T25": ["Cão-guia pode entrar em estabelecimentos abertos ao público?", "O direito de levar cão-guia vale em transporte coletivo internacional?"],
    "T26": ["Gestantes têm atendimento prioritário?", "A partir de que idade os idosos têm atendimento prioritário?"],
    "T27": ["As vias públicas e os parques devem ser acessíveis?", "O passeio público serve para quê?"],
    "T29": ["Como deve ser sinalizado um mobiliário urbano que ofereça risco no piso?", "A sinalização tátil de alerta é exigida em quais casos?"],
    "T30": ["O que a lei entende por mobiliário urbano?", "Semáforos e bancos de praça são mobiliário urbano?"],
    "T32": ["Qual percentual das outorgas de táxi é reservado a condutores com deficiência?", "Condutores com deficiência têm vagas reservadas na outorga de táxi?"],
}

NAO_CONSTA = [
    "Qual é o endereço da prefeitura de Osasco?", "Onde posso comprar óculos de grau mais barato?",
    "Como funciona o financiamento de um carro adaptado?", "Quais ônibus de São Paulo têm elevador?",
    "Quanto ganha um motorista de táxi por mês?", "Qual a velocidade máxima permitida nas ruas da cidade?",
    "Como faço para tirar a carteira de habilitação especial?", "Existe lei que obrigue elevadores em prédios antigos?",
    "O que a Constituição diz sobre o direito de ir e vir?", "Qual a cor do bastão usado por pessoas cegas?",
    "Como funcionam os semáforos sonoros no Japão?", "Qual a distância mínima entre faixas de pedestres?",
    "Como solicito uma cadeira de rodas pelo SUS?", "Qual o melhor aplicativo de navegação para pessoas cegas?",
    "Quem paga o conserto de um ônibus quebrado?", "O que diz a lei sobre acessibilidade em escolas?",
    "Pessoa com deficiência pode se aposentar mais cedo?", "Qual a diferença entre cegueira e baixa visão?",
    "Quanto custa um cão-guia?", "Que horas abre o posto de saúde mais próximo?",
]


def resumo(texto, max_palavras=70):
    """Resumo extrativo: remove marcadores e fica com as primeiras frases (<= max_palavras)."""
    t = re.sub(r"^Para fins de aplicação desta Lei, consideram-se:\s*", "", texto)
    t = re.sub(r"\s+", " ", t.replace("[...]", " ")).strip()
    frases = re.split(r"(?<=[.;])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9])", t)
    escolhidas = []
    for f in frases:
        if escolhidas and len(" ".join(escolhidas + [f]).split()) > max_palavras:
            break
        escolhidas.append(f)
    palavras = " ".join(escolhidas).split()
    if len(palavras) > max_palavras:
        return " ".join(palavras[:max_palavras]) + "..."
    return " ".join(palavras)


def como_json(d):
    return json.dumps(d, ensure_ascii=False, separators=(",", ":"))


def _norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9 ]", "", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip()


def construir(buscar, trechos):
    """buscar(pergunta, k) -> [(trecho, score), ...]. Devolve a lista de exemplos."""
    rnd = random.Random(SEED)
    por_id = {t["id"]: t for t in trechos}
    permitidos = {i for i in por_id if i not in FORA_DO_TREINO}
    exemplos = []

    def registrar(tipo, pergunta, contexto, alvo):
        achados = [(t, 0.0) for t in contexto]
        exemplos.append({"tipo": tipo, "pergunta": pergunta, "trechos": [t["id"] for t in contexto],
                         "system": SYSTEM_RAG, "user": montar_prompt_rag(pergunta, achados),
                         "alvo": como_json(alvo)})

    for tid, perguntas in PERGUNTAS.items():
        assert tid in permitidos, f"{tid} está reservado para teste"
        gold = por_id[tid]
        for i, p in enumerate(perguntas):
            texto = RESPOSTAS[tid][i] if VERSAO == "v2" else resumo(gold["texto"])
            alvo = {"resposta": texto, "fonte": gold["fonte"], "status": "ok"}
            vizinhos = [t for t, _ in buscar(p, 10) if t["id"] in permitidos and t["id"] != tid][:6]
            for _ in range(2):  # dois contextos diferentes por pergunta
                ctx = [gold] + rnd.sample(vizinhos, 2)
                rnd.shuffle(ctx)
                registrar("resposta", p, ctx, alvo)
    for p in NAO_CONSTA:
        viz = [t for t, _ in buscar(p, 12) if t["id"] in permitidos]
        registrar("nao_consta", p, viz[:3], RECUSA)
        registrar("nao_consta", p, viz[2:5], RECUSA)
    rnd.shuffle(exemplos)
    return exemplos


def conferir_vazamento(exemplos):
    teste = {_norm(json.loads(l)["pergunta"]) for l in open(CASOS, encoding="utf-8")}
    repetidas = [e["pergunta"] for e in exemplos if _norm(e["pergunta"]) in teste]
    assert not repetidas, f"pergunta de treino igual à de teste: {repetidas}"


def main():
    from busca import Buscador
    b = Buscador()
    exemplos = construir(b.buscar, b.trechos)
    conferir_vazamento(exemplos)
    with open(SAIDA, "w", encoding="utf-8") as f:
        for e in exemplos:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    n_nc = sum(e["tipo"] == "nao_consta" for e in exemplos)
    print(f"{len(exemplos)} exemplos ({len(exemplos) - n_nc} com resposta, {n_nc} 'não consta') -> {SAIDA.name}")
    print("Trechos fora do treino:", ", ".join(FORA_DO_TREINO))


if __name__ == "__main__":
    main()
