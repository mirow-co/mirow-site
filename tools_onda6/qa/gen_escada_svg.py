# -*- coding: utf-8 -*-
r"""Gera as variantes de SVG animado da escada para o heroi de CARREIRAS (onda 63).

    python tools_onda6/qa/gen_escada_svg.py [pasta-de-saida]

Escreve onda63-escada-A.svg, -B.svg e -C.svg.

PEDIDO (Mario, 18/08/2026): trocar o MP4 de 39,7 MB do heroi de carreiras por
"um consultor e uma consultora subindo uma escada juntos", podendo ser desenho
corporativo. Alvo: dezenas de KB, nao dezenas de MB.

AS TRES DIRECOES (deliberadamente de familias diferentes, nao primas):
  A - MASSA SOLIDA  escada preenchida + silhuetas cheias; luz ciano sobe degrau
                    a degrau. Peso, construcao.
  B - BLUEPRINT     so traco: escada e figuras em linha fina, guia tracejada
                    subindo. Projeto, prancheta, consultoria.
  C - BARRAS        os degraus sao colunas de grafico ascendente e o par sobe por
                    cima. Amarra na "escada de crescimento" do vocabulario de slide.

DECISOES QUE VALEM PARA AS TRES
-------------------------------
* **O loop fecha pela ESCADA, nao pelas figuras.** As figuras ficam paradas na
  tela e o cenario anda exatamente UM periodo por ciclo. Como todo degrau e igual,
  o instante do retorno e invisivel: da subida infinita. Animar a figura subindo
  exigiria teletransporta-la de volta a cada volta -- o corte visivel da animacao ruim.
* **Composicao pensada para o texto.** O titulo do heroi fica a ESQUERDA, entao a
  arte se concentra a partir de ~55% da largura. `preserveAspectRatio="xMaxYMax
  slice"` mantem as figuras visiveis quando a caixa e estreita (mobile), cortando
  pela esquerda -- que e justamente a parte vazia.
* **Animacao 100% CSS declarativa.** SVG referenciado por `background-image`/`<img>`
  roda em "secure animated mode": keyframes e SMIL rodam, script nao. Por isso nao
  ha um `<script>` aqui. Verificado no mockup, nao presumido.
* **Paleta R4 apenas.** navy #020E66, ciano #00ADEC, azul-claro #AAD5E8, escuro
  #071C25. Nada fora dela.
* **prefers-reduced-motion** congela tudo.
"""
import io
import os
import sys

W, H = 1440, 620
PASSO_W, PASSO_H = 170, 66
N = 14
BASE_X, BASE_Y = -420, 760
FIG_X = 980
T = 2.8                                  # segundos por degrau

NAVY, CIANO, CLARO, ESCURO = "#020E66", "#00ADEC", "#AAD5E8", "#071C25"


# ---------------------------------------------------------------- figuras
def piso_em(x):
    """Altura do piso do degrau que esta sob `x`. As figuras PISAM nele.

    Erro que isto conserta: a figura e desenhada de y=-104 (cabeca) a y=0 (pes),
    entao um `translate(x, 0)` a joga inteira para FORA do viewBox, acima do topo.
    Os pes tem de ir na altura do degrau, nao no zero."""
    i = int((x - BASE_X) // PASSO_W)
    return BASE_Y - i * PASSO_H


def figura(dx, dy, escala, cor, cabelo, atraso, modo):
    """Pessoa estilizada de perfil, em passada. modo: 'cheio' | 'traco'."""
    cabeca = '<circle cx="0" cy="-104" r="13"/>'
    if cabelo == "preso":
        cabeca += '<circle cx="-12" cy="-100" r="7.5"/>'
    if modo == "cheio":
        pintura = 'fill="%s"' % cor
    else:
        pintura = ('fill="none" stroke="%s" stroke-width="3.2" '
                   'stroke-linejoin="round" stroke-linecap="round"' % cor)
    return '''
      <g class="figura" transform="translate(%(dx)d %(dy)d) scale(%(esc).3f)" style="--atraso:%(at)ss">
        <g class="corpo" %(pintura)s>
          %(cabeca)s
          <path d="M -9 -90 L 9 -90 L 14 -42 L -12 -42 Z"/>
          <g class="braco-tras"><path d="M 2 -84 L 21 -63 L 16 -57 L -3 -78 Z"/></g>
          <g class="perna-tras"><path d="M -8 -46 L 2 -46 L 6 0 L -6 0 Z"/></g>
          <g class="perna-frente"><path d="M 0 -46 L 11 -46 L 17 0 L 6 0 Z"/></g>
          <g class="braco-frente"><path d="M -2 -84 L -23 -66 L -18 -59 L 3 -77 Z"/></g>
        </g>
      </g>''' % dict(dx=dx, dy=dy, esc=escala, cor=cor, at=atraso, pintura=pintura,
                     cabeca=cabeca)


def par(modo, cor_tras, cor_frente):
    """As duas pessoas: a de tras entra antes no DOM (fica atras) e meio passo
    defasada. Diferenciadas por cabelo e cor de acento -- nao por vestuario."""
    # um degrau exato de distancia: a de tras pisa no degrau de baixo
    y_frente = piso_em(FIG_X)
    y_tras = piso_em(FIG_X - PASSO_W)
    return (figura(-PASSO_W, y_tras, 1.02, cor_tras, "preso", T, modo) +
            figura(0, y_frente, 1.10, cor_frente, "curto", 0, modo))


# ---------------------------------------------------------------- geometria
def silhueta_escada():
    p = ["M %d %d" % (BASE_X, H + 90)]
    for i in range(N):
        x, y = BASE_X + i * PASSO_W, BASE_Y - i * PASSO_H
        p += ["L %d %d" % (x, y), "L %d %d" % (x + PASSO_W, y)]
    p.append("L %d %d" % (BASE_X + N * PASSO_W, H + 90))
    return " ".join(p) + " Z"


def linha_escada():
    p = ["M %d %d" % (BASE_X, BASE_Y + PASSO_H)]
    for i in range(N):
        x, y = BASE_X + i * PASSO_W, BASE_Y - i * PASSO_H
        p += ["L %d %d" % (x, y), "L %d %d" % (x + PASSO_W, y)]
    return " ".join(p)


def arestas(classe="aresta"):
    out = []
    for i in range(N):
        x, y = BASE_X + i * PASSO_W, BASE_Y - i * PASSO_H
        out.append('<path class="%s" style="--i:%d" d="M %d %d L %d %d"/>'
                   % (classe, i, x, y, x + PASSO_W, y))
    return "\n      ".join(out)


def barras():
    """Variante C: cada degrau e uma coluna de grafico que sobe do rodape."""
    out = []
    larg = int(PASSO_W * 0.74)
    for i in range(N):
        x = BASE_X + i * PASSO_W + (PASSO_W - larg) // 2
        y = BASE_Y - i * PASSO_H
        out.append(
            '<g class="barra" style="--i:%d">'
            '<rect x="%d" y="%d" width="%d" height="%d" fill="%s" fill-opacity=".55"/>'
            '<rect class="topo" x="%d" y="%d" width="%d" height="7" fill="%s"/>'
            '</g>' % (i, x, y, larg, H + 90 - y, CLARO, x, y - 3, larg, CIANO))
    return "\n      ".join(out)


# ---------------------------------------------------------------- CSS comum
CSS_COMUM = '''
    @keyframes andar { to { transform: translate(-%(PW)dpx, %(PH)dpx); } }
    .cenario { animation: andar %(T)ss linear infinite; }

    @keyframes balanco { 0%%,100%% { transform: translateY(0); } 50%% { transform: translateY(-6px); } }
    @keyframes pernaA  { 0%%,100%% { transform: rotate(26deg); }  50%% { transform: rotate(-22deg); } }
    @keyframes pernaB  { 0%%,100%% { transform: rotate(-22deg); } 50%% { transform: rotate(26deg); } }
    @keyframes bracoA  { 0%%,100%% { transform: rotate(-18deg); } 50%% { transform: rotate(15deg); } }
    @keyframes bracoB  { 0%%,100%% { transform: rotate(15deg); }  50%% { transform: rotate(-18deg); } }

    .corpo { animation: balanco %(T)ss ease-in-out infinite; animation-delay: var(--atraso); }
    .perna-frente,.perna-tras,.braco-frente,.braco-tras {
      transform-box: fill-box; transform-origin: top center;
      animation-duration: %(T2)ss; animation-timing-function: ease-in-out;
      animation-iteration-count: infinite; animation-delay: var(--atraso);
    }
    .perna-frente { animation-name: pernaA; }
    .perna-tras   { animation-name: pernaB; }
    .braco-frente { animation-name: bracoA; }
    .braco-tras   { animation-name: bracoB; }

    @media (prefers-reduced-motion: reduce) {
      .cenario,.corpo,.perna-frente,.perna-tras,.braco-frente,.braco-tras,
      .aresta,.barra,.guia { animation: none !important; }
    }
''' % dict(PW=PASSO_W, PH=PASSO_H, T=T, T2=T * 2)

MOLDE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %(W)d %(H)d"
     preserveAspectRatio="xMaxYMax slice" role="img"
     aria-label="Duas pessoas subindo uma escada, juntas">
  <title>%(titulo)s</title>
  <defs>%(defs)s<clipPath id="palco"><rect width="%(W)d" height="%(H)d"/></clipPath></defs>
  <style>%(css)s%(css_extra)s</style>
  <rect width="%(W)d" height="%(H)d" fill="%(fundo)s"/>%(atmosfera)s
  <g clip-path="url(#palco)">
    <g class="cenario">
      %(cenario)s
    </g>
    <g transform="translate(%(FIG_X)d 0)">%(figuras)s</g>
  </g>
</svg>
'''


def montar(titulo, defs, css_extra, fundo, atmosfera, cenario, figuras):
    return MOLDE % dict(W=W, H=H, titulo=titulo, defs=defs, css=CSS_COMUM,
                        css_extra=css_extra, fundo=fundo, atmosfera=atmosfera,
                        cenario=cenario, figuras=figuras, FIG_X=FIG_X)


# ---------------------------------------------------------------- variantes
def variante_a():
    """MASSA SOLIDA: escada cheia, silhuetas cheias, luz subindo."""
    defs = ('<linearGradient id="ceu" x1="0" y1="0" x2=".3" y2="1">'
            '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="#010833"/>'
            '</linearGradient>'
            '<linearGradient id="face" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="%s" stop-opacity=".30"/>'
            '<stop offset="1" stop-color="%s" stop-opacity=".09"/></linearGradient>'
            % (NAVY, CLARO, CLARO))
    css = '''
    @keyframes acender {
      0%%,64%%,100%% { stroke: %(CLARO)s; stroke-opacity:.50; }
      12%%          { stroke: %(CIANO)s; stroke-opacity:.95; }
    }
    .aresta { fill:none; stroke:%(CLARO)s; stroke-opacity:.50; stroke-width:3.5;
      animation: acender %(T6)ss linear infinite;
      animation-delay: calc(var(--i) * %(Tp).3fs); }
''' % dict(CLARO=CLARO, CIANO=CIANO, T6=T * 6, Tp=T * 6.0 / N)
    atm = ('<rect width="%d" height="%d" fill="url(#ceu)"/>' % (W, H))
    cen = ('<path d="%s" fill="url(#face)"/>\n      %s'
           % (silhueta_escada(), arestas()))
    return montar("Subindo juntos", defs, css, NAVY, atm, cen,
                  par("cheio", CLARO, CIANO))


def variante_b():
    """BLUEPRINT: so traco, com guia tracejada subindo."""
    defs = ('<linearGradient id="ceu" x1="0" y1="0" x2=".3" y2="1">'
            '<stop offset="0" stop-color="#010A3D"/>'
            '<stop offset="1" stop-color="%s"/></linearGradient>' % ESCURO)
    css = '''
    @keyframes correr { to { stroke-dashoffset: -220; } }
    .guia { stroke-dasharray: 14 16; animation: correr %(T3)ss linear infinite; }
    .malha line { stroke: %(CIANO)s; stroke-opacity:.07; stroke-width:1; }
''' % dict(T3=T * 3, CIANO=CIANO)
    malha = "".join('<line x1="0" y1="%d" x2="%d" y2="%d"/>' % (y, W, y)
                    for y in range(70, H, 70))
    atm = ('<rect width="%d" height="%d" fill="url(#ceu)"/>'
           '<g class="malha">%s</g>' % (W, H, malha))
    cen = ('<path d="%s" fill="none" stroke="%s" stroke-opacity=".80" stroke-width="3.5" '
           'stroke-linejoin="round"/>'
           '<path class="guia" d="%s" fill="none" stroke="%s" stroke-opacity="1" '
           'stroke-width="2.6"/>' % (linha_escada(), CLARO, linha_escada(), CIANO))
    return montar("Subindo juntos", defs, css, ESCURO, atm, cen,
                  par("traco", CLARO, CIANO))


def variante_c():
    """BARRAS: a escada e um grafico de crescimento."""
    defs = ('<linearGradient id="ceu" x1="0" y1="0" x2=".3" y2="1">'
            '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="#010833"/>'
            '</linearGradient>' % NAVY)
    css = '''
    @keyframes pulsar { 0%%,70%%,100%% { fill-opacity:.55; } 14%% { fill-opacity:.95; } }
    .barra .topo { animation: pulsar %(T6)ss linear infinite;
      animation-delay: calc(var(--i) * %(Tp).3fs); }
''' % dict(T6=T * 6, Tp=T * 6.0 / N)
    atm = '<rect width="%d" height="%d" fill="url(#ceu)"/>' % (W, H)
    return montar("Subindo juntos", defs, css, NAVY, atm, barras(),
                  par("cheio", CLARO, CIANO))


if __name__ == "__main__":
    destino = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.dirname(os.path.abspath(__file__))
    for letra, fn in (("A", variante_a), ("B", variante_b), ("C", variante_c)):
        caminho = os.path.join(destino, "onda63-escada-%s.svg" % letra)
        with io.open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(fn())
        print("%s  (%.1f KB)" % (caminho, os.path.getsize(caminho) / 1024.0))
