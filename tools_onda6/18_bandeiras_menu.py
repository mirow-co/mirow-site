# -*- coding: utf-8 -*-
"""
18_bandeiras_menu.py — item 4d da lista do Mario (onda 7).

Uso:  python tools_onda6/18_bandeiras_menu.py <raiz-que-contem-public>

Causa raiz do "miolo da bandeira do Brasil com cores distorcidas":
o tema tem, no bundle-css.css, a regra

    .menu__languages-button svg path{fill:var(--primaryColor)}

ou seja, TODO elemento <path> dentro do seletor de idioma e pintado de navy,
ignorando o atributo fill do proprio SVG (CSS vence atributo de apresentacao).
As bandeiras inseridas na onda 5 desenhavam o losango amarelo e o globo azul do
Brasil com <path> — e por isso viravam um bloco navy. A bandeira do Reino Unido
tinha o mesmo problema (as cruzes sao <path>); a da Alemanha usa <rect> e escapava.

Correcao SEM tocar no tema e SEM CSS novo: redesenhar as bandeiras usando apenas
<rect>, <polygon>, <line> e <circle> — elementos que a regra do tema nao alcanca.
Cores oficiais mantidas: Brasil verde #009B3A, losango #FEDF00, globo #002776.

Aplica nas ~272 paginas. Idempotente: reconhece data-onda7-flag e reescreve.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, paginas, resolve_public  # noqa: E402

ESTILO = ('style="width:17px;height:auto;display:inline-block;vertical-align:-3px;'
          'margin-right:8px;flex:none"')

BR = (
    '<svg data-onda7-flag="br" viewBox="0 0 20 14" width="17" height="12" '
    'aria-hidden="true" %s xmlns="http://www.w3.org/2000/svg">'
    '<rect width="20" height="14" fill="#009B3A"/>'
    '<polygon points="10,1.6 18.2,7 10,12.4 1.8,7" fill="#FEDF00"/>'
    '<circle cx="10" cy="7" r="3" fill="#002776"/>'
    '</svg>' % ESTILO
)

GB = (
    '<svg data-onda7-flag="gb" viewBox="0 0 60 40" width="17" height="11" '
    'aria-hidden="true" %s xmlns="http://www.w3.org/2000/svg">'
    '<rect width="60" height="40" fill="#012169"/>'
    '<g stroke="#FFFFFF" stroke-width="9"><line x1="0" y1="0" x2="60" y2="40"/>'
    '<line x1="60" y1="0" x2="0" y2="40"/></g>'
    '<g stroke="#C8102E" stroke-width="4"><line x1="0" y1="0" x2="60" y2="40"/>'
    '<line x1="60" y1="0" x2="0" y2="40"/></g>'
    '<g stroke="#FFFFFF" stroke-width="14"><line x1="30" y1="0" x2="30" y2="40"/>'
    '<line x1="0" y1="20" x2="60" y2="20"/></g>'
    '<g stroke="#C8102E" stroke-width="8"><line x1="30" y1="0" x2="30" y2="40"/>'
    '<line x1="0" y1="20" x2="60" y2="20"/></g>'
    '</svg>' % ESTILO
)

DE = (
    '<svg data-onda7-flag="de" viewBox="0 0 5 3" width="17" height="11" '
    'aria-hidden="true" %s xmlns="http://www.w3.org/2000/svg">'
    '<rect width="5" height="3" fill="#000000"/>'
    '<rect y="1" width="5" height="1" fill="#DD0000"/>'
    '<rect y="2" width="5" height="1" fill="#FFCE00"/>'
    '</svg>' % ESTILO
)

NOVAS = {"br": BR, "gb": GB, "de": DE}


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    alvos = paginas(pub, "menu__languages-list")
    print("paginas com o seletor de idioma: %d" % len(alvos))

    alterados = 0
    sem_bandeira = []
    for path, rel in alvos:
        html = ler(path)
        orig = html
        for chave, novo in NOVAS.items():
            rx = re.compile(
                r'<svg data-onda[57]-flag="%s".*?</svg>' % chave, re.S)
            if not rx.search(html):
                sem_bandeira.append((rel, chave))
                continue
            html = rx.sub(lambda _m: novo, html)
        if html != orig:
            gravar(path, html)
            alterados += 1

    if sem_bandeira:
        print("AVISO: %d bandeira(s) nao encontrada(s), ex.: %s"
              % (len(sem_bandeira), sem_bandeira[:3]))
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
