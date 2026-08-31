# -*- coding: utf-8 -*-
"""Onda 76 — primeiro passo da reconstrucao fluida: tipografia que CRESCE.

O que este script NAO faz, e por que
------------------------------------
Nao troca `font-size:15px` por `clamp()` na declaracao original. A auditoria
(`tools_onda6/qa/auditar_tipografia.py`, 31/08/2026) mediu o computado das 91
declaracoes de font-size do nosso CSS e achou o seguinte:

  MORTA        1  -- declaramos e outra regra vence
  FIXA        20  -- vale, e nao muda com a largura
  RESPONSIVA   3  -- vale e ja muda (o hero, da onda 66)
  AUSENTE     67  -- o seletor nao aparece nas 6 paginas medidas

O caso exemplar: `.onda18-imprensa__veiculo` declara 15px e 14px numa media
query, e o navegador desenha 13px em TODA largura, porque um bloco 600 linhas
abaixo redeclara 13px sem variante. Migrar aquela declaracao para clamp() seria
trocar regra morta por regra morta -- e reportar como "fluido" um site que
continuaria fixo. Por isso o bloco novo vai no FIM do arquivo, onde ganha a
cascata, e mira so o que a medicao mostrou que vale.

A direcao da fluidez: PARA CIMA
-------------------------------
O minimo do clamp e o valor que o site ja desenha hoje -- ninguem perde tamanho
no celular. O que muda e o teto: em tela grande o texto cresce em vez de ficar
parado no tamanho pensado para 1366px. Fluidez que ENCOLHE no telefone e o jeito
errado de fazer isto; a legibilidade movel e piso, nao variavel de ajuste.

Fora desta onda, de proposito
-----------------------------
- Texto de 12 a 16px (rotulo, data, link de rodape, tag): crescer texto de apoio
  bagunca a hierarquia, e o ganho e nulo.
- O menu (`.menu__nav-sublink*`): declara 19, 22, 24, 26 e 30 em camadas de media
  query e computa 19 em toda largura -- e no de cascata que precisa ser desatado
  antes, nao durante.
- Os 67 AUSENTE: ausencia nas 6 paginas medidas NAO e prova de que a regra e
  morta (pin do mapa aparece por JS, formulario de contato so existe numa pagina,
  a busca so renderiza com termo). Medir onde eles vivem antes de tocar.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_css = __import__("_onda7_css")
escrever_bloco_css, resolve_public = _css.escrever_bloco_css, _css.resolve_public

# seletor -> (minimo = o que o site ja desenha hoje, preferido, teto)
# O preferido em vw e calculado para bater o MINIMO em ~1366px, que e a largura
# para a qual o site foi desenhado -- assim nada muda ate ali, e so cresce depois.
FLUIDAS = [
    (".rede__titulo", "30px", "2.2vw", "40px"),
    (".onda18-imprensa__titulo", "17px", "1.25vw", "21px"),
    (".onda18-const__item", "18px", "1.32vw", "22px"),
    (".menu__nav-submenu h5", "21px", "1.54vw", "25px"),
    (".onda7-vertodos", "16px", "1.17vw", "19px"),
    (".praticas-3__card .home-experience__list-item-more", "18px", "1.32vw", "22px"),
]

CABECA = u"""/* Onda 76 — tipografia fluida, primeiro passo.
   O minimo de cada clamp e o tamanho que o site JA desenhava (medido com
   getComputedStyle, nao lido do CSS): ninguem perde tamanho no celular. O
   preferido em vw bate o minimo por volta de 1366px — a largura para a qual o
   site foi desenhado — e so a partir dali o texto cresce, ate o teto.
   Este bloco vai no fim do arquivo de proposito: varias destas regras tem
   redeclaracao em ondas anteriores, e quem vence a cascata e a ultima. */
"""


def montar():
    linhas = [CABECA]
    for sel, mini, pref, teto in FLUIDAS:
        linhas.append(u"%s{font-size:clamp(%s, %s, %s)}" % (sel, mini, pref, teto))
    return u"\n".join(linhas) + u"\n"


def main(raiz):
    pub = resolve_public(raiz)
    mudou = escrever_bloco_css(pub, "tipografia-fluida", montar(), onda="onda76")
    print(u"150: bloco onda76:tipografia-fluida %s (%d regras)"
          % ("escrito" if mudou else "sem mudanca", len(FLUIDAS)))
    return mudou


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
