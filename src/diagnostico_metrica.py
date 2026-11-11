"""Diagnóstico da métrica de acerto: acha respostas com a FONTE certa mas marcadas como erradas.
Uso (na raiz do projeto, com o .venv ativo):  python src/diagnostico_metrica.py
Não usa GPU nem modelo. Só lê os JSON já salvos em avaliacao/resultados/."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CASOS, RESULTADOS
from avaliacao import tokens, chave_fonte, cobertura

casos = [json.loads(l) for l in open(CASOS, encoding="utf-8")]
for arq in ["B.json", "C.json", "C2.json"]:
    res = json.loads((RESULTADOS / arq).read_text(encoding="utf-8"))
    print("=" * 70, "\n", arq)
    for c in casos:
        if c["tipo"] != "resposta":
            continue
        s = res[c["id"]]["saida"]
        if not s or s["status"] != "ok":
            continue
        fonte_ok = chave_fonte(s["fonte"]) == chave_fonte(c["fonte_esperada"])
        cob = cobertura(c["palavras_chave"], s["resposta"])
        if fonte_ok and cob < 0.5:
            tr = set(tokens(s["resposta"]))
            print(f"\n{c['id']} | {c['pergunta']}")
            print("  resposta:", s["resposta"])
            print("  cobertura:", round(cob, 2), "(precisa >= 0.5)")
            for p in c["palavras_chave"]:
                tp = tokens(p)
                falta = [t for t in tp if t not in tr]
                print(f"   - '{p}' -> faltam tokens: {falta}")
