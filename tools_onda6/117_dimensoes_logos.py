# -*- coding: utf-8 -*-
"""Onda 60 (PageSpeed 18/08): width/height nos logos da barra de clientes (CLS).

ESCOPO DELIBERADAMENTE ESTREITO. O relatorio lista 27 imagens sem dimensao, e o
site tem 446 <img> sem width/height em 138 arquivos distintos. Mas o proprio
relatorio MEDIU quem causa o deslocamento:

    "Dexco"  <li class="clientes-logos__item">   0.015   <- de um CLS total de 0.023
    o <p> do hero                                0.008
    o selo "AI POWERED"                          0.000

Os certificados do carrossel e os cards de lider contribuem 0.000 — estao abaixo da
dobra. Mexer neles seria risco visual sem ganho medido. Entao aqui entra so a barra
de logos, que e o culpado real.

COMO AS DIMENSOES SAO OBTIDAS: lidas do PROPRIO arquivo em disco a cada run
(IHDR do PNG, viewBox ou width/height do SVG). Nenhuma tabela de valores no script
— se um logo for trocado, o run seguinte corrige sozinho. Evita "valores gemeos".

POR QUE NAO MUDA PIXEL: o CSS da barra usa so `max-height`/`max-width`
(.clientes-logos__item img{max-height:24px;max-width:104px}), sem width/height fixos.
Declarar a dimensao natural e dizer ao navegador exatamente o que ele descobriria ao
baixar o arquivo — a caixa renderizada continua a mesma, mas ele ja reserva o espaco
antes de a imagem chegar, e o texto ao lado para de pular.

Idempotente: 2o run reporta 0 mudancas.
"""
import io
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public

RE_ITEM = re.compile(r'<li class="clientes-logos__item[^"]*">\s*<img\b[^>]*>', re.S)
RE_IMG = re.compile(r'<img\b[^>]*>')
RE_SRC = re.compile(r'src="([^"]+)"')


def dimensoes(caminho):
    """(w, h) inteiros do arquivo real, ou None se nao der para determinar."""
    ext = os.path.splitext(caminho)[1].lower()
    if ext == ".png":
        with io.open(caminho, "rb") as f:
            d = f.read(33)
        if d[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        w, h = struct.unpack(">II", d[16:24])
        return int(w), int(h)
    if ext == ".svg":
        with io.open(caminho, encoding="utf-8", errors="ignore") as f:
            cabeca = f.read(4000)
        m = re.search(r'viewBox="\s*[-\d.]+[,\s]+[-\d.]+[,\s]+([\d.]+)[,\s]+([\d.]+)', cabeca)
        if m:
            return int(round(float(m.group(1)))), int(round(float(m.group(2))))
        mw = re.search(r'<svg[^>]*\bwidth="([\d.]+)', cabeca)
        mh = re.search(r'<svg[^>]*\bheight="([\d.]+)', cabeca)
        if mw and mh:
            return int(round(float(mw.group(1)))), int(round(float(mh.group(1))))
    return None


def main(raiz):
    pub = resolve_public(raiz)
    tocados = 0
    sem_dim = set()
    total_img = 0
    for dp, _d, fs in os.walk(pub):
        if os.sep + ".git" in dp:
            continue
        for nome in fs:
            if not nome.endswith(".html"):
                continue
            fp = os.path.join(dp, nome)
            with io.open(fp, encoding="utf-8") as f:
                h = f.read()
            if "clientes-logos__item" not in h:
                continue
            orig = h

            def trata_item(m):
                bloco = m.group(0)
                img = RE_IMG.search(bloco)
                if not img:
                    return bloco
                tag = img.group(0)
                if " width=" in tag and " height=" in tag:
                    return bloco
                src = RE_SRC.search(tag)
                if not src:
                    return bloco
                rel = src.group(1).split("?")[0].lstrip("/")
                caminho = os.path.join(pub, rel.replace("/", os.sep))
                if not os.path.exists(caminho):
                    sem_dim.add(rel)
                    return bloco
                dim = dimensoes(caminho)
                if not dim:
                    sem_dim.add(rel)
                    return bloco
                nova = tag[:-1].rstrip() + ' width="%d" height="%d">' % dim
                return bloco.replace(tag, nova)

            h = RE_ITEM.sub(trata_item, h)
            if h != orig:
                with io.open(fp, "w", encoding="utf-8", newline="") as f:
                    f.write(h)
                tocados += 1
                total_img += len(RE_ITEM.findall(h))
    print("paginas alteradas: %d" % tocados)
    if sem_dim:
        print("sem dimensao determinavel (deixados como estavam):")
        for r in sorted(sem_dim):
            print("  %s" % r)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
