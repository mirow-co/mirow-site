# -*- coding: utf-8 -*-
"""90 — onda 33, S-120 (#70) e S-121 (#71): sitemap.xml e a raiz indo para /pt/.

Uso:
    python tools_onda6/90_sitemap_e_raiz.py <raiz-que-contem-public> [--dry-run]

DOIS PEDIDOS, os dois sobre a raiz do site:

S-120 (#70) — sitemap.xml
    O `public/robots.txt` (trabalho de GEO da #46) libera os crawlers de LLM e
    termina com `Sitemap: .../sitemap-index.xml` — um arquivo que NUNCA existiu.
    Crawler liberado sem mapa e GEO pela metade.

    Gera UM sitemap.xml (decisao do Mario, 04/08: "um sitemap.xml so") a partir do
    `rel=canonical` das paginas de CONTEUDO. Os stubs de redirect ficam fora: sao
    159 de 160 `noindex,follow`, e listar um noindex no sitemap e contradicao que
    o Search Console reporta como erro.

    `lastmod` vem do `dateModified` do JSON-LD do Yoast (110 das 113 paginas o
    tem); quem nao tem sai sem lastmod, que e opcional no protocolo — inventar
    data seria pior.

S-121 (#71) — a raiz do Pages
    `public/index.html` manda para `/mirow-site/en/`. Numa firma brasileira, cujo
    conteudo principal e PT, o padrao e `/pt/`. Decisao do Mario.

BASE e o unico lugar com o host: na virada de DNS da #42 muda aqui, e o robots.txt
(que tem o host escrito na linha Sitemap) e reescrito junto por este mesmo script.

Idempotente: no segundo run o sitemap e byte-identico, o robots ja aponta para ele e
a raiz ja vai para /pt/ — reporta 0 mudanca.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import ler, resolve_public  # noqa: E402

# Host do site. Na virada de DNS (#42) vira "https://mirow.com.br" e o PREFIXO
# do espelho vira "" — os dois trocam juntos, aqui.
BASE = "https://mirow-co.github.io"
PREFIXO = "/mirow-site/"

IDIOMA_PADRAO = "pt"     # S-121: para onde a raiz do Pages aponta

RAIZ_HTML = (u'<!DOCTYPE html><meta http-equiv="refresh" content="0;url=%s%s/">'
             % (PREFIXO, IDIOMA_PADRAO))


def eh_stub(rel, html):
    if rel == "index.html":
        return True
    return 'http-equiv="refresh"' in html and '<footer class="footer">' not in html


def paginas_de_conteudo(pub):
    """[(rel, html)] das paginas que valem indexacao (exclui stubs de redirect)."""
    out = []
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if not nome.endswith(".html"):
                continue
            p = os.path.join(dirpath, nome)
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            h = ler(p)
            if not eh_stub(rel, h):
                out.append((rel, h))
    out.sort()
    return out


def urls_do_sitemap(pub):
    """[(loc absoluta, lastmod ou None)] — a partir do canonical de cada pagina."""
    itens = {}
    for rel, h in paginas_de_conteudo(pub):
        m = re.search(r'rel="canonical" href="([^"]+)"', h)
        if not m:
            print("  AVISO: sem canonical, fora do sitemap: %s" % rel)
            continue
        can = m.group(1)
        if not can.startswith(PREFIXO):
            print("  AVISO: canonical fora do espelho (%s) em %s" % (can, rel))
            continue
        loc = BASE + can.rstrip("/") + "/"
        d = re.search(r'"dateModified":"([^"T]+)T', h)
        lastmod = d.group(1) if d else None
        # canonical duplicado nao deveria existir depois da S-107; se existir,
        # o primeiro (ordem alfabetica) vence e o segundo e avisado.
        if loc in itens:
            print("  AVISO: canonical repetido, ja no sitemap: %s (%s)" % (loc, rel))
            continue
        itens[loc] = lastmod
    return sorted(itens.items())


def xml_do_sitemap(itens):
    linhas = [u'<?xml version="1.0" encoding="UTF-8"?>',
              u'<!-- Gerado por tools_onda6/90_sitemap_e_raiz.py (onda 33, S-120).',
              u'     Nao editar a mao: e artefato, e a assercao S120 recalcula e compara. -->',
              u'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in itens:
        linhas.append(u'  <url>')
        linhas.append(u'    <loc>%s</loc>' % loc)
        if lastmod:
            linhas.append(u'    <lastmod>%s</lastmod>' % lastmod)
        linhas.append(u'  </url>')
    linhas.append(u'</urlset>')
    return u"\n".join(linhas) + u"\n"


def robots_apontando_pro_sitemap(atual, url_sitemap):
    """Troca a linha Sitemap: e a NOTA de virada de DNS que ficou obsoleta."""
    novo = re.sub(r'^Sitemap:.*$', u'Sitemap: %s' % url_sitemap, atual, flags=re.M)
    # a nota citava sitemap-index.xml, que nunca existiu
    novo = novo.replace(
        u"# NOTA: trocar o host abaixo para https://mirow.com.br/sitemap-index.xml\n"
        u"# na virada de DNS (junto com site/base do astro.config.mjs — Onda 3).",
        u"# NOTA: na virada de DNS (#42), o host sai de mirow-co.github.io para\n"
        u"# mirow.com.br na constante BASE de tools_onda6/90_sitemap_e_raiz.py —\n"
        u"# rodar o script reescreve o sitemap.xml e esta linha juntos.")
    return novo


def grava_se_mudou(path, conteudo, dry, rotulo):
    atual = ler(path) if os.path.exists(path) else None
    if atual == conteudo:
        print("%s: sem mudanca" % rotulo)
        return False
    if not dry:
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(conteudo)
    print("%s: %s%s" % (rotulo, "criado" if atual is None else "atualizado",
                        " (dry-run)" if dry else ""))
    return True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    dry = "--dry-run" in sys.argv

    # ---- S-120: o sitemap
    itens = urls_do_sitemap(pub)
    com_data = sum(1 for _l, d in itens if d)
    print("sitemap: %d URLs (%d com lastmod, %d sem)"
          % (len(itens), com_data, len(itens) - com_data))
    grava_se_mudou(os.path.join(pub, "sitemap.xml"),
                   xml_do_sitemap(itens), dry, "  public/sitemap.xml")

    # ---- S-120: o robots aponta para ele
    url_sitemap = BASE + PREFIXO + "sitemap.xml"
    p_robots = os.path.join(pub, "robots.txt")
    grava_se_mudou(p_robots,
                   robots_apontando_pro_sitemap(ler(p_robots), url_sitemap),
                   dry, "  public/robots.txt")
    print("  Sitemap: %s" % url_sitemap)

    # ---- S-121: a raiz
    grava_se_mudou(os.path.join(pub, "index.html"), RAIZ_HTML, dry,
                   "raiz do Pages -> /%s/" % IDIOMA_PADRAO)


if __name__ == "__main__":
    main()
