# -*- coding: utf-8 -*-
"""71 — onda 18, S-70 (issue #128): planeta com os setores orbitando, na home.

Uso:
    python tools_onda6/71_home_planeta_setores.py <raiz-que-contem-public>

Pedido do Mario: "vamos colocar o planeta com os diversos setores orbitando esse
planeta na pagina inicial junto com 'nossas areas de expertise'."

Onde entra: dentro da <section class="home-experience"> da home (a que tem o
titulo "Praticas" e o subtitulo "Nossas areas de expertise"), logo DEPOIS dos 3
cards de pratica — a secao passa a ler: Praticas > Nossas areas de expertise >
3 cards > planeta com os 19 setores orbitando.

Os 19 setores (nome + icone) vem do bloco "Industrias / Solucoes para diversos
setores" que a S-69 tirou da pagina nossos-valores; os SVGs sao os mesmos arquivos
do tema (wp-content/uploads/2023/03/icon-segment-*.svg), nao ha asset novo. Os
nomes por idioma foram lidos das 3 versoes daquela pagina antes da remocao
(commit anterior a esta onda).

Tecnica (sem lib, sem video — a onda 17 acabou de tirar 22,8 MB da home):
  - 3 aneis concentricos; cada anel e um wrapper que gira com @keyframes
  - cada chip e posicionado por rotate(var(--a)) translate(var(--r))
  - o texto do chip tem a animacao INVERSA, de mesma duracao, para nao girar de
    cabeca para baixo
  - hover no bloco pausa tudo (animation-play-state:paused)
  - prefers-reduced-motion: sem rotacao (chips param onde estao)
  - abaixo de 992px o formato de orbita nao cabe: vira nuvem de chips estatica

REFERENCIA VISUAL: o Mario pediu "buscar em algum site que tenha planeta e temas
orbitando esse planeta para tentar imitar". Esta versao e uma primeira proposta
feita com a paleta Mirow (navy + ciano), SEM referencia externa capturada ainda —
esta anotado como pendencia na issue #128 para ele dizer se o formato serve ou se
quer que a gente busque e imite um site especifico.

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

SETORES = {
    "pt": [
        (u"Automotivo", "icon-segment-auto.svg"),
        (u"Agronegócio", "icon-segment-agro.svg"),
        (u"Educação", "icon-segment-edu.svg"),
        (u"Varejo e bens de consumo", "icon-segment-market.svg"),
        (u"Energia elétrica", "icon-segment-energy.svg"),
        (u"Óleo e gás", "icon-segment-oilgas.svg"),
        (u"Químicos", "icon-segment-chemical.svg"),
        (u"Utilidades", "icon-segment-utilities.svg"),
        (u"Esportes, mídia e entretenimento", "icon-segment-media.svg"),
        (u"Florestal, papel e celulose", "icon-segment-forestry.svg"),
        (u"Infraestrutura e cimento", "icon-segment-infra.svg"),
        (u"Máquinas e equipamentos", "icon-segment-equipaments.svg"),
        (u"Mineração e siderurgia", "icon-segment-mining.svg"),
        (u"Private Equity", "icon-segment-equity.svg"),
        (u"Serviços financeiros", "icon-segment-finance.svg"),
        (u"Saúde", "icon-segment-health.svg"),
        (u"Tecnologia", "icon-segment-tech.svg"),
        (u"Telecom", "icon-segment-telecom.svg"),
        (u"Transporte e logística", "icon-segment-logistics.svg"),
    ],
    "en": [
        (u"Automotive", "icon-segment-auto.svg"),
        (u"Agribusiness", "icon-segment-agro.svg"),
        (u"Education", "icon-segment-edu.svg"),
        (u"Retail and Consumer Goods", "icon-segment-market.svg"),
        (u"Electric Energy", "icon-segment-energy.svg"),
        (u"Oil and Gas", "icon-segment-oilgas.svg"),
        (u"Chemicals", "icon-segment-chemical.svg"),
        (u"Utilities", "icon-segment-utilities.svg"),
        (u"Sports, Media and Entertainment", "icon-segment-media.svg"),
        (u"Forestry, Pulp and Paper", "icon-segment-forestry.svg"),
        (u"Infrastructure and Cement", "icon-segment-infra.svg"),
        (u"Machinery and Equipment", "icon-segment-equipaments.svg"),
        (u"Mining and Steel", "icon-segment-mining.svg"),
        (u"Private Equity", "icon-segment-equity.svg"),
        (u"Financial Services", "icon-segment-finance.svg"),
        (u"Healthcare", "icon-segment-health.svg"),
        (u"Technology", "icon-segment-tech.svg"),
        (u"Telecom", "icon-segment-telecom.svg"),
        (u"Transportation and logistics", "icon-segment-logistics.svg"),
    ],
    "de": [
        (u"Automobil", "icon-segment-auto.svg"),
        (u"Landwirtschaft", "icon-segment-agro.svg"),
        (u"Bildung", "icon-segment-edu.svg"),
        (u"Einzelhandel und Konsumgüter", "icon-segment-market.svg"),
        (u"Elektrizität", "icon-segment-energy.svg"),
        (u"Öl und Gas", "icon-segment-oilgas.svg"),
        (u"Chemikalien", "icon-segment-chemical.svg"),
        (u"Utilities", "icon-segment-utilities.svg"),
        (u"Sport, Medien und Unterhaltung", "icon-segment-media.svg"),
        (u"Forstwirtschaft, Papier und Zellstoff", "icon-segment-forestry.svg"),
        (u"Infrastruktur und Zement", "icon-segment-infra.svg"),
        (u"Maschinen und Ausrüstungen", "icon-segment-equipaments.svg"),
        (u"Bergbau und Stahlindustrie", "icon-segment-mining.svg"),
        (u"Private Equity", "icon-segment-equity.svg"),
        (u"Finanzdienstleistungen", "icon-segment-finance.svg"),
        (u"Gesundheit", "icon-segment-health.svg"),
        (u"Technologie", "icon-segment-tech.svg"),
        (u"Telekommunikation", "icon-segment-telecom.svg"),
        (u"Transport und Logistik", "icon-segment-logistics.svg"),
    ],
}

TITULO = {
    "pt": (u"Setores em que atuamos", u"19 indústrias — os projetos giram em torno do mesmo núcleo"),
    "en": (u"Industries we serve", u"19 industries — every project orbits the same core"),
    "de": (u"Branchen, in denen wir arbeiten", u"19 Branchen — alle Projekte kreisen um denselben Kern"),
}

# (quantidade de chips, raio em px, duracao da volta, sentido)
ANEIS = [(3, 175, "58s", ""), (6, 305, "76s", " reverse"), (10, 420, "96s", "")]

CSS = """/* ---- S-70: planeta com os setores orbitando (home) ---------------------
   Sem lib e sem video: 3 aneis girando por @keyframes, chips posicionados por
   rotate+translate e texto com a animacao inversa para ficar sempre de pe. */
.onda18-orbe{position:relative;z-index:6;margin:36px 0 0;padding:0 0 10px}
.onda18-orbe__titulo{color:#020E66;font-size:34px;font-weight:700;margin:0 0 6px;
  text-align:center}
.onda18-orbe__sub{color:#071C25;font-size:17px;margin:0 0 10px;text-align:center;
  opacity:.72}
/* z-index: a secao do tema desenha gradientes decorativos por cima — sem isto os
   chips da metade de cima saem lavados */
.onda18-orbe__palco{position:relative;z-index:6;width:900px;height:900px;
  max-width:100%;margin:0 auto}
/* o planeta */
.onda18-orbe__planeta{position:absolute;left:50%;top:50%;width:210px;height:210px;
  margin:-105px 0 0 -105px;border-radius:50%;
  background:radial-gradient(circle at 32% 28%,#1B4FD8 0%,#0A2596 42%,#020E66 100%);
  box-shadow:0 0 0 1px rgba(0,173,236,.45),0 0 60px 10px rgba(0,173,236,.18);
  overflow:hidden;z-index:2}
/* meridianos e paralelos, so com bordas */
.onda18-orbe__planeta::before,.onda18-orbe__planeta::after{content:"";
  position:absolute;left:50%;top:50%;border:1px solid rgba(170,213,232,.28);
  border-radius:50%}
.onda18-orbe__planeta::before{width:210px;height:70px;margin:-35px 0 0 -105px}
.onda18-orbe__planeta::after{width:82px;height:210px;margin:-105px 0 0 -41px}
.onda18-orbe__marca{position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);
  text-align:center;color:#fff;font-size:15px;font-weight:700;letter-spacing:.14em;
  z-index:3}
/* as orbitas */
.onda18-orbe__anel{position:absolute;left:50%;top:50%;border-radius:50%;
  border:1px dashed rgba(170,213,232,.22);pointer-events:none}
.onda18-orbe__gira{position:absolute;left:0;top:0;right:0;bottom:0;
  animation:onda18-orbita var(--dur) linear infinite}
.onda18-orbe__chip{position:absolute;left:50%;top:50%;
  transform:rotate(var(--a)) translate(var(--r)) rotate(calc(-1 * var(--a)))}
.onda18-orbe__contra{display:block;
  animation:onda18-orbita var(--dur) linear infinite reverse}
.onda18-orbe__pill{display:inline-flex;align-items:center;gap:8px;
  transform:translate(-50%,-50%);
  background:#020E66;border:1px solid rgba(0,173,236,.55);
  padding:7px 13px;border-radius:18px;
  white-space:normal;max-width:168px;line-height:1.2;text-align:left;
  color:#fff;font-size:13px;font-weight:600;
  box-shadow:0 2px 10px rgba(2,14,102,.18);
  transition:border-color 200ms ease,background 200ms ease}
.onda18-orbe__pill img{width:19px;height:19px;display:block;flex:none;
  filter:brightness(0) invert(1)}
.onda18-orbe__gira--rev .onda18-orbe__contra{animation-direction:normal}
.onda18-orbe__gira--rev{animation-direction:reverse}
/* parar ao passar o mouse: o executivo consegue ler o setor */
.onda18-orbe__palco:hover .onda18-orbe__gira,
.onda18-orbe__palco:hover .onda18-orbe__contra{animation-play-state:paused}
.onda18-orbe__pill:hover{background:#00ADEC;border-color:#00ADEC;color:#020E66}
.onda18-orbe__pill:hover img{filter:none}
@keyframes onda18-orbita{from{transform:rotate(0)}to{transform:rotate(360deg)}}

/* telas menores: o palco encolhe por escala (mantem as proporcoes da orbita) */
@media only screen and (max-width: 1440px){
  .onda18-orbe__palco{transform:scale(.86);margin:-63px auto}
}
@media only screen and (max-width: 1200px){
  .onda18-orbe__palco{transform:scale(.72);margin:-126px auto}
}
/* abaixo de 992px orbita nao cabe: nuvem de chips, sem rotacao */
@media only screen and (max-width: 991px){
  .onda18-orbe__titulo{font-size:26px}
  .onda18-orbe__sub{font-size:15px}
  .onda18-orbe__palco{width:auto;height:auto;transform:none;margin:0;
    display:flex;flex-wrap:wrap;justify-content:center;gap:10px;padding:24px 0 0}
  .onda18-orbe__anel{display:none}
  .onda18-orbe__planeta{position:relative;left:auto;top:auto;margin:0 auto 18px;
    width:150px;height:150px;flex:0 0 100%}
  .onda18-orbe__planeta::before{width:150px;height:50px;margin:-25px 0 0 -75px}
  .onda18-orbe__planeta::after{width:58px;height:150px;margin:-75px 0 0 -29px}
  .onda18-orbe__gira{position:static;animation:none;display:flex;flex-wrap:wrap;
    justify-content:center;gap:10px}
  .onda18-orbe__chip{position:static;transform:none}
  .onda18-orbe__contra{animation:none}
  .onda18-orbe__pill{transform:none;font-size:13px;padding:7px 12px}
}
@media (prefers-reduced-motion: reduce){
  .onda18-orbe__gira,.onda18-orbe__contra{animation:none !important}
}"""


def bloco(lang, prefix):
    setores = SETORES.get(lang, SETORES["pt"])
    titulo, sub = TITULO.get(lang, TITULO["pt"])

    partes = []
    i = 0
    for idx, (qtd, raio, dur, sentido) in enumerate(ANEIS):
        # o anel tracejado (decorativo) e o wrapper que gira
        partes.append('<div class="onda18-orbe__anel" style="width:%dpx;height:%dpx;'
                      'margin:-%dpx 0 0 -%dpx"></div>' % (raio * 2, raio * 2, raio, raio))
        chips = []
        for k in range(qtd):
            if i >= len(setores):
                break
            nome, icone = setores[i]
            i += 1
            ang = 360.0 * k / qtd + (180.0 / qtd) * idx
            chips.append(
                '<span class="onda18-orbe__chip" style="--a:%.1fdeg;--r:%dpx">'
                '<span class="onda18-orbe__contra" style="--dur:%s">'
                '<span class="onda18-orbe__pill">'
                '<img src="%s%s/%s" alt="" aria-hidden="true" width="19" height="19" '
                'loading="lazy">%s</span></span></span>'
                % (ang, raio, dur, prefix, ICON_DIR, icone, nome))
        classe = "onda18-orbe__gira"
        if sentido:
            classe += " onda18-orbe__gira--rev"
        partes.append('<div class="%s" style="--dur:%s">%s</div>'
                      % (classe, dur, "".join(chips)))

    planeta = ('<div class="onda18-orbe__planeta"></div>'
               '<span class="onda18-orbe__marca">MIROW &amp; CO.</span>')

    return ('%s<section class="onda18-orbe"><div class="container"><div class="row">'
            '<div class="col"><h3 class="onda18-orbe__titulo">%s</h3>'
            '<p class="onda18-orbe__sub">%s</p>'
            '<div class="onda18-orbe__palco">%s%s</div></div></div></div></section>%s'
            % (MARK_INI, titulo, sub, planeta, "".join(partes), MARK_FIM))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

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
                novo = h.replace("<!-- /onda6:praticas -->",
                                 "<!-- /onda6:praticas -->\n" + novo_bloco, 1)
            if novo != h:
                gravar(p, novo)
                alterados += 1
                print("  %s (%s, 19 setores)" % (rel, lang))
    print("resumo: %d home(s) com o planeta e os setores orbitando" % alterados)


if __name__ == "__main__":
    main()
