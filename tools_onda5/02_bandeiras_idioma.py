# -*- coding: utf-8 -*-
"""
02_bandeiras_idioma.py — adiciona bandeirinhas SVG ao seletor de idioma do header.

Uso:  python tools_onda5/02_bandeiras_idioma.py <raiz-da-arvore>

- Atua em TODAS as paginas .html do espelho (o header e o mesmo em todas).
- Insere um <svg> minusculo antes do texto de cada link dentro de
  <ul class="menu__languages-list">. Emoji de bandeira nao renderiza no Windows,
  por isso SVG inline com estilo inline (sem CSS novo, sem tocar no tema).
- Idempotente: se o link ja tem data-onda5-flag, nao mexe.
"""
import os
import re
import sys

ESTILO = ("width:17px;height:auto;display:inline-block;vertical-align:-3px;"
          "margin-right:8px;flex:none")

BANDEIRAS = {
    # Brasil
    "Portugu": (
        '<svg data-onda5-flag="br" viewBox="0 0 20 14" width="17" height="12" '
        'aria-hidden="true" style="%s" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="20" height="14" fill="#009B3A"/>'
        '<path d="M10 1.6 18.2 7 10 12.4 1.8 7Z" fill="#FEDF00"/>'
        '<circle cx="10" cy="7" r="3" fill="#002776"/></svg>' % ESTILO),
    # Reino Unido
    "English": (
        '<svg data-onda5-flag="gb" viewBox="0 0 60 40" width="17" height="11" '
        'aria-hidden="true" style="%s" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="60" height="40" fill="#012169"/>'
        '<path d="M0 0 60 40M60 0 0 40" stroke="#FFFFFF" stroke-width="9"/>'
        '<path d="M0 0 60 40M60 0 0 40" stroke="#C8102E" stroke-width="4"/>'
        '<path d="M30 0V40M0 20H60" stroke="#FFFFFF" stroke-width="14"/>'
        '<path d="M30 0V40M0 20H60" stroke="#C8102E" stroke-width="8"/></svg>' % ESTILO),
    # Alemanha
    "Deutsch": (
        '<svg data-onda5-flag="de" viewBox="0 0 5 3" width="17" height="11" '
        'aria-hidden="true" style="%s" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="5" height="3" fill="#000000"/>'
        '<rect y="1" width="5" height="1" fill="#DD0000"/>'
        '<rect y="2" width="5" height="1" fill="#FFCE00"/></svg>' % ESTILO),
}

UL_RE = re.compile(r'(<ul class="menu__languages-list">)(.*?)(</ul>)', re.S)
A_RE = re.compile(r'(<a\b[^>]*>)(\s*)([^<]+?)(\s*)(</a>)')


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def bandeira_para(rotulo):
    for chave, svg in BANDEIRAS.items():
        if rotulo.startswith(chave):
            return svg
    return None


def tratar_ul(m):
    abre, corpo, fecha = m.group(1), m.group(2), m.group(3)
    if "data-onda5-flag" in corpo:
        return m.group(0)

    def sub_a(am):
        svg = bandeira_para(am.group(3))
        if not svg:
            return am.group(0)
        # o span com white-space:nowrap mantem bandeira + rotulo na mesma linha
        # (o dropdown tem largura shrink-to-fit; sem isso a bandeira quebra linha)
        return (am.group(1) + '<span style="white-space:nowrap">' + svg
                + am.group(3) + "</span>" + am.group(5))

    return abre + A_RE.sub(sub_a, corpo) + fecha


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados, ja_ok, sem_switcher = 0, 0, 0
    for root, _dirs, files in os.walk(pub):
        for f in files:
            if not f.endswith(".html"):
                continue
            path = os.path.join(root, f)
            with open(path, encoding="utf-8") as fh:
                html = fh.read()
            if 'class="menu__languages-list"' not in html:
                sem_switcher += 1
                continue
            novo = UL_RE.sub(tratar_ul, html)
            if novo != html:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(novo)
                alterados += 1
            else:
                ja_ok += 1
    print("bandeiras: %d arquivo(s) alterado(s), %d ja tinham, %d sem seletor de idioma"
          % (alterados, ja_ok, sem_switcher))


if __name__ == "__main__":
    main()
