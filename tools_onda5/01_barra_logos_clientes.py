# -*- coding: utf-8 -*-
"""
01_barra_logos_clientes.py — insere a barra de logomarcas de clientes nas homes (PT/EN/DE).

Uso:  python tools_onda5/01_barra_logos_clientes.py <raiz-da-arvore>

- Insere a secao logo APOS o hero (<section class="banner">...</section>) e ANTES de
  <div class="wrap-gradient-1">.
- Cria/atualiza o CSS proprio em wp-content/uploads/2026/07/clientes/clientes-logos.css
  e adiciona o <link> no <head> (uma vez).
- NAO altera tema, cores, fontes nem qualquer elemento existente.
- Idempotente: reconhece os marcadores <!-- onda5:clientes-logos --> e reescreve o bloco.
"""
import os
import re
import sys

MARK_INI = "<!-- onda5:clientes-logos -->"
MARK_FIM = "<!-- /onda5:clientes-logos -->"
CSS_REL = "wp-content/uploads/2026/07/clientes/clientes-logos.css"
CSS_LINK_ID = "onda5-clientes-logos-css"

# (slug, arquivo, nome de exibicao/alt)
CLIENTES = [
    ("mercedes-benz", "mercedes-benz.svg", "Mercedes-Benz"),
    ("volkswagen", "volkswagen.svg", "Volkswagen"),
    ("ipiranga", "ipiranga.svg", "Ipiranga"),
    ("suzano", "suzano.svg", "Suzano"),
    ("klabin", "klabin.svg", "Klabin"),
    ("dexco", "dexco.svg", "Dexco"),
    ("edp", "edp.svg", "EDP"),
    ("energisa", "energisa.svg", "Energisa"),
    ("eneva", "eneva.svg", "Eneva"),
    ("taesa", "taesa.png", "Taesa"),
    ("yara", "yara.svg", "Yara"),
    ("wilson-sons", "wilson-sons.svg", "Wilson Sons"),
    ("santos-brasil", "santos-brasil.jpg", "Santos Brasil"),
    ("xp", "xp.svg", "XP Inc."),
    ("sulamerica", "sulamerica.svg", "SulAmerica"),
]

TITULOS = {
    "pt": "Empresas que confiam na Mirow &amp; Co.",
    "en": "Companies that trust Mirow &amp; Co.",
    "de": "Unternehmen, die Mirow &amp; Co. vertrauen",
}

# homes do espelho -> idioma
HOMES = [
    ("pt/index.html", "pt"),
    ("en/index.html", "en"),
    ("en/homepage/index.html", "en"),
    ("de/index.html", "de"),
]

CSS = """/* onda5 — barra de logomarcas de clientes. CSS proprio, nao toca no tema. */
.clientes-logos{display:block;background:#ffffff;padding:46px 0 42px}
.clientes-logos__title{display:block;text-align:center;margin:0 0 30px;
  font-family:var(--secondaryFontFamily,"Libre Franklin",sans-serif);
  font-size:12px;line-height:1.4;letter-spacing:.14em;text-transform:uppercase;
  font-weight:400;color:#7a7f8c}
.clientes-logos__list{display:flex;flex-wrap:wrap;justify-content:center;align-items:center;
  gap:26px 40px;margin:0;padding:0;list-style:none}
.clientes-logos__item{display:flex;align-items:center;justify-content:center;
  height:44px;flex:0 0 auto}
.clientes-logos__item img{display:block;width:auto;height:auto;
  max-height:30px;max-width:132px;object-fit:contain;
  filter:grayscale(1) opacity(.65);transition:filter 300ms ease-in-out}
.clientes-logos__item--alto img{max-height:44px;max-width:96px}
.clientes-logos__item:hover img{filter:grayscale(1) opacity(1)}
@media only screen and (max-width: 991px){
  .clientes-logos{padding:34px 0 30px}
  .clientes-logos__list{gap:20px 28px}
  .clientes-logos__item{height:36px}
  .clientes-logos__item img{max-height:24px;max-width:104px}
  .clientes-logos__item--alto img{max-height:36px;max-width:78px}
}
"""

# logos de proporcao quadrada/vertical, que precisam de mais altura para nao ficarem minusculos
ALTOS = {"klabin", "yara", "volkswagen", "santos-brasil"}


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def base_prefix(html):
    """Descobre o prefixo de URL usado pelo espelho (ex.: /mirow-site/ ou /)."""
    m = re.search(r'(?:src|href)="(/[^"]*?/)wp-content/', html)
    return m.group(1) if m else "/"


def bloco(idioma, prefix):
    itens = []
    for slug, arq, nome in CLIENTES:
        cls = "clientes-logos__item clientes-logos__item--alto" if slug in ALTOS else "clientes-logos__item"
        itens.append(
            '        <li class="%s"><img src="%swp-content/uploads/2026/07/clientes/%s" '
            'alt="%s" loading="lazy" decoding="async"></li>' % (cls, prefix, arq, nome)
        )
    return (
        "%s\n"
        '<section class="clientes-logos">\n'
        '  <div class="container">\n'
        '    <div class="row">\n'
        '      <div class="col-12">\n'
        '        <p class="clientes-logos__title">%s</p>\n'
        '      </div>\n'
        '    </div>\n'
        '    <ul class="clientes-logos__list">\n'
        "%s\n"
        "    </ul>\n"
        "  </div>\n"
        "</section>\n"
        "%s\n" % (MARK_INI, TITULOS[idioma], "\n".join(itens), MARK_FIM)
    )


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    # 1) CSS proprio
    css_path = os.path.join(pub, CSS_REL.replace("/", os.sep))
    os.makedirs(os.path.dirname(css_path), exist_ok=True)
    antigo = ""
    if os.path.exists(css_path):
        with open(css_path, encoding="utf-8") as f:
            antigo = f.read()
    if antigo != CSS:
        with open(css_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(CSS)
        print("css escrito: %s" % CSS_REL)
    else:
        print("css ja atualizado: %s" % CSS_REL)

    alterados = 0
    for rel, idioma in HOMES:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: nao existe %s" % rel)
            continue
        with open(path, encoding="utf-8") as f:
            html = f.read()
        orig = html
        prefix = base_prefix(html)

        # link do CSS no head (uma vez)
        if CSS_LINK_ID not in html:
            link = '<link rel="stylesheet" id="%s" href="%s%s" media="all" />\n' % (
                CSS_LINK_ID, prefix, CSS_REL)
            html = html.replace("</head>", link + "</head>", 1)

        novo = bloco(idioma, prefix)
        if MARK_INI in html:
            html = re.sub(
                re.escape(MARK_INI) + r".*?" + re.escape(MARK_FIM) + r"\n?",
                novo, html, flags=re.S)
        else:
            m = re.search(r'</section>(\s*)<div class="wrap-gradient-1">', html)
            if not m:
                print("AVISO: ancora do hero nao encontrada em %s — nada feito" % rel)
                continue
            html = html[:m.end(1)] + novo + html[m.end(1):]

        if html != orig:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(html)
            alterados += 1
            print("barra de logos aplicada: %s (%s)" % (rel, idioma))
        else:
            print("sem mudanca: %s" % rel)

    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
