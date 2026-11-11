# Guiding Hand: assistente de direitos e mobilidade (RAG + LoRA local)

Trabalho de Generative AI for Engineering (FIAP), tema **Mobilidade**. Um assistente local que responde dúvidas de pessoas com deficiência visual sobre direitos, acessibilidade e transporte, **só com base em trechos de lei**: devolve JSON, cita a fonte e recusa ("não consta") quando a base não responde. Detalhes, diagrama, placar e os 5 erros estão em **[RELATORIO.md](RELATORIO.md)**.

**Grupo**

- João Rodrigo Solano Nogueira, RM 551319
- Julia Amorim Bezerra, RM 99609
- Lana Giulia Auada Leite, RM 551143
- Tony Willian da Silva Segalin, RM 550667

## Resultado em uma tabela (35 casos de teste: 27 com resposta, 8 "não consta")

| | A: sem contexto | B: RAG + limiar | C: RAG + LoRA v2 + limiar |
|---|---|---|---|
| Acerto (/27) | 7 | 19 | 25 |
| Citação correta (/27) | 0 | 21 | 22 |
| Recusa correta (/8) | 2 | 8 | 8 |
| JSON válido (/35) | 33 | 34 | 35 |
| Alucinação (/35) | 89% | 0% | 0% |

Busca: recall@1 = 81,5% e recall@3 = 96,3%, com limiar de similaridade 0,8754. As diferenças pequenas (por exemplo, citação 22 contra 21) não são conclusivas: são 35 casos e um único treino. O acerto do C é 25 com a métrica corrigida para números por extenso e 23 sem ela (explicação no relatório).

## Estrutura

```
base/        trechos.jsonl (32 trechos com fonte), FONTES.md (fonte, formato, licença, nº de trechos)
avaliacao/   casos_teste.jsonl (gabarito), limiar.json, resultados/*.json (saídas de cada config), placares .csv
notebooks/   01 base, 02 busca (recall, limiar), 03 A × B, 04 LoRA v1, 05 LoRA v2 e placar final (com saídas salvas)
src/         código (busca, geração, métricas, treino, recálculo do placar)
api/         main.py (API FastAPI) e testar_api.py (demonstração)
modelo-lora_v2/   adaptador LoRA usado na config C e na API (modelo-lora/ é o v1)
```

Nos notebooks e nos arquivos de resultado a configuração final aparece como **C2** (LoRA v2); no relatório ela é chamada só de C.

## Como reproduzir

Testado no Windows 11 (PowerShell, VS Code), Python 3.14, GPU NVIDIA com 4 GB (RTX 3050 Ti). As versões das bibliotecas estão fixadas no `requirements.txt`. Na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
python src/smoke_test.py    # confere se o modelo carrega na GPU
```

1. **Base e gabarito** (CPU, segundos). O notebook 01 mostra a tabela da base e confere o gabarito.
   ```powershell
   python base/construir_base.py
   python avaliacao/construir_testes.py
   ```
2. **Notebooks 02 e 03** (busca e A × B; baixam o modelo na primeira vez, alguns minutos). Abra no VS Code, escolha o kernel `.venv` e use Run All. Antes de cada notebook seguinte, feche o anterior: cada um ocupa a GPU.
3. **LoRA v2** (cerca de 10 minutos, pico de 1,6 GB de VRAM; feche os notebooks antes):
   ```powershell
   python src/gerar_dados_treino.py v2
   python src/treinar_lora.py v2
   ```
   Se der falta de memória, em `src/treinar_lora.py` troque `MAX_TOKENS = 1000` por `700`. O erro do Windows `os error 1455` é falta de memória virtual (feche programas ou aumente o arquivo de paginação).
4. **Notebook 05** (config C e placar final). Gera `avaliacao/placar_final.csv` e as figuras.
5. **Placar com e sem a correção da métrica** (sem GPU, lê os JSON salvos):
   ```powershell
   $env:PYTHONIOENCODING = "utf-8"
   python src/placar_corrigido.py | Out-File -Encoding utf8 avaliacao/placar_corrigido.txt
   ```

O LoRA v1 (`python src/gerar_dados_treino.py` e `python src/treinar_lora.py`, sem argumento) e o notebook 04 documentam o primeiro treino, que ficou praticamente empatado com o RAG simples (explicação no relatório).

## API

```powershell
uvicorn api.main:app --port 8000
```

Abra http://127.0.0.1:8000/docs para testar. Rotas: `POST /perguntar` (corpo `{"pergunta": "..."}`), `GET /saude`, `GET /privacidade`. Em outro terminal, `python api/testar_api.py` roda 5 perguntas de demonstração (duas com resposta, duas "não consta" e uma com CPF, que é recusada).

A resposta traz `resposta`, `fonte`, `status` (`ok` ou `nao_consta`), `trecho_citado` (o texto da lei que sustenta a resposta) e `trechos_consultados` com a similaridade. A API acrescenta duas travas que não estavam nos placares: se o JSON vier inválido ou a fonte citada não existir na base, responde "não consta".

## LGPD

A base é só texto de lei. A API não grava a pergunta (o log guarda só status, similaridade e tempo), recusa perguntas com CPF, e-mail ou telefone e roda tudo local, sem serviços externos. Não é parecer jurídico.

## Limitações

Base pequena (32 trechos da Lei Brasileira de Inclusão e leis correlatas), sem legislação municipal, valores nem horários; 35 casos de teste e um único treino; limiar calibrado nos mesmos casos em que é medido. O texto das leis deve ser conferido no Planalto.
