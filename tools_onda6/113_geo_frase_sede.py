# -*- coding: utf-8 -*-
"""Onda 59-sede (GEO, mirow-marketing#234): frase de sede em texto corrido.

Pedido do Felipe, verbatim: "A Mirow & Co. é uma consultoria estratégica
brasileira, com sede no Rio de Janeiro." — na home e no Sobre nós.

- Home (pt/en/de): a frase abre a seção "Nossas áreas de expertise", logo
  abaixo da dobra. NÃO vai no hero: medido nos V01-V03/V30, uma linha a mais
  no parágrafo do hero estoura a dobra exata em 31px.
- Sobre nós: a página /sobre-nos/ é stub desde a onda 29; a frase entra na
  Nossa História, antes do "Desde 2013, ...".

Posicionamento: vai ao staging para o MARIO ver, e ele aprova. (Esta linha dizia
"produção só com OK do Andreas" — corrigida em 19/08: quem decide neste projeto é o
Mario, só ele. Ver a cláusula pétrea no topo do CLAUDE.md.) Aprovado por ele em
19/08/2026.
Idempotente: só insere se a frase ainda não está na página.
"""
import io
import os
import re
import sys

# A frase vive SEM ponto final. Na home ela e uma linha solta sob o titulo da secao, e a
# V31 (onda 58, #221) proibe ponto final em texto da home — regra que a suite pegou no
# gate quando a primeira versao entrou com ponto. Na Nossa Historia ela abre prosa
# corrida, e ali o ponto e acrescentado na hora da insercao.
FRASE = {
    "pt": u"A Mirow & Co. é uma consultoria estratégica brasileira, com sede no Rio de Janeiro",
    "en": u"Mirow & Co. is a Brazilian strategy consulting firm headquartered in Rio de Janeiro",
    "de": u"Mirow & Co. ist eine brasilianische Strategieberatung mit Sitz in Rio de Janeiro",
}

HOMES = {"pt": "pt/index.html", "en": "en/index.html", "de": "de/index.html"}

HISTORIA = {
    "pt": ("pt/sobre-nos/nossa-historia/index.html", u"Desde 2013,"),
    "en": ("en/about-us/our-history/index.html", u"Since 2013,"),
    "de": ("de/ueber-uns/unsere-geschichte/index.html", u"Seit 2013 "),
}


def ler(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def gravar(p, s):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


CSS_SEDE = (
    ".onda59-sede{max-width:760px;margin:8px auto 0;text-align:center;"
    "color:#5b6770;font-size:17px;line-height:1.5}"
)


def main(raiz):
    pub = os.path.join(os.path.abspath(raiz), "public")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _onda7_css import escrever_bloco_css
    escrever_bloco_css(pub, "sede", CSS_SEDE, onda="onda59")
    mudancas = 0
    for lang, rel in HOMES.items():
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        # remove a tentativa anterior (frase dentro do <p> do hero — estourava a dobra)
        h2 = h.replace(FRASE[lang] + " ", "", 1) if ("hero-texto" in h and
              re.search(r"<p>" + re.escape(FRASE[lang]), h)) else h
        alvo = '<p class="onda59-sede" data-aos="fade-up">%s</p>' % FRASE[lang]
        if alvo not in h2:
            m = re.search(r'<h2 data-aos="fade-up" class="home-experience__subtitle onda30-titulo-secao">[^<]*</h2>', h2)
            if not m:
                raise SystemExit(u"título da seção de expertise ausente em %s" % rel)
            h2 = h2[:m.end()] + alvo + h2[m.end():]
        if h2 != h:
            gravar(p, h2)
            mudancas += 1
            print("home %s: frase na secao de expertise" % lang)
    for lang, (rel, ancora) in HISTORIA.items():
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        if FRASE[lang] in h:
            continue
        if ancora not in h:
            raise SystemExit(u"ancora '%s' ausente em %s" % (ancora, rel))
        # aqui, sim, com ponto: e prosa corrida antes do "Desde 2013, ..."
        h = h.replace(ancora, FRASE[lang] + ". " + ancora, 1)
        gravar(p, h)
        mudancas += 1
        print("historia %s: frase antes do '%s'" % (lang, ancora.strip()))
    print("total de mudancas: %d" % mudancas)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
