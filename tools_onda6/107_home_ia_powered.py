# -*- coding: utf-8 -*-
u"""107 — onda 53 (#211): a home passa a dizer que a consultoria e tradicional
mas usa IA, com "AI Powered" ao lado do slogan e a IA como area TRANSVERSAL
abaixo das 3 praticas.

Uso:
    python tools_onda6/107_home_ia_powered.py <raiz-que-contem-public>

Os 3 pedidos do Mario (13/08), verbatim:
  1. trocar texto para "Focamos em estrategia, compras e go-to-market/pricing —
     entregamos resultados garantidos, lado a lado com a sua equipe" ->
     "Oferecemos consultoria estrategica tradicional que utiliza IA nos seus
     projetos de estrategia e inovacao, compras e go-to-market/pricing —
     entregamos resultados garantidos, lado a lado com a sua equipe"
  2. colocar do lado de estrategia confianca e resultados AI powered
  3. colocar dentro das areas de expertise Inteligencia Artificial como
     transversal abaixo das 3 areas

Decisoes de implementacao:
  - O texto PT e o do Mario, LITERAL. EN e DE sao traducao minha e estao
    marcadas para conferencia dele (em alemao, "IA" vira "KI" no corpo do texto;
    o SELO segue "AI Powered" nas 3 linguas, por ser rotulo de marca).
  - "Ao lado" = o h2 do slogan e o selo num flex row (.onda53-slogan). O selo
    quebra para baixo sozinho quando a caixa aperta — nao ha largura fixa.
  - "Transversal" e literal no layout: o bloco entra DENTRO do .praticas-3 (que
    e flex-wrap) com flex-basis 100%, entao ele atravessa as 3 colunas por
    construcao, nao por posicionamento manual.
  - Sem link no bloco de IA: nao existe pagina de pratica de IA (as issues
    #212-#214 poem IA DENTRO das 3 praticas existentes). Quando existir, o link
    entra aqui.

Idempotente: cada mudanca so entra se ainda nao estiver la.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

# ---------------------------------------------------------------- conteudo ---
# subtitulo do hero: (texto velho, texto novo)
SUBTITULO = {
    "pt": (
        u"Focamos em estratégia, compras e go-to-market/pricing — entregamos "
        u"resultados garantidos, lado a lado com a sua equipe",
        u"Oferecemos consultoria estratégica tradicional que utiliza IA nos seus "
        u"projetos de estratégia e inovação, compras e go-to-market/pricing — "
        u"entregamos resultados garantidos, lado a lado com a sua equipe",
    ),
    "en": (
        u"We focus on strategy, procurement and go-to-market/pricing — we deliver "
        u"guaranteed results, side by side with your team",
        u"We offer traditional strategy consulting that uses AI in your strategy "
        u"and innovation, procurement and go-to-market/pricing projects — we "
        u"deliver guaranteed results, side by side with your team",
    ),
    "de": (
        u"Wir fokussieren uns auf Strategie, Einkauf und Go-to-Market/Pricing — "
        u"wir liefern garantierte Ergebnisse, Seite an Seite mit Ihrem Team",
        u"Wir bieten klassische Strategieberatung, die KI in Ihren Projekten in "
        u"Strategie und Innovation, Einkauf und Go-to-Market/Pricing einsetzt — "
        u"wir liefern garantierte Ergebnisse, Seite an Seite mit Ihrem Team",
    ),
}

SELO = u'<span class="onda53-selo-ia">AI Powered</span>'

# bloco transversal de IA sob as 3 praticas
IA = {
    "pt": (u"Transversal às três práticas", u"Inteligência Artificial",
           u"Fazemos nossos projetos com forte uso de IA para ampliar o alcance "
           u"do nosso trabalho em qualquer uma das áreas de expertise"),
    "en": (u"Cutting across all three practices", u"Artificial Intelligence",
           u"We run our projects with heavy use of AI to widen the reach of our "
           u"work in any of our areas of expertise"),
    "de": (u"Übergreifend über alle drei Practices", u"Künstliche Intelligenz",
           u"Wir führen unsere Projekte mit starkem KI-Einsatz durch, um die "
           u"Reichweite unserer Arbeit in allen Expertisebereichen zu erweitern"),
}

# glifo de 3 nos ligados: os 3 cards acima, atravessados. Inline (sem asset novo).
GLIFO = (
    u'<svg class="onda53-ia__glifo" width="46" height="24" viewBox="0 0 46 24" '
    u'aria-hidden="true" focusable="false">'
    u'<line x1="7" y1="12" x2="23" y2="12" stroke="#00ADEC" stroke-width="2"/>'
    u'<line x1="23" y1="12" x2="39" y2="12" stroke="#00ADEC" stroke-width="2"/>'
    u'<circle cx="7" cy="12" r="5" fill="#020E66"/>'
    u'<circle cx="23" cy="12" r="5" fill="#00ADEC"/>'
    u'<circle cx="39" cy="12" r="5" fill="#020E66"/></svg>'
)


def bloco_ia(lang):
    tag, titulo, texto = IA[lang]
    return (
        u'<div class="praticas-3__transversal onda53-ia" data-aos="fade-up">'
        u'%s<div class="onda53-ia__texto">'
        u'<span class="onda53-ia__tag">%s</span>'
        u'<h4 class="onda53-ia__titulo">%s</h4>'
        u'<p class="onda53-ia__desc">%s</p>'
        u'</div></div>'
    ) % (GLIFO, tag, titulo, texto)


CSS = u"""/* onda53 (#211) — a home diz que a consultoria e tradicional mas usa IA.
   Selo "AI Powered" ao lado do slogan + IA como faixa TRANSVERSAL sob as 3
   praticas. Nada aqui toca no tema: sao classes proprias. */

/* 1. selo ao lado de Estrategia/Confianca/Resultados. O h2 e o selo num flex
   row; em caixa estreita o selo desce sozinho (sem media query com numero
   magico — quem decide e o proprio flex-wrap). */
/* onda53 v4: o selo e EYEBROW ACIMA do slogan (era ao lado, e flutuava sem
   ancora na altura do "Confianca"). Coluna, nao linha. */
.onda53-slogan{display:block}
/* ritmo do card, medido NA TINTA por analise de pixel (a caixa de linha mente:
   o line-height de 160% do slogan enche a caixa de entrelinha). Gap de tinta
   entre as 3 palavras: 20px. O gap ate a frase era 46px — mais que o dobro —
   e o Mario pediu "igualmente distribuido". As margens abaixo sao o que faz os
   tres gaps darem ~20px; o -20 no h2 desconta a entrelinha morta do line-height. */
.onda53-selo-ia{margin-bottom:-6px}/* onda53 v4: negativo de proposito — o
   slogan tem ~25px de entrelinha morta acima da tinta, entao puxar 20px nao
   encosta em nada e devolve à dobra o que o eyebrow custou (34px medidos). */
.onda53-slogan h2{margin-bottom:-20px}
/* onda53 v2 (13/08) — a 1a versao era pilula ciano solida com canto 14px: lia
   como etiqueta de e-commerce ("o ai powered precisa melhorar", Mario). Agora
   segue o STICKER dos nossos decks (R15: caixa alta, tique vertical colado a
   esquerda, sem preenchimento) — mesmo registro do eyebrow que o horizonte3.com
   usa no hero (medido: 12px, peso 600, letter-spacing 2,2px, regua de 22x1px),
   que foi a referencia que o Andreas citou. Selo ANOTA o slogan, nao compete.
   Peso 500 / tracking .12em, nao 700 / .18em da 1a tentativa: o sticker da R15 e
   "Arial 12pt REGULAR caixa alta" — bold contraria o padrao da propria casa — e
   os pares medidos ficam em 400-500 com tracking quase nulo (Accenture 12px/500
   ls .02em; McKinsey 14px/300 ls normal; Bain 13px/500). Tracking largo e
   convencao de DOC de design system, nao do que os grandes renderizam.
   PESO 600, nao 500: a S127 barrou o 500 — ele NAO esta entre os pesos que o
   <head> carrega (200/300/400/600/700/900) e o navegador o sintetizaria, que e
   a classe de bug da onda 35. Dos pesos reais, 600 e o mais proximo do registro
   "medium" dos pares; 400 (o regular da R15) esmaece sobre a foto do hero. */
.onda53-selo-ia{display:inline-flex;align-items:center;gap:11px;
  color:#00ADEC;font-weight:600;font-size:13px;line-height:1;
  letter-spacing:.12em;text-transform:uppercase;white-space:nowrap;
  background:none;padding:0;border-radius:0;box-shadow:none}
.onda53-selo-ia::before{content:"";flex:0 0 auto;width:2px;height:1.55em;
  background:#00ADEC}

/* 2. faixa transversal de IA. Ela e filha do .praticas-3 (flex-wrap), entao o
   flex-basis 100% ja a faz atravessar as 3 colunas — a "transversalidade" e
   estrutural, nao um posicionamento a mao. */
.praticas-3__transversal{flex:1 1 100%;display:flex;align-items:flex-start;
  gap:18px;margin-top:4px;padding:22px 26px;background:#F2F7FB;
  border-left:4px solid #00ADEC;box-sizing:border-box}
.onda53-ia__glifo{flex:0 0 auto;margin-top:4px}
.onda53-ia__texto{flex:1 1 auto;min-width:0}
.onda53-ia__tag{display:block;color:#00ADEC;font-weight:700;font-size:13px;
  letter-spacing:.04em;margin-bottom:4px}
.onda53-ia__titulo{color:#020E66;font-weight:700;margin:0 0 8px}
.onda53-ia__desc{color:#071C25;margin:0}
@media only screen and (max-width: 767px){
  .praticas-3__transversal{padding:18px 18px;gap:14px}
  /* onda53 v2: o padding/font-size daqui era da pilula antiga — valor gemeo
     morto. O sticker encolhe so o corpo, o tique acompanha via em. */
  .onda53-selo-ia{font-size:12px;letter-spacing:.10em}
}"""


def idioma(rel):
    return rel.split(os.sep)[0]


def aplicar(pub):
    mud = {"subtitulo": 0, "selo": 0, "ia": 0}
    for rel in [os.path.join("pt", "index.html"),
                os.path.join("en", "index.html"),
                os.path.join("de", "index.html")]:
        p = os.path.join(pub, rel)
        if not os.path.exists(p):
            print(u"  ! ausente: %s" % rel)
            continue
        lang = idioma(rel)
        h = ler(p)
        orig = h

        # 1. subtitulo do hero
        velho, novo = SUBTITULO[lang]
        if novo in h:
            pass
        elif velho in h:
            h = h.replace(velho, novo, 1)
            mud["subtitulo"] += 1
        else:
            print(u"  ! %s: subtitulo antigo nao encontrado (mudou desde a onda 53?)" % rel)

        # 2. selo ao lado do slogan
        if "onda53-selo-ia" not in h:
            m = re.search(r'<h2 data-aos="fade-right">.*?</h2>', h, re.S)
            if m:
                # onda53 v4 (13/08): o selo sai de AO LADO e vira EYEBROW ACIMA
                # do slogan ("so ali ai powered nao ficou bom", Mario). E a
                # posicao que a pesquisa mediu como padrao — horizonte3.com poe
                # "— AI TRANSFORMATION" acima do titulo, e a Deloitte usa kicker.
                # Ao lado, o selo flutuava sem ancora na altura do "Confianca".
                h = (h[:m.start()] + u'<div class="onda53-slogan">' + SELO
                     + m.group(0) + u'</div>' + h[m.end():])
                mud["selo"] += 1
            else:
                print(u"  ! %s: slogan do hero nao encontrado" % rel)

        # 3. faixa transversal de IA sob as 3 praticas
        if "onda53-ia" not in h:
            m = re.search(r'<div class="praticas-3">', h)
            if m:
                # fecha no </div> que fecha o .praticas-3: conta aninhamento
                i, prof = m.end(), 1
                for t in re.finditer(r'<div\b|</div>', h[m.end():]):
                    prof += 1 if t.group(0).startswith("<div") else -1
                    if prof == 0:
                        i = m.end() + t.start()
                        break
                h = h[:i] + bloco_ia(lang) + h[i:]
                mud["ia"] += 1
            else:
                print(u"  ! %s: bloco .praticas-3 nao encontrado" % rel)

        if h != orig:
            gravar(p, h)
            print(u"  + %s" % rel)
        else:
            print(u"  = %s (nada a fazer)" % rel)
    return mud


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    pub = resolve_public(sys.argv[1])
    print(u"107 — onda 53: home AI Powered (#211)")
    mud = aplicar(pub)
    escrever_bloco_css(pub, "home-ia", CSS, onda="onda53")
    # a assinatura e (pub, chave, css, onda=...). Chamar fora de ordem punha o
    # CSS INTEIRO dentro do marcador; como o marcador mudava a cada edicao, o
    # helper nunca reconhecia o bloco e ANEXAVA outro — 5 blocos, 20 copias de
    # cada regra, e a S127 lendo font-weight velho das copias mortas.
    print(u"  subtitulo: %(subtitulo)d · selo: %(selo)d · faixa IA: %(ia)d" % mud)
    return 0


if __name__ == "__main__":
    sys.exit(main())
