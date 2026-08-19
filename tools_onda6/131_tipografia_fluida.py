# -*- coding: utf-8 -*-
u"""131 — onda 66: a tipografia deixa de saltar em 992px e passa a ser contínua.

Uso: python tools_onda6/131_tipografia_fluida.py <raiz-que-contem-public>

O QUE ESTE SCRIPT CONSERTA
--------------------------
Medido em 19/08 com `tools_onda6/qa/baseline.py`, varrendo 320→2560px de 64 em 64:

    slogan          salto de  63,2%  entre 960px e 1024px  (38,0 -> 62,0)
    titulo-secao    salto de  41,2%  entre 960px e 1024px  (34,0 -> 48,0)

É o penhasco de breakpoint que a reconstrução existe para eliminar. Cada tamanho
era um par calibrado à mão por faixa, e quem abre numa largura entre as faixas vê
o degrau.

O PRINCÍPIO DESTA MIGRAÇÃO: PRESERVAR OS EXTREMOS, INTERPOLAR O MEIO
--------------------------------------------------------------------
Nenhum `clamp()` aqui foi escolhido por gosto. Cada um passa pelos MESMOS valores
que estão no ar hoje nas larguras aprovadas, e só preenche o vão entre elas:

    elemento                    hoje                     clamp                        conferência
    slogan (.banner__title)     38 <992 · 62 >=992       clamp(38, 8.8px+3.8vw, 62)   768->38 · 1400->62
    .onda30-titulo-secao        28 <768 · 34 <992 · 48   clamp(28, 17.6px+2.17vw, 48) 768->34,3 · 1400->48
    .onda29-abertura__titulo    40 <992 · 62 >=992       clamp(40, 12.2px+3.55vw, 62) 768->39,5 · 1400->62
    .onda29-abertura__apoio     18 <992 · 22 >=992       clamp(18, 14.6px+0.53vw, 22) 768->18,7 · 1400->22
    .onda18-orbe__titulo        32 <768 · 44 <992 · 64   clamp(32, 19.7px+3.16vw, 64) 768->44 · 1400->64
    .our-numbers__list strong   52 <992 · 72 >=992       clamp(52, 27.7px+3.16vw, 72) 768->52 · 1400->72
    .our-numbers__list span     19 <992 · 26 >=992       clamp(19, 10.5px+1.11vw, 26) 768->19 · 1400->26
    .onda41-imprensa__logo--txt 19 <992 · 24 >=992       clamp(19, 12.9px+0.79vw, 24) 768->19 · 1400->24

Ou seja: em 768px e em 1400px+ o site fica **igual ao aprovado**; o que muda é que
entre essas larguras a curva sobe em vez de pular. É a migração fluida mais
conservadora possível — e a única em que "não mudou nada nos extremos" é
verificável, não uma esperança.

O QUE FICA DE FORA DESTA PASSADA, DE PROPÓSITO
----------------------------------------------
* **`line-height` e margens do slogan.** Medido tinta a tinta: o gap slogan→parágrafo
  é 13,1px em <=768 e 10,2px em >=992, e a entrelinha morta salta de 3,0 para 18,6px
  porque o `line-height` salta de 1,16 para 1,6 em 992. Os dois degraus (leading e
  margem) são consistentes ENTRE SI — a margem de -20px existe para comer a
  entrelinha morta de 18,6px. Tornar o leading fluido é mudança de DESENHO do hero
  (as três palavras encostam), não migração; e mexer só na margem reintroduziria o
  bug da onda 63. Fica para o passo de espaçamentos, com a V36 de guarda.
* **`.hero-numeros__valor`.** O baseline acusou salto de 287% (16 -> 62px) entre
  1152 e 1216px. **Era artefato da sonda:** o card está `display:none` abaixo de
  1200px, e eu medi o `font-size` do elemento OCULTO, que é o default do tema.
  Número de elemento não renderizado não significa nada. A sonda foi corrigida.
* **`.menu__nav-*`.** O submenu tem sete tamanhos com `!important` cruzando quatro
  media queries, e três ondas (26, 28, 83) calibraram a altura dos painéis com
  assertion de igualdade (V15/V16, tolerância de 2px). Mexer ali sem migrar o
  painel inteiro quebra as duas.

O MÉTODO: EDITAR NO LUGAR, NÃO SOMAR OVERRIDE
---------------------------------------------
Cada par vira UM `clamp()`, e as declarações de media query que ele substitui são
**removidas**. Um bloco de override que somasse o `clamp()` por cima dos pares
antigos criaria exatamente a classe de bug dos "valores gêmeos" (quatro bugs da
onda 31, o peso da 35): dois lugares declarando o mesmo tamanho, divergindo depois
sem ninguém ver.

O slogan é a exceção necessária: o 38/62 mora no **tema** (`.banner__title` do
`bundle-css.css`), não na nossa camada. Ali não há o que editar no lugar — entra
como override dentro do nosso bloco marcado, que é o que a REGRA Nº ZERO permite
("sempre por cima do tema").

Idempotente: rodar 2x reporta 0 mudanças.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, resolve_public  # noqa: E402

CSS_REL = os.path.join("wp-content", "uploads", "2026", "07", "onda6", "onda6.css")

# (descricao, antes, depois) — strings EXATAS do arquivo. Nada de regex adivinhando.
TROCAS = [
    # ---------------------------------------------------- titulos de secao da home
    (u".onda30-titulo-secao: 48px fixo -> clamp",
     "font-size:48px !important;font-weight:700 !important;line-height:1.1 !important;",
     "font-size:clamp(28px,17.6px + 2.17vw,48px) !important;"
     "font-weight:700 !important;line-height:1.1 !important;"),
    (u".onda30-titulo-secao: sai o 34px de <=991 (o clamp ja da 34,3 em 768)",
     ".onda30-titulo-secao{font-size:34px !important;margin-bottom:22px !important}",
     ".onda30-titulo-secao{margin-bottom:22px !important}"),
    (u".onda30-titulo-secao: sai o 28px de <=767 (e o piso do clamp)",
     ".onda30-titulo-secao{font-size:28px !important}",
     "/* onda66: o 28px de <=767 virou o PISO do clamp em .onda30-titulo-secao */"),

    # ------------------------------------------------- abertura padrao (imprensa etc.)
    (u".onda29-abertura__titulo: 62px fixo -> clamp",
     "font-size:62px;font-weight:700;line-height:1.1;margin:0}",
     "font-size:clamp(40px,12.2px + 3.55vw,62px);font-weight:700;line-height:1.1;margin:0}"),
    (u".onda29-abertura__titulo: sai o 40px de <=991 (e o piso do clamp)",
     ".onda29-abertura__titulo{font-size:40px}",
     "/* onda66: o 40px de <=991 virou o PISO do clamp em .onda29-abertura__titulo */"),
    (u".onda29-abertura__apoio: 22px fixo -> clamp",
     "font-size:22px;font-weight:400;line-height:1.4;margin:14px 0 0;max-width:60ch}",
     "font-size:clamp(18px,14.6px + 0.53vw,22px);font-weight:400;line-height:1.4;"
     "margin:14px 0 0;max-width:60ch}"),
    (u".onda29-abertura__apoio: sai o 18px de <=991 (e o piso do clamp)",
     ".onda29-abertura__apoio{font-size:18px}",
     "/* onda66: o 18px de <=991 virou o PISO do clamp em .onda29-abertura__apoio */"),

    # ------------------------------------------------------------- planeta de setores
    (u".onda18-orbe__titulo: 64px fixo -> clamp",
     ".onda18-orbe__titulo{color:#e9f0ff;font-size:64px;font-weight:700;line-height:1.05;",
     ".onda18-orbe__titulo{color:#e9f0ff;font-size:clamp(32px,19.7px + 3.16vw,64px);"
     "font-weight:700;line-height:1.05;"),
    (u".onda18-orbe__titulo: sai o 44px de <=991 (o clamp da 44,0 em 768)",
     ".onda18-orbe__titulo{font-size:44px}",
     "/* onda66: o 44px de <=991 saiu — o clamp de .onda18-orbe__titulo da 44,0 em 768px */"),
    (u".onda18-orbe__titulo: sai o 32px de <=767 (e o piso do clamp)",
     ".onda18-orbe__titulo{font-size:32px;margin-bottom:20px}",
     ".onda18-orbe__titulo{margin-bottom:20px}"),

    # ------------------------------------------------------------- numeros da secao
    (u".our-numbers__list strong: 72px fixo -> clamp",
     ".our-numbers__list strong{font-size:72px;font-size:4.5rem;padding-bottom:12px}",
     ".our-numbers__list strong{font-size:clamp(52px,27.7px + 3.16vw,72px);"
     "padding-bottom:12px}"),
    (u".our-numbers__list strong: sai o 52px de <=991 (e o piso do clamp)",
     ".our-numbers__list strong{font-size:52px;font-size:3.25rem}",
     "/* onda66: o 52px de <=991 virou o PISO do clamp em .our-numbers__list strong */"),
    (u".our-numbers__list span: 26px fixo -> clamp",
     ".our-numbers__list span{font-size:26px;font-size:1.625rem}",
     ".our-numbers__list span{font-size:clamp(19px,10.5px + 1.11vw,26px)}"),
    (u".our-numbers__list span: sai o 19px de <=991 (e o piso do clamp)",
     ".our-numbers__list span{font-size:19px;font-size:1.1875rem}",
     "/* onda66: o 19px de <=991 virou o PISO do clamp em .our-numbers__list span */"),

    # ------------------------------------------------- wordmark de texto da imprensa
    (u".onda41-imprensa__logo--texto: 24px fixo -> clamp",
     ".onda41-imprensa__logo--texto{font-weight:900;font-size:24px;line-height:1.1;",
     ".onda41-imprensa__logo--texto{font-weight:900;"
     "font-size:clamp(19px,12.9px + 0.79vw,24px);line-height:1.1;"),
    (u".onda41-imprensa__logo--texto: sai o 19px de <=991 (e o piso do clamp)",
     ".onda41-imprensa__logo--texto{font-size:19px}",
     "/* onda66: o 19px de <=991 virou o PISO do clamp em "
     ".onda41-imprensa__logo--texto */"),
]

# O slogan mora no TEMA (.banner__title do bundle-css.css): 38px <992 / 62px >=992.
# Nao ha o que editar no lugar; entra como override no nosso bloco marcado, que e o
# que a REGRA Nº ZERO permite. O clamp passa por 38 em 768px e por 62 em 1400px+.
CSS_SLOGAN = """
/* ---- onda66: o slogan do hero deixa de saltar 63% em 992px -----------------
   Medido pelo baseline (320->2560 de 64 em 64): 38,0 -> 62,0px entre 960 e 1024px.
   O par 38/62 e do TEMA (.banner__title), nao da nossa camada, entao aqui e
   override e nao edicao no lugar.
   A reta passa pelos dois valores aprovados: 768px -> 38,0 e 1400px -> 62,0.
   line-height e margens NAO mudam nesta passada — ver o cabecalho do
   131_tipografia_fluida.py para o porque (o gap tinta a tinta de 13,1/10,2px e a
   entrelinha morta de 3,0/18,6px sao consistentes entre si). */
.hero-texto .onda53-slogan h2,
.banner__content .onda53-slogan h2{
  font-size:clamp(38px, 8.8px + 3.8vw, 62px) !important}
"""


def main(argv):
    pub = resolve_public(argv[1] if len(argv) > 1 else ".")
    caminho = os.path.join(pub, CSS_REL)
    css = io.open(caminho, encoding="utf-8").read()

    feitas, pulos, faltas = 0, 0, []
    for desc, antes, depois in TROCAS:
        if depois in css:
            pulos += 1
            print(u"  = %s" % desc)
            continue
        n = css.count(antes)
        if n != 1:
            faltas.append(u"%s: %d ocorrencia(s) de %r" % (desc, n, antes[:70]))
            continue
        css = css.replace(antes, depois)
        feitas += 1
        print(u"  + %s" % desc)

    if faltas:
        for f in faltas:
            print(u"  ERRO: %s" % f)
        raise SystemExit(1)

    if feitas:
        with io.open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(css)

    mudou_bloco = escrever_bloco_css(pub, "slogan-fluido", CSS_SLOGAN, onda="onda66")

    # rele o que gravou (licao da onda 60b: nao declarar, medir)
    de_volta = io.open(caminho, encoding="utf-8").read()
    clamps = len(re.findall(r"font-size:\s*clamp\(", de_volta))
    print(u"\n%d troca(s) aplicada(s), %d ja estavam; bloco onda66:slogan-fluido %s"
          % (feitas, pulos, u"gravado" if mudou_bloco else u"ja estava igual"))
    print(u"%d declaracao(oes) font-size:clamp() no arquivo" % clamps)
    if clamps < 8:
        raise SystemExit(u"esperava ao menos 8 clamp() apos a migracao, achei %d" % clamps)


if __name__ == "__main__":
    main(sys.argv)
