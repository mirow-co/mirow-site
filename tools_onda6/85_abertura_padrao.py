# -*- coding: utf-8 -*-
"""85 — onda 29, S-108 (#166): abertura padrao nas paginas sem banner.

Uso:
    python tools_onda6/85_abertura_padrao.py <raiz-que-contem-public>

Achado da onda 27: tres aberturas conviviam no site — hero da home, banner de foto
das internas e NADA em ~26 paginas, que comecavam direto no titulo sobre o
gradiente. Ao abrir cada uma dessas 26, o quadro ficou mais claro e sao DOIS
problemas diferentes:

(a) 6 paginas de conteudo com o titulo nu (imprensa e politica de privacidade, nas
    tres linguas): recebem uma **faixa de abertura navy** com a tipografia do
    banner interno do tema (titulo 62px, apoio 22px) — o mesmo ritmo das outras
    paginas, sem inventar foto.

(b) 12 paginas **VAZIAS** — `<main>` com zero caractere de texto. Sao stubs de
    arquivo do WordPress (`/pratica/`, `/lider/`, `/sobre-nos/` e os equivalentes
    em EN/DE): renderizam barra e rodape e nada no meio. Nao e caso de "abertura
    diferente": e pagina em branco. Viram **redirect** para a pagina real
    correspondente (leitura: arquivo de praticas -> home, onde as praticas moram;
    arquivo de lideres -> pagina de lideres; pai "sobre nos" -> Nossos Valores,
    o primeiro item do submenu).

A pagina Nossos Valores NAO entra: ela tem abertura propria desenhada ("Nossa
Cultura"), nao esta quebrada — so e diferente de proposito.

Idempotente: a faixa so entra se o marcador ainda nao existir; o stub so e escrito
se o conteudo mudar.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

MARK_FAIXA = "<!-- onda29:abertura -->"
MARK_STUB = "onda29:stub-vazia"

# (b) pagina vazia -> pagina real. Chave = caminho relativo do index.html.
REDIRECIONAR = {
    "pratica/index.html": "/mirow-site/pt/",
    "pt/pratica/index.html": "/mirow-site/pt/",
    "en/practice/index.html": "/mirow-site/en/",
    "de/branchen/index.html": "/mirow-site/de/",
    "lider/index.html": "/mirow-site/pt/sobre-nos/lideres/",
    "pt/lider/index.html": "/mirow-site/pt/sobre-nos/lideres/",
    "en/leader/index.html": "/mirow-site/en/about-us/leaders/",
    "de/lider/index.html": "/mirow-site/de/ueber-uns/fuehrungskraefte/",
    "sobre-nos/index.html": "/mirow-site/pt/sobre-nos/nossos-valores/",
    "pt/sobre-nos/index.html": "/mirow-site/pt/sobre-nos/nossos-valores/",
    "en/about-us/index.html": "/mirow-site/en/about-us/our-values/",
    "de/ueber-uns/index.html": "/mirow-site/de/ueber-uns/unsere-werte/",
}

TITULO_STUB = {"pt": u"Mirow &amp; Co.", "en": u"Mirow &amp; Co.", "de": u"Mirow &amp; Co."}
TEXTO_STUB = {
    "pt": (u"Esta página não existe mais por si só.", u"Ir para a página certa"),
    "en": (u"This page no longer stands on its own.", u"Go to the right page"),
    "de": (u"Diese Seite existiert nicht mehr eigenständig.", u"Zur richtigen Seite"),
}

CSS = u"""/* ---- S-108: faixa de abertura das paginas sem banner --------------------
   Imprensa e politica de privacidade abriam com o titulo nu sobre o gradiente,
   enquanto toda pagina interna abre com uma faixa. Aqui a faixa existe sem foto:
   navy solido e a MESMA tipografia do `.internal-banner` do tema (62px/22px),
   para o ritmo ser o mesmo sem inventar imagem. */
.onda29-abertura{background:#020E66;padding:150px 0 70px;position:relative}
.onda29-abertura__titulo{color:#fff;font-family:var(--fontFamily);
  font-size:62px;font-weight:700;line-height:1.1;margin:0}
.onda29-abertura__apoio{color:#fff;font-family:var(--secondaryFontFamily);
  font-size:22px;font-weight:400;line-height:1.4;margin:14px 0 0;max-width:60ch}
/* o conteudo que segue nao precisa mais do respiro que compensava a falta da faixa */
.onda29-abertura + .page-default,
.onda29-abertura + div .page-default{padding-top:60px}
@media only screen and (max-width: 991px){
  .onda29-abertura{padding:110px 0 50px}
  .onda29-abertura__titulo{font-size:40px}
  .onda29-abertura__apoio{font-size:18px}
}"""


def faixa(titulo, apoio, marcador_extra=""):
    apoio_html = (u'<h2 class="onda29-abertura__apoio">%s</h2>' % apoio) if apoio else u""
    return (u'%s<section class="onda29-abertura"><div class="container"><div class="row">'
            u'<div class="col">%s<h1 class="onda29-abertura__titulo">%s</h1>%s'
            u'</div></div></div></section>'
            % (MARK_FAIXA, marcador_extra, titulo, apoio_html))


RE_H1 = re.compile(r'<!-- wp:heading \{"level":1\} -->\s*'
                   r'(?P<marca><!-- onda12:imprensa-formatacao -->)?\s*'
                   r'<h1 class="wp-block-heading">(?P<titulo>.*?)</h1>\s*'
                   r'<!-- /wp:heading -->\s*', re.S)
RE_H5 = re.compile(r'<!-- wp:heading \{"level":5\} -->\s*'
                   r'<h5 class="wp-block-heading">(?P<apoio>.*?)</h5>\s*'
                   r'<!-- /wp:heading -->\s*'
                   r'(?:<!-- wp:spacer -->\s*<div style="height:\d+px"[^>]*></div>\s*'
                   r'<!-- /wp:spacer -->\s*)?', re.S)
ABRE_DEFAULT = '<div class="container page-default">'


def com_faixa(html):
    """(a) move o titulo (e a linha de apoio) do corpo para a faixa de abertura."""
    if MARK_FAIXA in html:
        return html, None
    i = html.find(ABRE_DEFAULT)
    if i < 0:
        return html, None
    # a area de trabalho e so o comeco do container, para nao pegar um <h1> perdido
    trecho = html[i:i + 4000]
    m1 = RE_H1.search(trecho)
    if not m1:
        return html, None
    titulo = m1.group("titulo").strip()
    marca = m1.group("marca") or ""
    trecho2 = trecho[:m1.start()] + trecho[m1.end():]
    apoio = ""
    m5 = RE_H5.search(trecho2, 0, 600)
    if m5:
        apoio = re.sub(r'<[^>]+>', '', m5.group("apoio")).strip()
        trecho2 = trecho2[:m5.start()] + trecho2[m5.end():]
    novo = html[:i] + faixa(titulo, apoio, marca) + trecho2 + html[i + 4000:]
    return novo, titulo


def stub(lang, destino):
    frase, botao = TEXTO_STUB.get(lang, TEXTO_STUB["pt"])
    return (u'<!DOCTYPE html><html lang="%s"><head><meta charset="utf-8">\n'
            u'<!-- %s: a pagina de arquivo do WordPress era vazia (main sem texto) -->\n'
            u'<meta http-equiv="refresh" content="0;url=%s">\n'
            u'<link rel="canonical" href="%s">\n'
            u'<meta name="robots" content="noindex,follow">\n'
            u'<title>%s</title></head>\n'
            u'<body><p>%s <a href="%s">%s</a>.</p></body></html>\n'
            % (lang, MARK_STUB, destino, destino, TITULO_STUB.get(lang, "Mirow &amp; Co."),
               frase, destino, botao))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mudou = escrever_bloco_css(pub, "abertura-padrao", CSS, onda="onda29")
    print("bloco onda29:abertura-padrao %s" % ("gravado" if mudou else "ja estava igual"))

    # (b) primeiro os stubs: assim a faixa nao e aplicada a uma pagina que vai virar
    # redirect (e a contagem do (a) fica honesta)
    from _onda7_css import idioma_da_pagina
    n_stub = 0
    for rel, destino in sorted(REDIRECIONAR.items()):
        p = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(p):
            print("  AVISO: nao achei %s" % rel)
            continue
        atual = ler(p)
        lang = idioma_da_pagina(atual) if MARK_STUB not in atual else rel.split("/")[0]
        if lang not in ("pt", "en", "de"):
            lang = "pt"
        novo = stub(lang, destino)
        if atual == novo:
            continue
        with io.open(p, "w", encoding="utf-8", newline="") as f:
            f.write(novo)
        n_stub += 1
        print("  vazia -> redirect: %-32s -> %s" % (rel, destino))
    print("S-108 (b) paginas vazias viradas redirect: %d" % n_stub)

    # (a) a faixa de abertura
    n_faixa = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            p = os.path.join(dirpath, nome)
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            h = ler(p)
            if "menu__nav-item" not in h or ABRE_DEFAULT not in h:
                continue
            # so paginas SEM banner (as com banner ja tem abertura)
            if re.search(r'class="(banner|internal-banner|experience-single__banner|'
                         r'blog-single__banner)', h):
                continue
            novo, titulo = com_faixa(h)
            if titulo and novo != h:
                gravar(p, novo)
                n_faixa += 1
                print("  faixa de abertura: %-40s (%s)" % (rel, titulo))
    print("S-108 (a) paginas com faixa de abertura: %d" % n_faixa)


if __name__ == "__main__":
    main()
