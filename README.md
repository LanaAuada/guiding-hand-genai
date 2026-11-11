# Guiding Hand · Assistente de direitos e acessibilidade (LLM local + RAG + LoRA)

Projeto da disciplina **Generative AI for Engineering** (FIAP, Engenharia de Software, Global Solution 2026).
Parte do produto **Guiding Hand**, óculos inteligentes que ajudam pessoas cegas ou com baixa visão a andar pela cidade.

**Grupo**

- João Rodrigo Solano Nogueira · RM 551319
- Julia Amorim Bezerra · RM 99609
- Lana Giulia Auada Leite · RM 551143
- Tony Willian da Silva Segalin · RM 550667

> Status: **em construção** (partes 1 a 3 parciais). Este README será completado na última etapa.

## Ficha técnica

| Item | Descrição |
|---|---|
| Tema | Mobilidade |
| Problema | Pessoas com deficiência visual têm dúvidas sobre direitos, acessibilidade e transporte, e respostas soltas na internet podem estar erradas. |
| O que a IA resolve | Responde perguntas curtas sobre direitos de mobilidade de pessoas com deficiência, **citando o artigo da lei**, e responde **"não consta"** quando a base não tem a resposta. |
| Modelo (local) | Qwen2.5-1.5B-Instruct (fallback 0.5B), roda em GPU de 4 GB |
| Busca | multilingual-e5-small sobre a base de trechos |
| Configurações comparadas | **A** modelo sem contexto · **B** RAG simples · **C** RAG + LoRA |
| Saída | JSON: `resposta`, `fonte`, `status` (`ok` ou `nao_consta`) |
| LGPD | A base é só texto de lei; perguntas não são gravadas com identificação (detalhes na etapa final) |

## Estrutura

```
base/        trechos.jsonl (32 trechos com fonte), FONTES.md, construir_base.py
avaliacao/   casos_teste.jsonl (27 com resposta + 8 "não consta"), construir_testes.py
notebooks/   01_base_conhecimento.ipynb (com saídas salvas)
src/         config.py
api/         (a fazer)
```

## Como reproduzir (até aqui)

```
python -m venv .venv && .venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
python base/construir_base.py
python avaliacao/construir_testes.py     # valida o gabarito contra a base
jupyter notebook notebooks/01_base_conhecimento.ipynb
```

## Andamento

- [x] 1. Tarefa da IA e casos de teste com gabarito, incluindo "não consta"
- [x] 2. Base de conhecimento em trechos com fonte
- [ ] 3. Busca com recall@1 e recall@3 e limiar
- [ ] 4. Geração fundamentada (JSON, citação, recusa)
- [ ] 5. Especialização (LoRA) comparada ao RAG simples
- [ ] 6. Placar das três configurações
- [ ] 7. Cinco erros reais com correção
- [ ] 8. API, README final, relatório e vídeo
