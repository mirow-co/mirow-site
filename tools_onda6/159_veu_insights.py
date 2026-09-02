# -*- coding: utf-8 -*-
"""Onda 85: o veu sobre a foto dos Insights fica no MINIMO que a leitura permite.

    python tools_onda6/159_veu_insights.py .

Pedido dos socios em 05/08 (issue #187, item 2): "Insights: melhorar
contraste/cor das fotos -- aparecem apagadas".

O DIAGNOSTICO
-------------
Medido no navegador, comparando a foto RENDERIZADA com o arquivo de origem: a do
card do Brazil Truck sai com 0,342 de saturacao e 102 de luminancia contra
0,418 e 133 do arquivo -- 18% menos cor e 23% mais escura.

A causa nao e filtro nem opacidade: e um `::after` do tema que cobre a foto com
`linear-gradient(rgba(4,21,69,.78) 0%, rgba(4,21,69,.3) 45%, transparent 75%)`.

E O QUE IMPEDE DE SIMPLESMENTE TIRAR
------------------------------------
O `<h3>` do card fica EM CIMA da foto. O veu nao e decoracao: e o que segura o
titulo branco sobre foto clara. Apagar o veu resolveria a reclamacao dos socios
criando um problema pior -- e um que nem sempre aparece, porque depende da foto.

ENTAO A PERGUNTA CERTA E OUTRA: qual e o veu MAIS LEVE que ainda deixa o titulo
legivel na PIOR foto do acervo? Medido pelo
`qa/medir_veu_insights.py`, que compoe cada foto com o navy em varias
opacidades e calcula a razao de contraste WCAG contra o texto branco:

    veu       0.78   0.70   0.62   0.55   0.48   0.40   0.30
    pior foto  9.8    7.6    5.9    4.8    3.9    3.1    2.4

A pior e a `iStock-1652035117` -- ceu claro. Com 0,62 ela ainda da 5,9:1, folga
confortavel sobre o minimo AA de 4,5:1. Com 0,55 cai para 4,8 e a margem some.

**0,62 nao e um numero escolhido por gosto: e o degrau medido.** O par do meio
desce na mesma proporcao (0,30 -> 0,24), para o gradiente manter a forma.

Ganho: a faixa de cima da foto mostra ~26% mais da imagem que antes.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_css = __import__("_onda7_css")
escrever_bloco_css, resolve_public = _css.escrever_bloco_css, _css.resolve_public

# os tres pontos do gradiente: (posicao, alfa). O de hoje e 0.78 / 0.30 / 0.
TOPO = 0.62
MEIO = 0.24

CSS = u"""/* Onda 85 (#187, socios 05/08: "as fotos aparecem apagadas") — o veu navy que
   o tema poe sobre a foto do card cai de .78 para %.2f no topo e de .30 para %.2f
   no meio. NAO e gosto: e o degrau medido por qa/medir_veu_insights.py, que
   compoe cada uma das 10 fotos do acervo com o navy e calcula o contraste WCAG
   do titulo branco. Com .62 a PIOR foto (iStock-1652035117, ceu claro) ainda da
   5,9:1 contra o minimo AA de 4,5:1; com .55 cai para 4,8 e a margem some.
   O veu existe porque o <h3> fica EM CIMA da foto — por isso ele diminui em vez
   de sair. Guardado pela S185, que refaz a conta a partir dos arquivos reais. */
.page-insights__list-image::after,
.page-insights__list-item .page-insights__list-image::after{
  background-image:linear-gradient(rgba(4,21,69,%.2f) 0%%, rgba(4,21,69,%.2f) 45%%,
    rgba(4,21,69,0) 75%%)}
""" % (TOPO, MEIO, TOPO, MEIO)


def main(raiz):
    pub = resolve_public(raiz)
    mudou = escrever_bloco_css(pub, "veu-insights", CSS, onda="onda85")
    print(u"159: bloco onda85:veu-insights %s (topo %.2f, meio %.2f)"
          % (u"escrito" if mudou else u"ja estava igual", TOPO, MEIO))
    return 1 if mudou else 0


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
