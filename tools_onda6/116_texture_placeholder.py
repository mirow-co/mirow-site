# -*- coding: utf-8 -*-
"""Onda 60 (PageSpeed 18/08): mata o unico erro de console — 404 de texture-7.png.

DIAGNOSTICO (medido, nao suposto):
- O CSS do TEMA pede `url("../resources/images//texture-7.png")` em **22 lugares**
  (.wrap-gradient-1, .wrap-gradient-2, .home-experience::after, .menu__nav,
  .menu__nav-submenu>div, .page-insights__list-item, .blog-single__content, ...).
- O arquivo NUNCA foi espelhado: `themes/mirow/resources/images/` so tem
  icon-search.svg, nao esta em nenhum commit do repo, e responde 404 no ar.
- Nosso onda6.css NAO pede o arquivo — ali `texture-7` aparece apenas dentro de um
  COMENTARIO que documenta o que o tema faz. (Correcao de um diagnostico meu
  anterior, que confiou num grep sem distinguir comentario de declaracao viva.)

POR QUE PLACEHOLDER, E NAO CSS:
- Zerar `background-image` nao serve: em 12 dos 22 seletores a imagem divide a
  declaracao com um `linear-gradient(...)`, e gradiente TAMBEM e background-image —
  zerar mataria o gradiente. Re-declarar cada um copiaria valor do tema para o nosso
  CSS, criando "valores gemeos" (a classe de bug das ondas 31 e 35).
- Como a textura nunca carregou, TODO o visual aprovado em 59 ondas ja e o visual
  sem ela. Um PNG 1x1 totalmente transparente e, por construcao, pixel-identico ao
  que esta no ar hoje — e remove o 404.

SE A TEXTURA ORIGINAL APARECER: trocar este arquivo pela real muda o visual de 22
seletores de uma vez. Isso passa a ser decisao do Mario, nao conserto de bug.

Idempotente: nao reescreve se o placeholder ja estiver la.
"""
import base64
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public

# PNG 1x1, RGBA, alfa 0 (70 bytes). Com background-size:cover, nao pinta nada.
PNG_1X1_TRANSPARENTE = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
    "z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")

# GIF 1x1 transparente (43 bytes) — mesmo papel, para as referencias .gif
GIF_1X1_TRANSPARENTE = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")

# SVG vazio com viewBox valido — nao desenha nada
SVG_VAZIO = (u'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">'
             u'<!-- placeholder: asset original nao espelhado (onda 60) --></svg>'
             ).encode("utf-8")

# Todos os assets que o CSS pede e que NUNCA foram espelhados. A assercao S157
# desta mesma onda encontrou os tres ultimos — o PageSpeed so viu o texture-7,
# porque os outros so sao buscados nas paginas com formulario.
FALTANTES = [
    # (caminho relativo a public/, conteudo, por que placeholder e seguro)
    (("wp-content", "themes", "mirow", "resources", "images", "texture-7.png"),
     PNG_1X1_TRANSPARENTE,
     u"textura de fundo pedida por 22 seletores do tema; unico erro de console "
     u"do relatorio de 18/08"),
    (("wp-content", "themes", "mirow", "resources", "images", "form-success.gif"),
     GIF_1X1_TRANSPARENTE,
     u"icone de sucesso do formulario"),
    (("wp-content", "themes", "mirow", "resources", "images", "form-select-arrow.svg"),
     SVG_VAZIO,
     u"seta do <select>; hoje os selects ja aparecem sem seta, e este placeholder "
     u"mantem exatamente isso"),
    (("wp-content", "plugins", "formidable", "images", "ajax_loader.gif"),
     GIF_1X1_TRANSPARENTE,
     u"spinner do plugin de formulario, ainda carregado em 55 paginas"),
]


def main(raiz):
    pub = resolve_public(raiz)
    gravados = 0
    for partes, conteudo, motivo in FALTANTES:
        rel = "/".join(partes)
        alvo = os.path.join(pub, *partes)
        pasta = os.path.dirname(alvo)
        if not os.path.isdir(pasta):
            os.makedirs(pasta)
            print("criada a pasta %s" % os.path.relpath(pasta, pub).replace(os.sep, "/"))
        if os.path.exists(alvo):
            with io.open(alvo, "rb") as f:
                atual = f.read()
            if atual == conteudo:
                continue
            print("ATENCAO: %s existe e NAO e o placeholder — nao sobrescrevo." % rel)
            print("         Se for o asset real, o 404 ja esta resolvido.")
            continue
        with io.open(alvo, "wb") as f:
            f.write(conteudo)
        gravados += 1
        print("placeholder gravado: %s (%d bytes) — %s" % (rel, len(conteudo), motivo))
    print("placeholders novos: %d (de %d assets faltantes)" % (gravados, len(FALTANTES)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
