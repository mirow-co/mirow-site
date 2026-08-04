# -*- coding: utf-8 -*-
"""71 — S-70 / issue #128: as 5 CONSTELACOES de setores ao redor da Mirow, na home.

Uso:
    python tools_onda6/71_home_planeta_setores.py <raiz-que-contem-public>

HISTORICO DO PEDIDO (3 versoes, mesma issue)
--------------------------------------------
v1 (onda 18) "planeta com os diversos setores orbitando esse planeta ... junto com
   'nossas areas de expertise'" -> 3 aneis girando com 19 chips.
v2 (onda 19) "tem muito overlap ... podemos fazer um search por paginas com
   constelacoes para agruparmos industrias semelhantes em grupos de constelacoes"
   -> 5 grupos em slots fixos, em lista. Matou o overlap, mas ficou uma lista.
v3 (esta)    "quero que sejam constelacoes ultramodernas mesmo, com cada grupo
   sendo uma esfera central enquanto os outros temas se conectam a ela. elas devem
   circundar mirow & co. a letra precisa ser mais facilmente legivel contra o
   background. texto preto sobre esse azul e dificil de ler. texto azul sobre azul
   dificil tambem."

PESQUISA DE REFERENCIA (03/08/2026)
-----------------------------------
Padrao pedido = hub-and-spoke / node-link graph, o visual de "rede de nos
brilhantes". O que as fontes convergem:
  - fundo ESCURO com esferas translucidas e linhas finas luminosas; um hub central
    mais brilhante que os outros (efeito starburst) — colecoes de referencia de
    "glowing network of interconnected nodes" e material de topologia no Dribbble
  - COR distingue cluster, TAMANHO distingue importancia/centralidade, e animacao
    serve para sugerir fluxo (guias de knowledge-graph visualization: yFiles,
    Tom Sawyer, Datavid)
  - layouts force-directed existem justamente para evitar sobreposicao de no; aqui
    a geometria e calculada a mao em Python, o que da o mesmo efeito de forma
    deterministica (e reproduzivel entre builds)
  - ESA Star Mapper (TULP), levantado na v2, segue valendo para a parte de
    "constelacao": estrela pequena, linha fina, nome do grupo como etiqueta fixa.

DECISOES DESTA VERSAO
---------------------
1. LEGIBILIDADE (o pedido explicito): a secao passa a ter seu proprio CEU ESCURO
   (painel navy #020E66 -> #071C25 com estrelas fracas). Todo texto vira branco ou
   azul-claro #AAD5E8. Nao ha mais texto preto nem navy sobre o azul medio do
   gradiente do tema — era isso que estava ilegivel.
2. Cada grupo e uma ESFERA (hub) com brilho proprio; os setores do grupo sao nos
   menores ligados a ela por linha fina. As 5 esferas circundam a esfera central
   MIROW & CO., ligadas a ela por linha tracejada.
3. Tudo em SVG unico com viewBox — escala sem quebrar, sem lib, sem imagem.
   Geometria calculada aqui, com os rotulos empilhados por hub: overlap continua
   impossivel por construcao.
4. Os icones dos setores SAIRAM. Num grafo de nos o "no" e a estrela; e o icone
   SVG do tema ja tinha custado a armadilha do plugin svgs-inline (precisa de
   ?ver=1, ver assercao H09). Menos peca, menos modo de falha.
5. O pulso das esferas respeita prefers-reduced-motion. Abaixo de 992px o SVG sai
   e entra a lista empilhada (mesmo conteudo, texto branco no mesmo ceu).

Idempotente: bloco entre marcadores.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (escrever_bloco_css, gravar, idioma_da_pagina, ler,  # noqa: E402
                        resolve_public)

MARK_INI = "<!-- onda18:planeta-setores -->"
MARK_FIM = "<!-- /onda18:planeta-setores -->"

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
           u"19 indústrias em 5 constelações — todas conectadas ao mesmo núcleo"),
    "en": (u"Industries we serve",
           u"19 industries in 5 constellations — all connected to the same core"),
    "de": (u"Branchen, in denen wir arbeiten",
           u"19 Branchen in 5 Konstellationen — alle mit demselben Kern verbunden"),
}

# --- geometria do ceu ------------------------------------------------------
# A largura do viewBox e a posicao dos hubs sao dimensionadas pelo ROTULO MAIS
# LONGO dos 3 idiomas (o aleao "Forstwirtschaft, Papier und Zellstoff" com 37
# caracteres e o pior caso). Antes o viewBox era 1200 e "INDUSTRIA & BASE
# FLORESTAL" saia cortado na borda direita.
VB_W, VB_H = 1300, 980
CX, CY, CR = 620, 470, 92          # esfera central
HUB_R = 46                          # esfera de cada grupo
# (hx, hy, lado) — lado 'e' = rotulos crescem para a esquerda, 'd' para a direita
HUBS = [
    (380, 232, "e"),   # 1 Energia & Recursos (5)
    (860, 232, "d"),   # 2 Industria & Base florestal (5)
    (380, 700, "e"),   # 3 Consumo & Agro (4)
    (860, 700, "d"),   # 4 Tecnologia & Midia (3)
    (620, 892, "d"),   # 5 Capital & Servicos (2)
]
PASSO = 34          # espacamento vertical entre setores do mesmo grupo
DIST_NO = 72        # distancia do no ao centro da esfera do grupo
DIST_TXT = 88       # distancia do rotulo ao centro da esfera do grupo
MARGEM = 20         # respiro minimo entre qualquer texto e a borda do ceu

CSS = """/* ---- S-70 v3 (#128): 5 constelacoes de esferas ao redor da Mirow --------
   Pedido do Mario: cada grupo e uma esfera com os temas conectados a ela, as
   esferas circundando a Mirow, e TEXTO LEGIVEL — preto sobre o azul do tema e
   navy sobre azul estavam ilegiveis. Por isso a secao ganha o proprio ceu
   escuro e todo texto e branco/azul-claro. Referencia do padrao: hub-and-spoke
   glowing network (ver cabecalho do script 71). */
.onda18-orbe{position:relative;z-index:6;margin:44px 0 0;padding:0}
.onda18-orbe__ceu{position:relative;border-radius:18px;overflow:hidden;
  background:radial-gradient(120% 90% at 50% 42%,#0A2596 0%,#020E66 46%,#071C25 100%);
  padding:34px 24px 26px;
  box-shadow:0 18px 50px rgba(2,14,102,.30)}
/* estrelas fracas do fundo */
.onda18-orbe__ceu::before{content:"";position:absolute;inset:0;pointer-events:none;
  background-image:radial-gradient(1.5px 1.5px at 12% 18%,rgba(255,255,255,.55),transparent),
    radial-gradient(1.5px 1.5px at 78% 12%,rgba(255,255,255,.40),transparent),
    radial-gradient(1.5px 1.5px at 32% 78%,rgba(255,255,255,.45),transparent),
    radial-gradient(1.5px 1.5px at 88% 66%,rgba(255,255,255,.35),transparent),
    radial-gradient(1.5px 1.5px at 56% 30%,rgba(255,255,255,.30),transparent),
    radial-gradient(1.5px 1.5px at 22% 52%,rgba(255,255,255,.28),transparent),
    radial-gradient(1.5px 1.5px at 68% 88%,rgba(255,255,255,.32),transparent)}
.onda18-orbe__titulo{position:relative;color:#fff;font-size:34px;font-weight:700;
  margin:0 0 6px;text-align:center}
.onda18-orbe__sub{position:relative;color:#AAD5E8;font-size:17px;margin:0 0 4px;
  text-align:center}
.onda18-orbe__mapa{position:relative;display:block;width:100%;height:auto}

/* pulso suave das esferas — sugere que a rede esta viva, sem girar nada */
.onda18-orbe__hub-brilho{animation:onda18-pulso 6s ease-in-out infinite}
.onda18-orbe__hub-brilho--2{animation-delay:-1.2s}
.onda18-orbe__hub-brilho--3{animation-delay:-2.4s}
.onda18-orbe__hub-brilho--4{animation-delay:-3.6s}
.onda18-orbe__hub-brilho--5{animation-delay:-4.8s}
@keyframes onda18-pulso{0%,100%{opacity:.30}50%{opacity:.62}}

/* a lista empilhada, para mobile (o mesmo conteudo, no mesmo ceu) */
.onda18-orbe__lista{display:none;margin:0;padding:0;list-style:none;position:relative}
.onda18-const{margin:0 0 22px}
.onda18-const:last-child{margin-bottom:0}
.onda18-const__nome{display:block;color:#00ADEC;font-size:14px;font-weight:700;
  letter-spacing:.08em;text-transform:uppercase;margin:0 0 8px;padding:0 0 6px;
  border-bottom:1px solid rgba(0,173,236,.45)}
.onda18-const__lista{list-style:none;margin:0;padding:0}
.onda18-const__item{position:relative;padding-left:18px;margin:0 0 6px;
  color:#fff;font-size:15px;font-weight:600;line-height:1.3}
.onda18-const__item::before{content:"";position:absolute;left:0;top:50%;
  width:7px;height:7px;margin-top:-3px;border-radius:50%;background:#00ADEC;
  box-shadow:0 0 0 3px rgba(0,173,236,.25)}

@media only screen and (max-width: 991px){
  .onda18-orbe__titulo{font-size:26px}
  .onda18-orbe__sub{font-size:15px}
  .onda18-orbe__ceu{padding:26px 20px 22px;border-radius:14px}
  .onda18-orbe__mapa{display:none}
  .onda18-orbe__lista{display:block;margin-top:20px}
}
@media (prefers-reduced-motion: reduce){
  .onda18-orbe__hub-brilho{animation:none;opacity:.45}
}"""


def defs():
    """Gradientes das esferas — a central mais clara que as dos grupos."""
    return (
        '<defs>'
        '<radialGradient id="o18nucleo" cx="34%" cy="28%" r="78%">'
        '<stop offset="0%" stop-color="#5B8CFF"/><stop offset="45%" stop-color="#1B4FD8"/>'
        '<stop offset="100%" stop-color="#020E66"/></radialGradient>'
        '<radialGradient id="o18hub" cx="34%" cy="28%" r="80%">'
        '<stop offset="0%" stop-color="#37C6F5"/><stop offset="52%" stop-color="#0A79B8"/>'
        '<stop offset="100%" stop-color="#04225E"/></radialGradient>'
        '<radialGradient id="o18halo" cx="50%" cy="50%" r="50%">'
        '<stop offset="55%" stop-color="#00ADEC" stop-opacity=".38"/>'
        '<stop offset="100%" stop-color="#00ADEC" stop-opacity="0"/></radialGradient>'
        '</defs>')


def largura(texto, fs, ls=0.0):
    """Largura aproximada de um texto em SVG (Archivo/Libre Franklin, ~0.56em)."""
    return len(texto) * fs * 0.56 + len(texto) * ls


def cabe(texto, x, lado, fs, ls=0.0):
    w = largura(texto, fs, ls)
    return (x - w) >= MARGEM if lado == "e" else (x + w) <= (VB_W - MARGEM)


def fonte_que_cabe(texto, x, lado, fs_max, fs_min, ls=0.0, onde=""):
    """Maior fonte (inteira) em que o texto cabe no ceu. Avisa se nem a minima cabe."""
    fs = fs_max
    while fs > fs_min and not cabe(texto, x, lado, fs, ls):
        fs -= 1
    if not cabe(texto, x, lado, fs, ls):
        print("  AVISO: %r estoura o ceu mesmo em %dpx (%s) — reveja a geometria"
              % (texto, fs, onde))
    return fs


def borda_esfera(x0, y0, x1, y1, r):
    """Ponto na borda de uma esfera (x0,y0,r) na direcao de (x1,y1)."""
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy) or 1.0
    return x0 + dx / d * r, y0 + dy / d * r


def mapa(lang):
    """O SVG inteiro do ceu, com geometria calculada."""
    nomes = NOMES.get(lang, NOMES["pt"])
    grupos = GRUPOS.get(lang, GRUPOS["pt"])
    p = []

    p.append('<svg class="onda18-orbe__mapa" viewBox="0 0 %d %d" role="img" '
             'aria-label="%s">' % (VB_W, VB_H, grupos and u"Setores da Mirow & Co."))
    p.append(defs())

    # (1) linhas hub -> nucleo (tracejadas, atras de tudo)
    for hx, hy, _lado in HUBS:
        ax, ay = borda_esfera(hx, hy, CX, CY, HUB_R)
        bx, by = borda_esfera(CX, CY, hx, hy, CR)
        p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#AAD5E8" '
                 'stroke-opacity=".38" stroke-width="1" stroke-dasharray="5 6"/>'
                 % (ax, ay, bx, by))

    # (2) cada constelacao: linhas hub -> no, nos e rotulos
    for g, (hx, hy, lado) in enumerate(HUBS):
        membros = MEMBROS[g]
        n = len(membros)
        sinal = -1 if lado == "e" else 1
        y0 = hy - (n - 1) * PASSO / 2.0
        for k, idx in enumerate(membros):
            ny = y0 + k * PASSO
            nx = hx + sinal * DIST_NO
            ax, ay = borda_esfera(hx, hy, nx, ny, HUB_R)
            p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#00ADEC" '
                     'stroke-opacity=".55" stroke-width="1"/>' % (ax, ay, nx, ny))
            p.append('<circle cx="%.1f" cy="%.1f" r="9" fill="#00ADEC" fill-opacity=".18"/>'
                     % (nx, ny))
            p.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#7FE3FF"/>' % (nx, ny))
            tx = hx + sinal * DIST_TXT
            fs = fonte_que_cabe(nomes[idx], tx, lado, 16, 13,
                                onde="setor do grupo %d" % (g + 1))
            p.append('<text x="%.1f" y="%.1f" fill="#FFFFFF" font-size="%d" '
                     'font-weight="600" text-anchor="%s" dominant-baseline="middle">%s</text>'
                     % (tx, ny, fs, "end" if lado == "e" else "start", nomes[idx]))

        # a esfera do grupo: halo pulsante + corpo + aro
        p.append('<circle class="onda18-orbe__hub-brilho onda18-orbe__hub-brilho--%d" '
                 'cx="%d" cy="%d" r="%d" fill="url(#o18halo)"/>'
                 % (g + 1, hx, hy, HUB_R + 26))
        p.append('<circle cx="%d" cy="%d" r="%d" fill="url(#o18hub)"/>' % (hx, hy, HUB_R))
        p.append('<circle cx="%d" cy="%d" r="%d" fill="none" stroke="#7FE3FF" '
                 'stroke-opacity=".55" stroke-width="1"/>' % (hx, hy, HUB_R))
        # nome do grupo: ACIMA da coluna de rotulos e alinhado com ela — centrado
        # na esfera ele caia na mesma altura do 1o setor e os dois se sobrepunham
        gx = hx + sinal * DIST_TXT
        gnome = grupos[g].upper()
        gfs = fonte_que_cabe(gnome, gx, lado, 18, 13, ls=1.4,
                             onde="nome do grupo %d" % (g + 1))
        p.append('<text x="%.1f" y="%.1f" fill="#7FE3FF" font-size="%d" '
                 'font-weight="700" letter-spacing="1.4" text-anchor="%s">%s</text>'
                 % (gx, y0 - 38, gfs, "end" if lado == "e" else "start", gnome))
        # quantos setores, dentro da esfera
        p.append('<text x="%d" y="%d" fill="#FFFFFF" font-size="26" font-weight="700" '
                 'text-anchor="middle" dominant-baseline="middle">%d</text>'
                 % (hx, hy, n))

    # (3) o nucleo
    p.append('<circle cx="%d" cy="%d" r="%d" fill="url(#o18halo)"/>' % (CX, CY, CR + 40))
    p.append('<circle cx="%d" cy="%d" r="%d" fill="url(#o18nucleo)"/>' % (CX, CY, CR))
    p.append('<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="#AAD5E8" '
             'stroke-opacity=".30" stroke-width="1"/>' % (CX, CY, CR, CR * 0.33))
    p.append('<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="#AAD5E8" '
             'stroke-opacity=".30" stroke-width="1"/>' % (CX, CY, int(CR * 0.38), CR))
    p.append('<circle cx="%d" cy="%d" r="%d" fill="none" stroke="#7FE3FF" '
             'stroke-opacity=".65" stroke-width="1.5"/>' % (CX, CY, CR))
    p.append('<text x="%d" y="%d" fill="#FFFFFF" font-size="19" font-weight="700" '
             'letter-spacing="2.4" text-anchor="middle" dominant-baseline="middle">'
             'MIROW &amp; CO.</text>' % (CX, CY))
    p.append('</svg>')
    return "".join(p)


def lista(lang):
    """Fallback empilhado (mobile) — mesmo conteudo, texto branco no mesmo ceu."""
    nomes = NOMES.get(lang, NOMES["pt"])
    grupos = GRUPOS.get(lang, GRUPOS["pt"])
    out = ['<ul class="onda18-orbe__lista">']
    for g, membros in enumerate(MEMBROS):
        itens = "".join('<li class="onda18-const__item">%s</li>' % nomes[i] for i in membros)
        out.append('<li class="onda18-const"><span class="onda18-const__nome">%s</span>'
                   '<ul class="onda18-const__lista">%s</ul></li>' % (grupos[g], itens))
    out.append('</ul>')
    return "".join(out)


def bloco(lang):
    titulo, sub = TITULO.get(lang, TITULO["pt"])
    return ('%s<section class="onda18-orbe"><div class="container"><div class="row">'
            '<div class="col"><div class="onda18-orbe__ceu">'
            '<h3 class="onda18-orbe__titulo">%s</h3>'
            '<p class="onda18-orbe__sub">%s</p>%s%s'
            '</div></div></div></div></section>%s'
            % (MARK_INI, titulo, sub, mapa(lang), lista(lang), MARK_FIM))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    total = sum(len(m) for m in MEMBROS)
    if total != 19:
        raise SystemExit("os 5 grupos somam %d setores, deveriam somar 19" % total)
    if len(HUBS) != len(MEMBROS):
        raise SystemExit("HUBS e MEMBROS tem tamanhos diferentes")

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
            novo_bloco = bloco(lang)

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
                print("  %s (%s, 5 esferas, 19 setores)" % (rel, lang))
    print("resumo: %d home(s) com as constelacoes" % alterados)


if __name__ == "__main__":
    main()
