# -*- coding: utf-8 -*-
u"""130 — issue #242: os logos dos veículos novos da onda 65.

As 14 matérias da #237 trouxeram dez veículos que nunca apareceram na página.
Um deles (Broadcast) é a agência do grupo Estadão e usa `estadao.svg`, que já
existe. Dos nove restantes, **oito têm asset oficial** e um não:

    Exame ............... SVG inline do header (id="logo-exame", fill #e11d22)
    TN Petróleo ......... logo-tn-topo.png do header
    Cenário Energia ..... New_Logo-Colorida-Fundo-Transparente (uploads/2025/01)
    Logweb .............. logweb-logo.png (JSON-LD Organization.logo)
    Balcão Automotivo ... Novo-Logo-Balcao-RGB-1024x374.png do header
    Youtopia ............ Logo_Youtopia.png (storage.ghost.io)
    AutoIndústria ....... Autoindustria_Logo.png do header
    Ipesi ............... logo_ipesi.png do header
    Revista Amazônia .... NÃO TEM — ver abaixo

**Revista Amazônia vai de fallback de texto, de propósito.** O site dela publica
só o wordmark BRANCO (`Amazonia-logo-BRANCA-300x95-1.webp`), porque o header dela
é escuro; numa lista de fundo branco ele é invisível. As alternativas eram usar o
avatar quadrado 500x500 (que num slot de 176x52 renderiza a 52x52, fora do padrão
dos outros wordmarks) ou **inverter a marca do veículo** — e inverter a marca de
terceiro não é nossa decisão. O fallback tipográfico já existe e já está no ar em
três veículos (epbr, CZ Insights, Money Times).

O QUE ESTE SCRIPT FAZ COM O QUE BAIXA
-------------------------------------
Raster vira **WebP na dimensão EXATA do original** — só troca de formato, nunca de
dimensão. É a regra que a onda 62c estabeleceu, e ela não é zelo: na onda 61, gerar
o logo da EDP a "3x o exibido" derrubou a largura renderizada de 81,38 para 81,00 px,
porque depois do load quem define a caixa é o **aspecto real do arquivo**, não os
atributos `width`/`height` — e, com a fileira centrada, sete logos que ninguém tocou
mudaram de antialiasing. Mantendo a dimensão idêntica, essa classe não pode
acontecer.

O SVG da Exame é normalizado: o `fill` sai do `<svg>` e passa para o `<path>` (a
cor não pode depender de estilo do root nem da classe `cls-1`, cujo CSS mora no
site deles), entram `width`/`height` do viewBox, e saem as classes do Tailwind.

Idempotente: arquivo que já existe no destino não é rebaixado.

Uso: python tools_onda6/130_imprensa_logos_novos.py <raiz-que-contem-public>
"""
import io
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public  # noqa: E402

UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/127 Safari/537.36")}

DIR_LOGOS = os.path.join("wp-content", "uploads", "2026", "08", "imprensa-logos")

# (arquivo destino, url de origem, nota de proveniencia para o mestre P3)
RASTER = [
    ("tnpetroleo.webp",
     "https://tnpetroleo.com.br/static/css/img/logo-tn-topo.png",
     u"tnpetroleo.com.br/static/css/img/logo-tn-topo.png (logo do header oficial)"),
    ("cenarioenergia.webp",
     "https://cenarioenergia.com.br/wp-content/uploads/2025/01/"
     "New_Logo-Colorida-Fundo-Transparente-300x117-transformed__1_-"
     "removebg-preview-1-e1768267930282.png",
     u"cenarioenergia.com.br/wp-content/uploads/2025/01/New_Logo-Colorida-"
     u"Fundo-Transparente (versão colorida do header; a outra é branca)"),
    ("logweb.webp",
     "https://logweb.com.br/wp-content/uploads/2023/05/logweb-logo.png",
     u"logweb.com.br/wp-content/uploads/2023/05/logweb-logo.png "
     u"(JSON-LD Organization.logo)"),
    ("balcaoautomotivo.webp",
     "https://www.balcaoautomotivo.com/wp-content/uploads/2021/06/"
     "Novo-Logo-Balcao-RGB-1024x374.png",
     u"balcaoautomotivo.com/wp-content/uploads/2021/06/"
     u"Novo-Logo-Balcao-RGB-1024x374.png (logo do header oficial)"),
    ("youtopia.webp",
     "https://storage.ghost.io/c/0c/ce/0cceb189-436d-4289-aa24-ba16ceb9a983/"
     "content/images/2025/01/Logo_Youtopia.png",
     u"storage.ghost.io/.../content/images/2025/01/Logo_Youtopia.png "
     u"(JSON-LD Organization.logo)"),
    ("autoindustria.webp",
     "https://www.autoindustria.com.br/wp-content/uploads/2017/05/"
     "Autoindustria_Logo.png",
     u"autoindustria.com.br/wp-content/uploads/2017/05/Autoindustria_Logo.png "
     u"(logo do header oficial)"),
    ("ipesi.webp",
     "https://ipesi.com.br/wp-content/uploads/2018/10/logo_ipesi.png",
     u"ipesi.com.br/wp-content/uploads/2018/10/logo_ipesi.png "
     u"(logo do header oficial)"),
]

EXAME_HOME = "https://exame.com/"
EXAME_NOTA = (u"SVG inline do header de exame.com (id=\"logo-exame\", "
              u"fill #e11d22), extraído em 2026-08-19; fill movido para o "
              u"<path> e width/height derivados do viewBox")

TETO = 120 * 1024  # mesmo piso da S160/S163: PNG/WebP referenciado não passa disso


def baixar(url, limite=8 * 1024 * 1024):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=45).read(limite)


def para_webp(bruto, destino):
    u"""Grava WebP na dimensão EXATA do original. Devolve (w, h, bytes)."""
    from PIL import Image
    im = Image.open(io.BytesIO(bruto))
    w, h = im.size
    if im.mode not in ("RGBA", "RGB"):
        im = im.convert("RGBA" if "A" in im.mode or im.mode == "P" else "RGB")
    im.save(destino, "WEBP", quality=92, method=6)
    depois = Image.open(destino)
    if depois.size != (w, h):
        raise SystemExit(u"dimensão mudou em %s: %s -> %s"
                         % (os.path.basename(destino), (w, h), depois.size))
    return w, h, os.path.getsize(destino)


REX_SVG_EXAME = re.compile(r'<svg[^>]*id="logo-exame".*?</svg>', re.S)


def normalizar_exame(html):
    m = REX_SVG_EXAME.search(html)
    if not m:
        raise SystemExit(u"não achei o <svg id=\"logo-exame\"> na home da Exame")
    svg = m.group(0)
    vb = re.search(r'viewBox="([\d.\s-]+)"', svg)
    if not vb:
        raise SystemExit(u"SVG da Exame sem viewBox")
    partes = vb.group(1).split()
    largura, altura = partes[2], partes[3]
    cor = re.search(r'fill:\s*(#[0-9a-fA-F]{3,6})', svg)
    if not cor:
        raise SystemExit(u"SVG da Exame sem fill no root — a cor viria da folha "
                         u"externa deles e o arquivo sairia preto")
    # a cor passa para o path: nao pode depender do style do root nem da classe
    # cls-1, cuja regra mora no CSS do site deles
    svg = re.sub(r'<path\b', '<path fill="%s"' % cor.group(1), svg, count=1)
    # fora as classes do Tailwind e o style do root; entram width/height
    svg = re.sub(r'\sclass="[^"]*"', '', svg, count=1)
    svg = re.sub(r'\sstyle="[^"]*"', '', svg, count=1)
    svg = svg.replace('<svg ', '<svg width="%s" height="%s" ' % (largura, altura), 1)
    svg = re.sub(r'\sclass="cls-1"', '', svg)
    return svg


def main(argv):
    pub = resolve_public(argv[1] if len(argv) > 1 else ".")
    dest_dir = os.path.join(pub, DIR_LOGOS)
    if not os.path.isdir(dest_dir):
        raise SystemExit(u"não achei %s" % dest_dir)

    novos, pulados, notas = 0, 0, []

    for arq, url, nota in RASTER:
        p = os.path.join(dest_dir, arq)
        if os.path.exists(p):
            print(u"  = %s (já existe)" % arq)
            pulados += 1
            continue
        try:
            bruto = baixar(url)
        except Exception as e:
            print(u"  ! %s: download falhou (%s)" % (arq, str(e)[:70]))
            continue
        w, h, tam = para_webp(bruto, p)
        if tam > TETO:
            os.remove(p)
            print(u"  ! %s: %d KB acima do teto de 120 KB — descartado" % (arq, tam // 1024))
            continue
        print(u"  + %s  %dx%d  %d bytes (origem: %d bytes)"
              % (arq, w, h, tam, len(bruto)))
        novos += 1
        notas.append((arq, nota))

    # Exame: SVG inline do header
    p = os.path.join(dest_dir, "exame.svg")
    if os.path.exists(p):
        print(u"  = exame.svg (já existe)")
        pulados += 1
    else:
        try:
            raw = baixar(EXAME_HOME, limite=2 * 1024 * 1024)
            html = raw.decode("utf-8", "replace")
            svg = normalizar_exame(html)
            io.open(p, "w", encoding="utf-8", newline="").write(svg)
            # rele o que gravou (licao da onda 60b: nao declarar, medir)
            de_volta = io.open(p, encoding="utf-8").read()
            if "logo-exame" not in de_volta or "fill=" not in de_volta:
                raise SystemExit(u"exame.svg gravado sem id ou sem fill")
            print(u"  + exame.svg  %d bytes" % os.path.getsize(p))
            novos += 1
            notas.append(("exame.svg", EXAME_NOTA))
        except SystemExit:
            raise
        except Exception as e:
            print(u"  ! exame.svg: %s" % str(e)[:90])

    print(u"\n%d logo(s) novo(s), %d já existente(s)" % (novos, pulados))
    if notas:
        print(u"\nProveniência para o mestre P3 "
              u"(08_Site/2026-08-06_imprensa-veiculos-curadoria.json):")
        for arq, nota in notas:
            print(u"  %-24s %s" % (arq, nota))
    print(u"\nRevista Amazônia fica com arquivo: null (fallback de texto) — o site "
          u"dela só publica wordmark BRANCO, invisível em fundo branco.")


if __name__ == "__main__":
    main(sys.argv)
