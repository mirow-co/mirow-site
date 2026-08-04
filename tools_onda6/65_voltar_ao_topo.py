# -*- coding: utf-8 -*-
"""65 — onda 18, S-51 (issue #109): botao fixo "voltar ao inicio da pagina".

Uso:
    python tools_onda6/65_voltar_ao_topo.py <raiz-que-contem-public>

Pedido do Mario: "quero que tenha um botao o tempo todo levando ao inicio da
pagina incial, que acompanhe o usuario da pagina no lado direito" + "em todas as
paginas deve ter o botao para subir para o inicio da pagina".

Entra em TODA pagina com <footer class="footer"> (as 275): um <a> fixo na lateral
direita, escondido no topo e revelado depois de ~400px de rolagem. Sem
dependencia de lib: 12 linhas de JS inline (o tema carrega jQuery, mas inline
evita mais um arquivo com ?v=).

Acessibilidade: e um link real para #topo (funciona sem JS), com aria-label por
idioma; o scroll suave vem de scroll-behavior no CSS, com respeito a
prefers-reduced-motion.

Idempotente: bloco entre marcadores, regravado igual no 2o run.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (escrever_bloco_css, gravar, idioma_da_pagina, ler,  # noqa: E402
                        resolve_public)

MARK_INI = "<!-- onda18:voltar-topo -->"
MARK_FIM = "<!-- /onda18:voltar-topo -->"

ROTULO = {
    "pt": u"Voltar ao início da página",
    "en": u"Back to top of page",
    "de": u"Zurück zum Seitenanfang",
}

CSS = """/* S-51: botao "voltar ao inicio", fixo na lateral direita, em toda pagina. */
html{scroll-behavior:smooth}
@media (prefers-reduced-motion: reduce){html{scroll-behavior:auto}}
.onda18-topo{position:fixed;right:22px;bottom:34px;z-index:900;
  width:52px;height:52px;display:flex;align-items:center;justify-content:center;
  background:#020E66;border:2px solid #00ADEC;border-radius:50%;
  color:#fff;text-decoration:none;
  opacity:0;visibility:hidden;transform:translateY(10px);
  transition:opacity 220ms ease,transform 220ms ease,visibility 220ms ease,
    background 220ms ease}
.onda18-topo.is-visivel{opacity:1;visibility:visible;transform:none}
.onda18-topo:hover,.onda18-topo:focus-visible{background:#00ADEC;color:#020E66}
.onda18-topo svg{width:22px;height:22px;display:block}
.onda18-topo svg path{fill:currentColor}
@media only screen and (max-width: 767px){
  /* no mobile encosta mais no canto para nao cobrir texto */
  .onda18-topo{right:14px;bottom:18px;width:44px;height:44px}
  .onda18-topo svg{width:19px;height:19px}
}
@media print{.onda18-topo{display:none}}"""

SETA = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
        '<path d="M12 4.6l8.2 8.2-2.1 2.1L13.5 10.3V19.4h-3V10.3l-4.6 4.6-2.1-2.1z"/>'
        '</svg>')

JS = ("<script>(function(){var b=document.querySelector('.onda18-topo');if(!b)return;"
      "function t(){if(window.pageYOffset>400){b.classList.add('is-visivel');}"
      "else{b.classList.remove('is-visivel');}}"
      "window.addEventListener('scroll',t,{passive:true});t();})();</script>")


def bloco(lang):
    rotulo = ROTULO.get(lang, ROTULO["pt"])
    return ('%s<a class="onda18-topo" href="#topo" aria-label="%s" title="%s">%s</a>%s%s'
            % (MARK_INI, rotulo, rotulo, SETA, JS, MARK_FIM))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mudou = escrever_bloco_css(pub, "voltar-topo", CSS, onda="onda18")
    print("bloco onda18:voltar-topo %s" % ("gravado" if mudou else "ja estava igual"))

    alterados = 0
    sem_body = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if '<footer class="footer">' not in h:
                continue
            if "</body>" not in h:
                sem_body += 1
                continue
            novo_bloco = bloco(idioma_da_pagina(h))

            if MARK_INI in h:
                velho = h[h.index(MARK_INI):h.index(MARK_FIM) + len(MARK_FIM)]
                novo = h.replace(velho, novo_bloco, 1)
            else:
                novo = h.replace("</body>", novo_bloco + "\n</body>", 1)

            # ancora do topo: o <body> ganha id="topo" se ainda nao tiver
            if 'id="topo"' not in novo:
                novo = re.sub(r'(<body\b)', r'\1 id="topo"', novo, count=1)

            if novo != h:
                gravar(p, novo)
                alterados += 1
    print("resumo: %d pagina(s) com o botao de voltar ao topo, %d sem </body>"
          % (alterados, sem_body))


if __name__ == "__main__":
    main()
