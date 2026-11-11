# Roteiro do vídeo (3 a 4 minutos, 4 pessoas)

1. **Problema (30 s).** O Guiding Hand ajuda pessoas com deficiência visual na cidade. Dúvidas de direitos (táxi, estacionamento, locadoras) estão em leis longas. Um modelo sem contexto responde com segurança e inventa.
2. **Demonstração da alucinação (40 s).** Notebook 03: pergunta "Quanto da frota de táxi deve ser acessível?". A: "50%" e cita a Lei Maria da Penha. B: 10% e cita o art. 51 da Lei 13.146/2015.
3. **Pipeline (40 s).** Mostrar o diagrama do relatório: base de 32 trechos, busca top-3, limiar, modelo com LoRA, JSON com fonte e recusa.
4. **Placar (60 s).** Tabela A, B, C: alucinação de 89% para 0%, acerto 7, 19 e 25 de 27, JSON 100% válido. Dizer o que **não** é conclusivo: citação 22 contra 21 e recusa com limiar são empate; 35 casos e um treino.
5. **API ao vivo (40 s).** `/docs`: uma pergunta com resposta (mostrar `trecho_citado`), uma "não consta" e uma com CPF recusada.
6. **Erros e LGPD (30 s).** Citar 1 dos 5 erros (por exemplo, Q15: resposta certa, artigo errado) e a correção proposta; resumir as 3 medidas de privacidade.

Dica: gravar a tela com o Teams ou o Xbox Game Bar (Win + G) e subir como não listado no YouTube.
