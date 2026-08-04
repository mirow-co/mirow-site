# -*- coding: utf-8 -*-
"""74 — onda 19, S-75 (issue #133): sai o bloco "Como podemos ajudar? / Transforme
sua carreira".

Uso:
    python tools_onda6/74_remover_bloco_links.py <raiz-que-contem-public>

Pedido do Mario: "remova esse bloco como podemos ajudar e transforme sua carreira."

E a <section class="links"> do tema — dois cartoes grandes com textura, um para
contato e outro para carreiras, repetidos no pe de quase toda pagina. Os dois
caminhos continuam no menu do header E na barra clonada do rodape (onda 15), mais
os atalhos fixos de WhatsApp/e-mail da S-76 — ou seja, nada de contato se perde.

Observacao: a onda 18 (S-63) ja tinha removido UMA dessas secoes, a da pagina de
carreiras que dizia "Ja e cliente?". Aqui a remocao passa a valer para todas.

Idempotente: deixa um marcador no lugar; no 2o run nao acha mais nenhuma secao.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

MARCA = "<!-- onda19:s75-bloco-links-removido -->"


def remover_todas(html):
    """Remove todas as <section class="links"> da pagina."""
    n = 0
    while True:
        ini = html.find('<section class="links">')
        if ini < 0:
            break
        fim = html.find("</section>", ini)
        if fim < 0:
            break
        fim += len("</section>")
        html = html[:ini] + (MARCA if n == 0 else "") + html[fim:]
        n += 1
    return html, n


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    paginas = 0
    secoes = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if '<section class="links">' not in h:
                continue
            novo, quantas = remover_todas(h)
            if novo != h:
                gravar(p, novo)
                paginas += 1
                secoes += quantas
    print("resumo: %d bloco(s) removido(s) em %d pagina(s)" % (secoes, paginas))


if __name__ == "__main__":
    main()
