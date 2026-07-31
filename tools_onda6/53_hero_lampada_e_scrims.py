# -*- coding: utf-8 -*-
"""53 — S-34: hero volta a lampada (esticada) + paineis translucidos de leitura.

Uso:
    python tools_onda6/53_hero_lampada_e_scrims.py <raiz-que-contem-public>

Pedido do Mario (31/07): "eu nao gostei desse malha atual. quero voltar a
imagem da lampada que tinhamos antes. mas o negocio de esticar esta certo e
ficou bom. a barra direita (big numbers) precisa ter um fundo com um branco
transparente, de forma a ficar facilmente legivel. [...] todo esse texto
branco precisa ter um fundinho meio transparente para que nao prejudique a
leitura do texto."

O QUE FAZ
---------
1. Troca a imagem-base do hero: malha-hero.jpg -> lampada-hero.jpg (frame de
   10,3s do video-bg-home-1.mp4 original — a lampada acesa sobre o plexus,
   extraido via Chrome/canvas; o MP4 de 22,8 MB continua fora da pagina).
   O full-bleed da S-30 (div na section, sem mascara) fica como esta.
   A camada viva (canvas plexus) permanece — anima os nos sobre a foto.
2. Envelopa o bloco de texto do hero (slogan + subtitulo + pills) num
   <div class="hero-texto"> (marcadores onda15:hero-texto) — os elementos sao
   irmaos soltos na .col e CSS nao envelopa.
3. CSS (bloco onda15:hero-scrims): vidro fosco branco-translucido atras
   (a) do bloco de texto e (b) dos big numbers a direita — legibilidade sem
   esconder a foto ("fundo com um branco transparente", pedido verbatim).

Idempotente.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

HOMES = ["pt/index.html", "en/index.html", "de/index.html", "en/homepage/index.html"]

REX_TEXTO = re.compile(
    r'(<h2 data-aos="fade-right">.*?<!-- /onda8:hero-contatos -->)', re.S)

CSS = """/* S-34: legibilidade do hero sobre a foto da lampada. Vidro fosco branco
   translucido — pedido explicito de "fundo com um branco transparente". */
.hero-texto{
  display:inline-block;max-width:780px;
  background:rgba(255,255,255,.10);
  -webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);
  border-radius:14px;padding:26px 30px;margin-left:-30px}
.banner--malha .hero-numeros{
  background:rgba(255,255,255,.10);
  -webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);
  border-radius:14px;padding:20px 24px}"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alvo = os.path.join(pub, "wp-content", "uploads", "2026", "07", "onda6", "lampada-hero.jpg")
    if not os.path.exists(alvo):
        raise SystemExit("ERRO: lampada-hero.jpg ausente em onda6/")
    mudou = escrever_bloco_css(pub, "hero-scrims", CSS, onda="onda15")
    print("bloco onda15:hero-scrims %s" % ("gravado" if mudou else "ja estava igual"))
    alterados = []
    for rel in HOMES:
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        novo = h.replace("onda6/malha-hero.jpg", "onda6/lampada-hero.jpg")
        if "onda15:hero-texto" not in novo:
            novo = REX_TEXTO.sub(
                r'<!-- onda15:hero-texto --><div class="hero-texto">\1'
                r'</div><!-- /onda15:hero-texto -->', novo, count=1)
        if novo != h:
            gravar(p, novo)
            alterados.append(rel)
    print("paginas alteradas: %s" % (", ".join(alterados) or "nenhuma (ja estava igual)"))


if __name__ == "__main__":
    main()
