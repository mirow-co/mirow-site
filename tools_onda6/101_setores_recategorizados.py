# -*- coding: utf-8 -*-
"""Onda 42 / S-140 (issue mirow-marketing#194): os setores da home
recategorizados para representar o portfólio real.

Pedido do Mario (06/08): "as industrias na pagina inicial devem ser divididas
de forma diferente, tendo industria pesada/ energia/ base florestal, etc. como
algumas dessas categorias, para melhor representar os projetos que a mirow fez
(busque em mirow-rag se precisar)."

Taxonomia proposta na #194, ancorada no acervo (mirow-rag: ~300 clientes/28
setores — forte em papel e celulose, automotivo, energia, portos/logística) e
no mestre de clientes liberados. 5 cards viram 6; os 19 itens atuais são
cobertos, nenhum some.

O script REESCREVE só o <ul class="onda18-orbe__cards"> das 3 homes — título
da seção, marca e CSS do card (vocabulário navy da onda 18) ficam como estão.

Uso: python tools_onda6/101_setores_recategorizados.py <raiz>
"""
import io
import re
import sys

from _onda7_css import resolve_public, ler, gravar, idioma_da_pagina

MARK = "onda42:setores-recategorizados"

CARDS = {
 "pt": [
  (u"Base Florestal",
   [u"Papel e celulose", u"Madeira e painéis", u"Embalagens",
    u"Química florestal"]),
  (u"Indústria Pesada",
   [u"Automotivo", u"Máquinas e equipamentos", u"Mineração e siderurgia",
    u"Químicos e fertilizantes", u"Infraestrutura e cimento"]),
  (u"Energia",
   [u"Energia elétrica", u"Geração e transmissão", u"Óleo e gás",
    u"Utilidades"]),
  (u"Logística e Portos",
   [u"Portos e terminais", u"Transporte e logística",
    u"Combustíveis e distribuição"]),
  (u"Consumo e Agro",
   [u"Agronegócio", u"Varejo e bens de consumo", u"Saúde", u"Educação"]),
  (u"Serviços e Tecnologia",
   [u"Serviços financeiros e seguros", u"Private equity",
    u"Tecnologia e telecom", u"Esportes, mídia e entretenimento"]),
 ],
 "en": [
  (u"Forest-based Industry",
   [u"Pulp & paper", u"Wood & panels", u"Packaging", u"Forest chemicals"]),
  (u"Heavy Industry",
   [u"Automotive", u"Machinery & equipment", u"Mining & steel",
    u"Chemicals & fertilizers", u"Infrastructure & cement"]),
  (u"Energy",
   [u"Electric power", u"Generation & transmission", u"Oil & gas",
    u"Utilities"]),
  (u"Logistics & Ports",
   [u"Ports & terminals", u"Transportation & logistics",
    u"Fuels & distribution"]),
  (u"Consumer & Agri",
   [u"Agribusiness", u"Retail & consumer goods", u"Healthcare",
    u"Education"]),
  (u"Services & Technology",
   [u"Financial services & insurance", u"Private equity",
    u"Technology & telecom", u"Sports, media & entertainment"]),
 ],
 "de": [
  (u"Forstbasierte Industrie",
   [u"Zellstoff & Papier", u"Holz & Platten", u"Verpackung",
    u"Forstchemie"]),
  (u"Schwerindustrie",
   [u"Automobil", u"Maschinen & Anlagen", u"Bergbau & Stahl",
    u"Chemie & Düngemittel", u"Infrastruktur & Zement"]),
  (u"Energie",
   [u"Elektrizität", u"Erzeugung & Übertragung", u"Öl & Gas",
    u"Versorgung"]),
  (u"Logistik & Häfen",
   [u"Häfen & Terminals", u"Transport & Logistik",
    u"Kraftstoffe & Distribution"]),
  (u"Konsum & Agrar",
   [u"Agrarwirtschaft", u"Einzelhandel & Konsumgüter", u"Gesundheit",
    u"Bildung"]),
  (u"Dienstleistungen & Technologie",
   [u"Finanzdienstleistungen & Versicherungen", u"Private Equity",
    u"Technologie & Telekom", u"Sport, Medien & Unterhaltung"]),
 ],
}

HOMES = ["pt/index.html", "en/index.html", "de/index.html"]


def montar_ul(idioma):
    lis = []
    for nome, itens in CARDS[idioma]:
        sub = "".join(u'<li class="onda18-const__item">%s</li>' % i
                      for i in itens)
        lis.append(u'<li class="onda18-const"><span class="onda18-const__nome">'
                   u'%s</span><ul class="onda18-const__lista">%s</ul></li>'
                   % (nome, sub))
    return (u'<ul class="onda18-orbe__cards"><!-- %s -->%s</ul>'
            % (MARK, "".join(lis)))


def ajustar_grid(pub):
    """5 colunas viram 3 (2 fileiras de 3): com 6 cards, repeat(5,1fr) deixava
    um orfao sozinho na 2a fileira. Editado NO LUGAR no bloco da onda 18
    (regra dos valores gemeos — nao somar bloco de override)."""
    css = "%s/wp-content/uploads/2026/07/onda6/onda6.css" % pub
    h = io.open(css, encoding="utf-8").read()
    antigo = ".onda18-orbe__cards{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;"
    novo = (".onda18-orbe__cards{display:grid;"
            "grid-template-columns:repeat(3,1fr);"
            "/* onda42 (#194): 6 cards em 2 fileiras de 3; era repeat(5) p/ 5 cards */"
            "gap:16px;")
    if antigo in h:
        io.open(css, "w", encoding="utf-8", newline="\n").write(
            h.replace(antigo, novo, 1))
        print("grid dos setores: 5 -> 3 colunas")
    elif novo in h:
        print("ok (grid ja em 3 colunas)")
    else:
        raise SystemExit("nao achei a regra do grid dos setores no onda6.css")


def main(root):
    pub = resolve_public(root)
    ajustar_grid(pub)
    mudadas = 0
    for rel in HOMES:
        p = "%s/%s" % (pub, rel)
        h = ler(p)
        if MARK in h:
            print("ok (ja feito): %s" % rel)
            continue
        idioma = idioma_da_pagina(h)
        i = h.find('<ul class="onda18-orbe__cards">')
        if i < 0:
            raise SystemExit("sem cards de setores em %s" % rel)
        # os cards tem <ul> aninhado — acha o </ul> que fecha o container
        # contando o aninhamento, em vez de confiar no primeiro </ul>.
        prof = 0
        j = i
        for m in re.finditer(r'<ul\b|</ul>', h[i:h.find('</section>', i)]):
            if m.group(0) == '<ul':
                prof += 1
            else:
                prof -= 1
                if prof == 0:
                    j = i + m.end()
                    break
        antigo = h[i:j]
        gravar(p, h.replace(antigo, montar_ul(idioma), 1))
        mudadas += 1
        print("setores recategorizados: %s (%s, 6 cards)" % (rel, idioma))
    print("%d pagina(s) mudada(s)" % mudadas)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
