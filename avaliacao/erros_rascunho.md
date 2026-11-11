# Rascunho: 5 erros reais (causa e correção)

> Rascunho com base nas saídas dos notebooks 02, 03 e 04. Antes de entregar, confirmar cada caso nos arquivos
> `avaliacao/resultados/*.json` e atualizar o erro 4 com o resultado do notebook 05.

## Erro 1 · Q02: a busca trouxe o trecho errado (recall@3 falhou)
- **Pergunta:** "O que significa acessibilidade segundo a Lei Brasileira de Inclusão?"
- **Esperado:** Lei 13.146/2015, art. 3º, I (T02). **Buscou:** T17, T11, T21 (T02 ficou de fora dos 3 primeiros).
- **Saída (B e C):** definiu acessibilidade pelo art. 53 e citou "art. 53". Resposta fiel ao trecho, mas não é o artigo do gabarito.
- **Causa:** dois trechos tratam de acessibilidade. O art. 53 é curto e fala "A acessibilidade é direito...", casando melhor com a pergunta. O T02 começa com texto padrão ("Para fins de aplicação desta Lei, consideram-se:") que dilui a similaridade. A similaridade dos modelos e5 fica numa faixa estreita (0,85 a 0,93), então pequenas diferenças decidem o ranking.
- **Correção:** (1) limpar o prefixo padrão dos trechos de definição; (2) busca híbrida (palavras-chave + embeddings) ou reranqueamento; (3) aceitar mais de um trecho correto no gabarito quando dois artigos respondem a pergunta.

## Erro 2 · Q04: o limiar recusou uma pergunta que a base respondia
- **Pergunta:** "O que são barreiras urbanísticas?"
- **Esperado:** T04. **Buscou:** T04 em 1º lugar, mas com similaridade 0,848, abaixo do limiar 0,8754.
- **Saída (B e C com limiar):** `nao_consta` (recusa indevida). Sem o limiar, B e C responderam certo.
- **Causa:** o limiar é um valor único para toda a base. Perguntas curtas contra trechos longos têm similaridade menor mesmo quando o trecho está certo. O limiar também foi calibrado nos mesmos 35 casos e a margem é estreita (maior "não consta" = 0,873).
- **Correção:** decidir a recusa por mais de um sinal (limiar + diferença entre o 1º e o 2º trecho); calibrar o limiar com casos separados dos de teste; ou deixar o modelo decidir quando o limiar estiver na zona cinza.

## Erro 3 · Q05: o modelo escolheu o trecho errado mesmo com o certo em 1º lugar
- **Pergunta:** "Recusar uma adaptação razoável conta como discriminação?"
- **Esperado:** T05 (art. 4º). **Buscou:** T05, T22, T11 (T05 em 1º, similaridade 0,884).
- **Saída:** B citou o art. 46; C (v1) respondeu com o texto da pena de crime e citou o art. 88.
- **Causa:** o modelo de 1,5 bilhão de parâmetros tem dificuldade de escolher qual dos 3 trechos responde. Os três falam em discriminação e direitos, e o modelo se apoiou em palavras soltas. Só o T05 menciona "adaptações razoáveis".
- **Correção:** mostrar ao modelo só o melhor trecho quando a diferença de similaridade for grande; pedir que o modelo devolva primeiro o id do trecho usado e preencher a fonte pelo código (assim a fonte nunca é inventada); reranqueamento.

## Erro 4 · Q12 (LoRA v1): resposta que não responde (faltou o "2%")
- **Pergunta:** "Que percentual das vagas de estacionamento deve ser reservado a veículos de pessoa com deficiência?"
- **Buscou:** T13 em 1º (certo). **Saída (C v1):** copiou a primeira frase do art. 47 ("devem ser reservadas vagas próximas aos acessos...") e não trouxe o percentual.
- **Causa:** erro de desenho do treino v1. O alvo era um resumo extrativo que copiava o início do trecho; no T13 o alvo terminava antes do "2%". O LoRA aprendeu a copiar o começo, não a responder.
- **Correção (aplicada no v2):** respostas-alvo diretas e curtas, escritas à mão e conferidas contra o trecho (`src/respostas_treino.py`). **Resultado do v2: preencher após o notebook 05 (seção 5).**

## Erro 5 · Q11: ranking trocado + quebra de formato
- **Pergunta:** "Quais elementos fazem parte do transporte coletivo para fins de acessibilidade?"
- **Esperado:** T12 (art. 46, § 1º). **Buscou:** T14, T12, T31 (o certo em 2º).
- **Saída:** B misturou texto fora do JSON ("\n\nFonte: Lei...") dentro da resposta. C (v1) devolveu JSON válido, mas citou o art. 48 (T14).
- **Causa:** dois problemas em camadas: (a) os arts. 46 § 1º e 48 listam os mesmos termos (veículos, estações, terminais), e o art. 48 ficou em 1º na busca; (b) no B, o modelo quebrou o formato.
- **Correção:** (a) reranqueamento ou busca híbrida; (b) tentar de novo uma vez quando o JSON vier inválido (na API) e/ou usar decodificação restrita a JSON. O LoRA ajudou no formato nesse caso, mas não resolveu a escolha do trecho.
