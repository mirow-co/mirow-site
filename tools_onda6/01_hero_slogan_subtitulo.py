# -*- coding: utf-8 -*-
"""
01_hero_slogan_subtitulo.py — troca o titulo e o subtitulo do hero das homes.

Uso:  python tools_onda6/01_hero_slogan_subtitulo.py <raiz-da-arvore>

- Titulo do hero (<h2> dentro de <section class="banner">) passa a ser o slogan de
  3 palavras decidido pelo Mario (30/07), com UMA PALAVRA POR LINHA. Revisao do
  Mario no mesmo dia: o separador "|" saiu; agora sao <br>, que o `.banner h2` do
  tema aceita sem precisar de CSS novo.
- Paragrafo do hero passa a ser o subtitulo novo.
- NAO altera <title>, meta description nem qualquer classe/tag/estilo do tema.
- Idempotente: se o texto novo ja esta la, nada muda.
"""
import io
import os
import re
import sys

TEXTOS = {
    "pt": (
        u"Estratégia<br>Confiança<br>Resultado",
        u"Trabalhamos lado a lado com a alta gestão, combinando profundidade "
        u"analítica e abordagens inovadoras para resolver os desafios que mais "
        u"importam — e entregar resultados que permanecem",
    ),
    "en": (
        u"Strategy<br>Trust<br>Results",
        u"We work side by side with senior leadership, combining analytical depth "
        u"and innovative approaches to solve the challenges that matter most — and "
        u"deliver results that last",
    ),
    "de": (
        u"Strategie<br>Vertrauen<br>Ergebnisse",
        u"Wir arbeiten Seite an Seite mit dem Top-Management und verbinden "
        u"analytische Tiefe mit innovativen Ansätzen, um die entscheidenden "
        u"Herausforderungen zu lösen – und Ergebnisse zu liefern, die Bestand haben",
    ),
}

HOMES = [
    ("pt/index.html", "pt"),
    ("en/index.html", "en"),
    ("en/homepage/index.html", "en"),
    ("de/index.html", "de"),
]


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = 0
    for rel, idioma in HOMES:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: nao existe %s" % rel)
            continue
        with io.open(path, encoding="utf-8") as f:
            html = f.read()
        orig = html
        titulo, sub = TEXTOS[idioma]

        i = html.find('<section class="banner"')
        if i < 0:
            print("AVISO: hero nao encontrado em %s" % rel)
            continue
        fim = html.find("</section>", i)
        hero = html[i:fim]
        novo_hero = re.sub(r'(<h2[^>]*>)(.*?)(</h2>)',
                           lambda m: m.group(1) + titulo + m.group(3),
                           hero, count=1, flags=re.S)
        novo_hero = re.sub(r'(<p>)(.*?)(</p>)',
                           lambda m: m.group(1) + sub + m.group(3),
                           novo_hero, count=1, flags=re.S)
        html = html[:i] + novo_hero + html[fim:]

        if html != orig:
            with io.open(path, "w", encoding="utf-8", newline="") as f:
                f.write(html)
            alterados += 1
            print("hero atualizado: %s (%s)" % (rel, idioma))
        else:
            print("sem mudanca: %s" % rel)
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
