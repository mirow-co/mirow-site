# -*- coding: utf-8 -*-
"""Onda 59 (GEO, mirow-marketing#231): /pt/lider/591/ -> /pt/lider/michael-munch/.

- Cria a pagina de conteudo em pt/lider/michael-munch/ (copia da 591 com
  canonical/og:url/hreflang reescritos).
- pt/lider/591/ vira stub redirect noindex (padrao onda 29/33).
- Todo outro HTML que referencie pt/lider/591/ passa a apontar para o novo slug
  (hreflang das versoes EN/DE, stubs de variante de caminho, sitemap).

Idempotente: 2o run reporta 0 mudancas.
"""
import io
import os
import sys

ANTIGO = "pt/lider/591/"
NOVO = "pt/lider/michael-munch/"

STUB = (
    "<!DOCTYPE html><html lang=\"pt\"><head><meta charset=\"utf-8\">\n"
    "<!-- onda59:geo-slug: slug numerico do Michael Munch trocado por slug nominal (mirow-marketing#231) -->\n"
    "<meta http-equiv=\"refresh\" content=\"0;url=/pt/lider/michael-munch/\">\n"
    "<link rel=\"canonical\" href=\"https://mirow.com.br/pt/lider/michael-munch/\">\n"
    "<meta name=\"robots\" content=\"noindex,follow\">\n"
    "<title>Mirow &amp; Co.</title></head>\n"
    "<body><p>Esta página mudou de endereço. "
    "<a href=\"/pt/lider/michael-munch/\">Ir para a página</a>.</p></body></html>"
)


def ler(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def gravar(p, s):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def main(raiz):
    pub = os.path.join(raiz, "public")
    dir_antigo = os.path.join(pub, "pt", "lider", "591")
    dir_novo = os.path.join(pub, "pt", "lider", "michael-munch")
    mudancas = 0

    # 1. Pagina de conteudo no slug novo
    idx_antigo = os.path.join(dir_antigo, "index.html")
    idx_novo = os.path.join(dir_novo, "index.html")
    if not os.path.isdir(dir_novo):
        os.makedirs(dir_novo)
    html_conteudo = None
    if os.path.exists(idx_antigo):
        h = ler(idx_antigo)
        if "onda59:geo-slug" not in h:  # ainda e a pagina de conteudo
            html_conteudo = h.replace(ANTIGO, NOVO)
    if html_conteudo is not None:
        gravar(idx_novo, html_conteudo)
        mudancas += 1
        print("criada: pt/lider/michael-munch/index.html")

    # 2. 591 vira stub
    if not os.path.exists(idx_antigo) or ler(idx_antigo) != STUB:
        gravar(idx_antigo, STUB)
        mudancas += 1
        print("stub: pt/lider/591/index.html")

    # 3. Reescrever referencias no resto do site (inclui sitemap.xml)
    for base, _dirs, files in os.walk(pub):
        for nome in files:
            if not nome.endswith((".html", ".xml")):
                continue
            p = os.path.join(base, nome)
            if os.path.normpath(p) in (os.path.normpath(idx_antigo), os.path.normpath(idx_novo)):
                continue
            h = ler(p)
            if ANTIGO in h:
                gravar(p, h.replace(ANTIGO, NOVO))
                mudancas += 1
                print("reescrito: %s" % os.path.relpath(p, pub))

    print("total de mudancas: %d" % mudancas)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
