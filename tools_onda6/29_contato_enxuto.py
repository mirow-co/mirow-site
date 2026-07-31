# -*- coding: utf-8 -*-
"""
29_contato_enxuto.py — onda 9: pagina de contato enxuta.

Uso:  python tools_onda6/29_contato_enxuto.py <raiz-que-contem-public>

Pedido do Mario: a pagina de contato fica com TRES coisas, nesta ordem:

    1. o titulo/frase do banner ("Get in touch with our team and ask any
       questions you may have" e os equivalentes em PT e DE);
    2. o formulario de contato (<section class="contact">);
    3. a barra "Transform your career" (<section class="links">).

Tudo o mais sai. Na pratica isso significa remover a secao
<section class="offices"> — o bloco de escritorios, com abas de cidade,
endereco, link do Google Maps e galeria de fotos.

Paginas atingidas (todas as variantes de contato do espelho):
    contato/  ·  pt/contato/  ·  en/contact-us/  ·  de/kontakt/  ·  novo/contato/

Detalhes que importam
---------------------
- A ancora do banner aponta para #mainContent, que e o <div> logo depois do
  banner. Ele continua existindo: o que sai e a <section> DENTRO dele, entao a
  seta do banner passa a levar direto ao formulario — que e o comportamento
  desejado.
- A remocao e feita por corte de texto entre <section class="offices"> e o
  </section> correspondente (contagem de <section> aninhadas), nunca por regex
  guloso — a pagina tem outras <section> depois.
- Nada de CSS novo: o tema nao muda, so some um bloco de conteudo.

Idempotente: rodar de novo nao acha mais nenhuma secao e nao grava nada.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

PAGINAS = [
    "contato/index.html",
    "pt/contato/index.html",
    "en/contact-us/index.html",
    "de/kontakt/index.html",
    "novo/contato/index.html",
]

ABERTURA = '<section class="offices"'


def remover_secao(html, abertura):
    """Remove a <section> que comeca em `abertura`, respeitando aninhamento."""
    i = html.find(abertura)
    if i < 0:
        return html, False
    pos = i
    profundidade = 0
    while True:
        prox_abre = html.find("<section", pos + 1)
        prox_fecha = html.find("</section>", pos + 1)
        if prox_fecha < 0:
            raise SystemExit("HTML malformado: </section> nao encontrado")
        if 0 <= prox_abre < prox_fecha:
            profundidade += 1
            pos = prox_abre
            continue
        if profundidade == 0:
            fim = prox_fecha + len("</section>")
            break
        profundidade -= 1
        pos = prox_fecha
    return html[:i] + html[fim:], True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    escritos = 0
    for rel in PAGINAS:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: pagina ausente (%s)" % rel)
            continue
        html = ler(path)
        original = html
        removidas = 0
        while True:
            html, achou = remover_secao(html, ABERTURA)
            if not achou:
                break
            removidas += 1
        if html != original:
            gravar(path, html)
            escritos += 1
            print("offices removida (%dx): %s" % (removidas, rel))
        else:
            print("sem mudanca: %s" % rel)

    print("\nresumo: %d arquivo(s) alterado(s)" % escritos)


if __name__ == "__main__":
    main()
