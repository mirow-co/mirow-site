# -*- coding: utf-8 -*-
"""
28_hero_slogan_alto.py — onda 8.2: slogan comeca mais em cima e mais espacado.

Uso:  python tools_onda6/28_hero_slogan_alto.py <raiz-que-contem-public>
      (rodar ANTES do 27_cache_busting.py, que carimba a versao dos assets)

Pedido do Mario (medido em 1400x900, home PT, antes):

    Estrategia  top=196
    Confianca   top=268     (72px de linha, ~5px de respiro entre as palavras)
    Resultado   top=340
    subtitulo   top=436  |  pills top=519, bottom=567
    header termina em 98 -> quase 100px de azul vazio acima do slogan

Ele quer: (1) "Estrategia" mais em cima, ocupando parte daquele vazio;
(2) mais espacamento, igual entre as tres palavras; (3) "Resultado" NO MESMO
LUGAR — o bloco cresce para cima, sem empurrar subtitulo e pills para baixo.

Como a conta fecha
------------------
O hero tem altura calculada (dobra exata, onda 8) e o conteudo e centralizado
verticalmente. Nesse arranjo, crescer o h2 empurraria metade para cima e metade
para baixo — o subtitulo desceria. E ancorar o bloco embaixo (flex-end) exigiria
um padding diferente por idioma e por altura de tela, que e justamente o "valor
magico" que a onda 8 eliminou.

A saida e nao mexer na ALTURA DE LAYOUT do h2: o line-height cresce e uma
margem superior NEGATIVA devolve exatamente o que ele ganhou, com a margem
inferior fechando a conta:

    margin-top + 3 x line-height + margin-bottom = 241,8px   (o valor de hoje:
                                                              3 x 71,92 + 26)

Assim o bloco (h2 + subtitulo + pills) mantem a mesma altura, a centralizacao
nao muda, e subtitulo e pills ficam no pixel exato em QUALQUER idioma e altura
de tela — o texto do slogan cresce so para cima, por cima do vazio.

A margem negativa e calibrada para "Resultado" cair onde ja estava:

    topo de "Resultado" = topo do h2 + (line-height - 67)/2 + 2 x line-height

(67px e a caixa de glifo do Arial 62px, medida no CDP.)

Telas baixas (< 840px de altura, ex.: 1366x768) tem so ~30px de folga entre o
header e o slogan, entao la o aumento e menor (126% em vez de 160%) — pela mesma
formula, com "Resultado" tambem parado. Sem isso o slogan entraria embaixo do
menu.

Idempotente.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, resolve_public  # noqa: E402

CSS = u"""/* onda8.2 — slogan mais alto e mais espacado, com "Resultado" parado */
@media only screen and (min-width: 992px){
  /* 3 x 99,2 = 297,6; -68,6 + 297,6 + 12,8 = 241,8 = altura de margem de hoje */
  .homepage .banner h2{
    line-height:160%;
    margin-top:-68.6px;
    margin-bottom:12.8px;
  }
}
@media only screen and (min-width: 992px) and (max-height: 839px){
  /* pouca folga sob o header: aumento menor, mesma conta */
  .homepage .banner h2{
    line-height:126%;
    margin-top:-15.8px;
    margin-bottom:23.4px;
  }
}
"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    if escrever_bloco_css(pub, "hero-slogan-alto", CSS, onda="onda8"):
        print("css onda8:hero-slogan-alto gravado")
    else:
        print("css onda8:hero-slogan-alto ja atualizado")


if __name__ == "__main__":
    main()
