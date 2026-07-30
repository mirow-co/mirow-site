# -*- coding: utf-8 -*-
"""Helpers compartilhados da onda 7.

Todo CSS novo da onda 7 vive em blocos marcados dentro de
public/wp-content/uploads/2026/07/onda6/onda6.css — o mesmo arquivo da onda 6,
para nao multiplicar <link>. Cada script controla o SEU bloco pela chave, o que
mantem os scripts independentes e idempotentes.
"""
import io
import os
import re

CSS_REL = "wp-content/uploads/2026/07/onda6/onda6.css"
CSS_LINK_ID = "onda6-css"


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def base_prefix(html):
    """Prefixo de URL do espelho (ex.: /mirow-site/)."""
    m = re.search(r'(?:src|href)="(/[^"]*?/)wp-content/', html)
    return m.group(1) if m else "/"


def idioma_da_pagina(html):
    """Idioma da pagina pelo cookie que o Polylang grava no rodape.

    E o unico marcador confiavel: as 272 paginas tem exatamente um
    pll_language=xx (144 pt, 58 en, 70 de). Detectar por caminho falha nas
    paginas de topo, e detectar por link falha por causa dos hreflang alternate.
    """
    m = re.search(r'pll_language=([a-z]{2})', html)
    return m.group(1) if m and m.group(1) in ("pt", "en", "de") else "pt"


def garantir_link_css(html, prefix):
    if CSS_LINK_ID in html:
        return html
    link = '<link rel="stylesheet" id="%s" href="%s%s" media="all" />\n' % (
        CSS_LINK_ID, prefix, CSS_REL)
    return html.replace("</head>", link + "</head>", 1)


def escrever_bloco_css(pub, chave, css):
    """Grava/atualiza um bloco marcado no onda6.css. Devolve True se mudou."""
    path = os.path.join(pub, CSS_REL.replace("/", os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    atual = ""
    if os.path.exists(path):
        with io.open(path, encoding="utf-8") as f:
            atual = f.read()
    ini = "/* onda7:%s:ini */" % chave
    fim = "/* onda7:%s:fim */" % chave
    bloco = "%s\n%s\n%s\n" % (ini, css.strip(), fim)
    if ini in atual:
        novo = re.sub(re.escape(ini) + r".*?" + re.escape(fim) + r"\n?",
                      bloco, atual, flags=re.S)
    else:
        novo = atual.rstrip("\n") + "\n\n" + bloco
    if novo != atual:
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(novo)
        return True
    return False


def ler(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def gravar(path, html):
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(html)


def paginas(pub, contendo):
    """Todos os index.html sob public/ que contenham o trecho dado."""
    out = []
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            p = os.path.join(dirpath, nome)
            try:
                h = ler(p)
            except Exception:
                continue
            if contendo in h:
                out.append((p, os.path.relpath(p, pub).replace(os.sep, "/")))
    out.sort(key=lambda t: t[1])
    return out
