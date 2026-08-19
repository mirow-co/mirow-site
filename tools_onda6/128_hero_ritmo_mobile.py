# -*- coding: utf-8 -*-
r"""128_hero_ritmo_mobile.py — o card esquerdo do hero para de se sobrepor no mobile.

    python tools_onda6/128_hero_ritmo_mobile.py <raiz-que-contem-public> [--check]

Idempotente: rodar 2x reporta 0 mudancas.

PEDIDO (Mario, 19/08/2026, com foto do iPhone): "me ajude a melhor distribuir os
elementos do card esquerdo nas paginas mobile e desktop. olhe como esta no momento,
com texto sobre texto, dificil legibilidade."

A CAUSA, MEDIDA (nao deduzida do CSS)
-------------------------------------
`.onda53-slogan h2{margin-bottom:-20px}` foi escrito SEM media query, entao vale em
toda largura. Ele foi calibrado NA TINTA no desktop, onde o slogan tem 62px com
line-height 160% -- ou seja ~18,6px de entrelinha MORTA de cada lado -- e puxar 20px
so come vazio. Medido no navegador:

    largura   fonte/entrelinha   entrelinha morta   margin aplicada   folga h2->p
    390 px    38 / 44,08 px      ~3,0 px            -20 px            -20 px  COLIDE
    768 px    38 / 44,08 px      ~3,0 px            -20 px            -20 px  COLIDE
    1024 px   62 / 99,2 px       ~18,6 px            +7 px (onda 8.2)  +7 px  ok
    1400 px   62 / 99,2 px       ~18,6 px            +7 px             +7 px  ok

Abaixo de 992px o bloco da onda 8.2 (que e `min-width:992px`) nao vale, entao quem
manda e o -20px -- e ali ele desconta entrelinha que nao existe. A tinta da ultima
linha ("Resultados") termina em y=327 e o paragrafo comeca em y=300: 27px de texto
por cima de texto.

Segundo achado, menor, no mesmo card: o eyebrow "AI Powered" (margin-bottom:-6px,
tambem sem media query) termina em y=182 e a tinta do "Estrategia" comeca em y=181.
Encostam. Mesma causa, mesma correcao.

O CONSERTO
----------
Escopar os dois valores negativos ao desktop, onde foram medidos, e dar ao mobile
espacamento positivo proprio. Editado NO LUGAR, nao por bloco de override somado --
regra dos "valores gemeos" do CLAUDE.md: o -20 e o -6 continuam existindo uma vez
so, agora dentro do `@media (min-width:992px)` a que sempre pertenceram.

Os numeros do mobile foram escolhidos para o gap de TINTA ficar parelho, que e o
mesmo criterio que o Mario pediu na onda 53 para o desktop.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public

CSS = "wp-content/uploads/2026/07/onda6/onda6.css"

ANTIGO_SELO = ".onda53-selo-ia{margin-bottom:-6px}"
ANTIGO_H2 = ".onda53-slogan h2{margin-bottom:-20px}"

NOVO = """/* onda63 (19/08): os dois negativos abaixo valiam em TODA largura, mas foram
   medidos na tinta do DESKTOP, onde a entrelinha morta e ~18,6px (62px/160%).
   Abaixo de 992px a fonte cai para 38px/116% e a entrelinha morta vira ~3px --
   os -20px passavam a comer 27px do paragrafo, e o -6px encostava o eyebrow no
   "Estrategia". Medido no navegador em 390/768/1024/1400. Escopados aqui, com
   ritmo proprio para o mobile; editado NO LUGAR (valores gemeos). */
@media only screen and (min-width:992px){
  .onda53-selo-ia{margin-bottom:-6px}
  .onda53-slogan h2{margin-bottom:-20px}
}
@media only screen and (max-width:991px){
  .onda53-selo-ia{margin-bottom:18px}
  .onda53-slogan h2{margin-bottom:20px}
}"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    check = "--check" in sys.argv
    pub = resolve_public(sys.argv[1])
    fp = os.path.join(pub, CSS.replace("/", os.sep))

    with io.open(fp, encoding="utf-8") as f:
        css = f.read()

    if "onda63 (19/08)" in css:
        print("0 mudanca(s) -- ja aplicado")
        return

    faltando = [t for t in (ANTIGO_SELO, ANTIGO_H2) if t not in css]
    if faltando:
        raise SystemExit("nao achei no CSS: %s" % faltando)

    # remove a declaracao solta do selo e substitui a do h2 pelo bloco escopado,
    # para os valores continuarem existindo UMA vez so
    novo = css.replace(ANTIGO_SELO, "")
    novo = novo.replace(ANTIGO_H2, NOVO)

    if check:
        print("[--check] aplicaria o bloco escopado (2 declaracoes movidas)")
        return

    with io.open(fp, "w", encoding="utf-8", newline="") as f:
        f.write(novo)
    print("1 mudanca -- negativos escopados em >=992px, ritmo proprio em <=991px")


if __name__ == "__main__":
    main()
