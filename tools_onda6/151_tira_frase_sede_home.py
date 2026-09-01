# -*- coding: utf-8 -*-
"""Onda 77: a frase de sede sai da HOME, nos tres idiomas.

Pedido do Mario em 31/08/2026, verbatim: "remova a frase 'A Mirow & Co. e uma
consultoria estrategica brasileira, com sede no Rio de Janeiro' por completo da
pagina inicial do site".

Procedencia, para o registro (nao para justificar): a frase veio do handoff GEO do
Felipe (mirow-marketing#234), foi para o staging na onda 59-sede e o repo registra
aprovacao em 19/08 (docstring do 113 e commit 1d581af1). O Mario diz que nunca
pediu. Seja qual for o caminho, a decisao de hoje e dele e e esta: sai da home.

O que este script faz:
  - remove o <p class="onda59-sede"> das 3 homes (o paragrafo INTEIRO, nao so o
    texto -- deixar a casca vazia manteria o espacamento e um no de acessibilidade
    sem conteudo);
  - e idempotente: rodar 2x nao muda nada na segunda.

O que ele NAO faz, de proposito:
  - nao toca na Nossa Historia, onde a mesma frase abre a prosa. O pedido falou da
    pagina inicial, e apagar prosa de outra pagina sem pedido e decidir pelo dono.
  - nao toca na `description` do JSON-LD nem na meta description, que nao sao texto
    visivel da pagina. Perguntado ao Mario.

O 113_geo_frase_sede.py foi alterado na mesma onda para NAO reinserir na home --
sem isso, a proxima execucao dele traria a frase de volta, e a S180 gritaria.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_css = __import__("_onda7_css")
ler, gravar = _css.ler, _css.gravar

HOMES = ["pt/index.html", "en/index.html", "de/index.html"]
# o paragrafo inteiro, com a classe que a onda 59 deu a ele
ALVO = re.compile(r'\s*<p class="onda59-sede"[^>]*>.*?</p>', re.S)


def main(raiz):
    pub = os.path.join(os.path.abspath(raiz), "public")
    n = 0
    for rel in HOMES:
        p = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(p):
            continue
        h = ler(p)
        novo, quantos = ALVO.subn("", h)
        if quantos:
            gravar(p, novo)
            n += quantos
            print(u"  %s: %d paragrafo(s) removido(s)" % (rel, quantos))
    print(u"151: %d ocorrencia(s) da frase de sede fora da home" % n)
    return n


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
