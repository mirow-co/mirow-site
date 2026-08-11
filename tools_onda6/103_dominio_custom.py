# -*- coding: utf-8 -*-
"""Onda 47 / S-44 (issue mirow-marketing#101, cutover #42): domínio custom.

Prepara o espelho para ser servido em https://mirow.com.br (raiz), em vez do
staging https://mirow-co.github.io/mirow-site/ (subpath). É a "Rota A" pedida
pelo Mario em 03/08: na virada de DNS só a raiz/www muda de A/CNAME; o site
estático precisa parar de depender do prefixo /mirow-site/.

O que este script faz (idempotente — re-rodar não muda nada):

1. Em todo arquivo de texto de public/ (html, css, js, xml, txt):
   a. https://mirow-co.github.io/mirow-site/  ->  https://mirow.com.br/
   b. https://mirow-co.github.io (sem path)   ->  https://mirow.com.br
   c. /mirow-site/                            ->  /   (root-relative)
   (a ordem importa: o absoluto antes do relativo, senão o relativo quebraria
   a URL absoluta no meio.)
2. Canonical e hreflang viram URLs ABSOLUTAS em https://mirow.com.br
   (Google exige canonical absoluto; hreflang recíproco idem).
3. Escreve public/CNAME com "mirow.com.br" (é o que liga o domínio custom no
   GitHub Pages a partir do branch gh-pages).
4. Cria public/404.html com a marca (GitHub Pages serve /404.html nativo).

O que ele NÃO faz: mexer em DNS, em MX, em subdomínio, ou no WordPress. Nada
aqui toca produção — produção só muda quando os registros A/CNAME mudarem no
painel (sessão conjunta com o Mario).

Uso: python tools_onda6/103_dominio_custom.py <raiz>
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public, ler, gravar  # noqa: E402

HOST = "https://mirow.com.br"
STAGING = "https://mirow-co.github.io"
PREFIXO = "/mirow-site/"

EXTS = (".html", ".css", ".js", ".xml", ".txt", ".json")

PAG_404 = u"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Página não encontrada — Mirow &amp; Co.</title>
<style>
  body{margin:0;font-family:Arial,Helvetica,sans-serif;
       background:linear-gradient(160deg,#071C25,#041545 55%,#020E66);
       color:#fff;min-height:100vh;display:flex;align-items:center;
       justify-content:center;text-align:center}
  .caixa{padding:40px;max-width:560px}
  h1{font-size:22px;margin:0 0 12px;color:#fff}
  p{font-size:15px;line-height:1.6;color:#AAD5E8;margin:0 0 28px}
  a.btn{display:inline-block;background:#00ADEC;color:#fff;text-decoration:none;
        padding:12px 28px;border-radius:4px;font-weight:bold;font-size:15px}
  .marca{margin-top:48px;font-size:13px;letter-spacing:.35em;color:#7F7F7F}
</style>
</head>
<body>
<div class="caixa">
  <h1>Página não encontrada</h1>
  <p>O endereço que você procurou não existe ou mudou de lugar.</p>
  <a class="btn" href="/pt/">Ir para a página inicial</a>
  <div class="marca">MIROW &amp; CO.</div>
</div>
</body>
</html>
"""


def arquivos_texto(pub):
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome.lower().endswith(EXTS):
                yield os.path.join(dirpath, nome)


def absolutiza_seo(html):
    """canonical e hreflang com URL absoluta no host final."""
    def troca(m):
        tag = m.group(0)
        return tag.replace('href="/', 'href="%s/' % HOST, 1)
    html = re.sub(r'<link rel="canonical" href="/[^"]*"[^>]*>', troca, html)
    html = re.sub(r'<link rel="alternate" href="/[^"]*" hreflang="[^"]*"[^>]*>',
                  troca, html)
    return html


def main():
    raiz = sys.argv[1] if len(sys.argv) > 1 else "."
    pub = resolve_public(raiz)

    # ordem importa: absoluto antes do relativo; escapado (JSON-LD) antes do cru
    REGRAS = [
        (STAGING + PREFIXO, HOST + "/"),
        (STAGING + PREFIXO.rstrip("/"), HOST),
        (STAGING, HOST),
        # JSON-LD do Yoast: URLs com barras escapadas viram absolutas
        (u"/mirow-site\\/", u"https:\\/\\/mirow.com.br\\/"),
        (PREFIXO, u"/"),
        # siteData do tema e JS de medição: raiz do site vira string vazia
        (u"var BASE = '/mirow-site';", u"var BASE = '';"),
        (u'"root_url":"/mirow-site"', u'"root_url":""'),
        # kama-click-counter: url do contador na raiz
        (u'"/mirow-site?download=', u'"/?download='),
    ]
    tocados = 0
    trocas = 0
    for path in arquivos_texto(pub):
        antes = ler(path)
        depois = antes
        n_pref = depois.count(PREFIXO)
        for velho, novo in REGRAS:
            depois = depois.replace(velho, novo)
        if path.lower().endswith(".html"):
            depois = absolutiza_seo(depois)
        if depois != antes:
            gravar(path, depois)
            tocados += 1
            trocas += n_pref
    print("arquivos alterados: %d (paths /mirow-site/ reescritos: %d)"
          % (tocados, trocas))

    cname = os.path.join(pub, "CNAME")
    conteudo = "mirow.com.br\n"
    if not os.path.exists(cname) or ler(cname) != conteudo:
        with io.open(cname, "w", encoding="ascii", newline="\n") as f:
            f.write(conteudo)
        print("CNAME gravado: mirow.com.br")

    p404 = os.path.join(pub, "404.html")
    if not os.path.exists(p404) or ler(p404) != PAG_404:
        gravar(p404, PAG_404)
        print("404.html gravado")

    # sobrou referência ao staging ou ao prefixo? falha alto.
    sobras = []
    for path in arquivos_texto(pub):
        h = ler(path)
        if "mirow-site" in h or STAGING in h:
            sobras.append(os.path.relpath(path, pub))
    if sobras:
        print("SOBRAS (%d): %s" % (len(sobras), ", ".join(sobras[:10])))
        sys.exit(1)
    print("0 sobras de /mirow-site/ ou github.io em public/")


if __name__ == "__main__":
    main()
