# -*- coding: utf-8 -*-
u"""136 — issue #241: recuperado 1 dos 2 links que faltavam na imprensa.

Uso: python tools_onda6/136_imprensa_transporte_moderno.py <raiz-que-contem-public>

O QUE FOI RECUPERADO
--------------------
O consolidado do Felipe registrava, sem link: *"06/02/2026 — a confirmar — Juros
altos levam montadoras de caminhões a…"*, com a nota de que só existia o post do
LinkedIn.

Achado e conferido em 19/08/2026:

    Transporte Moderno · 30/01/2026 · "Juros altos levam montadoras de caminhões
    a rever estoques e destravar capital de giro"
    https://transportemoderno.com.br/2026/01/30/juros-altos-levam-montadoras-de-
    caminhoes-a-rever-estoques-e-destravar-capital-de-giro/

**A data era outra.** O consolidado dizia 06/02/2026 — essa é a data do post no
LinkedIn, não da matéria. O artigo saiu em **30/01/2026 às 14h00** (atualizado em
16/02). Vai ao ar a data da publicação.

**Elmar Gans é citado nominalmente, em cinco falas** — não é menção de passagem:

* *"Estudos conduzidos pela Mirow & Co. em montadoras de veículos leves e pesados
  indicam que até 20% dos volumes estocados podem ser eliminados"*
* *"Historicamente, as montadoras mantêm estoques com cobertura acima do
  necessário…"*
* *"Prevalecia a cultura do 'melhor sobrar do que faltar'…"*
* *"Há estoques com R$ 400 milhões em reposição que podem continuar entregando os
  mesmos resultados operando com R$ 70 milhões a menos"*
* *"Com a eletrificação, haverá uma troca grande de modelos em circulação…"*

O SINDIPESA republicou em 02/02/2026 e é onde a busca acha primeiro; entra o
**original**, não a republicação — pela mesma razão que a S165 existe: o veículo
declarado tem de bater com quem publicou.

O QUE NÃO FOI RECUPERADO
------------------------
**07/10/2025, O Globo**, sobre o cruzamento dos setores elétrico e automotivo.
Sei qual é o estudo — o de eletrificação feito com a Acende Brasil, R$ 200 bi/ano,
que teve repercussão ampla em out/2025 (Correio de Minas, canalve, Revelator,
Agência iNFRA, Transpoquip). **O que não consegui é a URL do O Globo:** o
`globo.com` bloqueia o crawler de busca, e a busca interna do site não devolve
resultado por `curl`. Publicar uma republicação no lugar seria rotular errado.

Fica na #241 com dois caminhos que dependem de acesso que eu não tenho: o post
original no LinkedIn da firma (costuma trazer o link no comentário) ou a busca do
Globo logado.

Idempotente: se a URL já estiver no mestre, reporta 0 mudanças.
"""
import io
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public  # noqa: E402

UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127 Safari/537.36")}

BASE_MESTRE = os.path.join(
    os.path.expanduser("~"), "OneDrive - Mirow", "Mirow & Co", "05_Marketing",
    "05_NovoMarketing", "08_Site")
M_MATERIAS = os.path.join(BASE_MESTRE, "2026-08-19_imprensa-materias-curadoria.json")
M_VEICULOS = os.path.join(BASE_MESTRE, "2026-08-06_imprensa-veiculos-curadoria.json")

DIR_LOGOS = os.path.join("wp-content", "uploads", "2026", "08", "imprensa-logos")

URL = ("https://transportemoderno.com.br/2026/01/30/juros-altos-levam-montadoras-"
       "de-caminhoes-a-rever-estoques-e-destravar-capital-de-giro/")

MATERIA = {
    "data": "2026-01-30",
    "veiculo": u"Transporte Moderno",
    "titulo": (u"Juros altos levam montadoras de caminhões a rever estoques e "
               u"destravar capital de giro"),
    "url": URL,
    "quem": u"Elmar Gans",
    "tema": u"Automotivo",
    "verificado": "lido",
    "fonte_do_titulo": u"og:title medido em 2026-08-19",
    "nota": (u"issue #241: o consolidado do Felipe registrava este item sem link e "
             u"datado 06/02/2026 — essa era a data do post no LinkedIn. A matéria "
             u"saiu em 30/01/2026 às 14h00 (atualizada em 16/02). Elmar Gans é "
             u"citado nominalmente em cinco falas, com números próprios (até 20% "
             u"do volume estocado eliminável; estoque de R$ 400 mi operando com "
             u"R$ 70 mi a menos). O SINDIPESA republicou em 02/02 e é o que a "
             u"busca acha primeiro; entra o original."),
}

LOGO = {
    "nome": u"Transporte Moderno",
    "arquivo": "transportemoderno.webp",
    "origem": "https://storage.transportemoderno.com.br/uploads/2015/03/tm_logo1.png",
    "fonte": (u"storage.transportemoderno.com.br/uploads/2015/03/tm_logo1.png "
              u"(logo do header oficial), convertido para WebP na dimensão exata"),
}

TETO = 120 * 1024


def baixar_logo(pub):
    destino = os.path.join(pub, DIR_LOGOS, LOGO["arquivo"])
    if os.path.exists(destino):
        print(u"  = %s (ja existe)" % LOGO["arquivo"])
        return True
    try:
        bruto = urllib.request.urlopen(
            urllib.request.Request(LOGO["origem"], headers=UA), timeout=45).read()
    except Exception as e:
        print(u"  ! logo nao baixou (%s) — o veiculo entra com wordmark de texto"
              % str(e)[:60])
        return False
    from PIL import Image
    im = Image.open(io.BytesIO(bruto))
    w, h = im.size
    if im.mode == "P" or "A" in im.mode:
        im = im.convert("RGBA")
    elif im.mode != "RGB":
        im = im.convert("RGB")
    im.save(destino, "WEBP", quality=92, method=6)
    depois = Image.open(destino)
    if depois.size != (w, h):
        os.remove(destino)
        raise SystemExit(u"dimensao mudou: %s -> %s" % ((w, h), depois.size))
    tam = os.path.getsize(destino)
    if tam > TETO:
        os.remove(destino)
        print(u"  ! logo com %d KB, acima do teto — vai de texto" % (tam // 1024))
        return False
    # a licao do caso Revista Amazonia: logo branco e invisivel em fundo branco
    fundo = Image.new("RGB", depois.size, (255, 255, 255))
    conv = depois.convert("RGBA")
    fundo.paste(conv, mask=conv.split()[-1])
    px = fundo.load()
    passo = max(1, min(w, h) // 120)
    total = tinta = 0
    for y in range(0, h, passo):
        for x in range(0, w, passo):
            r, g, b = px[x, y]
            total += 1
            if (255 - r) + (255 - g) + (255 - b) > 60:
                tinta += 1
    frac = float(tinta) / total if total else 0.0
    print(u"  + %s  %dx%d  %d bytes  tinta sobre branco %.1f%%"
          % (LOGO["arquivo"], w, h, tam, frac * 100))
    if frac < 0.01:
        os.remove(destino)
        print(u"  ! invisivel em fundo branco — descartado, vai de texto")
        return False
    return True


def main(argv):
    pub = resolve_public(argv[1] if len(argv) > 1 else ".")
    tem_logo = baixar_logo(pub)

    # --- mestre de veiculos
    with io.open(M_VEICULOS, encoding="utf-8") as f:
        vei = json.load(f)
    if LOGO["nome"] not in [v["nome"] for v in vei["veiculos"]]:
        vei["veiculos"].append({"nome": LOGO["nome"],
                                "arquivo": LOGO["arquivo"] if tem_logo else None,
                                "fonte": LOGO["fonte"] if tem_logo else
                                u"logo nao obtido em 19/08/2026 — wordmark de texto"})
        vei["veiculos"].sort(key=lambda v: v["nome"].lower())
        vei["_atualizado"] = "2026-08-19"
        with io.open(M_VEICULOS, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(vei, ensure_ascii=False, indent=1) + u"\n")
        print(u"  + veiculo no mestre de logos")
    else:
        print(u"  = veiculo ja estava no mestre de logos")

    # --- mestre de materias
    with io.open(M_MATERIAS, encoding="utf-8") as f:
        mat = json.load(f)
    if URL in [m["url"] for m in mat["materias"]]:
        print(u"  = materia ja estava no mestre")
        return
    mat["materias"].append(MATERIA)
    mat["materias"].sort(key=lambda x: (x["data"], x["veiculo"]), reverse=True)
    mat["_atualizado"] = "2026-08-19"
    with io.open(M_MATERIAS, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(mat, ensure_ascii=False, indent=1) + u"\n")
    print(u"  + materia no mestre (%d no total)" % len(mat["materias"]))
    print(u"\nAgora rode: python tools/gen_imprensa.py .")


if __name__ == "__main__":
    main(sys.argv)
