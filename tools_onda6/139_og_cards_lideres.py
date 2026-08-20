# -*- coding: utf-8 -*-
"""Onda 68 (#247) -- cartao de preview 1200x630 para as 18 paginas de lider.

O PROBLEMA MEDIDO. As 18 paginas individuais de lider (6 lideres x 3 idiomas)
declaravam como `og:image` o RETRATO do lider, que no espelho existe apenas a
**232x246**. Isso e menor que o minimo que WhatsApp/LinkedIn/Facebook pedem para
desenhar o cartao grande -- e as mesmas paginas declaram
`twitter:card=summary_large_image`, ou seja prometem cartao grande e entregam uma
imagem de miniatura. Resultado pratico: link de socio compartilhado sai como
tijolinho, ou sem imagem.

O QUE ESTE SCRIPT NAO FAZ: nao estica a foto para preencher 630px de altura. Nao
existe original maior no espelho (conferido: so 232x246 e 232x239), e subir 232
para 630 e 2,7x -- rosto humano a 2,7x de upscale fica borrado, e borrado num
cartao que representa um socio da firma e pior que pequeno. A foto entra a 1,4x
(324x344) como ELEMENTO do cartao, nao como painel de fundo.

FONTE DE VERDADE (P3): nome, cargo e foto sao LIDOS de cada pagina de lider --
`<h1 class="blog-single__title">`, `<p class="onda59-cargo">` e o background do
`.blog-single__thumb`. Nada e redigitado aqui. Se a onda 59 corrigir um cargo, o
cartao acompanha na proxima execucao.

Sao 6 cartoes, nao 18: o cargo ("Managing Partner", "Senior Expert") esta em
INGLES nas tres linguas -- conferido nas 18 paginas --, entao pt/en/de
compartilham o mesmo cartao.

TIPOGRAFIA: Titillium Web, a fonte que o site realmente serve, extraida dos
`.woff2` do proprio repo via fontTools. Nao e Arial: usar outra fonte no cartao
faria o preview divergir da pagina que ele anuncia.

FORMATO: JPEG q90, nao WebP nem PNG. WebP esta fora porque o crawler de WhatsApp
e de LinkedIn tem historico de nao renderizar WebP em preview, e cartao que o
scraper ignora e pior que cartao pesado. PNG foi a primeira tentativa e o proprio
script a REPROVOU: 127,7 KB no cartao do Raoni, acima do teto de 120 KB da S163 --
PNG nao comprime fotografia. JPEG q90 resolve os dois lados: ~40 KB e o texto, a
56px, nao mostra artefato.

Idempotente por ASSINATURA DAS ENTRADAS, nao por comparacao de pixel -- ver o
docstring de `assinatura()` para a medicao que derrubou a primeira abordagem.
Confere o que gravou: dimensao, peso e presenca de tinta clara.

Uso:  python tools_onda6/139_og_cards_lideres.py .
"""

from __future__ import print_function

import hashlib
import io
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from _onda7_css import ler, resolve_public  # noqa: E402

# --- identidade (R4) ---
NAVY = (2, 14, 102)
CIANO = (0, 173, 236)
BRANCO = (255, 255, 255)
AZUL_CLARO = (170, 213, 232)

LARG, ALT = 1200, 630
DESTINO = "wp-content/uploads/2026/08/onda68"
TETO_KB = 120  # o mesmo teto da S163; vale como disciplina mesmo em JPEG

# Versao do DESENHO. Entra no hash de assinatura: mexer no layout obriga a regerar
# os 6 cartoes sem depender de eu lembrar de apagar arquivo na mao.
LAYOUT_V = 1

# O manifesto de assinaturas e estado de BUILD, entao mora fora de `public/` -- o
# que esta em public/ vai para producao. Versionado, porque e ele que sustenta a
# idempotencia entre execucoes e entre maquinas.
MANIFESTO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "dados", "og-cards-lideres.json")

FONTES = "wp-content/uploads/2026/07/fontes"
# medido com fontTools: familia/subfamilia/usWeightClass de cada woff2 do repo
WOFF_BOLD = "NaPDcZTIAOhVxoMyOr9n_E7ffHjDGItzYw.woff2"      # Titillium Web Bold 700
WOFF_REG = "NaPecZTIAOhVxoMyOr9n_E7fdMPmDQ.woff2"           # Titillium Web Regular 400
WOFF_SEMI = "NaPDcZTIAOhVxoMyOr9n_E7ffBzCGItzYw.woff2"      # Titillium Web SemiBold 600


def _ttf_de_woff2(pub, nome, cache):
    """Converte um .woff2 do repo em .ttf temporario para o PIL abrir.

    O PIL nao le woff2. A conversao acontece em tempo de BUILD e o .ttf nao e
    versionado -- a fonte de verdade continua sendo o woff2 que o site serve.
    """
    if nome in cache:
        return cache[nome]
    from fontTools.ttLib import TTFont
    origem = os.path.join(pub, FONTES.replace("/", os.sep), nome)
    if not os.path.exists(origem):
        raise SystemExit("woff2 ausente: %s" % origem)
    t = TTFont(origem)
    fd, destino = tempfile.mkstemp(suffix=".ttf")
    os.close(fd)
    t.flavor = None
    t.save(destino)
    cache[nome] = destino
    return destino


def paginas_de_lider(pub):
    """[(slug, nome, cargo, caminho_da_foto)] lido das paginas, sem redigitar."""
    achados = {}
    for dp, _d, fs in os.walk(pub):
        for f in fs:
            if f != "index.html":
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            if not re.search(r'/(?:lider|leader|fuehrungskraft)/[^/]+/index\.html$', rel):
                continue
            h = ler(p)
            if 'rel="canonical"' in h and re.search(r'name="robots"[^>]*noindex', h):
                continue  # stub de redirect
            mn = re.search(r'<h1 class="blog-single__title">([^<]+)</h1>', h)
            mc = re.search(r'<p class="onda59-cargo"><strong>([^<]+)</strong></p>', h)
            mf = re.search(r"background-image:\s*url\(['\"]?([^'\")]+)['\"]?\)", h)
            if not (mn and mc and mf):
                continue
            slug = rel.split("/")[-2]
            achados.setdefault(slug, (slug, mn.group(1).strip(),
                                      mc.group(1).strip(), mf.group(1)))
    return [achados[k] for k in sorted(achados)]


def _quebrar(texto, fonte, largura):
    """Quebra por PALAVRA usando a largura REAL da fonte, nunca por contagem."""
    palavras = texto.split()
    linhas, atual = [], ""
    for p in palavras:
        teste = (atual + " " + p).strip()
        if fonte.getlength(teste) <= largura or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def desenhar(nome, cargo, foto, fbold, freg, fsemi):
    im = Image.new("RGB", (LARG, ALT), NAVY)
    d = ImageDraw.Draw(im)

    # filete ciano na aresta esquerda: a barra lateral da identidade
    d.rectangle([0, 0, 11, ALT], fill=CIANO)

    # --- foto: 1,4x do original, canto direito, com moldura fina ---
    fw, fh = 324, 344
    px = LARG - fw - 74
    py = (ALT - fh) // 2
    try:
        f = Image.open(foto).convert("RGB").resize((fw, fh), Image.LANCZOS)
        im.paste(f, (px, py))
        d.rectangle([px - 1, py - 1, px + fw, py + fh], outline=AZUL_CLARO, width=2)
    except Exception:
        px = LARG  # sem foto, o texto usa a largura toda

    # --- texto ---
    x = 74
    disp = px - x - 56 if px < LARG else LARG - 2 * x

    linhas = _quebrar(nome, fbold, disp)
    alt_nome = len(linhas) * 66
    alt_cargo = 40
    y = (ALT - (alt_nome + 18 + alt_cargo)) // 2

    for ln in linhas:
        d.text((x, y), ln, font=fbold, fill=BRANCO)
        y += 66
    y += 18
    d.text((x, y), cargo, font=fsemi, fill=CIANO)

    # regua + wordmark no pe, no construto da casa
    d.rectangle([x, ALT - 92, x + 132, ALT - 90], fill=AZUL_CLARO)
    d.text((x, ALT - 74), "MIROW & CO.", font=freg, fill=AZUL_CLARO)
    return im


def assinatura(nome, cargo, caminho_foto):
    """Hash das ENTRADAS do cartao. E o contrato de idempotencia deste script.

    A primeira tentativa comparava PIXEL com tolerancia, e nao funciona: medido no
    ida-e-volta do JPEG q90, a mediana da diferenca e 1 nivel, o p99 e 7 e o
    **maximo e 51** -- as bordas do texto branco sobre navy e do filete ciano, onde
    o ringing do JPEG e mais forte. Para passar precisaria de tolerancia ~55, que
    mascararia mudanca de desenho de verdade. Ou seja: comparar pixel de formato com
    perda nao distingue ruido de conteudo, e afrouxar o limiar ate passar transforma
    o guarda em enfeite.

    O cartao e funcao pura de (nome, cargo, bytes da foto, codigo do desenho). Entao
    a idempotencia se ancora nas entradas, e o LAYOUT_V abaixo entra no hash: mexer
    no desenho obriga a regerar, sem depender de eu lembrar de apagar os arquivos.
    """
    h = hashlib.sha1()
    h.update(("LAYOUT_V=%d|" % LAYOUT_V).encode("utf-8"))
    h.update((nome + "|" + cargo + "|").encode("utf-8"))
    try:
        with open(caminho_foto, "rb") as f:
            h.update(f.read())
    except Exception:
        h.update(b"sem-foto")
    return h.hexdigest()


def ler_manifesto(caminho):
    try:
        with io.open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    cache = {}
    fbold = ImageFont.truetype(_ttf_de_woff2(pub, WOFF_BOLD, cache), 56)
    fsemi = ImageFont.truetype(_ttf_de_woff2(pub, WOFF_SEMI, cache), 32)
    freg = ImageFont.truetype(_ttf_de_woff2(pub, WOFF_REG, cache), 21)

    lideres = paginas_de_lider(pub)
    print("lideres lidos das paginas: %d" % len(lideres))
    if not lideres:
        raise SystemExit("nenhum lider reconhecido -- markup mudou?")

    dest = os.path.join(pub, DESTINO.replace("/", os.sep))
    if not os.path.isdir(dest):
        os.makedirs(dest)

    manifesto = ler_manifesto(MANIFESTO)
    novo_manifesto = {}

    escritos, cartoes = 0, {}
    for slug, nome, cargo, reffoto in lideres:
        foto = os.path.join(pub, reffoto.lstrip("/").replace("/", os.sep))
        alvo = os.path.join(dest, "og-lider-%s.jpg" % slug)
        cartoes[slug] = "%s/og-lider-%s.jpg" % (DESTINO, slug)
        ass = assinatura(nome, cargo, foto)
        novo_manifesto[slug] = ass
        if manifesto.get(slug) != ass or not os.path.exists(alvo):
            im = desenhar(nome, cargo, foto, fbold, freg, fsemi)
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=90, optimize=True,
                    progressive=True, subsampling=0)
            with open(alvo, "wb") as fh:
                fh.write(buf.getvalue())
            escritos += 1
        print("  %-28s %-22s %-18s %6.1f KB"
              % (slug, nome[:22], cargo[:18], os.path.getsize(alvo) / 1024.0))

    if novo_manifesto != manifesto:
        with io.open(MANIFESTO, "w", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(novo_manifesto, indent=2, sort_keys=True,
                                ensure_ascii=False) + u"\n")

    # --- confere o que gravou ---
    falhas = []
    for slug, ref in cartoes.items():
        fp = os.path.join(pub, ref.replace("/", os.sep))
        im = Image.open(fp)
        im.load()
        kb = os.path.getsize(fp) / 1024.0
        if im.size != (LARG, ALT):
            falhas.append("%s saiu %dx%d" % (slug, im.size[0], im.size[1]))
        if kb > TETO_KB:
            falhas.append("%s tem %.0f KB, acima do teto de %d KB da S163"
                          % (slug, kb, TETO_KB))
        rgb = im.convert("RGB")
        px = rgb.load()
        claros = sum(1 for y in range(0, ALT, 4) for x in range(0, LARG, 4)
                     if min(px[x, y]) > 200)
        if claros < 200:
            falhas.append("%s quase sem tinta clara (%d amostras)" % (slug, claros))
    if falhas:
        print("")
        for f in falhas:
            print("  FALHA: %s" % f)
        raise SystemExit(1)

    # --- aponta as 18 paginas para o cartao do seu lider ---
    trocadas = 0
    for dp, _d, fs in os.walk(pub):
        for f in fs:
            if f != "index.html":
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            m = re.search(r'/(?:lider|leader|fuehrungskraft)/([^/]+)/index\.html$', rel)
            if not m or m.group(1) not in cartoes:
                continue
            h = ler(p)
            novo = re.sub(
                r'(<meta property="og:image" content=")[^"]+(")',
                lambda mm: mm.group(1) + "https://mirow.com.br/" + cartoes[m.group(1)]
                + mm.group(2), h, count=1)
            if novo != h:
                with io.open(p, "w", encoding="utf-8", newline="") as fh:
                    fh.write(novo)
                trocadas += 1

    print("\ncartoes gravados: %d   paginas repontadas: %d" % (escritos, trocadas))
    print("resumo: %d arquivo(s) alterado(s)" % (escritos + trocadas))


if __name__ == "__main__":
    main()
