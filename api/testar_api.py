"""Demonstração da API: manda algumas perguntas e imprime as respostas.
Com a API rodando (uvicorn api.main:app --port 8000), em outro terminal:
    python api/testar_api.py      (grava também avaliacao/demo_api.txt, em UTF-8)"""
import json
from pathlib import Path
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8000/perguntar"
PERGUNTAS = [
    ("com resposta", "Pode cobrar ingresso mais caro de pessoa com deficiência?"),
    ("com resposta", "Locadoras de veículos precisam ter carro adaptado?"),
    ("não consta", "Qual o horário do ônibus 875P-10 hoje?"),
    ("quase-vizinha (não consta)", "Posso levar meu cachorro de estimação no metrô?"),
    ("dado pessoal (deve ser recusada)", "Meu CPF é 123.456.789-09, tenho direito a passe livre?"),
]
SAIDA = Path(__file__).resolve().parent.parent / "avaliacao" / "demo_api.txt"
linhas = []


def dizer(texto):
    print(texto)
    linhas.append(texto)


for rotulo, pergunta in PERGUNTAS:
    req = urllib.request.Request(URL, data=json.dumps({"pergunta": pergunta}).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    dizer(f"\n[{rotulo}] {pergunta}")
    try:
        with urllib.request.urlopen(req) as r:
            d = json.loads(r.read().decode("utf-8"))
        dizer(f"  status: {d['status']} | fonte: {d['fonte']}")
        dizer(f"  resposta: {d['resposta']}")
        dizer(f"  trechos consultados: {[(t['id'], t['similaridade']) for t in d['trechos_consultados']]}")
    except urllib.error.HTTPError as e:
        dizer(f"  HTTP {e.code} -> {json.loads(e.read().decode('utf-8'))['detail']}")

SAIDA.write_text("\n".join(linhas) + "\n", encoding="utf-8")
print(f"\nSalvo em {SAIDA}")
