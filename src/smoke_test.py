import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from config import MODELO_LLM

print("Modelo:", MODELO_LLM)
tok = AutoTokenizer.from_pretrained(MODELO_LLM)
model = AutoModelForCausalLM.from_pretrained(MODELO_LLM, torch_dtype=torch.float16).to("cuda")

msgs = [{"role": "user", "content": "Em uma frase: o que é acessibilidade?"}]
ids = tok.apply_chat_template(msgs, add_generation_prompt=True,
                              return_tensors="pt", return_dict=True).to("cuda")
out = model.generate(**ids, max_new_tokens=60, do_sample=False)
print(tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True))
print("VRAM pico (GB):", round(torch.cuda.max_memory_allocated() / 1e9, 2))