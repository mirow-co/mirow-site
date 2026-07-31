# -*- coding: utf-8 -*-
"""47 — S-23 (issue #73): hero da home = malha animada (Variante B), sai o MP4.

Uso:
    python tools_onda6/47_hero_malha_animada.py <raiz-que-contem-public>

O QUE FAZ
---------
Nas 4 homes, dentro de <div class="banner__background">, troca o

    <video autoplay ...><source src=".../video-bg-home-1.mp4" ...></video>   (22,8 MB)

pela Variante B aprovada pelo Mario (30/07, issue #73):

    <img class="hero-malha__img" src=".../onda6/malha-hero.jpg">             (~212 KB)
    <canvas class="hero-malha__canvas"></canvas>
    <script src=".../onda6/onda13-hero-plexus.js" defer></script>

O JS anima por curta duracao (fade-in 1,2s + 7s de movimento + 2s de freio) e
desliga o requestAnimationFrame — o quadro final vira imagem estatica.
prefers-reduced-motion recebe direto o quadro parado.

- CSS novo em bloco marcado (onda13:hero-malha) — a regra do tema mira
  `.banner__background video`; a img/canvas precisam das suas proprias.
- O src do <script> NAO leva ?v= aqui: o 27_cache_busting.py carimba (o asset
  entra na lista ASSETS dele e na ASSETS_PROPRIOS da suite).
- Ganho colateral (e principal): ~22,6 MB a menos no carregamento da home.

Idempotente: paginas ja migradas nao contem mais o <video> e nada muda.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import base_prefix, escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

HOMES = ["pt/index.html", "en/index.html", "de/index.html", "en/homepage/index.html"]

REX_VIDEO = re.compile(
    r'(<div class="banner__background">)\s*<video.*?</video>\s*(</div>)', re.S)

NOVO = (u'{ini}\n'
        u'                <!-- onda13:hero-malha -->\n'
        u'                <img class="hero-malha__img" '
        u'src="{pfx}wp-content/uploads/2026/07/onda6/malha-hero.jpg" alt="">\n'
        u'                <canvas class="hero-malha__canvas"></canvas>\n'
        u'                <script src="{pfx}wp-content/uploads/2026/07/onda6/'
        u'onda13-hero-plexus.js" defer></script>\n'
        u'                <!-- /onda13:hero-malha -->\n'
        u'            {fim}')

CSS = """/* S-23 (#73): a regra do tema so cobre `.banner__background video`; a malha
   estatica + canvas precisam do proprio posicionamento. opacity .5 na imagem =
   o mesmo que o tema aplicava no video (sem isso o slogan branco briga com a
   malha acesa do canto inferior esquerdo — verificado no prototipo). */
.banner__background .hero-malha__img{
  position:absolute;top:0;left:0;width:100% !important;height:100% !important;
  object-fit:cover;opacity:.5;backface-visibility:hidden}
.banner__background .hero-malha__canvas{
  position:absolute;top:0;left:0;width:100%;height:100%}"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mudou_css = escrever_bloco_css(pub, "hero-malha", CSS, onda="onda13")
    print("bloco onda13:hero-malha %s" % ("gravado" if mudou_css else "ja estava igual"))

    for rel in ("wp-content/uploads/2026/07/onda6/malha-hero.jpg",
                "wp-content/uploads/2026/07/onda6/onda13-hero-plexus.js"):
        if not os.path.exists(os.path.join(pub, rel.replace("/", os.sep))):
            raise SystemExit("ERRO: asset ausente: %s" % rel)

    alterados = []
    for rel in HOMES:
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        pfx = base_prefix(h)
        novo = REX_VIDEO.sub(
            lambda m: NOVO.format(ini=m.group(1), fim=m.group(2), pfx=pfx), h, count=1)
        if novo != h:
            gravar(p, novo)
            alterados.append(rel)
    print("paginas alteradas: %s" % (", ".join(alterados) or "nenhuma (ja estava igual)"))


if __name__ == "__main__":
    main()
