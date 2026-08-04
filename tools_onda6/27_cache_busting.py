# -*- coding: utf-8 -*-
"""
27_cache_busting.py — onda 8.1: ?v=<N> em todos os assets proprios das ondas.

Uso:  python tools_onda6/27_cache_busting.py <raiz-que-contem-public>

RODAR SEMPRE POR ULTIMO na sequencia da onda: qualquer script que insira um
<link>/<script> novo o faz sem query, e e este aqui que carimba a versao.

Por que existe
--------------
O Mario abriu o site no ar e viu os contatos do hero quebrados: texto azul
empilhado, icones minusculos, clique sem efeito. O CSS novo ESTAVA no servidor —
o navegador dele e que serviu a versao velha do onda6.css, do cache, porque a URL
do <link> nunca muda. Sem o CSS: os <li> viram lista vertical, o <a> pega o azul
padrao do navegador e o `.banner__background` (absolute, z-index 1) fica por cima
dos links e come o clique. Ou seja: um bug de cache com cara de bug de layout.

A partir daqui todo asset proprio das ondas carrega ?v=<VERSAO>. Nas proximas
ondas basta INCREMENTAR a constante abaixo e rodar este script — todas as
paginas passam a pedir o arquivo novo.

    VERSAO = 9   ->  onda6.css?v=9

Cobre os quatro assets proprios: onda6/onda6.css, onda6/onda8-dobra.js,
onda6/onda9-rede.js (mapa da pagina "Nossa rede") e clientes/clientes-logos.css.
O tema nao e tocado (os assets dele tem a versao que o WordPress ja carimbou).

Idempotente: se a versao ja e a atual, nao mexe.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

# >>> proximas ondas: incrementar aqui e rodar o script <<<
VERSAO = 28

ASSETS = [
    "wp-content/uploads/2026/07/onda6/onda6.css",
    "wp-content/uploads/2026/07/onda6/onda8-dobra.js",
    "wp-content/uploads/2026/07/onda6/onda9-rede.js",
    "wp-content/uploads/2026/07/onda6/onda13-hero-plexus.js",
    "wp-content/uploads/2026/07/onda6/onda17-horizonte.js",
    "wp-content/uploads/2026/07/clientes/clientes-logos.css",
]


def carimbar(html):
    """Poe/atualiza ?v=VERSAO em toda referencia aos nossos assets."""
    for asset in ASSETS:
        # casa o caminho com ou sem query, em href="" ou src=""
        rex = re.compile(r'((?:href|src)=")([^"]*?' + re.escape(asset) + r')(\?[^"]*)?(")')
        html = rex.sub(lambda m: u'%s%s?v=%d%s' % (m.group(1), m.group(2), VERSAO, m.group(4)),
                       html)
    return html


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    alterados = 0
    tocados = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if not nome.endswith(".html"):
                continue
            path = os.path.join(dirpath, nome)
            html = ler(path)
            if not any(a in html for a in ASSETS):
                continue
            tocados += 1
            novo = carimbar(html)
            if novo != html:
                gravar(path, novo)
                alterados += 1

    print("paginas com asset proprio: %d" % tocados)
    print("versao carimbada: v=%d" % VERSAO)
    print("\nresumo: %d arquivo(s) HTML alterado(s)" % alterados)


if __name__ == "__main__":
    main()
