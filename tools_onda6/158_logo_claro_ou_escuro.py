# -*- coding: utf-8 -*-
"""Onda 83: decide, MEDINDO, se cada logo precisa de placa branca ou nao.

    python tools_onda6/158_logo_claro_ou_escuro.py .

O DEFEITO
---------
O Mario: "ta sem link visivel no ufrj, chicago booth, malik".

Medido: `ufrj.webp` e `malik.webp` tem **0,0% de pixel escuro** quando compostos
sobre branco -- sao a versao NEGATIVA da marca, arte branca. E os dois estavam
numa placa branca. Branco sobre branco: o chip mostra o nome e um retangulo
vazio ao lado.

O que torna isso pior que um descuido: o CSS da onda 79 tem a classe
`.onda78-inst__logo--claro{background:transparent}` -- exatamente para este caso
-- e um comentario meu dizendo que "a classificacao saiu de MEDICAO de
luminancia, nao de olhometro". **Nao havia classificacao nenhuma.** Nenhuma
linha de codigo aplicava aquela classe. Eu documentei um mecanismo que nao
existia, que e o modo mais caro de errar: quem ler o comentario para de procurar.

O CONSERTO
----------
A classificacao passa a existir, e a medir o arquivo:

  raster  -> compoe sobre branco e conta pixel escuro (media RGB < 200). Sem
             compor, o RGB debaixo de pixel transparente nao significa nada --
             licao da onda 62c.
  vetor   -> le as cores de `fill=` e do que sobrou de `<style>` (nenhum, depois
             da onda 80) e olha a tinta que NAO e branca.

Logo com menos de 3% de tinta escura e CLARO: vai sem placa, direto sobre o card
escuro. O resto ganha a placa branca.

O resultado nao e escrito aqui: e devolvido ao 152, que monta o chip. Este
modulo e so a medida, para poder ser testado sozinho e usado pela assercao.
"""
import io
import os
import re
import sys

LIMIAR_ESCURO = 200      # media RGB abaixo disso conta como tinta visivel no branco
LIMIAR_CLARO = 3.0       # % de tinta escura abaixo do qual o logo e "claro"

RE_FILL = re.compile(r'fill\s*[=:]\s*["\']?\s*(#[0-9A-Fa-f]{3,8}|rgb\([^)]*\)|[a-z]+)')


def _luminancia_hex(cor):
    c = cor.strip().lower()
    if c in ("none", "transparent", "currentcolor", "inherit"):
        return None
    nomes = {"white": 255, "black": 0, "red": 76, "blue": 29, "gray": 128, "grey": 128}
    if c in nomes:
        return nomes[c]
    m = re.match(r"^#([0-9a-f]{3})$", c)
    if m:
        r, g, b = (int(x * 2, 16) for x in m.group(1))
        return (r + g + b) / 3.0
    m = re.match(r"^#([0-9a-f]{6})", c)
    if m:
        v = m.group(1)
        return (int(v[0:2], 16) + int(v[2:4], 16) + int(v[4:6], 16)) / 3.0
    m = re.match(r"^rgb\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)", c)
    if m:
        return (int(m.group(1)) + int(m.group(2)) + int(m.group(3))) / 3.0
    return None


def tinta_escura(path):
    """% da area do logo que aparece como tinta escura sobre fundo branco.

    Devolve None quando nao consegue medir -- e quem chama trata "nao medi" como
    diferente de "medi e deu zero" (R13, regra 2).
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == ".svg":
        try:
            with io.open(path, encoding="utf-8", errors="replace") as f:
                svg = f.read()
        except Exception:
            return None
        lums = [l for l in (_luminancia_hex(c) for c in RE_FILL.findall(svg))
                if l is not None]
        if not lums:
            # sem fill declarado, o SVG desenha em preto (default do formato)
            return 100.0
        escuras = [l for l in lums if l < LIMIAR_ESCURO]
        return 100.0 * len(escuras) / len(lums)
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        im = Image.open(path).convert("RGBA")
    except Exception:
        return None
    fundo = Image.new("RGB", im.size, (255, 255, 255))
    fundo.paste(im, mask=im)
    dados = list(fundo.getdata())
    if not dados:
        return None
    escuros = sum(1 for r, g, b in dados if (r + g + b) / 3.0 < LIMIAR_ESCURO)
    return 100.0 * escuros / len(dados)


def e_claro(path):
    """True quando o logo e arte clara e NAO deve receber a placa branca."""
    t = tinta_escura(path)
    if t is None:
        return False          # nao medi -> placa, que e o caso seguro
    return t < LIMIAR_CLARO


def main(raiz):
    pasta = os.path.join(os.path.abspath(raiz), "public", "wp-content", "uploads",
                         "2026", "08", "onda79", "logos")
    if not os.path.isdir(pasta):
        print(u"158: pasta de logos ausente")
        return 0
    claros = []
    print(u"%-30s %8s  %s" % ("arquivo", "tinta", "placa"))
    for nome in sorted(os.listdir(pasta)):
        if os.path.splitext(nome)[1].lower() not in (".svg", ".webp", ".png", ".jpg"):
            continue
        p = os.path.join(pasta, nome)
        t = tinta_escura(p)
        claro = e_claro(p)
        if claro:
            claros.append(nome)
        print(u"%-30s %7s  %s" % (nome, "?" if t is None else "%.1f%%" % t,
                                  u"SEM placa (arte clara)" if claro else u"branca"))
    print(u"\n158: %d logo(s) claro(s), que iriam sumir numa placa branca: %s"
          % (len(claros), ", ".join(claros) or u"nenhum"))
    return len(claros)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
