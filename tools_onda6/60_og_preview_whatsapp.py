# -*- coding: utf-8 -*-
"""60 — S-40: preview de link (WhatsApp/LinkedIn) com o logo Mirow.

Uso:
    python tools_onda6/60_og_preview_whatsapp.py <raiz-que-contem-public>

Pedido do Mario (31/07): ao colar o link no WhatsApp aparecia uma foto
generica do WordPress. Duas causas: (a) o og:image default era a
Capa-4...jpg; (b) todas as URLs de og:image/og:url eram RELATIVAS
(/mirow-site/...) — WhatsApp/OG exigem URL absoluta.

O QUE FAZ (nas 275 paginas)
---------------------------
1. og:image com a Capa-4 (default generico do WP) -> cartao com o logo
   (onda6/og-mirow.png, 1200x630, navy + logo branco). Paginas com imagem
   propria (posts de insights) MANTEM a sua.
2. Toda og:image / og:image:secure_url / og:url / twitter:image relativa
   vira absoluta com o host do Pages.
3. og:image:width/height 1200x630 adicionados quando o cartao e usado.

ATENCAO (migracao de DNS): o HOST abaixo e o do GitHub Pages. Quando o site
virar mirow.com.br, rodar de novo com o HOST novo (e atualizar a assercao).

Idempotente.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

HOST = "https://mirow-co.github.io"
CARTAO = HOST + "/mirow-site/wp-content/uploads/2026/07/onda6/og-mirow.png"

REX_META = re.compile(
    r'(<meta (?:property|name)="(og:image|og:image:secure_url|og:url|twitter:image)" '
    r'content=")([^"]*)(")')

DIMS = ('<meta property="og:image:width" content="1200" />'
        '<meta property="og:image:height" content="630" />')


def tratar(html):
    usa_cartao = [False]

    def troca(m):
        prefixo, chave, valor, fim = m.group(1), m.group(2), m.group(3), m.group(4)
        if chave in ("og:image", "og:image:secure_url", "twitter:image") and "Capa-4" in valor:
            usa_cartao[0] = True
            return prefixo + CARTAO + fim
        if valor.startswith("/"):
            return prefixo + HOST + valor + fim
        return m.group(0)

    novo = REX_META.sub(troca, html)
    if usa_cartao[0] and 'property="og:image:width"' not in novo:
        novo = novo.replace('<meta property="og:image" content="%s" />' % CARTAO,
                            '<meta property="og:image" content="%s" />%s' % (CARTAO, DIMS), 1)
    return novo


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    if not os.path.exists(os.path.join(
            pub, "wp-content", "uploads", "2026", "07", "onda6", "og-mirow.png")):
        raise SystemExit("ERRO: og-mirow.png ausente")
    alterados = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            novo = tratar(h)
            if novo != h:
                gravar(p, novo)
                alterados += 1
    print("resumo: %d pagina(s) com OG corrigido" % alterados)


if __name__ == "__main__":
    main()
