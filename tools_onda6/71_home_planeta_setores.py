# -*- coding: utf-8 -*-
"""71 — S-70 / issue #128: planeta com os setores em CONSTELACOES, na home.

Uso:
    python tools_onda6/71_home_planeta_setores.py <raiz-que-contem-public>

HISTORICO DO PEDIDO
-------------------
Onda 18: "vamos colocar o planeta com os diversos setores orbitando esse planeta na
pagina inicial junto com 'nossas areas de expertise'. vamos buscar em alglum site
que tenha planeta e temas orbitando esse planeta para tentar imitar."
  -> 1a versao: 3 aneis girando com os 19 setores em chips.

Onda 19 (mesma issue): "tem muito overlap nos projetos que temos. sera que podemos
fazer um search por paginas com constelacoes para agruparmos industrias semelhantes
em grupos de constelacoes."
  -> esta versao. A rotacao era a causa do overlap: 19 rotulos de largura muito
     diferente ("Esportes, midia e entretenimento" tem ~3x a largura de "Saude")
     em 3 raios se cruzam em algum quadro da animacao, sempre.

PESQUISA DE REFERENCIA (o "search" pedido, 03/08/2026)
------------------------------------------------------
Nao existe um caso canonico de consultoria com esse padrao. A referencia mais
solida do padrao em si e o ESA Star Mapper (https://sci.esa.int/star_mapper/,
visualizacao da TULP Interactive sobre dados da missao Hipparcos). O que se
aproveita dele:
  - estrelas pequenas e linhas FINAS ligando as estrelas de um mesmo grupo
  - o nome da CONSTELACAO e a etiqueta permanente; o nome de cada estrela e
    camada secundaria
  - constelacoes ocupam regioes FIXAS do ceu — e isso que resolve o overlap aqui
Tambem olhados, sem agregar: colecao de data-visualization do Awwwards (padrao
"dots + connection lines"), Pega Constellation (design system homonimo, nada a
ver) e material de cluster diagram.

DECISAO DE DESIGN
-----------------
Sai a rotacao. Os 19 setores viram 5 constelacoes em posicoes fixas ao redor do
planeta, cada uma ligada a ele por uma linha tracejada. Overlap deixa de ser
possivel por construcao. O movimento que sobra e uma flutuacao de 6px, com fase
diferente por grupo.

Os 5 grupos (agrupamento por proximidade de cadeia produtiva e de tipo de decisao
de compra — proposta do Claude, vale revisao do Mario):
  1 Energia & Recursos         (5) oleo e gas, energia eletrica, utilidades,
                                   mineracao e siderurgia, quimicos
  2 Industria & Base florestal (5) florestal/papel/celulose, maquinas e
                                   equipamentos, automotivo, infraestrutura e
                                   cimento, transporte e logistica
  3 Consumo & Agro             (4) varejo e bens de consumo, agronegocio, saude,
                                   educacao
  4 Tecnologia & Midia         (3) tecnologia, telecom, esportes/midia/entret.
  5 Capital & Servicos         (2) servicos financeiros, private equity

Nomes dos 19 setores (3 idiomas) e icones sao os mesmos do bloco "Industrias /
Solucoes para diversos setores" que a S-69 tirou da pagina nossos-valores —
nenhum asset novo.

Idempotente: bloco entre marcadores.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (escrever_bloco_css, gravar, idioma_da_pagina, ler,  # noqa: E402
                        resolve_public)

MARK_INI = "<!-- onda18:planeta-setores -->"
MARK_FIM = "<!-- /onda18:planeta-setores -->"
ICON_DIR = "wp-content/uploads/2023/03"

# nome do setor por idioma, na ordem original do bloco de industrias
NOMES = {
    "pt": [u"Automotivo", u"Agronegócio", u"Educação", u"Varejo e bens de consumo",
           u"Energia elétrica", u"Óleo e gás", u"Químicos", u"Utilidades",
           u"Esportes, mídia e entretenimento", u"Florestal, papel e celulose",
           u"Infraestrutura e cimento", u"Máquinas e equipamentos",
           u"Mineração e siderurgia", u"Private Equity", u"Serviços financeiros",
           u"Saúde", u"Tecnologia", u"Telecom", u"Transporte e logística"],
    "en": [u"Automotive", u"Agribusiness", u"Education", u"Retail and Consumer Goods",
           u"Electric Energy", u"Oil and Gas", u"Chemicals", u"Utilities",
           u"Sports, Media and Entertainment", u"Forestry, Pulp and Paper",
           u"Infrastructure and Cement", u"Machinery and Equipment",
           u"Mining and Steel", u"Private Equity", u"Financial Services",
           u"Healthcare", u"Technology", u"Telecom", u"Transportation and logistics"],
    "de": [u"Automobil", u"Landwirtschaft", u"Bildung", u"Einzelhandel und Konsumgüter",
           u"Elektrizität", u"Öl und Gas", u"Chemikalien", u"Utilities",
           u"Sport, Medien und Unterhaltung", u"Forstwirtschaft, Papier und Zellstoff",
           u"Infrastruktur und Zement", u"Maschinen und Ausrüstungen",
           u"Bergbau und Stahlindustrie", u"Private Equity", u"Finanzdienstleistungen",
           u"Gesundheit", u"Technologie", u"Telekommunikation", u"Transport und Logistik"],
}
ICONES = ["icon-segment-auto.svg", "icon-segment-agro.svg", "icon-segment-edu.svg",
          "icon-segment-market.svg", "icon-segment-energy.svg", "icon-segment-oilgas.svg",
          "icon-segment-chemical.svg", "icon-segment-utilities.svg",
          "icon-segment-media.svg", "icon-segment-forestry.svg", "icon-segment-infra.svg",
          "icon-segment-equipaments.svg", "icon-segment-mining.svg",
          "icon-segment-equity.svg", "icon-segment-finance.svg", "icon-segment-health.svg",
          "icon-segment-tech.svg", "icon-segment-telecom.svg", "icon-segment-logistics.svg"]

# nome da constelacao por idioma
GRUPOS = {
    "pt": [u"Energia & Recursos", u"Indústria & Base florestal", u"Consumo & Agro",
           u"Tecnologia & Mídia", u"Capital & Serviços"],
    "en": [u"Energy & Resources", u"Industry & Forest-based", u"Consumer & Agri",
           u"Technology & Media", u"Capital & Services"],
    "de": [u"Energie & Ressourcen", u"Industrie & Forstbasis", u"Konsum & Agrar",
           u"Technologie & Medien", u"Kapital & Dienstleistungen"],
}
# indice (na lista de 19) dos setores de cada constelacao
MEMBROS = [
    [5, 4, 7, 12, 6],      # oleo e gas, energia eletrica, utilidades, mineracao, quimicos
    [9, 11, 0, 10, 18],    # florestal, maquinas, automotivo, infra, transporte
    [3, 1, 15, 2],         # varejo, agro, saude, educacao
    [16, 17, 8],           # tecnologia, telecom, esportes/midia
    [14, 13],              # servicos financeiros, private equity
]

TITULO = {
    "pt": (u"Setores em que atuamos",
           u"19 indústrias em 5 constelações — todas girando em torno do mesmo núcleo"),
    "en": (u"Industries we serve",
           u"19 industries in 5 constellations — all orbiting the same core"),
    "de": (u"Branchen, in denen wir arbeiten",
           u"19 Branchen in 5 Konstellationen — alle um denselben Kern"),
}

CSS = """/* ---- S-70 v2 (#128): 19 setores em 5 CONSTELACOES de posicao fixa --------
   A v1 girava 3 aneis de chips e os rotulos se cruzavam (o mais longo tem ~3x a
   largura do mais curto). Referencia do padrao: ESA Star Mapper (TULP) —
   estrelas pequenas, linha fina ligando o grupo, nome da constelacao como
   etiqueta permanente, regioes fixas do ceu. Sem rotacao = sem colisao. */
.onda18-orbe{position:relative;z-index:6;margin:36px 0 0;padding:0 0 10px}
.onda18-orbe__titulo{color:#020E66;font-size:34px;font-weight:700;margin:0 0 6px;
  text-align:center}
.onda18-orbe__sub{color:#071C25;font-size:17px;margin:0 0 10px;text-align:center;
  opacity:.72}
.onda18-orbe__palco{position:relative;z-index:6;width:980px;height:600px;
  max-width:100%;margin:0 auto}

/* o planeta, no centro */
.onda18-orbe__planeta{position:absolute;left:50%;top:50%;width:200px;height:200px;
  margin:-100px 0 0 -100px;border-radius:50%;
  background:radial-gradient(circle at 32% 28%,#1B4FD8 0%,#0A2596 42%,#020E66 100%);
  box-shadow:0 0 0 1px rgba(0,173,236,.45),0 0 60px 12px rgba(0,173,236,.20);
  overflow:hidden;z-index:3}
.onda18-orbe__planeta::before,.onda18-orbe__planeta::after{content:"";
  position:absolute;left:50%;top:50%;border:1px solid rgba(170,213,232,.28);
  border-radius:50%}
.onda18-orbe__planeta::before{width:200px;height:66px;margin:-33px 0 0 -100px}
.onda18-orbe__planeta::after{width:78px;height:200px;margin:-100px 0 0 -39px}
.onda18-orbe__marca{position:absolute;left:50%;top:50%;
  transform:translate(-50%,-50%);color:#fff;font-size:14px;font-weight:700;
  letter-spacing:.14em;z-index:4;white-space:nowrap}

/* uma constelacao */
.onda18-const{position:absolute;width:268px;
  animation:onda18-flutua 9s ease-in-out infinite}
.onda18-const__nome{display:block;color:#020E66;font-size:15px;font-weight:700;
  letter-spacing:.06em;text-transform:uppercase;margin:0 0 8px;padding:0 0 7px;
  border-bottom:1px solid rgba(0,173,236,.55)}
.onda18-const__lista{list-style:none;margin:0;padding:0;position:relative}
/* a "linha da constelacao", ligando as estrelas do grupo */
.onda18-const__lista::before{content:"";position:absolute;left:3px;top:10px;
  bottom:10px;border-left:1px dashed rgba(2,14,102,.35)}
.onda18-const__item{position:relative;display:flex;align-items:center;gap:8px;
  margin:0 0 7px;padding-left:18px;color:#071C25;font-size:14px;font-weight:600;
  line-height:1.25}
.onda18-const__item:last-child{margin-bottom:0}
/* a estrela */
.onda18-const__item::before{content:"";position:absolute;left:0;top:50%;
  width:7px;height:7px;margin-top:-3px;border-radius:50%;background:#00ADEC;
  box-shadow:0 0 0 3px rgba(0,173,236,.22)}
.onda18-const__item img,.onda18-const__item svg{width:20px !important;
  height:20px !important;flex:none;display:block}
/* a linha que liga a constelacao ao planeta */
.onda18-const::after{content:"";position:absolute;height:0;
  border-top:1px dashed rgba(2,14,102,.28);transform-origin:0 50%;
  pointer-events:none}

/* os 5 slots — regioes fixas, e por isso nao ha como um rotulo cobrir o outro */
.onda18-const--1{left:0;top:0;animation-delay:0s}
.onda18-const--1::after{left:268px;top:80px;width:220px;transform:rotate(38deg)}
.onda18-const--2{right:0;top:0;animation-delay:-1.6s}
.onda18-const--2::after{left:0;top:80px;width:220px;transform:rotate(142deg)}
.onda18-const--3{left:0;top:250px;animation-delay:-3.2s}
.onda18-const--3::after{left:268px;top:56px;width:200px;transform:rotate(-16deg)}
.onda18-const--4{right:0;top:250px;animation-delay:-4.8s}
.onda18-const--4::after{left:0;top:48px;width:200px;transform:rotate(196deg)}
.onda18-const--5{left:50%;margin-left:-134px;bottom:0;animation-delay:-6.4s}
.onda18-const--5::after{left:134px;top:0;width:120px;transform:rotate(-90deg)}

@keyframes onda18-flutua{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}

@media only screen and (max-width: 1200px){
  .onda18-orbe__palco{transform:scale(.8);margin:-60px auto}
}
/* abaixo de 992px o ceu nao cabe: as constelacoes viram colunas empilhadas */
@media only screen and (max-width: 991px){
  .onda18-orbe__titulo{font-size:26px}
  .onda18-orbe__sub{font-size:15px}
  .onda18-orbe__palco{width:auto;height:auto;transform:none;margin:0;
    display:flex;flex-wrap:wrap;gap:26px 30px;justify-content:center;padding:22px 0 0}
  .onda18-orbe__planeta{position:relative;left:auto;top:auto;margin:0 auto;
    width:150px;height:150px;flex:0 0 100%}
  .onda18-orbe__planeta::before{width:150px;height:50px;margin:-25px 0 0 -75px}
  .onda18-orbe__planeta::after{width:58px;height:150px;margin:-75px 0 0 -29px}
  .onda18-orbe__marca{position:absolute}
  .onda18-const{position:static;width:250px;margin:0;animation:none}
  .onda18-const::after{display:none}
}
@media (prefers-reduced-motion: reduce){
  .onda18-const{animation:none}
}"""


def bloco(lang, prefix):
    nomes = NOMES.get(lang, NOMES["pt"])
    grupos = GRUPOS.get(lang, GRUPOS["pt"])
    titulo, sub = TITULO.get(lang, TITULO["pt"])

    consts = []
    for g, membros in enumerate(MEMBROS):
        itens = "".join(
            '<li class="onda18-const__item">'
            '<img src="%s%s/%s?ver=1" alt="" aria-hidden="true" width="20" height="20"'
            '>%s</li>' % (prefix, ICON_DIR, ICONES[i], nomes[i])
            for i in membros)
        consts.append(
            '<div class="onda18-const onda18-const--%d">'
            '<span class="onda18-const__nome">%s</span>'
            '<ul class="onda18-const__lista">%s</ul></div>'
            % (g + 1, grupos[g], itens))

    planeta = ('<div class="onda18-orbe__planeta"></div>'
               '<span class="onda18-orbe__marca">MIROW &amp; CO.</span>')

    return ('%s<section class="onda18-orbe"><div class="container"><div class="row">'
            '<div class="col"><h3 class="onda18-orbe__titulo">%s</h3>'
            '<p class="onda18-orbe__sub">%s</p>'
            '<div class="onda18-orbe__palco">%s%s</div></div></div></div></section>%s'
            % (MARK_INI, titulo, sub, planeta, "".join(consts), MARK_FIM))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    total = sum(len(m) for m in MEMBROS)
    if total != 19:
        raise SystemExit("os 5 grupos somam %d setores, deveriam somar 19" % total)

    mudou = escrever_bloco_css(pub, "planeta-setores", CSS, onda="onda18")
    print("bloco onda18:planeta-setores %s" % ("gravado" if mudou else "ja estava igual"))

    alterados = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if "<!-- /onda6:praticas -->" not in h:
                continue
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            lang = idioma_da_pagina(h)
            prefix = "/mirow-site/" if "/mirow-site/wp-content/" in h else "/"
            novo_bloco = bloco(lang, prefix)

            if MARK_INI in h:
                velho = h[h.index(MARK_INI):h.index(MARK_FIM) + len(MARK_FIM)]
                novo = h.replace(velho, novo_bloco, 1)
            else:
                ini = h.find('<section class="home-experience">')
                if ini < 0:
                    continue
                fim = h.find("</section>", ini)
                if fim < 0:
                    continue
                fim += len("</section>")
                novo = h[:fim] + "\n" + novo_bloco + h[fim:]
            if novo != h:
                gravar(p, novo)
                alterados += 1
                print("  %s (%s, 5 constelacoes, 19 setores)" % (rel, lang))
    print("resumo: %d home(s) com as constelacoes" % alterados)


if __name__ == "__main__":
    main()
