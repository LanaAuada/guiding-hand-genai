"""Trecho a colar em src/avaliacao.py (substitui a função tokens): normaliza números por extenso."""
NUMEROS = {"um": "1", "uma": "1", "dois": "2", "duas": "2", "tres": "3", "quatro": "4",
           "cinco": "5", "seis": "6", "sete": "7", "oito": "8", "nove": "9", "dez": "10",
           "vinte": "20", "trinta": "30", "cinquenta": "50"}


def tokens(s):
    toks = re.findall(r"[a-z0-9%]+", sem_acento(s.lower()))
    return [NUMEROS.get(t, t) for t in toks]
