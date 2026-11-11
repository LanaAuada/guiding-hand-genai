"""Recalcula o placar a partir dos JSON salvos (sem GPU, sem modelo): sem e com correção de números por extenso.
Uso: python src/placar_corrigido.py"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd
pd.set_option("display.width", 250)
import avaliacao
from config import CASOS, TRECHOS, RESULTADOS, RAIZ

casos = [json.loads(l) for l in open(CASOS, encoding="utf-8")]
trechos = [json.loads(l) for l in open(TRECHOS, encoding="utf-8")]
ARQ = {"A (sem contexto)": "A.json", "B (RAG + limiar)": "B.json", "B sem limiar": "B_sem_limiar.json",
       "C (RAG + LoRA v1 + limiar)": "C.json", "C sem limiar": "C_sem_limiar.json",
       "C2 (RAG + LoRA v2 + limiar)": "C2.json", "C2 sem limiar": "C2_sem_limiar.json"}
res = {n: json.loads((RESULTADOS / a).read_text(encoding="utf-8")) for n, a in ARQ.items()}

det = {}
for flag, rot in [(False, "sem_correcao"), (True, "com_correcao")]:
    avaliacao.NORMALIZAR_NUMEROS = flag
    tab, det[rot] = avaliacao.placar(res, casos, trechos)
    print(f"\n=== PLACAR {rot.upper().replace('_', ' ')} ===")
    print(tab.T.to_string())
    tab.to_csv(RAIZ / "avaliacao" / f"placar_{rot}.csv")

print("\n=== CASOS QUE MUDARAM DE ACERTO COM A CORREÇÃO ===")
for n in ARQ:
    a, b = det["sem_correcao"][n], det["com_correcao"][n]
    mudou = a.id[a.acerto != b.acerto].tolist()
    print(f"{n}: {mudou if mudou else 'nenhum'}")

# ---------- Visto x NÃO visto no treino (v2), com a métrica corrigida ----------
log2 = json.loads((RESULTADOS / "treino_log_v2.json").read_text(encoding="utf-8"))
fora = set(log2["trechos_fora_do_treino"])
grupo = {c["id"]: ("NAO visto" if c["trecho_esperado"] in fora else "visto") for c in casos if c["tipo"] == "resposta"}
linhas = []
for n, d in det["com_correcao"].items():
    d = d[d.tipo == "resposta"].copy(); d["grupo"] = d.id.map(grupo)
    for g, sub in d.groupby("grupo"):
        linhas.append({"config": n, "grupo": g, "n": len(sub), "acerto": int(sub.acerto.sum()),
                       "citação correta": int(sub.citacao_correta.sum())})
print("\n=== VISTO x NAO VISTO (métrica corrigida) ===")
print(pd.DataFrame(linhas).pivot(index="config", columns="grupo", values=["n", "acerto", "citação correta"]).to_string())

# ---------- Erros do C2 (com limiar), métrica corrigida ----------
d = det["com_correcao"]["C2 (RAG + LoRA v2 + limiar)"]
err = d[((d.tipo == "resposta") & ~(d.acerto & d.citacao_correta)) | ((d.tipo == "nao_consta") & ~d.recusa_correta)]
print("\n=== ERROS DO C2 (com limiar) ===")
for id_ in err.id:
    c = next(x for x in casos if x["id"] == id_); r = res["C2 (RAG + LoRA v2 + limiar)"][id_]
    print(f"\n{id_} | {c['pergunta']}\n   esperado: {c['fonte_esperada'] or 'nao_consta'} | buscou: {r['trechos']} | top1: {round(r['top_score'], 3)}")
    print("   saída:", (r.get("raw") or str(r["saida"]))[:300])

# ---------- Falsos negativos possíveis: fonte certa, acerto zero (revisão manual) ----------
print("\n=== FONTE CERTA MAS ACERTO=0 (conferir à mão) ===")
for n in ["B (RAG + limiar)", "C (RAG + LoRA v1 + limiar)", "C2 (RAG + LoRA v2 + limiar)"]:
    dd = det["com_correcao"][n]
    ids = dd.id[(dd.tipo == "resposta") & dd.citacao_correta & ~dd.acerto].tolist()
    print(f"{n}: {ids if ids else 'nenhum'}")
