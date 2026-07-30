# -*- coding: utf-8 -*-
"""
11_cargos_e_emails_lideres.py — arruma o cargo do Andreas e garante os icones de e-mail.

Uso:  python tools_onda6/11_cargos_e_emails_lideres.py <raiz-da-arvore>

Problema apontado pelo Mario: no card do Andreas o e-mail estava emendado no cargo
("Managing Partner - andreas.mirow@mirow.com.br"), estourando o subtitulo do card.

O que o script faz, em TODAS as paginas (homes + paginas de lideres, 3 linguas):
- Cargo limpo numa linha: "Managing Partner - andreas.mirow@mirow.com.br" ->
  "Managing Partner", nos cards da home, nos cards das paginas de lideres e no
  <h5 class="modal-leaders__role"> dos modais.
- Garante o e-mail como icone/link separado (mailto:) na lista de contatos do card
  da pagina de lideres e do modal, para o Andreas e para o Felipe. O markup do icone
  (SVG do envelope) e COLHIDO da propria pagina, para nao introduzir arte nova.
- Na home o tema nao tem slot de contato dentro do card (o card e o proprio botao que
  abre o modal, e link dentro de <button> seria HTML invalido) — la o e-mail aparece
  no modal que o card abre.
- Idempotente.
"""
import io
import os
import re
import sys

# nome -> e-mail que deve existir como link mailto
EMAILS = {
    u"Andreas Mirow": "andreas.mirow@mirow.com.br",
    u"Felipe Diniz": "felipe.diniz@mirow.com.br",
}

# cargo emendado -> cargo limpo
CARGOS = [
    (u"Managing Partner - andreas.mirow@mirow.com.br", u"Managing Partner"),
]


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def svg_envelope(html):
    """Colhe o SVG de envelope (mailto) que a propria pagina ja usa."""
    m = re.search(r'<a href="mailto:[^"]+">\s*(<svg.*?</svg>)', html, re.S)
    return m.group(1) if m else None


def garante_mailto(bloco, email, svg):
    """Insere <li><a mailto><svg></a></li> na lista de contatos, se faltar."""
    if "mailto:" in bloco or svg is None:
        return bloco, False
    item = '<li><a href="mailto:%s">%s</a></li>' % (email, svg)
    for fecha in ("</ul>",):
        i = bloco.find("__contacts")
        if i < 0:
            return bloco, False
        j = bloco.find(fecha, i)
        if j < 0:
            return bloco, False
        return bloco[:j] + item + bloco[j:], True
    return bloco, False


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = 0
    vistos = 0
    for root, _dirs, files in os.walk(pub):
        for f in files:
            if f != "index.html":
                continue
            path = os.path.join(root, f)
            with io.open(path, encoding="utf-8") as fh:
                html = fh.read()
            if "leaders__card" not in html and "page-leaders__list-item" not in html \
                    and "modal-leaders__role" not in html:
                continue
            vistos += 1
            rel = os.path.relpath(path, pub).replace(os.sep, "/")
            orig = html
            feitos = []

            for velho, novo in CARGOS:
                if velho in html:
                    feitos.append("cargo limpo (%dx)" % html.count(velho))
                    html = html.replace(velho, novo)

            svg = svg_envelope(html)
            for nome, email in EMAILS.items():
                # cards das paginas de lideres
                for rex in (re.compile(r'<button class="page-leaders__list-item".*?</button>', re.S),
                            re.compile(r'<div class="modal fade".*?</div></div></div></div></div>', re.S)):
                    saida = []
                    pos = 0
                    for m in rex.finditer(html):
                        bloco = m.group(0)
                        if nome in bloco and "mailto:%s" % email not in bloco:
                            bloco, mexeu = garante_mailto(bloco, email, svg)
                            if mexeu:
                                feitos.append("mailto de %s" % nome)
                        saida.append(html[pos:m.start()])
                        saida.append(bloco)
                        pos = m.end()
                    saida.append(html[pos:])
                    html = "".join(saida)

            if html != orig:
                with io.open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(html)
                alterados += 1
                print("%s: %s" % (rel, "; ".join(sorted(set(feitos))) or "ajuste"))
    print("\nresumo: %d de %d pagina(s) com lideres alterada(s)" % (alterados, vistos))


if __name__ == "__main__":
    main()
