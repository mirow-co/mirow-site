# -*- coding: utf-8 -*-
"""100 — onda 49, S-144 (#102): shims de sitemap nos caminhos antigos do WP.

Uso:
    python tools_onda6/100_wp_sitemap_shims.py <raiz-que-contem-public> [--dry-run]

POR QUE EXISTE
    A #102 pedia 301 via .htaccess (Rota A/HostGator), mas a virada real foi para
    o GitHub Pages (#101), que nao faz redirect de servidor. O AWStats de 2026
    (05_Analises/awstats_raw/ssl no repo privado) mostra que os crawlers ainda
    pedem os sitemaps do WordPress aos milhares por mes (/wp-sitemap.xml ~3,8 mil
    hits; cada sub-sitemap por idioma ~3,6 mil) — e hoje todos respondem 404.

    Um 404 em sitemap faz o Search Console reclamar e atrasa o crawler a achar o
    mapa novo. O conserto sem servidor: servir em CADA caminho antigo um
    <sitemapindex> minimo apontando para o sitemap canonico
    (https://mirow.com.br/sitemap.xml, gerado pelo 90_sitemap_e_raiz.py). Index
    de sitemap e valido em qualquer caminho; o crawler que chegar pelo endereco
    velho e levado ao mapa real em um salto.

    O conteudo dos shims e IDENTICO em todos os caminhos e e recalculado pela
    S144 (padrao S120: a assercao regera e compara byte a byte).

Idempotente: segundo run reporta 0 mudanca.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import ler, resolve_public  # noqa: E402

# Mesmo host do 90_sitemap_e_raiz.py (nao importar para nao acoplar a ordem de
# execucao; a S144 confere que os dois batem).
BASE = "https://mirow.com.br"
SITEMAP_CANONICO = BASE + "/sitemap.xml"

# Caminhos antigos do WP que os crawlers ainda pedem (top do AWStats 2026,
# repo privado 05_Analises/awstats_raw/ssl — todos 404 no espelho em 11/08).
IDIOMAS = ("pt", "en", "de")
SUFIXOS_POR_IDIOMA = (
    "wp-sitemap.xml",
    "wp-sitemap-posts-post-1.xml",
    "wp-sitemap-posts-page-1.xml",
    "wp-sitemap-posts-experience-1.xml",
    "wp-sitemap-posts-leader-1.xml",
    "wp-sitemap-taxonomies-category-1.xml",
    "wp-sitemap-taxonomies-post_tag-1.xml",
    "wp-sitemap-users-1.xml",
)
RAIZ_EXTRAS = (
    "wp-sitemap.xml",        # WP core na raiz
    "sitemap_index.xml",     # estilo Yoast
    "author-sitemap.xml",
    "leader-sitemap.xml",
)


def caminhos_legados():
    """Lista relativa (com /) de todos os shims a existir em public/."""
    out = list(RAIZ_EXTRAS)
    for lang in IDIOMAS:
        for suf in SUFIXOS_POR_IDIOMA:
            out.append("%s/%s" % (lang, suf))
    return sorted(set(out))


def xml_do_shim():
    return (
        u'<?xml version="1.0" encoding="UTF-8"?>\n'
        u'<!-- Shim da onda 49 (S-144, #102): este caminho era um sitemap do\n'
        u'     WordPress; o mapa canonico agora e %s .\n'
        u'     Gerado por tools_onda6/100_wp_sitemap_shims.py — nao editar a mao. -->\n'
        u'<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        u'  <sitemap>\n'
        u'    <loc>%s</loc>\n'
        u'  </sitemap>\n'
        u'</sitemapindex>\n' % (SITEMAP_CANONICO, SITEMAP_CANONICO))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    dry = "--dry-run" in sys.argv
    conteudo = xml_do_shim()
    mudou = 0
    for rel in caminhos_legados():
        p = os.path.join(pub, rel.replace("/", os.sep))
        atual = ler(p) if os.path.exists(p) else None
        if atual == conteudo:
            continue
        if not dry:
            with io.open(p, "w", encoding="utf-8", newline="") as f:
                f.write(conteudo)
        print("  %s: %s%s" % (rel, "criado" if atual is None else "atualizado",
                              " (dry-run)" if dry else ""))
        mudou += 1
    print("shims: %d caminho(s), %d mudanca(s)" % (len(caminhos_legados()), mudou))


if __name__ == "__main__":
    main()
