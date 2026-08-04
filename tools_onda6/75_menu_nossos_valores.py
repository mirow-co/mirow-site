# -*- coding: utf-8 -*-
"""75 — onda 19, ajuste da S-67 (issue #125): o ROTULO do menu tambem muda.

Uso:
    python tools_onda6/75_menu_nossos_valores.py <raiz-que-contem-public>

Pedido do Mario: "nosso trabalho precisa ser nossos valores."

Na onda 18 so a URL mudou (/sobre-nos/nosso-trabalho/ -> /sobre-nos/nossos-valores/);
o rotulo ficou "Nosso Trabalho" de proposito, esperando esta decisao. Agora o texto
visivel muda em toda parte: submenu "Sobre nos" do header e da barra do rodape,
titulo/OG/schema da propria pagina e qualquer link solto.

Escopo do replace: so as OCORRENCIAS DE TEXTO do rotulo (nunca caminho de arquivo,
nunca a classe page-our-work, nunca o nome da imagem bg-banner-our-work).

Idempotente: se o rotulo novo ja esta lá, o padrao antigo nao aparece.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

# (de, para) — texto visivel, por idioma. Ordem importa: o mais especifico primeiro.
TROCAS = [
    (u">Nosso Trabalho<", u">Nossos Valores<"),
    (u">Nosso trabalho<", u">Nossos Valores<"),
    (u">Our Work<", u">Our Values<"),
    (u">Our work<", u">Our Values<"),
    (u">Unsere Arbeit<", u">Unsere Werte<"),
    # titulo da aba / OG / schema (aparecem como texto entre tags ou em conteudo)
    (u"Nosso Trabalho -", u"Nossos Valores -"),
    (u"Our Work -", u"Our Values -"),
    (u"Unsere Arbeit -", u"Unsere Werte -"),
    (u'"Nosso Trabalho"', u'"Nossos Valores"'),
    (u'"Our Work"', u'"Our Values"'),
    (u'"Unsere Arbeit"', u'"Unsere Werte"'),
]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    alterados = 0
    total = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not (n.endswith(".html") or n.endswith(".xml")):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            novo = h
            for de, para in TROCAS:
                if de in novo:
                    total += novo.count(de)
                    novo = novo.replace(de, para)
            if novo != h:
                gravar(p, novo)
                alterados += 1
    print("resumo: %d ocorrencia(s) do rotulo trocadas em %d arquivo(s)"
          % (total, alterados))


if __name__ == "__main__":
    main()
