# -*- coding: utf-8 -*-
"""86 — onda 29, S-107 (#165): uma URL por pagina.

Uso:
    python tools_onda6/86_urls_unicas.py <raiz-que-contem-public> [--dry-run]

Achado da onda 27: 216 das 283 paginas eram o MESMO conteudo em URLs diferentes —
heranca do espelho WordPress, onde cada pagina de pratica responde em `/pratica/`,
`/practice/` e `/branchen/`, com e sem o prefixo `/pt/`. O `rel=canonical` estava
correto em todas, entao o Google ja escolhia a URL boa; o problema era de
experiencia: o visitante podia cair numa URL com cara de alemao e receber a pagina
em portugues, e um link compartilhado podia ser qualquer uma das 6 variantes.

Decisao do Mario (04/08): redirecionar as duplicatas para a canonica.

O que faz, na ordem:
  1. Descobre as duplicatas pelo PROPRIO canonical do WordPress (URL da pagina !=
     canonical). Nao ha adivinhacao nem heuristica de conteudo: 145 paginas
     duplicadas apontando para 73 URLs canonicas.
  2. Reescreve os links internos de TODAS as paginas para a URL canonica — inclusive
     os do menu, que apontavam para `/mirow-site/insights/`, `/carreiras/`,
     `/contato/` e `/imprensa/` (variantes de raiz). Sem isso o menu levaria a um
     redirect a cada clique.
  3. Grava um stub de redirect em cada URL duplicada (mesmo procedimento da S-95).

NAO toca: `public/index.html` (o redirect da raiz do Pages), `en/homepage/` (que tem
canonical proprio — e uma home de verdade, ver S-16) e os stubs ja existentes.

Idempotente: stub so e reescrito se mudar; o passo 2 nao encontra mais nada para
trocar no segundo run.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

MARK = "onda29:url-unica"
# stubs que ja existiam (S-67 e S-95) NAO podem ser reescritos: o marcador deles
# e cobrado por assercao propria, e o destino ja e a URL certa
MARCAS_DE_STUB = ("onda29:stub-vazia", "onda25:redirect-s95",
                  "onda18:redirect-s67", MARK)

TEXTO = {
    "pt": (u"Esta página mudou de endereço.", u"Ir para a página"),
    "en": (u"This page has moved.", u"Go to the page"),
    "de": (u"Diese Seite ist umgezogen.", u"Zur Seite"),
}


def mapa_de_duplicatas(pub):
    """{rel do index.html duplicado: URL canonica}, pelo canonical do proprio HTML."""
    dupl = {}
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            p = os.path.join(dirpath, nome)
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            if rel == "index.html":            # redirect da raiz do Pages
                continue
            h = ler(p)
            if any(m in h for m in MARCAS_DE_STUB):
                continue
            c = re.search(r'rel="canonical" href="([^"]+)"', h)
            if not c:
                continue
            propria = "/mirow-site/" + rel[:-len("index.html")]
            canonica = c.group(1).rstrip("/") + "/"
            if canonica != propria:
                dupl[rel] = canonica
    return dupl


def idioma(rel, canonica):
    for lang in ("pt", "en", "de"):
        if canonica.startswith("/mirow-site/%s/" % lang):
            return lang
    return "pt"


def stub(lang, destino):
    frase, botao = TEXTO.get(lang, TEXTO["pt"])
    return (u'<!DOCTYPE html><html lang="%s"><head><meta charset="utf-8">\n'
            u'<!-- %s: uma URL por pagina — esta era duplicata da canonica -->\n'
            u'<meta http-equiv="refresh" content="0;url=%s">\n'
            u'<link rel="canonical" href="%s">\n'
            u'<meta name="robots" content="noindex,follow">\n'
            u'<title>Mirow &amp; Co.</title></head>\n'
            u'<body><p>%s <a href="%s">%s</a>.</p></body></html>\n'
            % (lang, MARK, destino, destino, frase, destino, botao))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    dry = "--dry-run" in sys.argv

    dupl = mapa_de_duplicatas(pub)
    print("duplicatas encontradas: %d -> %d URLs canonicas"
          % (len(dupl), len(set(dupl.values()))))

    # --- passo 2: os links internos apontam para a canonica.
    # Mais longo primeiro: `/mirow-site/branchen/` nao pode comer
    # `/mirow-site/branchen/estrategia/`.
    trocas = []
    for rel, canonica in dupl.items():
        antiga = "/mirow-site/" + rel[:-len("index.html")]
        trocas.append((antiga, canonica))
    trocas.sort(key=lambda t: -len(t[0]))
    # variantes escapadas que aparecem em JSON inline (mesmo caso da S-95)
    trocas_json = [(a.replace("/", r"\/"), b.replace("/", r"\/")) for a, b in trocas]
    trocas_url = [(a.replace("/", "%2F"), b.replace("/", "%2F")) for a, b in trocas]

    n_links = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if not (nome.endswith(".html") or nome.endswith(".xml")):
                continue
            p = os.path.join(dirpath, nome)
            h = ler(p)
            if any(m in h for m in MARCAS_DE_STUB):
                continue
            novo = h
            for de, para in trocas + trocas_json + trocas_url:
                if de in novo:
                    novo = novo.replace(de, para)
            if novo != h:
                n_links += 1
                if not dry:
                    gravar(p, novo)
    print("paginas com links internos reescritos: %d%s"
          % (n_links, " (dry-run)" if dry else ""))

    # --- passo 3: os stubs
    n_stub = 0
    for rel, canonica in sorted(dupl.items()):
        p = os.path.join(pub, rel.replace("/", os.sep))
        conteudo = stub(idioma(rel, canonica), canonica)
        if ler(p) == conteudo:
            continue
        n_stub += 1
        if not dry:
            with io.open(p, "w", encoding="utf-8", newline="") as f:
                f.write(conteudo)
    print("stubs de redirect gravados: %d%s" % (n_stub, " (dry-run)" if dry else ""))


if __name__ == "__main__":
    main()
