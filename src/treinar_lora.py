"""Treina o LoRA (QLoRA 4-bit) em GPU de 4 GB. Salva o adaptador em modelo-lora/.

Pré-requisito: python src/gerar_dados_treino.py [v1|v2]
Uso:           python src/treinar_lora.py [v1|v2]   (v2 = respostas diretas)
IMPORTANTE: feche os notebooks que estejam com o modelo carregado (03, 04) antes de rodar,
senão a GPU não tem memória livre.
"""
import json
import random
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import MODELO_LLM, RAIZ, RESULTADOS, SEED
from gerar_dados_treino import FORA_DO_TREINO

VERSAO = sys.argv[1] if len(sys.argv) > 1 else "v1"
SUFIXO = "" if VERSAO == "v1" else "_" + VERSAO
DADOS = RAIZ / "base" / f"treino_lora{SUFIXO}.jsonl"
SAIDA = RAIZ / f"modelo-lora{SUFIXO}"
LOG = RESULTADOS / f"treino_log{SUFIXO}.json"

EPOCAS = 3
LR = 2e-4
ACUMULACAO = 4        # exemplos por passo do otimizador (batch efetivo)
MAX_TOKENS = 1000     # exemplos maiores que isso são descartados
LORA = dict(r=8, lora_alpha=16, lora_dropout=0.05, task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])


def codificar(tok, ex):
    msgs = [{"role": "system", "content": ex["system"]}, {"role": "user", "content": ex["user"]}]
    prompt = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
    p = tok(prompt, add_special_tokens=False)["input_ids"]
    a = tok(ex["alvo"] + "<|im_end|>", add_special_tokens=False)["input_ids"]
    return p, a


def perda(model, p, a):
    """Perda só nos tokens da resposta. logits_to_keep poupa memória (só calcula o final)."""
    ids = torch.tensor([p + a], device="cuda")
    n = len(a)
    try:
        out = model(input_ids=ids, logits_to_keep=n + 1)
    except TypeError:
        out = model(input_ids=ids)
    logits = out.logits[:, -(n + 1):-1, :].float()
    return F.cross_entropy(logits.reshape(-1, logits.size(-1)), ids[:, -n:].reshape(-1))


def main():
    random.seed(SEED)
    torch.manual_seed(SEED)
    exemplos = [json.loads(l) for l in open(DADOS, encoding="utf-8")]
    tok = AutoTokenizer.from_pretrained(MODELO_LLM)
    pares = [codificar(tok, e) for e in exemplos]
    pares = [(p, a) for p, a in pares if len(p) + len(a) <= MAX_TOKENS]
    print(f"{len(pares)} de {len(exemplos)} exemplos usados (limite {MAX_TOKENS} tokens)")

    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    model = AutoModelForCausalLM.from_pretrained(MODELO_LLM, quantization_config=bnb,
                                                 device_map={"": 0}, dtype=torch.bfloat16)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    model.config.use_cache = False
    model = get_peft_model(model, LoraConfig(**LORA))
    model.print_trainable_parameters()

    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=LR, weight_decay=0.0)
    passos_total = EPOCAS * (len(pares) // ACUMULACAO)
    aquece = max(1, passos_total // 10)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min((s + 1) / aquece, max(0.05, (passos_total - s) / max(1, passos_total - aquece))))

    model.train()
    perdas_passo, perdas_epoca, t0, passo = [], [], time.time(), 0
    for ep in range(EPOCAS):
        random.shuffle(pares)
        soma_ep, acum, soma_acum = [], 0, 0.0
        for p, a in pares:
            with torch.autocast("cuda", dtype=torch.bfloat16):
                loss = perda(model, p, a)
            (loss / ACUMULACAO).backward()
            soma_ep.append(loss.item())
            soma_acum += loss.item()
            acum += 1
            if acum == ACUMULACAO:
                torch.nn.utils.clip_grad_norm_(params, 1.0)
                opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
                passo += 1
                perdas_passo.append(round(soma_acum / ACUMULACAO, 4))
                print(f"época {ep + 1}/{EPOCAS} · passo {passo}/{passos_total} · perda {perdas_passo[-1]:.4f}"
                      f" · {time.time() - t0:.0f}s", flush=True)
                acum, soma_acum = 0, 0.0
        perdas_epoca.append(round(sum(soma_ep) / len(soma_ep), 4))
        print(f"== fim da época {ep + 1}: perda média {perdas_epoca[-1]:.4f}", flush=True)

    SAIDA.mkdir(exist_ok=True)
    model.save_pretrained(SAIDA)
    RESULTADOS.mkdir(exist_ok=True)
    LOG.write_text(json.dumps({
        "modelo_base": MODELO_LLM, "quantizacao": "nf4 4-bit (QLoRA)", "lora": LORA,
        "epocas": EPOCAS, "lr": LR, "batch_efetivo": ACUMULACAO, "n_exemplos": len(pares),
        "trechos_fora_do_treino": FORA_DO_TREINO, "perda_por_passo": perdas_passo,
        "perda_por_epoca": perdas_epoca, "segundos": round(time.time() - t0),
        "vram_pico_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Adaptador salvo em {SAIDA} | VRAM pico: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")


if __name__ == "__main__":
    main()
