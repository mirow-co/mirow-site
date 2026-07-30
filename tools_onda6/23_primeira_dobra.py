# -*- coding: utf-8 -*-
"""
23_primeira_dobra.py — onda 8, pedido 1 do Mario (primeira dobra EXATA).

Uso:  python tools_onda6/23_primeira_dobra.py <raiz-que-contem-public>

Objetivo: ao abrir qualquer home (pt/en/en-homepage/de), a primeira dobra mostra
titulo + subtitulo + links de contato + video da lampada + a faixa de logos de
clientes INTEIRA — e nada alem dela (nenhum pixel do gradiente azul-claro da
secao seguinte).

Como a conta e feita
--------------------
O hero (.banner) deixa de ter altura fixa de 100vh e passa a valer

    height: calc(100svh - var(--onda8-logos-h))

ou seja, a altura da janela menos a altura REAL da faixa de logos. Como o hero
comeca no topo do documento (o header e position:absolute, sobreposto ao hero),
hero + faixa de logos fecham exatamente uma tela.

A altura da faixa de logos NAO e um valor magico: um script minusculo
(onda8-dobra.js) mede a secao .clientes-logos no proprio navegador e grava o
resultado na variavel CSS --onda8-logos-h (com ResizeObserver, para acompanhar
a mudanca de quantas fileiras de logos cabem quando a janela muda de largura).
O CSS traz o fallback de 250px para o caso de o JS nao rodar.

Por que isso e robusto nas 3 linguas: o subtitulo do PT tem 2 linhas e o do DE
tem 3 — antes isso mudava a altura do hero e empurrava a faixa de logos para
fora da dobra. Com altura calculada, o tamanho do texto nao entra na conta; o
conteudo e centralizado verticalmente no espaco que sobra (align-items:center,
com padding-top maior que o header de 98px para o texto nunca encostar no menu).

O tema nao e alterado: CSS em bloco marcado no onda6.css e um <script> proprio
no fim do <body> das 4 homes.

Idempotente.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (base_prefix, escrever_bloco_css, garantir_link_css,  # noqa: E402
                        gravar, ler, resolve_public)

HOMES = ["pt/index.html", "en/index.html", "en/homepage/index.html", "de/index.html"]

JS_REL = "wp-content/uploads/2026/07/onda6/onda8-dobra.js"
JS_ID = "onda8-dobra-js"

INI = u"<!-- onda8:dobra -->"
FIM = u"<!-- /onda8:dobra -->"

CSS = u"""/* onda8 — primeira dobra exata: hero + faixa de logos = 1 tela */
:root{--onda8-logos-h:250px}
@media only screen and (min-width: 992px){
  .homepage .banner{
    height:calc(100vh - var(--onda8-logos-h));
    height:calc(100svh - var(--onda8-logos-h));
    min-height:430px;
    padding:118px 0 20px;
    align-items:center;
  }
  /* a lampada preenche o hero, qualquer que seja a altura calculada */
  .homepage .banner .banner__background video{object-fit:cover;height:100% !important}
  /* a faixa de logos nao pode crescer alem do que entrou na conta */
  .homepage .clientes-logos{padding-top:40px;padding-bottom:36px}
}
/* telas baixas (ex.: 1366x768): aperta o respiro para o subtitulo nao ser cortado */
@media only screen and (min-width: 992px) and (max-height: 820px){
  .homepage .banner{padding:106px 0 12px;min-height:360px}
}
"""

JS = u"""/* onda8 — mede a faixa de logos e alimenta --onda8-logos-h.
   Sem isso a conta da primeira dobra dependeria de um numero magico, que quebra
   quando muda a quantidade de fileiras de logos (largura da janela) ou o idioma. */
(function () {
  var faixa = document.querySelector('.homepage .clientes-logos');
  if (!faixa) { return; }
  var pendente = null;
  function medir() {
    pendente = null;
    var h = Math.round(faixa.getBoundingClientRect().height);
    if (h > 0) {
      document.documentElement.style.setProperty('--onda8-logos-h', h + 'px');
    }
  }
  function agendar() {
    if (pendente) { return; }
    pendente = window.requestAnimationFrame(medir);
  }
  medir();
  window.addEventListener('load', agendar);
  window.addEventListener('resize', agendar);
  window.addEventListener('orientationchange', agendar);
  if (window.ResizeObserver) { new window.ResizeObserver(agendar).observe(faixa); }
  if (document.fonts && document.fonts.ready) { document.fonts.ready.then(agendar); }
})();
"""


def garantir_classe_homepage(html):
    """en/homepage/ veio do espelho com <main class=""> — sem a classe .homepage.

    Por causa disso ela ficou de fora de TODAS as regras de home das ondas 6/7/8
    (hero compacto, menos vazio antes das praticas, e agora a primeira dobra).
    Aqui a classe e reposta, deixando as 4 homes com o mesmo comportamento.
    """
    return re.sub(r'<main class="">', u'<main class=" homepage ">', html, count=1)


def garantir_script(html, prefix):
    """Coloca o <script> da dobra logo antes de </body>, uma unica vez."""
    html = re.sub(re.escape(INI) + r".*?" + re.escape(FIM) + r"\n?", "", html, flags=re.S)
    tag = (u'%s\n<script id="%s" src="%s%s"></script>\n%s\n'
           % (INI, JS_ID, prefix, JS_REL, FIM))
    if "</body>" not in html:
        return html, False
    return html.replace("</body>", tag + u"</body>", 1), True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    if escrever_bloco_css(pub, "dobra", CSS, onda="onda8"):
        print("css onda8:dobra gravado")
    else:
        print("css onda8:dobra ja atualizado")

    jspath = os.path.join(pub, JS_REL.replace("/", os.sep))
    os.makedirs(os.path.dirname(jspath), exist_ok=True)
    atual = ""
    if os.path.exists(jspath):
        with io.open(jspath, encoding="utf-8") as f:
            atual = f.read()
    if atual != JS:
        with io.open(jspath, "w", encoding="utf-8", newline="\n") as f:
            f.write(JS)
        print("js onda8-dobra.js gravado")
    else:
        print("js onda8-dobra.js ja atualizado")

    alterados = 0
    for rel in HOMES:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: nao existe %s" % rel)
            continue
        html = ler(path)
        prefix = base_prefix(html)
        novo, ok = garantir_script(garantir_classe_homepage(html), prefix)
        if not ok:
            print("AVISO: sem </body> em %s" % rel)
            continue
        novo = garantir_link_css(novo, prefix)
        if novo != html:
            gravar(path, novo)
            alterados += 1
            print("dobra + script: %s" % rel)
        else:
            print("sem mudanca: %s" % rel)

    print("\nresumo: %d arquivo(s) HTML alterado(s)" % alterados)


if __name__ == "__main__":
    main()
