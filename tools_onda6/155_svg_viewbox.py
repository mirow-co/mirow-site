# -*- coding: utf-8 -*-
"""Onda 80: normaliza os SVG dos logos para que ELES POSSAM ESCALAR.

    python tools_onda6/155_svg_viewbox.py .

O DEFEITO QUE ORIGINOU ESTE SCRIPT
----------------------------------
O Mario abriu o staging da onda 79 e disse: "os logos estao cortados. mckinsey
nao da para ler dentro da caixinha, nem o logo da aracruz, nem booz allen, nem
tu berlin, puc rio". Medido no navegador (nao lido do CSS):

    tags dos logos        -> svg, IMG      <-- o tema troca <img> por <svg> inline
    caixas dos primeiros  -> 24x16 42x16 88x16 17x16 ...
    viewBox dos injetados -> "sem viewBox" em 4 dos 5 primeiros
    overflow computado    -> hidden

Ou seja: 11 dos 21 arquivos SVG vinham da origem com `width`/`height` fixos e SEM
`viewBox`. SVG inline sem viewBox **nao tem como escalar** -- nao existe sistema
de coordenadas a mapear para a caixa. Entao `height:16px` nao reduz o desenho:
recorta, porque o `overflow` do svg e `hidden`. O McKinsey de 360x45 aparecia
como os 88x16 pixels do canto superior esquerdo dele.

Isso e o erro 17 do CLAUDE.md numa forma nova: o `object-fit:contain` que eu
escrevi na onda 78 mede o efeito certo -- **em `<img>`**. Quando o tema promove a
imagem a SVG inline, `object-fit` deixa de existir e a regra vira decoracao. A
V42 media que os 26 logos apareciam; nao media se apareciam INTEIROS.

O CONSERTO, na raiz
-------------------
Para cada .svg da pasta de logos:
  1. se o <svg> nao tem `viewBox` mas tem `width`/`height` numericos, escreve
     `viewBox="0 0 W H"` a partir deles -- a caixa que o proprio arquivo declara;
  2. REMOVE `width` e `height` do <svg> raiz.

O passo 2 nao e cosmetico e e o que quase todo mundo esquece: com viewBox E
width=360 no atributo, `width:auto` do CSS resolve para os 360px do atributo, e o
desenho fica encolhido dentro de uma caixa larga e vazia -- some do mesmo jeito,
por outro caminho. Sem os atributos, a razao de aspecto vem do viewBox e o
`height` do CSS manda.

O que ele NAO faz: nao mexe no desenho, nao recorta margem interna, nao troca
cor. Arquivo que ja tem viewBox e nao tem width/height sai intacto (idempotente).
"""
import io
import os
import re
import sys

PASTA = os.path.join("wp-content", "uploads", "2026", "08", "onda79", "logos")

RE_SVG = re.compile(r"<svg\b[^>]*>", re.S | re.I)
RE_VB = re.compile(r'\bviewBox\s*=\s*"([^"]*)"', re.I)


def _num(tag, attr):
    """Le width/height do atributo, aceitando unidade (px, pt) e decimal."""
    m = re.search(r'\b' + attr + r'\s*=\s*"\s*([0-9.]+)\s*(?:px|pt)?\s*"', tag, re.I)
    if not m:
        return None
    try:
        v = float(m.group(1))
    except ValueError:
        return None
    return v if v > 0 else None


def normalizar(tag):
    """Devolve a tag <svg> com viewBox garantido e sem width/height. Ou None."""
    novo = tag
    if not RE_VB.search(novo):
        w, h = _num(novo, "width"), _num(novo, "height")
        if w is None or h is None:
            return None  # sem viewBox e sem medida: nao ha como inferir; deixa quieto
        vb = 'viewBox="0 0 %s %s"' % (_fmt(w), _fmt(h))
        novo = novo[:4] + " " + vb + novo[4:]
    for attr in ("width", "height"):
        novo = re.sub(r'\s+' + attr + r'\s*=\s*"[^"]*"', "", novo, flags=re.I)
    return novo if novo != tag else None


def _fmt(v):
    return ("%.6f" % v).rstrip("0").rstrip(".") if v != int(v) else str(int(v))


def main(raiz):
    pasta = os.path.join(os.path.abspath(raiz), "public", PASTA)
    if not os.path.isdir(pasta):
        print(u"155: pasta de logos ausente (%s)" % PASTA)
        return 0
    mudados, ja, sem_medida = 0, 0, []
    for nome in sorted(os.listdir(pasta)):
        if not nome.lower().endswith(".svg"):
            continue
        p = os.path.join(pasta, nome)
        with io.open(p, encoding="utf-8", errors="replace") as f:
            texto = f.read()
        m = RE_SVG.search(texto)
        if not m:
            sem_medida.append(nome)
            continue
        nova = normalizar(m.group(0))
        if nova is None:
            if RE_VB.search(m.group(0)):
                ja += 1
            else:
                sem_medida.append(nome)
            continue
        with io.open(p, "w", encoding="utf-8", newline="") as f:
            f.write(texto[:m.start()] + nova + texto[m.end():])
        mudados += 1
        print(u"  %-28s viewBox garantido, width/height fora" % nome)
    print(u"155: %d svg normalizado(s), %d ja estava(m) ok" % (mudados, ja))
    for n in sem_medida:
        print(u"   SEM MEDIDA (nao da para inferir viewBox): %s" % n)
    return mudados


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
