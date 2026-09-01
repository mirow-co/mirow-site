# -*- coding: utf-8 -*-
"""verificacoes.py — suite de asserções do site (P2 do processo).

Uso:
    python tools/verificacoes.py <raiz-que-contem-public> [--rapido] [--so=PREFIXO] [-v]
                                 [--para=etapa1,etapa2] [--desde=<ref-git>]
                                 [--tempos] [--espera-fixa]

    --rapido        só as asserções estáticas (sem Chrome/servidor local)
    --so=H          roda só as asserções cujo id começa com H (ex.: --so=H03)
    --para=texto    roda só as etapas pedidas (texto, css, asset, estrutura,
                    schema, medicao). Asserção sem etapa declarada roda SEMPRE.
    --desde=HEAD    descobre as etapas a partir do que mudou no git desde <ref>
    --tempos        lista as asserções mais lentas e o custo dos page loads
    --espera-fixa   volta à espera cega de 6 s por page load (para comparar)
    -v              mostra detalhe de cada asserção, inclusive as que passaram

Saída: uma linha por asserção — OK / FALHA / PENDENTE — e um resumo.
Código de saída 1 se houver qualquer FALHA. PENDENTE não derruba o build.

POR QUE ESTE ARQUIVO EXISTE
---------------------------
O processo anterior perdia pedidos do Mario: cada onda validava a si mesma por
screenshot, e o acumulado não era testado. Resultado: a Sotreq ficou fora da
barra de clientes, a "escadinha" do slogan nunca foi feita, e os ícones de
contato regrediram no header branco — tudo com QA "aprovado".

Aqui, cada pedido aceito vira uma asserção executável. A suíte roda INTEIRA
antes de todo deploy (`tools/deploy.ps1` aborta em falha). Pedido antigo passa a
ser protegido para sempre.

REGRAS
------
1. Toda onda nova ADICIONA asserções. Só se remove asserção com decisão
   explícita do Mario.
2. Pedido aceito mas ainda não implementado entra como PENDENTE, com o número
   da issue — nunca como sucesso silencioso, nunca ausente.
3. Asserção tem que falhar por um motivo legível. Mensagem diz o que se esperava
   e o que se achou.
"""
import hashlib
import io
import json
import os
import re
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time

# O console do Windows e cp1252: um caractere fora dessa tabela numa MENSAGEM
# DE FALHA fazia a suite ABORTAR no print, e o gate nao mostrava a falha --
# quem lesse a saida (ou um grep por FALHA) via silencio e concluia 'passou'.
# Falso verde por encoding, achado em 31/08/2026 ao exercitar a sabotagem da
# V41. A blindagem vale para TODA saida, nao so para a que eu escrevi.
for _fluxo in (sys.stdout, sys.stderr):
    try:
        _fluxo.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
import unicodedata
import urllib.request
import zlib

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "tools_onda6"))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "tools_onda6", "qa"))

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Onda 47 (#101/#42): o site e servido na RAIZ de mirow.com.br.
HOST = "https://mirow.com.br"

# ---------------------------------------------------------------- constantes

# As 3 homes do site (pt, en, de). A duplicata /en/homepage/ virou stub de
# redirect na onda 41 (S-135/#65): /en/ é a canônica.
HOMES = ["pt/index.html", "en/index.html", "de/index.html"]

# Versão de cache-busting esperada = a constante VERSAO do 27_cache_busting.py.
ASSETS_PROPRIOS = [
    "wp-content/uploads/2026/07/onda6/onda6.css",
    "wp-content/uploads/2026/07/onda6/onda8-dobra.js",
    "wp-content/uploads/2026/07/onda6/onda13-hero-plexus.js",
    "wp-content/uploads/2026/07/clientes/clientes-logos.css",
]

# Blocos de CSS marcados que precisam existir no onda6.css (um por entrega).
BLOCOS_CSS = [
    "onda7:home-hero", "onda7:lideres-link", "onda9:rede",
    "onda8:hero-contatos", "onda8:dobra", "onda8:hero-contatos-v2",
    "onda8:menu-contatos", "onda8:hero-slogan-alto",
    "onda10:header-contraste", "onda10:hero-escadinha", "onda10:numeros",
    "onda10:hero-numeros", "onda10:clientes-barra",
    "onda11:s13-form-topo", "onda12:praticas-nav", "onda13:hero-malha",
    "onda14:hero-malha-cheia", "onda14:menu-executivo", "onda14:fundo-sem-sobras",
    "onda15:hero-scrims", "onda15:barras-gemeas", "onda15:rodape-barra",
    "onda16:hero-layout-s41", "onda16:hover-marcas-s42",
    "onda47:hero-respiro",
    "onda17:hero-horizonte-s49",
    # onda 18 (S-50..S-71, pedidos do Mario de 03/08)
    "onda18:contato-botao", "onda18:barras", "onda18:voltar-topo",
    "onda18:carreiras", "onda18:insights-colorido", "onda18:home-lideres",
    "onda18:imprensa", "onda18:planeta-setores", "onda18:hero-numeros-s73",
    "onda19:lateral-e-idiomas", "onda21:menus-bain", "onda22:marca-secoes",
    "onda25:peso-submenu",
    # onda21:rede-v2 SAIU na onda 31: a página da rede é gerada por
    # tools/gen_rede.py e o estilo vive no bloco onda31:rede. O antigo era CSS
    # morto — as classes .onda21-* não existem mais na página.
    "onda26:fonte-unica", "onda27:barra-igual", "onda29:abertura-padrao",
    "onda30:titulo-secao", "onda31:rede", "onda36:logo-frente",
    "onda39:respiro-hero", "onda40:quebra-pilulas",
]

# Marcadores HTML das entregas, e em quantas páginas cada um precisa aparecer.
# n=4 -> só as homes; n=275 -> todas as páginas; n=3 -> uma por idioma.
# onda7:menu-carreiras só foi injetado em pt/en (204 páginas): as 71 páginas
# alemãs já traziam "Karriere" nativo do tema. O invariante de verdade — todas as
# páginas terem link de carreiras no menu — é a asserção H08, não o marcador.
# Sentinelas de piso para a tabela MARCADORES abaixo. Existem porque o piso das
# entregas de rodape/menu NAO e um numero: e "todas as paginas de conteudo", e esse
# total muda a cada onda que transforma pagina em stub (ja mudou em 29, 33, 57 e 68).
# Com o numero escrito a mao, cada uma dessas ondas produzia asserções vermelhas sem
# nenhum defeito de conteudo, e a correcao era editar a tabela -- ou seja, o teste
# cobrava a consequencia em vez da causa.
TODAS = "__todas_as_de_conteudo__"          # piso = numero de paginas de conteudo
PT_EN = ("pt", "en")                        # piso = as de conteudo em pt e en

MARCADORES = [
    # Onda 41 (S-135/#65): en/homepage virou stub — marcadores de home valem 3.
    ("onda5:clientes-logos", 3), ("onda6:praticas", 3), ("onda7:lideres-link", 3),
    # ATENCAO (onda 29 / S-107): as 275 paginas viraram 125 de CONTEUDO + 160
    # stubs de redirect (uma URL por pagina). Os marcadores de barra/rodape agora
    # se contam sobre as de conteudo — o numero e o piso, nao a meta.
    # ONDA 33 (S-118): as 12 paginas de perfil de quem saiu viraram stub, entao as
    # de conteudo cairam de 125 para 113 e os pisos abaixo desceram junto (120->110,
    # carreiras 80->74). Nao e regressao: e a mesma cobertura sobre menos paginas.
    # Onda 57 (#228): as 3 paginas de contato viraram stub de redirect, entao as
    # de conteudo cairam de 112 para 109 e os pisos de 110 desceram para 109.
    # Nao e regressao: e a mesma cobertura sobre menos paginas.
    ("onda7:menu-sobre", TODAS), ("onda7:menu-praticas", TODAS),
    # o marcador de carreiras nunca existiu nas paginas DE (medido: 44 pt + 41 en,
    # 0 de) — o item esta lá, o comentario e que nao. Piso = pt+en.
    ("onda7:menu-carreiras", PT_EN),
    ("onda8:menu-contatos", TODAS), ("onda8:hero-contatos", 3), ("onda8:dobra", 3),
    ("onda10:hero-numeros", 3),
    # onda11:s08-hero-contatos saiu na onda 57 (#228): o marcador so existia
    # nas 3 paginas de contato, que viraram stub. Os 4 canais seguem cobrados
    # nas pilulas do hero (V23) e nos icones da barra (V14).
    # onda13:hero-malha saiu em 03/08 (S-49/#107): o bloco do video virou os
    # canvases do Horizonte 2050.
    ("onda17:hero-horizonte", 3),
    # onda14:rodape-menu e onda15:rodape-contatos saíram em 31/07 (decisão
    # explícita do Mario na #91: "IDENTICAS" — a nav recriada virou o clone
    # literal onda15:rodape-barra).
    ("onda15:hero-texto", 3),
    # onda15:rodape-barra saiu na onda 42 (#191) — barra do rodape aposentada.
    # onda 18: botao de voltar ao topo em todas; planeta so nas homes
    ("onda18:voltar-topo", TODAS), ("onda18:planeta-setores", 3),
]

# Logos que a barra de clientes precisa mostrar. NÃO é lista hardcoded (era assim
# que divergia): vem de tools/clients-publicados.json, que o tools/gen_clients.py
# gera a partir do arquivo mestre de curadoria no repo PRIVADO mirow-co/mirow-marketing
# (08_Site/2026-07-30_clients-curadoria-interna.json). É o P3 em ação.
# Decodificador minimo de PNG truecolor, sem PIL no processo da suite.
# Nasceu local dentro de uma assercao V (contraste medido no pixel) e virou
# helper de modulo na onda 68, quando a S171 passou a precisar do mesmo
# decodificador para medir a TINTA do favicon. Duas copias de 40 linhas seria
# valor gemeo -- a classe de bug da onda 31.
# Dimensao e formato de imagem lendo o CABECALHO do arquivo, sem PIL -- a suite
# evita a dependencia de proposito (ver `_png_rgb`). Existe porque a onda 68 precisa
# comparar o `og:image:width/height/type` declarado com o arquivo real: o defeito que
# a S172 persegue nao e tag ausente, e tag presente e ERRADA (58 paginas diziam
# `image/png` para arquivo WebP, residuo das ondas 61/62c).
def _dim_imagem(caminho):
    """(largura, altura, formato) ou None se nao reconhecer."""
    try:
        with io.open(caminho, "rb") as f:
            d = f.read(64 * 1024)
    except Exception:
        return None
    if d[:8] == b"\x89PNG\r\n\x1a\n" and d[12:16] == b"IHDR":
        w, h = struct.unpack(">II", d[16:24])
        return (w, h, "PNG")
    if d[:6] in (b"GIF87a", b"GIF89a"):
        w, h = struct.unpack("<HH", d[6:10])
        return (w, h, "GIF")
    if d[:4] == b"RIFF" and d[8:12] == b"WEBP":
        sub = d[12:16]
        if sub == b"VP8 ":
            w = struct.unpack("<H", d[26:28])[0] & 0x3FFF
            h = struct.unpack("<H", d[28:30])[0] & 0x3FFF
            return (w, h, "WEBP")
        if sub == b"VP8L":
            b0, b1, b2, b3 = d[21], d[22], d[23], d[24]
            n = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)
            return ((n & 0x3FFF) + 1, ((n >> 14) & 0x3FFF) + 1, "WEBP")
        if sub == b"VP8X":
            w = 1 + (d[24] | (d[25] << 8) | (d[26] << 16))
            h = 1 + (d[27] | (d[28] << 8) | (d[29] << 16))
            return (w, h, "WEBP")
        return None
    if d[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(d):
            if d[i] != 0xFF:
                i += 1
                continue
            marca = d[i + 1]
            if marca in (0xD8, 0xD9) or 0xD0 <= marca <= 0xD7 or marca == 0x01:
                i += 2
                continue
            tam = struct.unpack(">H", d[i + 2:i + 4])[0]
            # SOF0..SOF15, menos os marcadores que nao sao SOF (C4, C8, CC)
            if 0xC0 <= marca <= 0xCF and marca not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", d[i + 5:i + 9])
                return (w, h, "JPEG")
            i += 2 + tam
        return None
    return None


_MOD110 = []


def _mod110():
    """O modulo 110_geo_bios_lideres, carregado uma vez.

    E o cadastro de lideres do projeto (`PAGINAS`), a mesma fonte de onde o bloco
    JSON-LD da onda 59, os cartoes de preview da onda 68 e a meta description das
    listagens sao montados. Asserção que precisa saber QUANTOS lideres existem
    pergunta a ele, em vez de trazer o numero escrito.
    """
    if not _MOD110:
        _MOD110.append(__import__("110_geo_bios_lideres"))
    return _MOD110[0]


_MOD111 = []
_MOD148 = []


def _mod111():
    """O modulo 111_geo_jsonld_lideres: `ALUMNI` e `EXPERIENCIA` (onda 73)."""
    if not _MOD111:
        _MOD111.append(__import__("111_geo_jsonld_lideres"))
    return _MOD111[0]


def _mod148():
    """O modulo 148_linkedin_lideres: o mestre `LINKEDIN` e a tabela `MORTOS`."""
    if not _MOD148:
        _MOD148.append(__import__("148_linkedin_lideres"))
    return _MOD148[0]


_MOD150 = []


def _mod150():
    """O modulo 150_tipografia_fluida: a tabela `FLUIDAS` da onda 76."""
    if not _MOD150:
        _MOD150.append(__import__("150_tipografia_fluida"))
    return _MOD150[0]


_MOD152 = []


def _mod152():
    """O modulo 152_cards_instituicoes: o mapa `CURTO` dos nomes de chip."""
    if not _MOD152:
        _MOD152.append(__import__("152_cards_instituicoes"))
    return _MOD152[0]


def _png_rgb(dados):
    # decodificador minimo de PNG truecolor, sem PIL no processo da suite
    if dados[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    i, larg, alt, prof, tipo, idat = 8, 0, 0, 0, 0, b""
    while i < len(dados):
        ln = struct.unpack(">I", dados[i:i + 4])[0]
        ct = dados[i + 4:i + 8]
        corpo = dados[i + 8:i + 8 + ln]
        if ct == b"IHDR":
            larg, alt, prof, tipo = struct.unpack(">IIBB", corpo[:10])
        elif ct == b"IDAT":
            idat += corpo
        elif ct == b"IEND":
            break
        i += 12 + ln
    if prof != 8 or tipo not in (2, 6):
        return None
    canais = 3 if tipo == 2 else 4
    bruto = zlib.decompress(idat)
    passo = larg * canais
    saida, ant = [], bytearray(passo)
    pos = 0
    for _y in range(alt):
        f = bruto[pos]
        pos += 1
        linha = bytearray(bruto[pos:pos + passo])
        pos += passo
        for x in range(passo):
            a = linha[x - canais] if x >= canais else 0
            b = ant[x]
            c = ant[x - canais] if x >= canais else 0
            if f == 1:
                linha[x] = (linha[x] + a) & 255
            elif f == 2:
                linha[x] = (linha[x] + b) & 255
            elif f == 3:
                linha[x] = (linha[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                linha[x] = (linha[x] + pr) & 255
        saida.append(bytes(linha))
        ant = linha
    return larg, alt, canais, saida


def _logos_esperados():
    p = os.path.join(AQUI, "clients-publicados.json")
    with io.open(p, encoding="utf-8") as f:
        return [c["slug"] for c in json.load(f)]


LOGOS_ESPERADOS = _logos_esperados()

# Slogan do hero, por idioma (S-01 muda a APRESENTAÇÃO — escadinha —, não as palavras).
SLOGAN = {
    "pt": ["Estratégia", "Confiança", "Resultados"],
    "en": ["Strategy", "Trust", "Results"],
    "de": ["Strategie", "Vertrauen", "Ergebnisse"],
}

# Os 4 canais de contato que precisam existir no hero das homes e no header de
# todas as páginas (onda 8 / 8.1).
CANAIS = [("WhatsApp", "wa.me/"), ("e-mail", "mailto:"),
          ("LinkedIn", "linkedin.com"), ("Instagram", "instagram.com")]

# Assets locais que faltam de propósito ou por herança do WordPress. Qualquer
# asset faltando FORA desta lista é FALHA — foi assim que se descobriu que o
# .gitignore engolia public/wp-includes/js/dist/.
FALTAS_CONHECIDAS = {
    # link RSD que o WP deixa em toda página; não é usado por nada.
    "xmlrpc.php": "herança do WordPress, link morto e inofensivo",
    # As 6 imagens da roda de práticas SAÍRAM desta lista na onda 33 (S-119/#69):
    # foram recuperadas do WordPress vivo por tools_onda6/89_recupera_imagens_praticas.py
    # e agora existem no disco. A E05 volta a cobrá-las de verdade, e a S119 garante
    # que continuem lá. Não recolocar como exceção: se faltarem, é falha.
}

# Pedidos aceitos e ainda não implementados: entram como PENDENTE com a issue.
# Ao implementar, MOVER para uma asserção de verdade (e tirar daqui).
PENDENTES = []

# Título da barra de clientes por idioma (S-02): gerado por tools/gen_clients.py
# a partir do arquivo mestre — os textos aqui têm que bater com os de lá.
TITULO_BARRA = {
    "pt": u"Exemplos de Empresas que confiam na Mirow &amp; Co.",
    "en": u"Examples of companies that trust Mirow &amp; Co.",
    "de": u"Beispiele für Unternehmen, die Mirow &amp; Co. vertrauen",
}

# Páginas de contato (todas as variantes do espelho) — S-07 e S-08.
# Só as URLs CANÔNICAS: depois da S-107 (#165) as variantes de raiz
# (`contato/`, `carreiras/`, `imprensa/`…) são stubs de redirect.
# Onda 57 (#228): as páginas de contato viraram stub de redirect por decisão do
# Mario ("nao esta agregando a nada. ja tem mil outras formas de contato"), e as
# asserções S07 e S08 saíram com elas. Não foram mantidas com a lista vazia de
# propósito: asserção que itera sobre nada PASSA sempre, e passar por vacuidade
# é pior que não existir — dá confiança sem medir coisa alguma.
# Os canais de contato seguem cobrados onde agora vivem: V23 (pílulas do hero) e
# V14 (ícones da barra).

# Páginas de carreiras — S-13.
CARREIRAS = ["pt/carreiras/index.html",
             "en/careers/index.html", "de/karrieren/index.html"]

# Páginas de imprensa — S-106 (#164) criou EN e DE; antes só existia em PT.
IMPRENSA = ["pt/imprensa/index.html", "en/press/index.html", "de/presse/index.html"]

# Páginas da Nossa Rede — geradas por tools/gen_rede.py (onda 31).
REDE = ["pt/sobre-nos/nossa-rede/index.html", "en/about-us/our-network/index.html",
        "de/ueber-uns/unser-netzwerk/index.html"]

# ------------------------------------------------------------------ mecânica


# ============================================================================
# ETAPAS — rodar so o que a mudanca pede (onda 60c, pedido do Mario)
# ============================================================================
# PROBLEMA MEDIDO: a fase estatica leva 1,2 s para 162 assercoes; a fase ao vivo
# leva ~20 min para 23, porque cada page load custava 6 s de espera cega. Trocar
# uma frase disparava o rol inteiro.
#
# COMO FUNCIONA: cada assercao pertence a uma ou mais ETAPAS. O seletor
# `--para=<etapa>` roda as etapas pedidas; `--desde=<ref-git>` descobre as etapas
# a partir dos arquivos que mudaram.
#
# REGRA DE SEGURANCA (importante): assercao NAO mapeada aqui roda SEMPRE. O mapa
# so pode ACELERAR, nunca esconder — esquecer de classificar uma assercao nova a
# deixa no caminho, e nao fora dele. E o gate do deploy continua rodando TUDO por
# padrao; a selecao e para o laco de desenvolvimento.
ETAPAS_VALIDAS = ("texto", "css", "asset", "estrutura", "schema", "medicao")

# prefixo de id -> etapas. Prefixo mais longo vence.
ETAPAS = {
    # --- ao vivo: tudo que depende de render (CSS, layout, fonte, hover) ---
    "V": ("css",),
    # --- estrutura de URL, sitemap, redirect, hreflang, canonical ---
    "S107": ("estrutura",), "S118": ("estrutura",), "S119": ("estrutura",),
    "S120": ("estrutura",), "S121": ("estrutura",), "S122": ("estrutura",),
    "S124": ("estrutura",), "S151": ("estrutura",),
    # --- schema/GEO/meta ---
    "S149": ("schema",), "S150": ("schema",), "S152": ("schema",),
    # --- assets referenciados (existencia, peso, dimensao, placeholder) ---
    "S123": ("asset",), "S153": ("asset", "texto"), "S157": ("asset", "css"),
    "S159": ("asset",), "S160": ("asset",), "S161": ("asset",),
    "S162": ("asset",), "S163": ("asset",), "S164": ("asset", "medicao"), "E": ("asset",),
    # onda 65: a lista de imprensa e gerada do mestre; mexer no dado e mexer no
    # texto das 3 paginas, e o logo de cada veiculo e asset
    "S165": ("texto",), "S166": ("texto", "asset"),
    # onda 67: a busca depende do indice (asset) e do markup das 3 paginas
    "S167": ("texto", "asset"), "S168": ("texto", "asset"),
    "S169": ("texto", "css"),
    "S170": ("texto",),
    "S171": ("asset", "texto"),
    "S172": ("asset", "texto"), "S173": ("asset", "texto"),
    "S174": ("schema", "asset", "texto"),
    "S175": ("schema", "texto"),
    # onda 73: o LinkedIn contra o mestre do 148, e o historico de empregadores
    "S176": ("texto", "estrutura"), "S177": ("schema",),
    # onda 74: o sameAs do Wikidata, contra o mestre de QIDs do 111
    "S178": ("schema",),
    # onda 75: link de imprensa morto e URL de arquivo aninhada
    "S179": ("texto",),
    # onda 76: tipografia fluida medida no navegador
    "V41": ("medicao", "css"),
    # onda 77: a frase de sede fora da home
    "S180": ("texto",),
    # onda 78: chips de instituicao nos cards de lider
    "S181": ("texto", "estrutura"), "V42": ("medicao", "css"),
    # --- CSS proprio: blocos marcados, pesos, cache busting ---
    "S127": ("css",), "S148": ("css",), "S128": ("css", "texto"),
    # --- medicao/analytics ---
    "M": ("medicao",), "LF": ("medicao",), "L": ("medicao",),
}


def etapas_de(cid):
    """Etapas de uma assercao. Sem mapeamento -> roda sempre."""
    melhor = None
    for pref, ets in ETAPAS.items():
        if cid.startswith(pref) and (melhor is None or len(pref) > len(melhor)):
            melhor = pref
    return ETAPAS[melhor] if melhor else None  # None = sempre


# padrao de caminho que mudou -> etapas a rodar
def etapas_do_diff(arquivos):
    ets = set()
    for f in arquivos:
        f = f.replace("\\", "/")
        if f.endswith(".css"):
            ets.update(("css", "asset"))
        elif f.endswith((".js",)):
            ets.update(("css", "asset", "medicao"))
        elif f.endswith((".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp",
                         ".woff", ".woff2")):
            ets.add("asset")
        elif f.endswith(("sitemap.xml", "robots.txt")):
            ets.add("estrutura")
        elif f.endswith(".html"):
            ets.add("texto")
            # stub de redirect e pagina nova mexem em estrutura
            ets.add("estrutura")
        elif "/tools" in f or f.startswith("tools"):
            ets.update(ETAPAS_VALIDAS)  # mudou ferramenta: nao arrisca
    return ets or set(ETAPAS_VALIDAS)


def _so_carimbo(ref):
    """Arquivos cuja unica diferenca e o carimbo de cache (`?v=NN`).

    Sem isto o `--desde` seria inutil: o 27_cache_busting.py toca as 282 paginas a
    cada onda, entao QUALQUER diff pareceria "mudou tudo". Um arquivo em que todas
    as linhas alteradas contem `?v=` nao mudou conteudo — mudou o carimbo.
    """
    cosmeticos = set()
    try:
        r = subprocess.run(["git", "diff", "-U0", ref], capture_output=True,
                           text=True, timeout=120)
    except Exception:
        return cosmeticos
    atual, linhas = None, []
    def fecha():
        if atual and linhas and all("?v=" in l for l in linhas):
            cosmeticos.add(atual)
    for l in r.stdout.splitlines():
        if l.startswith("+++ b/"):
            fecha()
            atual, linhas = l[6:].strip(), []
        elif l[:1] in "+-" and not l.startswith(("+++", "---")):
            linhas.append(l)
    fecha()
    return cosmeticos


def arquivos_mudados(ref):
    """Arquivos alterados desde `ref` (inclui nao-commitados), sem os que so
    levaram carimbo de cache."""
    saida = []
    for cmd in (["git", "diff", "--name-only", ref],
                ["git", "diff", "--name-only"],
                ["git", "ls-files", "--others", "--exclude-standard"]):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            saida += [l.strip() for l in r.stdout.splitlines() if l.strip()]
        except Exception:
            pass
    cosmeticos = _so_carimbo(ref)
    return sorted(set(saida) - cosmeticos)


class Suite(object):
    def __init__(self, pub, verboso=False, filtro=None, etapas=None):
        self.pub = pub
        self.verboso = verboso
        self.filtro = filtro
        self.etapas = etapas          # None = roda tudo
        self.tempos = []              # (segundos, id, titulo)
        self.puladas = 0
        self.res = []          # (id, titulo, estado, detalhe)
        self._cache = {}
        self._htmls = None

    # --- infra de leitura --------------------------------------------------
    def ler(self, rel):
        if rel not in self._cache:
            p = os.path.join(self.pub, rel.replace("/", os.sep))
            with io.open(p, encoding="utf-8", errors="replace") as f:
                self._cache[rel] = f.read()
        return self._cache[rel]

    def conteudo(self):
        """Só as páginas de conteúdo — exclui o stub de redirect da raiz.

        `public/index.html` é um `<meta refresh>` de 1 linha: não tem menu nem
        corpo, e não deve ser cobrado por asserção de conteúdo.
        """
        return [(rel, h) for rel, h in self.todas() if not self.eh_stub(rel, h)]

    @staticmethod
    def eh_stub(rel, html):
        """Stub de redirect (<meta refresh> sem corpo) nao e pagina de conteudo.

        Sao o public/index.html da raiz do Pages e os caminhos antigos que a S-67
        deixou redirecionando para nossos-valores. Nenhum deles tem menu, rodape
        ou corpo — cobra-los por assercao de conteudo e falso positivo.
        """
        if rel == "index.html":
            return True
        return ('http-equiv="refresh"' in html
                and '<footer class="footer">' not in html)

    def todas(self):
        """[(rel, html)] de todas as páginas HTML sob public/."""
        if self._htmls is None:
            out = []
            for dp, _d, fs in os.walk(self.pub):
                for n in fs:
                    if not n.endswith(".html"):
                        continue
                    rel = os.path.relpath(os.path.join(dp, n), self.pub).replace(os.sep, "/")
                    if rel == "404.html":
                        continue  # pagina especial do Pages, sem tema (S143 cobre)
                    out.append((rel, self.ler(rel)))
            out.sort()
            self._htmls = out
        return self._htmls

    # --- registro de resultado --------------------------------------------
    def check(self, cid, titulo, fn):
        if self.filtro and not cid.startswith(self.filtro):
            return
        # Selecao por etapa. Assercao sem etapa declarada (etapas_de -> None) roda
        # SEMPRE: o mapa pode acelerar, nunca esconder.
        if self.etapas is not None:
            minhas = etapas_de(cid)
            if minhas is not None and not (set(minhas) & self.etapas):
                self.puladas += 1
                return
        t0 = time.time()
        try:
            ok, detalhe = fn()
            estado = "OK" if ok else "FALHA"
        except Exception as e:  # asserção que explode conta como falha
            estado, detalhe = "FALHA", "erro na asserção: %r" % (e,)
        gasto = time.time() - t0
        self.tempos.append((gasto, cid, titulo))
        self.res.append((cid, titulo, estado, detalhe))
        self._imprime(cid, titulo, estado, detalhe)

    def pendente(self, cid, titulo, issue):
        if self.filtro and not cid.startswith(self.filtro):
            return
        d = "aguarda %s" % issue
        self.res.append((cid, titulo, "PENDENTE", d))
        self._imprime(cid, titulo, "PENDENTE", d)

    def _imprime(self, cid, titulo, estado, detalhe):
        if estado == "OK" and not self.verboso:
            print(u"  OK       %-6s %s" % (cid, titulo))
        else:
            marca = {"OK": "  OK     ", "FALHA": "  FALHA   ", "PENDENTE": "  PENDENTE"}[estado]
            print(u"%s %-6s %s%s" % (marca, cid, titulo, (u"  — " + detalhe) if detalhe else u""))


# ------------------------------------------------------- asserções estáticas

def estaticas(s):
    pub = s.pub

    # E — estrutura e integridade do espelho
    def e01():
        n = len(s.todas())
        return (n >= 270, u"%d páginas HTML (esperado >= 270)" % n)
    s.check("E01", u"o espelho tem as ~275 páginas", e01)

    def e02():
        p = os.path.join(pub, ".nojekyll")
        return (os.path.exists(p),
                u"public/.nojekyll ausente — o GitHub Pages ignoraria pastas com _")
    s.check("E02", u"public/.nojekyll existe", e02)

    def e03():
        p = os.path.join(pub, "index.html")
        if not os.path.exists(p):
            return (False, u"public/index.html ausente — a raiz do Pages daria 404")
        h = s.ler("index.html")
        return ("http-equiv=\"refresh\"" in h, u"index.html da raiz não é redirect: %r" % h[:80])
    s.check("E03", u"raiz do Pages redireciona", e03)

    def e04():
        maus = [rel for rel, h in s.todas() if "data-astro-cid" in h]
        return (not maus, u"%d página(s) do protótipo Astro rejeitado em public/: %s"
                % (len(maus), ", ".join(maus[:5])))
    s.check("E04", u"0 resquício do protótipo Astro em public/", e04)

    def e05():
        # Todo ARQUIVO local referenciado precisa existir no disco. Só entra o que
        # tem extensão de arquivo no último segmento: `wp-json/...` são endpoints
        # da API REST do WordPress, que não existem num espelho estático e não são
        # usados por nada na página.
        rex = re.compile(r'(?:href|src)="(/[^"?#]*?/)?(wp-[^"?#]+|novo/[^"?#]+|xmlrpc\.php)(?:[?#][^"]*)?"')
        faltando = {}
        for rel, h in s.todas():
            for m in rex.finditer(h):
                caminho = m.group(2)
                if caminho.startswith("wp-json/"):
                    continue
                if "." not in os.path.basename(caminho):
                    continue
                if not os.path.exists(os.path.join(pub, caminho.replace("/", os.sep))):
                    faltando.setdefault(caminho, 0)
                    faltando[caminho] += 1
        novas = sorted(k for k in faltando if k not in FALTAS_CONHECIDAS)
        return (not novas, u"%d asset(s) referenciado(s) e ausente(s) do disco: %s"
                % (len(novas), ", ".join(novas[:5])))
    s.check("E05", u"todo asset local referenciado existe", e05)

    def e06():
        # os assets de public/ têm que estar VERSIONADOS, não só existir no disco.
        # Foi assim que 4 arquivos de wp-includes/js/dist/ ficaram fora do git
        # (o .gitignore tinha `dist/` sem a barra inicial) e o site quebraria num
        # clone novo — o deploy antigo escondia o problema copiando o disco.
        raiz = os.path.dirname(pub)
        try:
            out = subprocess.check_output(
                ["git", "ls-files", "--others", "--ignored", "--exclude-standard", "public"],
                cwd=raiz, stderr=subprocess.STDOUT).decode("utf-8", "replace")
        except Exception as e:
            return (True, u"não deu para consultar o git (%r) — asserção pulada" % (e,))
        ign = [l for l in out.splitlines() if l.strip()]
        return (not ign, u"%d arquivo(s) em public/ ignorado(s) pelo .gitignore: %s"
                % (len(ign), ", ".join(ign[:5])))
    s.check("E06", u"nenhum arquivo de public/ ignorado pelo git", e06)

    # C — cache-busting (onda 8.1): a causa-raiz do "CSS quebrado"
    def versao_do_script():
        p = os.path.join(os.path.dirname(pub), "tools_onda6", "27_cache_busting.py")
        m = re.search(r"^VERSAO\s*=\s*(\d+)", io.open(p, encoding="utf-8").read(), re.M)
        return int(m.group(1))

    def c01():
        v = versao_do_script()
        for a in ASSETS_PROPRIOS:
            if not os.path.exists(os.path.join(pub, a.replace("/", os.sep))):
                return (False, u"asset próprio ausente: %s" % a)
        return (True, u"VERSAO = %d" % v)
    s.check("C01", u"os 3 assets próprios das ondas existem", c01)

    def c02():
        v = versao_do_script()
        vistas, semver = set(), []
        for rel, h in s.todas():
            for a in ASSETS_PROPRIOS:
                for m in re.finditer(re.escape(a) + r'(\?v=(\d+))?', h):
                    if m.group(2):
                        vistas.add(int(m.group(2)))
                    else:
                        semver.append((rel, a))
        if semver:
            return (False, u"%d referência(s) sem ?v=: %s" % (
                len(semver), ", ".join("%s -> %s" % t for t in semver[:3])))
        if vistas != {v}:
            return (False, u"versões carimbadas %s, esperado só {%d} (a VERSAO do "
                           u"27_cache_busting.py)" % (sorted(vistas), v))
        return (True, u"?v=%d em todas as referências" % v)
    s.check("C02", u"cache-busting consistente em todas as páginas", c02)

    def c03():
        css = s.ler("wp-content/uploads/2026/07/onda6/onda6.css")
        faltam = [b for b in BLOCOS_CSS
                  if ("/* %s:ini */" % b) not in css or ("/* %s:fim */" % b) not in css]
        return (not faltam, u"bloco(s) de CSS marcado(s) ausente(s): %s" % ", ".join(faltam))
    s.check("C03", u"todos os blocos marcados no onda6.css", c03)

    # M — marcadores das entregas ainda presentes (proteção contra regressão)
    def faz_marcador(marca, n):
        def f():
            conteudo = s.conteudo()
            achou = [rel for rel, h in conteudo if ("<!-- %s" % marca) in h]
            if n == TODAS:
                esperado = len(conteudo)
            elif isinstance(n, tuple):
                esperado = len([1 for rel, _h in conteudo
                                if rel.split("/")[0] in n])
            elif n == 275:
                esperado = 270
            else:
                esperado = n
            return (len(achou) >= esperado,
                    u"marcador <!-- %s --> em %d página(s), esperado >= %d"
                    % (marca, len(achou), esperado))
        return f
    for i, (marca, n) in enumerate(MARCADORES, 1):
        s.check("M%02d" % i, u"entrega presente: %s" % marca, faz_marcador(marca, n))

    # H — home
    def h01():
        from _onda7_css import idioma_da_pagina
        ruins = []
        for rel in HOMES:
            h = s.ler(rel)
            palavras = SLOGAN[idioma_da_pagina(h)]
            m = re.search(r'<h2 data-aos="fade-right">(.*?)</h2>', h, re.S)
            bloco = m.group(1) if m else ""
            if not all(p in bloco for p in palavras) or bloco.count("<br>") != 2:
                ruins.append("%s (%r)" % (rel, bloco[:60]))
        return (not ruins, u"slogan errado em: %s" % "; ".join(ruins))
    s.check("H01", u"slogan em 3 linhas nas 4 homes", h01)

    def h02():
        maus = [rel for rel, h in s.todas() if "embrace to enhance" in h.lower()]
        return (not maus, u'slogan antigo "Embrace to Enhance" em %d página(s): %s'
                % (len(maus), ", ".join(maus[:5])))
    s.check("H02", u'0 ocorrência de "Embrace to Enhance"', h02)

    def h03():
        ruins = []
        for rel in HOMES:
            h = s.ler(rel)
            # conta o <li>, não a classe: os itens "--alto" carregam duas classes
            # com o mesmo prefixo e contar a classe inflaria o total.
            n = h.count('<li class="clientes-logos__item')
            if n != len(LOGOS_ESPERADOS):
                ruins.append("%s tem %d itens" % (rel, n))
            if "clientes-logos__title" not in h:
                ruins.append("%s sem título da barra" % rel)
        return (not ruins, u"; ".join(ruins))
    s.check("H03", u"barra de clientes com %d logos nas 4 homes" % len(LOGOS_ESPERADOS), h03)

    def h04():
        ruins = []
        for rel in HOMES:
            h = s.ler(rel)
            # `webp` entrou na lista na onda 61: o edp, o mercedes-benz e o taesa
            # passaram a ser servidos em WebP. Esta asserção cobra que o CLIENTE esteja
            # na barra — o formato do arquivo não é o que ela mede.
            achados = re.findall(r"/clientes/([a-z0-9\-]+)\.(?:svg|png|jpg|jpeg|webp)", h)
            if sorted(achados) != sorted(LOGOS_ESPERADOS):
                falta = set(LOGOS_ESPERADOS) - set(achados)
                sobra = set(achados) - set(LOGOS_ESPERADOS)
                ruins.append("%s falta=%s sobra=%s" % (rel, sorted(falta), sorted(sobra)))
        return (not ruins, u"; ".join(ruins))
    s.check("H04", u"logos da barra batem com o arquivo mestre", h04)

    def h05():
        ruins = []
        for rel in HOMES:
            h = s.ler(rel)
            i = h.find("<!-- onda6:praticas -->")
            trecho = h[i:i + 6000] if i >= 0 else ""
            n = len(re.findall(r"pratica|practice", trecho))
            if i < 0:
                ruins.append("%s sem bloco de práticas" % rel)
            elif n < 3:
                ruins.append("%s com %d referência(s) de prática" % (rel, n))
        return (not ruins, u"; ".join(ruins))
    s.check("H05", u"bloco dos 3 cards de práticas nas 4 homes", h05)

    def h06():
        ruins = []
        for rel in HOMES:
            h = s.ler(rel)
            i = h.find("<!-- onda8:hero-contatos -->")
            trecho = h[i:i + 8000] if i >= 0 else ""
            faltam = [nome for nome, agulha in CANAIS if agulha not in trecho]
            if faltam:
                ruins.append("%s sem %s" % (rel, "/".join(faltam)))
        return (not ruins, u"; ".join(ruins))
    s.check("H06", u"4 canais de contato no hero das 4 homes", h06)

    def h07():
        ruins = []
        for rel, h in s.conteudo():
            i = h.find("<!-- onda8:menu-contatos -->")
            if i < 0:
                continue
            trecho = h[i:i + 8000]
            faltam = [nome for nome, agulha in CANAIS if agulha not in trecho]
            if faltam:
                ruins.append("%s sem %s" % (rel, "/".join(faltam)))
        return (not ruins, u"%d página(s) com canal faltando: %s"
                % (len(ruins), "; ".join(ruins[:3])))
    s.check("H07", u"4 canais no header de todas as páginas", h07)

    def h08():
        # Invariante de navegação: toda página oferece o caminho para carreiras.
        # Em pt/en isso vem do onda7:menu-carreiras; em de, do menu nativo do tema.
        alvos = ["/carreiras/", "/careers/", "/karrieren/"]
        ruins = [rel for rel, h in s.conteudo() if not any(a in h for a in alvos)]
        return (not ruins, u"%d página(s) sem link de carreiras no menu: %s"
                % (len(ruins), ", ".join(ruins[:5])))
    s.check("H08", u"link de carreiras no menu de todas as páginas", h08)

    def h09():
        # `?ver=1` nos SVGs da barra é load-bearing: sem ele o plugin svgs-inline
        # do tema inlina os logos, as ids genéricas colidem e eles saem picados.
        # Ver tools_onda6/14_logos_clientes_sem_inline_svg.py.
        ruins = []
        for rel in HOMES:
            h = s.ler(rel)
            for m in re.finditer(r'/clientes/([a-z0-9\-]+\.svg)(\?[^"]*)?"', h):
                if not m.group(2):
                    ruins.append("%s -> %s" % (rel, m.group(1)))
        return (not ruins, u"%d logo(s) SVG sem a query anti-inline: %s"
                % (len(ruins), ", ".join(ruins[:4])))
    s.check("H09", u"logos SVG com a query que impede o inline", h09)

    # R — página "Nossa rede" (onda 7), uma por idioma
    def r01():
        alvos = ["pt/sobre-nos/nossa-rede/index.html", "en/about-us/our-network/index.html",
                 "de/ueber-uns/unser-netzwerk/index.html"]
        faltam = [a for a in alvos
                  if not os.path.exists(os.path.join(pub, a.replace("/", os.sep)))]
        return (not faltam, u"página(s) de rede ausente(s): %s" % ", ".join(faltam))
    s.check("R01", u'página "Nossa rede" nos 3 idiomas', r01)

    # L — quadro de líderes sem quem saiu (onda 6)
    def l01():
        # Onda 33 (#81): a lista ganhou os 4 nomes que estavam em modal escondido na
        # en/homepage. A cobertura mais ampla — nenhuma página do site inteiro citando
        # quem saiu — é a S118; esta segue guardando as homes e o quadro de líderes.
        saiu = ["Giulia", "Mariana Sim", "Matheus",
                "Marcelo Soares", "Marcelo Massarente", "Lucas Santiago",
                "Fernando Fabbris"]
        ruins = []
        for rel in HOMES + ["pt/lider/index.html"]:
            p = os.path.join(pub, rel.replace("/", os.sep))
            if not os.path.exists(p):
                continue
            h = s.ler(rel)
            for nome in saiu:
                if nome in h:
                    ruins.append("%s contém %s" % (rel, nome))
        return (not ruins, u"; ".join(ruins))
    s.check("L01", u"quem saiu não aparece nas homes/líderes", l01)

    # S — pedidos das ondas 10-12 (promovidos de PENDENTE em 31/07/2026)
    def s01():
        # S-01: a APRESENTAÇÃO vira escadinha (3 spans .onda10-degrau); as
        # PALAVRAS continuam protegidas pela H01 (a tripla nova é a issue #79).
        ruins = []
        for rel in HOMES:
            h = s.ler(rel)
            m = re.search(r'<h2 data-aos="fade-right">(.*?)</h2>', h, re.S)
            bloco = m.group(1) if m else ""
            degraus = re.findall(r'onda10-degrau--([123])', bloco)
            if sorted(degraus) != ["1", "2", "3"]:
                ruins.append("%s tem degraus %s" % (rel, degraus))
        return (not ruins, u"; ".join(ruins))
    s.check("S01", u"slogan em escadinha (3 degraus) nas 4 homes", s01)

    def s02():
        from _onda7_css import idioma_da_pagina
        ruins = []
        for rel in HOMES:
            h = s.ler(rel)
            esperado = TITULO_BARRA[idioma_da_pagina(h)]
            m = re.search(r'clientes-logos__title[^>]*>([^<]*)<', h)
            achado = m.group(1).strip() if m else ""
            if achado != esperado:
                ruins.append("%s: %r" % (rel, achado[:60]))
        return (not ruins, u"título fora do mestre em: %s" % "; ".join(ruins))
    s.check("S02", u"título da barra igual ao gerado do arquivo mestre (3 línguas)", s02)

    def s04():
        # S-04: o bug era o estado .menu:hover (barra fica branca em TODAS as
        # páginas) sem cor de ícone tratada. O bloco tem que cobrir o hover e
        # usar o navy medido (16.5:1 contra branco).
        css = s.ler("wp-content/uploads/2026/07/onda6/onda6.css")
        ini = css.find("/* onda10:header-contraste:ini */")
        fim = css.find("/* onda10:header-contraste:fim */")
        if ini < 0 or fim < 0:
            return (False, u"bloco onda10:header-contraste ausente do onda6.css")
        bloco = css[ini:fim]
        faltam = [ag for ag in (".menu:hover", "#020e66") if ag not in bloco]
        return (not faltam, u"bloco sem: %s" % ", ".join(faltam))
    s.check("S04", u"contraste dos ícones cobre o estado hover do header", s04)

    def s06():
        # S-06 (reescrita na onda 14): a seção "nossos números" saiu da home
        # (S-31) — os números vivem no hero (S-27). Sem ponto FINAL nos textos.
        # Abreviação interna (o "Mrd." alemão) não conta.
        ruins = []
        for rel in HOMES:
            h = s.ler(rel)
            txts = re.findall(r'hero-numeros__texto">([^<]*)</span>', h)
            if not txts:
                ruins.append("%s sem números no hero" % rel)
            for txt in txts:
                if txt.rstrip().endswith("."):
                    ruins.append("%s: %r" % (rel, txt[-30:]))
        return (not ruins, u"; ".join(ruins))
    s.check("S06", u"números do hero sem ponto final", s06)



    def s09():
        # S-09/S-20: a mandala de 8 práticas sumiu; no lugar, a navegação
        # simples .praticas-nav (3 práticas atuais) nas ~97 páginas de prática.
        sobrou = [rel for rel, h in s.todas() if "mandala-wrap" in h]
        n_nav = sum(1 for _rel, h in s.todas() if "<!-- onda12:praticas-nav -->" in h)
        # 90 -> 20: a S-107 (#165) deixou 21 páginas de prática (uma URL cada)
        ok = not sobrou and n_nav >= 20
        return (ok, u"mandala em %d página(s) %s; praticas-nav em %d (esperado >= 20)"
                % (len(sobrou), ", ".join(sobrou[:3]), n_nav))
    s.check("S09", u"0 rodas de 8 práticas; navegação simples no lugar", s09)

    def s13():
        # S-13: o form de candidatura (.job-contact--topo) é a 1ª seção depois
        # do hero em carreiras — tem que vir ANTES de .career-path no fonte.
        ruins = []
        for rel in CARREIRAS:
            h = s.ler(rel)
            i = h.find("job-contact--topo")
            j = h.find("career-path")
            if i < 0:
                ruins.append("%s sem o form no topo" % rel)
            elif j >= 0 and j < i:
                ruins.append("%s com o form depois de career-path" % rel)
        return (not ruins, u"; ".join(ruins))
    s.check("S13", u"formulário de carreiras na 1ª dobra (antes das outras seções)", s13)

    # --- Formulário de candidatura novo -> AWS (onda 45, #202) --------------
    CARGOS_VALIDOS = set([
        u"Summer Intern (Dez-Fev do penúltimo a último ano de formação)",
        u"Summer Intern (Dez-Fev - formandos até 2022)",
        u"Summer Intern (Dez-Fev - formandos até 2023)",
        u"Summer Intern (Dez-Fev - formandos até 2024)",
        u"Summer Intern",
        u"Summer Intern (Dec-Feb - expected graduation until 2022)",
        u"Summer Intern (Dec-Feb - expected graduation until 2023)",
        u"Summer Intern (Dec-Feb - expected graduation until 2024)",
        u"Summer Intern (Dec-Feb at second-to-last or last year of graduation)",
        u"Intern (penúltimo a último ano de formação)",
        u"Intern (second-to-last or last year of graduation)",
        u"Intern",
        u"Business Analyst (recém formado até 3 anos)",
        u"Business Analyst (recém formado até 4 anos)",
        u"Business Analyst (recently graduated - up to 3yrs)",
        u"Business Analyst (recently graduated - up to 4 yrs)",
        u"Business Analyst", u"Fellow Associate", u"Associate",
        u"Summer Associate (MBA)", u"Engagement Manager", u"Associate Partner",
        u"Fellow BA",
    ])

    def s135():
        # As 3 páginas de carreiras têm o form novo e ZERO resquício do Formidable
        # do WordPress (o cutover não pode deixar um form que posta pro WP morto).
        ruins = []
        for rel in CARREIRAS:
            h = s.ler(rel)
            if 'id="mirow-carreiras-form"' not in h:
                ruins.append("%s sem form novo" % rel)
            if re.search(r'id="frm_form_\d+_container"', h) or "frm_ajax_submit" in h:
                ruins.append("%s ainda tem Formidable" % rel)
        return (not ruins, u"; ".join(ruins))
    s.check("S139", u"carreiras: form novo presente e Formidable do WP removido (3 idiomas)", s135)

    def s136():
        # O form posta no API Gateway (assinador) e tem o gate hCaptcha.
        ruins = []
        for rel in CARREIRAS:
            h = s.ler(rel)
            if "execute-api" not in h or "data-endpoint" not in h:
                ruins.append("%s sem endpoint do API Gateway" % rel)
            if 'class="h-captcha"' not in h and "h-captcha" not in h:
                ruins.append("%s sem widget hCaptcha" % rel)
            if "js.hcaptcha.com" not in h:
                ruins.append("%s sem script hCaptcha" % rel)
            if "X-Captcha-Token" not in h:
                ruins.append("%s sem header do captcha no submit" % rel)
        return (not ruins, u"; ".join(ruins))
    s.check("S140", u"carreiras: posta no API Gateway + gate hCaptcha (token em header)", s136)

    def s137():
        # MEDE O EFEITO: todo <option> de pretended_position tem que ser um cargo
        # que o /webhook/.../start aceita (cargos_corretos) — senão o candidato é
        # rejeitado com 400 e a candidatura some sem ninguém ver.
        ruins = []
        for rel in CARREIRAS:
            h = s.ler(rel)
            m = re.search(r'name="pretended_position"[^>]*>(.*?)</select>', h, re.S)
            if not m:
                ruins.append("%s sem select de cargo" % rel); continue
            for om in re.finditer(r'<option(?:\s+value="([^"]*)")?[^>]*>(.*?)</option>', m.group(1), re.S):
                val = om.group(1) if om.group(1) is not None else om.group(2).strip()
                val = val.strip()
                if val == "":
                    continue  # placeholder "Selecione"
                if val not in CARGOS_VALIDOS:
                    ruins.append("%s: cargo inválido %r" % (rel, val[:40]))
        return (not ruins, u"; ".join(ruins[:4]))
    s.check("S141", u"carreiras: todo cargo do select é aceito pelo /start (mede o efeito)", s137)

    def s138():
        # CSS do form existe no onda6.css (o cache-bust em si é invariante da C02).
        css = s.ler("wp-content/uploads/2026/07/onda6/onda6.css")
        det = []
        if "onda45:carreiras-form" not in css:
            det.append("bloco onda45 ausente no onda6.css")
        for rel in CARREIRAS:
            if "onda6.css?v=" not in s.ler(rel):
                det.append("%s sem referência versionada ao onda6.css" % rel)
        return (not det, u"; ".join(det))
    s.check("S142", u"carreiras: CSS do form presente no onda6.css (bloco onda45)", s138)

    def s143():
        # Onda 47 (#101/#42): o site é servido na raiz de mirow.com.br.
        # (a) CNAME liga o domínio custom no Pages; (b) 404.html com a marca;
        # (c) NENHUM resquício do staging (/mirow-site/ ou github.io) em nenhum
        # arquivo de texto de public/; (d) canonical absoluto no host final.
        det = []
        p_cname = os.path.join(pub, "CNAME")
        if not os.path.exists(p_cname):
            det.append("public/CNAME ausente")
        elif s.ler("CNAME").strip() != "mirow.com.br":
            det.append("CNAME != mirow.com.br")
        p404 = os.path.join(pub, "404.html")
        if not os.path.exists(p404):
            det.append("public/404.html ausente")
        # 2026-08-12 (#210): a marca na 404 deixou de ser wordmark em texto e
        # virou o logo SVG oficial (a S145 confere que o arquivo existe).
        elif not re.search(r'<img[^>]*class="logo"|MIROW', s.ler("404.html")):
            det.append("404.html sem a marca (nem logo, nem wordmark)")
        sujos = 0
        exemplo = None
        for dirpath, _dirs, files in os.walk(pub):
            for nome in files:
                if not nome.lower().endswith((".html", ".css", ".js", ".xml", ".txt", ".json")):
                    continue
                fp = os.path.join(dirpath, nome)
                with io.open(fp, encoding="utf-8", errors="ignore") as f:
                    conteudo = f.read()
                if "mirow-site" in conteudo or "mirow-co.github.io" in conteudo:
                    sujos += 1
                    exemplo = exemplo or os.path.relpath(fp, pub)
        if sujos:
            det.append(u"%d arquivo(s) ainda citam o staging (ex.: %s)" % (sujos, exemplo))
        for rel in HOMES:
            can = re.search(r'rel="canonical" href="([^"]+)"', s.ler(rel))
            if not can or not can.group(1).startswith(HOST):
                det.append(u"%s: canonical não é absoluto em %s" % (rel, HOST))
        return (not det, u"; ".join(det[:4]))
    s.check("S143", u"domínio custom: CNAME + 404 + 0 resquício do staging (#101)", s143)

    def s144():
        # Onda 49 (#102): os caminhos de sitemap do WP antigo (que os crawlers
        # ainda pedem aos milhares/mês, ver AWStats 2026 no repo privado) servem
        # um <sitemapindex> apontando para o sitemap canônico. Padrão S120: a
        # asserção RECALCULA via gerador e compara byte a byte — shim editado à
        # mão, caminho faltando ou host divergente do 90 quebram aqui.
        import importlib.util
        det = []
        raiz = os.path.dirname(pub)
        def carrega(nome_mod, arq):
            p = os.path.join(raiz, "tools_onda6", arq)
            spec = importlib.util.spec_from_file_location(nome_mod, p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
        gen = carrega("gen100", "100_wp_sitemap_shims.py")
        gen90 = carrega("gen90_s144", "90_sitemap_e_raiz.py")
        if gen.BASE != gen90.BASE:
            det.append(u"BASE do 100 (%s) diverge do 90 (%s)" % (gen.BASE, gen90.BASE))
        esperado = gen.xml_do_shim()
        faltam, divergem = [], []
        for rel in gen.caminhos_legados():
            fp = os.path.join(pub, rel.replace("/", os.sep))
            if not os.path.exists(fp):
                faltam.append(rel)
            elif s.ler(rel) != esperado:
                divergem.append(rel)
        if faltam:
            det.append(u"%d shim(s) ausente(s): %s" % (len(faltam), "; ".join(faltam[:3])))
        if divergem:
            det.append(u"%d shim(s) divergem do gerador: %s" % (len(divergem), "; ".join(divergem[:3])))
        # o alvo dos shims tem de ser o mesmo sitemap que o robots anuncia
        if (u"Sitemap: %s" % gen.SITEMAP_CANONICO) not in s.ler("robots.txt"):
            det.append(u"robots.txt não aponta para %s" % gen.SITEMAP_CANONICO)
        return (not det, u"%d caminho(s) legado(s); %s"
                % (len(gen.caminhos_legados()), "; ".join(det[:3]) or u"todos batem"))
    s.check("S144", u"sitemaps antigos do WP servem index p/ o sitemap canônico (#102)", s144)

    def s145():
        # #210: 404 destacada com logo Mirow e medição. Mede o efeito: cada
        # referência resolve para arquivo que EXISTE no disco (lição da M01/S123),
        # e os destinos dos links de idioma existem como páginas.
        html = s.ler("404.html")
        det = []
        m = re.search(r'<img[^>]*class="logo"[^>]*src="([^"?]+)', html)
        if not m:
            det.append(u"sem <img class=\"logo\"> na 404")
        elif not os.path.exists(os.path.join(pub, m.group(1).lstrip("/").replace("/", os.sep))):
            det.append(u"logo aponta p/ arquivo inexistente: %s" % m.group(1))
        # erro 10 do CLAUDE.md: tag literal nao tolera atributo novo. A onda 62d pos
        # `defer` na tag e `<script src=` deixou de casar, embora o script estivesse la.
        m = re.search(r'<script[^>]*[ ]src="([^"?]*onda31-medicao\.js)[^"]*"', html)
        if not m:
            det.append(u"404 sem onda31-medicao.js (page_view de 404 não conta)")
        elif not os.path.exists(os.path.join(pub, m.group(1).lstrip("/").replace("/", os.sep))):
            det.append(u"medição aponta p/ arquivo inexistente: %s" % m.group(1))
        if "googletagmanager.com/gtag/js?id=G-5VTS0MZK79" not in html:
            det.append(u"404 sem o loader gtag da propriedade institucional")
        for rota in ("pt", "en", "de"):
            if ('href="/%s/"' % rota) not in html:
                det.append(u"404 sem link para /%s/" % rota)
            elif not os.path.exists(os.path.join(pub, rota, "index.html")):
                det.append(u"/%s/ não existe no disco" % rota)
        return (not det, u"; ".join(det[:4]))
    s.check("S145", u"404 com logo Mirow real, medição GA4 e links pt/en/de resolvendo (#210)", s145)

    def s146():
        # #220: a coluna Vaivém (Folha, 10/02/2026) com o alerta do Andreas sobre
        # celulose entra na lista de imprensa das 3 páginas. Mede o EFEITO (P2.1):
        # não basta a URL aparecer — a data em <time datetime> tem de bater com
        # a que a Folha publica, o logo tem de resolver para arquivo no disco, e o
        # item tem de estar na POSIÇÃO QUE A DATA DELE MANDA.
        #
        # ONDA 65: esta asserção cobrava "tem de ser o PRIMEIRO da lista", e o
        # próprio comentário dela declarava o motivo entre parênteses — "(é o mais
        # recente do acervo)". Era um VALOR GÊMEO: em 13/08 topo e mais-recente
        # eram a mesma coisa; com as 14 matérias da #237, sete delas posteriores,
        # o item caiu para 8º — CORRETAMENTE — e a asserção bloqueou o deploy por
        # motivo certo e alvo errado. Terceira vez nesta classe (S125 na onda 33b,
        # S119 na 62c). Agora ela mede o invariante que "topo" representava: a
        # posição do item é igual ao número de matérias com data posterior — o que
        # vale com qualquer quantidade de matérias novas.
        URL_VAIVEM = ("https://www1.folha.uol.com.br/colunas/vaivem/2026/02/"
                      "exportacao-de-celulose-cresce-mas-setor-pode-ter-desequilibrio.shtml")
        alvos = ["pt/imprensa/index.html", "en/press/index.html", "de/presse/index.html"]
        det = []
        for rel in alvos:
            html = s.ler(rel)
            itens = re.findall(r'<li class="onda18-imprensa__item">.*?</li>', html, re.S)
            if not itens:
                det.append(u"%s sem lista de imprensa" % rel)
                continue
            if URL_VAIVEM not in html:
                det.append(u"%s sem a coluna Vaivém" % rel)
                continue
            pos = next((i for i, it in enumerate(itens) if URL_VAIVEM in it), -1)
            item = itens[pos]
            if 'datetime="2026-02-10"' not in item:
                det.append(u"%s: a coluna Vaivém não está datada 2026-02-10 "
                           u"(a data que a Folha publica)" % rel)
            if '>Folha de S.Paulo<' not in item:
                det.append(u"%s: a coluna Vaivém não está rotulada Folha de S.Paulo" % rel)
            # a posição é a que a data manda (o que "no topo" representava)
            posteriores = sum(1 for d in re.findall(r'datetime="([^"]+)"', html)
                              if d > "2026-02-10")
            if pos != posteriores:
                det.append(u"%s: Vaivém em %dº, mas há %d matéria(s) mais nova(s) "
                           u"— devia estar em %dº" % (rel, pos + 1, posteriores,
                                                      posteriores + 1))
            # a lista inteira tem de seguir em ordem decrescente de data
            datas = re.findall(r'datetime="([^"]+)"', html)
            if datas != sorted(datas, reverse=True):
                det.append(u"%s: lista fora de ordem cronológica" % rel)
            m = re.search(r'<img[^>]*class="onda41-imprensa__logo"[^>]*src="([^"?]+)', item)
            if not m:
                det.append(u"%s: a coluna Vaivém está sem logo" % rel)
            elif not os.path.exists(os.path.join(pub, m.group(1).lstrip("/").replace("/", os.sep))):
                det.append(u"%s: logo aponta p/ inexistente %s" % (rel, m.group(1)))
        return (not det, u"; ".join(det[:4]))
    s.check("S146", u"coluna Vaivém/Folha (10/02/2026, Andreas) na imprensa pt/en/de, na posição da data (#220)", s146)

    def s147():
        # #211 (onda 53): a home diz que a consultoria é tradicional mas usa IA.
        # Mede o que o pedido do Mario tem de verificável no HTML; o EFEITO
        # renderizado (selo AO LADO do slogan, faixa ATRAVESSANDO as 3 práticas,
        # subtítulo sem estourar a dobra) é da V30.
        marcas = {
            "pt/index.html": (u"consultoria estratégica tradicional que utiliza IA",
                              u"Inteligência Artificial", u"Transversal às três práticas"),
            "en/index.html": (u"traditional strategy consulting that uses AI",
                              u"Artificial Intelligence", u"Cutting across all three practices"),
            "de/index.html": (u"klassische Strategieberatung, die KI",
                              u"Künstliche Intelligenz", u"Übergreifend über alle drei Practices"),
        }
        det = []
        for rel, (subt, titulo, tag) in marcas.items():
            html = s.ler(rel)
            if subt not in html:
                det.append(u"%s: subtítulo não fala de IA" % rel)
            if u'class="onda53-selo-ia">AI Powered<' not in html:
                det.append(u"%s: sem o selo AI Powered" % rel)
            # o selo tem de estar DENTRO do wrapper que o põe ao lado do slogan
            if not re.search(r'<div class="onda53-slogan">'
                             r'<span class="onda53-selo-ia">AI Powered</span><h2', html):
                det.append(u"%s: selo não precede o slogan (eyebrow)" % rel)
            bloco = re.search(r'<div class="praticas-3">(.*?)<!-- /onda6:praticas', html, re.S)
            if not bloco:
                bloco = re.search(r'<div class="praticas-3">(.*)', html, re.S)
            if not bloco or "onda53-ia" not in bloco.group(1):
                det.append(u"%s: faixa de IA fora do bloco das práticas" % rel)
            elif bloco.group(1).find("onda53-ia") < bloco.group(1).rfind("praticas-3__card"):
                det.append(u"%s: faixa de IA antes do último card (tem de vir ABAIXO das 3)" % rel)
            for t in (titulo, tag):
                if t not in html:
                    det.append(u"%s: falta \"%s\"" % (rel, t[:28]))
        return (not det, u"; ".join(det[:4]))
    s.check("S147", u'home "AI Powered": selo no slogan e IA transversal sob as 3 práticas (#211)', s147)

    def s148():
        # Causa-raiz de um defeito real da onda 53: escrever_bloco_css tem a
        # assinatura (pub, chave, css, onda=...) e foi chamada fora de ordem —
        # o CSS INTEIRO virou o nome do marcador. Como o nome mudava a cada
        # edicao, o helper nunca reconhecia o bloco e ANEXAVA outro: 5 blocos,
        # 20 copias de cada regra, e font-weight morto que a S127 acusava.
        # Esta asserção pega a CLASSE: marcador tem de ser curto e de uma linha,
        # todo :ini tem o seu :fim, e nenhuma chave pode aparecer duas vezes.
        css = s.ler("wp-content/uploads/2026/07/onda6/onda6.css")
        det = []
        # o marcador aceita anotacao depois do :ini (ex.: a onda45 escreve
        # "/* onda45:carreiras-form:ini (#202/#203 — ...) */"), entao o que
        # importa e a CHAVE antes do :ini/:fim
        rex = re.compile(r'/\*([^*]{0,400}?):(ini|fim)\b[^*]{0,300}?\*/', re.S)
        marcas = rex.findall(css)
        inis = [n for n, k in marcas if k == "ini"]
        fims = [n for n, k in marcas if k == "fim"]
        for nome in inis:
            n = nome.strip()
            if "\n" in n or len(n) > 60:
                det.append(u"marcador gigante (%d chars, %d linha[s]) — CSS dentro"
                           u" do nome? começa com \"%s…\""
                           % (len(n), n.count("\n") + 1, n[:34].replace("\n", " ")))
            elif not re.match(r'^onda[\d.]+:[a-z0-9_-]+$', n):
                det.append(u"marcador fora do padrão onda<N>:<chave>: \"%s\"" % n[:40])
        vistos = {}
        for nome in inis:
            n = nome.strip()
            vistos[n] = vistos.get(n, 0) + 1
        dup = [n for n, c in vistos.items() if c > 1]
        if dup:
            det.append(u"bloco(s) duplicado(s): %s" % ", ".join(d[:30] for d in dup[:3]))
        if len(inis) != len(fims):
            det.append(u"%d :ini para %d :fim" % (len(inis), len(fims)))
        return (not det, u"%d bloco(s); %s" % (len(inis), "; ".join(det[:3]) or u"todos bem formados"))
    s.check("S148", u"blocos marcados do onda6.css bem formados e sem duplicata", s148)

    GEO_LISTAGENS = {"pt": "pt/sobre-nos/lideres/index.html",
                     "en": "en/about-us/leaders/index.html",
                     "de": "de/ueber-uns/fuehrungskraefte/index.html"}
    GEO_LIDERES = [u"Andreas Mirow", u"Felipe Diniz", u"Stephan Friedrich",
                   u"Renato Alvarenga", u"Michael Munch", u"Raoni Morais"]

    def s149():
        # #230 (GEO): o bloco JSON-LD dos líderes tem de PARSEAR (não basta a
        # string existir), ter Organization + exatamente 6 Person, cada Person
        # com sameAs de LinkedIn e url resolvendo para página que EXISTE no
        # disco (padrão S123: resolver a referência). Elmar e João Daniel FORA
        # por decisão do Felipe; foundingDate FORA porque não é dado publicado.
        det = []
        for lang, rel in GEO_LISTAGENS.items():
            h = s.ler(rel)
            m = re.search(r'<script type="application/ld\+json" id="onda59-geo">'
                          r'(.*?)</script>', h, re.S)
            if not m:
                det.append(u"%s: bloco onda59-geo ausente" % lang)
                continue
            try:
                g = json.loads(m.group(1))["@graph"]
            except (ValueError, KeyError) as e:
                det.append(u"%s: JSON inválido (%s)" % (lang, e))
                continue
            pessoas = [n for n in g if n.get("@type") == "Person"]
            orgs = [n for n in g if n.get("@type") != "Person"]
            # Quantos lideres, DERIVADO do `PAGINAS` do 110 -- que e a mesma fonte
            # de onde o proprio bloco JSON-LD e montado. Estava escrito `!= 6`, e
            # em 20/08 o Michael Munch saiu da firma: o bloco passou a ter 5 Person,
            # corretamente, e a asserção acusou as 3 linguas. Numero de pessoas numa
            # asserção e valor gemeo do cadastro; quem manda e o cadastro.
            esperado = len(_mod110().PAGINAS)
            if len(pessoas) != esperado or len(orgs) != 1:
                det.append(u"%s: %d Person / %d Organization (esperado %d/1)"
                           % (lang, len(pessoas), len(orgs), esperado))
            # Onda 60b. Tres fatos do Mario, e a distincao entre eles e o ponto:
            #   SEDE  = assento juridico, CNPJ 15.353.236/0001-89 ativo, RIO -> `address`
            #   ESCRITORIO = onde o time trabalha, SAO PAULO -> `location` (Place)
            #   fundacao 12/04/2012, `foundingLocation` no Rio (nasceu la em 2012)
            # A primeira versao desta asserção cobrava Sao Paulo no `address` porque eu
            # li "endereco novo" como mudanca de sede. Nao era.
            if "__PREENCHER" in m.group(1):
                det.append(u"%s: placeholder não-preenchido no ar" % lang)
            org = g[0] if g else {}
            sede = org.get("address") or {}
            if sede.get("addressLocality") != u"Rio de Janeiro" or sede.get("addressRegion") != "RJ":
                det.append(u"%s: sede é %r/%r (esperado Rio de Janeiro/RJ — o CNPJ de lá "
                           u"segue ativo)" % (lang, sede.get("addressLocality"),
                                              sede.get("addressRegion")))
            if sede.get("postalCode") != "22290-160":
                det.append(u"%s: CEP da sede = %r" % (lang, sede.get("postalCode")))
            escr = (org.get("location") or {}).get("address") or {}
            if escr.get("addressLocality") != u"São Paulo" or escr.get("addressRegion") != "SP":
                det.append(u"%s: escritório é %r/%r (esperado São Paulo/SP)"
                           % (lang, escr.get("addressLocality"), escr.get("addressRegion")))
            if escr.get("postalCode") != "04029-100":
                det.append(u"%s: CEP do escritório = %r" % (lang, escr.get("postalCode")))
            if org.get("foundingDate") != "2012-04-12":
                det.append(u"%s: foundingDate = %r (esperado 2012-04-12)"
                           % (lang, org.get("foundingDate")))
            if u"Rio" not in ((org.get("foundingLocation") or {}).get("name") or ""):
                det.append(u"%s: foundingLocation deixou de ser o Rio" % lang)
            nomes = u" ".join(p.get("name", "") for p in pessoas)
            for fora in (u"Elmar", u"Daniel Ramos"):
                if fora in nomes:
                    det.append(u"%s: %s entrou no schema sem decisão do Felipe" % (lang, fora))
            for p in pessoas:
                nome = p.get("name", "?")
                same = p.get("sameAs") or []
                if not any("linkedin.com/in/" in x for x in same):
                    det.append(u"%s: %s sem LinkedIn no sameAs" % (lang, nome))
                url = p.get("url", "")
                alvo = url.replace("https://mirow.com.br/", "").strip("/")
                fp = os.path.join(pub, alvo.replace("/", os.sep), "index.html")
                if not alvo or not os.path.exists(fp):
                    det.append(u"%s: url de %s não resolve no disco (%s)" % (lang, nome, url))
                elif "http-equiv=\"refresh\"" in s.ler(alvo + "/index.html"):
                    det.append(u"%s: url de %s aponta para stub redirect" % (lang, nome))
        return (not det, u"; ".join(det[:4]) or u"3 línguas: 6 Person válidos, urls resolvem")
    s.check("S149", u"JSON-LD GEO: os líderes do cadastro, parseáveis, com LinkedIn e url no disco (#230)", s149)

    def s150():
        # #232 (GEO): meta description presente, não-vazia e ÚNICA nas homes e
        # listagens de líderes; a da home pt é o texto do Felipe verbatim.
        FELIPE = (u"Mirow & Co. — consultoria estratégica brasileira, sede no Rio de "
                  u"Janeiro. Estratégia, inovação, pricing e compras para empresas de "
                  u"grande porte. Atendimento em português, inglês e alemão.")
        PAGS = ["pt/index.html", "en/index.html", "de/index.html"] + list(GEO_LISTAGENS.values())
        det = []
        for rel in PAGS:
            h = s.ler(rel)
            tags = re.findall(r'<meta name="description" content="([^"]*)"', h)
            if len(tags) != 1:
                det.append(u"%s: %d meta description (esperado 1)" % (rel, len(tags)))
            elif len(tags[0].strip()) < 50:
                det.append(u"%s: description curta/vazia" % rel)
            elif rel == "pt/index.html" and tags[0] != FELIPE:
                det.append(u"home pt: texto difere do sugerido pelo Felipe")
        return (not det, u"; ".join(det[:4]) or u"6 páginas com description única")
    s.check("S150", u"meta description nas homes e listagens de líderes (#232)", s150)

    def s151():
        # NASCEU na onda 59 (#231) cobrando que o slug numerico do Michael Munch
        # tivesse virado nominal: `michael-munch` era conteudo canonico e `591` era
        # stub apontando para ele. Em 20/08/2026 o Mario pediu para tirar a pessoa
        # "de tudo" -- ele deixou a firma no dia 19 --, e a premissa daquela versao
        # virou falsa por decisao, nao por defeito.
        #
        # A asserção NAO foi apagada: trocou de sujeito preservando o invariante que
        # ela sempre protegeu -- ninguem chega a uma pagina de perfil encerrada, e
        # ninguem da dois saltos para descobrir isso. Agora os 8 caminhos (4 do slug
        # nominal e 4 do numerico) tem de ser stub noindex apontando DIRETO para a
        # listagem de lideres, e nenhum arquivo servido pode referenciar nenhum deles.
        #
        # E ela deixa um registro que vale mais que o teste: na onda 68 a versao
        # anterior desta asserção acusou 8 referencias ao `591` dentro do JSON-LD do
        # Yoast da pagina do Michael. Elas estavam la desde a onda 59, ESCAPADAS
        # (`https:\/\/...\/591\/`), e esta asserção procurava a forma limpa --
        # entao passou verde por um mes. Quem as revelou foi o `143`, ao reserializar
        # o JSON com json.dumps do Python, que nao escapa barra. Ver erro 17.
        CAMINHOS = [
            "pt/lider/michael-munch/index.html",
            "en/leader/michael-munch/index.html",
            "de/lider/michael-munch/index.html",
            "de/leader/michael-munch/index.html",
            "pt/lider/591/index.html", "pt/leader/591/index.html",
            "lider/591/index.html", "leader/591/index.html",
        ]
        LIDERES = ("/sobre-nos/lideres/", "/about-us/leaders/",
                   "/ueber-uns/fuehrungskraefte/")
        det = []
        for rel in CAMINHOS:
            fp = os.path.join(pub, rel.replace("/", os.sep))
            if not os.path.exists(fp):
                det.append(u"%s desapareceu — deveria ser stub" % rel)
                continue
            h = s.ler(rel)
            if "noindex" not in h:
                det.append(u"%s não é noindex" % rel)
            m = re.search(r'content="0;url=([^"]+)"', h)
            if not m:
                det.append(u"%s sem destino de redirect" % rel)
            elif not any(a in m.group(1) for a in LIDERES):
                det.append(u"%s redireciona para %s, e não para a listagem "
                           u"(dois saltos)" % (rel, m.group(1)))

        # nenhum arquivo servido referencia o slug, o id numerico ou o nome. Cobre
        # .html, .xml E .json — o `busca-indice.json` da onda 67 e servido tambem, e
        # e onde um nome removido reaparece com mais facilidade.
        sujos = []
        for dp, _d, fs in os.walk(pub):
            for nome in fs:
                if not nome.lower().endswith((".html", ".xml", ".json", ".txt")):
                    continue
                fp = os.path.join(dp, nome)
                rel = os.path.relpath(fp, pub).replace(os.sep, "/")
                if rel in CAMINHOS:
                    continue
                with io.open(fp, encoding="utf-8", errors="ignore") as f:
                    conteudo = f.read()
                for agulha in ("michael-munch", "lider/591", "leader/591",
                               "Michael Munch", "Michael-Munch", "modal_591"):
                    if agulha in conteudo:
                        sujos.append(u"%s cita %s" % (rel, agulha))
                        break
        det.extend(sujos[:6])
        return (not det, u"; ".join(det[:6])
                + (u" (+%d)" % (len(det) - 6) if len(det) > 6 else u""))

    s.check("S151", u"perfil encerrado: os 8 caminhos são stub para a listagem, e nada os cita (#231)", s151)

    def s152():
        # #233 (GEO): as páginas individuais dos 6 líderes têm cargo + bio +
        # LinkedIn — e a bio BATE com o card da listagem do idioma (recalcular
        # e comparar, padrão S116/S120: a listagem é a fonte única).
        det = []
        for lang, rel in GEO_LISTAGENS.items():
            h = s.ler(rel)
            cards = re.findall(r'<button class="page-leaders__list-item".*?</button>', h, re.S)
            bios = {}
            for card in cards:
                mt = re.search(r'page-leaders__list-title">(.*?)<small', card, re.S)
                mb = re.search(r'content-summary">(.*?)</ul>', card, re.S)
                if mt and mb:
                    nome = re.sub(r"<[^>]+>", "", mt.group(1)).replace("Private:", "").strip()
                    li = re.findall(r"<li>(.*?)</li>", mb.group(1), re.S)
                    bios[nome] = re.sub(r"<[^>]+>", "", li[0]).strip() if li else ""
            m = re.search(r'id="onda59-geo">(.*?)</script>', h, re.S)
            pessoas = json.loads(m.group(1))["@graph"][1:] if m else []
            for p in pessoas:
                url = p.get("url", "").replace("https://mirow.com.br/", "").strip("/")
                try:
                    ind = s.ler(url + "/index.html")
                except IOError:
                    det.append(u"%s: página de %s ausente" % (lang, p.get("name")))
                    continue
                m2 = re.search(r"onda59:geo-bio:ini(.*?)onda59:geo-bio:fim", ind, re.S)
                if not m2:
                    det.append(u"%s: %s sem bloco de bio" % (lang, p.get("name")))
                    continue
                bloco = m2.group(1)
                if "onda59-cargo" not in bloco or "linkedin.com/in/" not in bloco:
                    det.append(u"%s: %s sem cargo ou LinkedIn" % (lang, p.get("name")))
                nome_card = [n for n in bios if n.split()[0] in p.get("name", "")]
                # Onda 72 (#250): quem tem BIO_MEDIA no 110 leva parágrafos na página
                # individual, não os bullets do card. A comparação segue sendo contra a
                # fonte que gera o bloco — só que a fonte, para esses, é a constante.
                esperado_bm = None
                for chave, textos in _mod110().BIO_MEDIA.items():
                    if nome_card and chave.split()[0] in p.get("name", ""):
                        esperado_bm = textos.get(lang, [None])[0]
                if esperado_bm is not None:
                    if esperado_bm not in bloco:
                        det.append(u"%s: bio média de %s diverge da constante do 110"
                                   % (lang, p.get("name")))
                elif nome_card and bios[nome_card[0]] and bios[nome_card[0]] not in bloco:
                    det.append(u"%s: bio de %s diverge da listagem" % (lang, p.get("name")))
        return (not det, u"; ".join(det[:4]) or u"18 páginas com cargo+bio+LinkedIn da listagem")
    s.check("S152", u"páginas individuais de líder com cargo, bio e LinkedIn (#233)", s152)

    def s153():
        # Onda 60 (PageSpeed 18/08). O relatório citou 4 <img> sem alt; esta asserção
        # cobra a CLASSE, não os 4 casos: nenhuma imagem de conteúdo sem alt, em
        # nenhuma das páginas. alt="" é permitido (decorativa declarada) — o que não
        # se aceita é o atributo AUSENTE, que é o que o Lighthouse acusa.
        det = []
        total = 0
        for rel, h in s.todas():
            for m in re.finditer(r"<img\b[^>]*>", h):
                tag = m.group(0)
                total += 1
                if not re.search(r'\balt\s*=', tag):
                    src = re.search(r'src="([^"]*)"', tag)
                    det.append(u"%s: %s" % (rel, (src.group(1) if src else tag)[:60]))
        return (not det, u"%d imagens; %s" % (
            total, u"; ".join(det[:4]) or u"todas com alt"))
    s.check("S153", u"toda imagem tem atributo alt (PageSpeed, a11y + SEO)", s153)

    def s154():
        # Onda 60. A logo do <h1> carregava alt="Stratigital" — nome do tema anterior —
        # em 109 páginas, então o cabeçalho de nível 1 de TODO o site anunciava a marca
        # errada para robô e leitor de tela. A asserção proíbe a classe: nenhuma marca
        # alheia em atributo visível. Mesma família do endereço velho no snippet do
        # Google: dado de terceiro publicado como nosso.
        ALHEIAS = ("Stratigital", "stratigital")
        det = [rel for rel, h in s.todas() if any(a in h for a in ALHEIAS)]
        return (not det, u"%d página(s) com marca alheia%s" % (
            len(det), (u": " + u", ".join(det[:3])) if det else u" — nenhuma"))
    s.check("S154", u"nenhuma marca alheia (Stratigital) no HTML", s154)

    def s155():
        # Onda 60. Botão sem nome acessível é lido como "botão" — era a única falha da
        # categoria Agentic Browsing (que mede se um agente de IA entende a página), e
        # falhava no mobile e no desktop. Cobra texto, aria-label ou title em todo
        # <button> das páginas de conteúdo.
        det = []
        for rel, h in s.todas():
            for m in re.finditer(r"<button\b([^>]*)>(.*?)</button>", h, re.S):
                attrs, dentro = m.group(1), m.group(2)
                if "aria-label" in attrs or "title=" in attrs:
                    continue
                texto = re.sub(r"<[^>]+>", "", dentro).strip()
                if texto:
                    continue
                # <img alt> ou <svg><title> dentro também dão nome ao botão
                if re.search(r'<img[^>]*\balt="[^"]+"', dentro) or "<title" in dentro:
                    continue
                det.append(u"%s: %s" % (rel, (attrs.strip() or u"<button>")[:50]))
        return (not det, u"; ".join(det[:4]) or u"todo botão tem nome acessível")
    s.check("S155", u"todo botão tem nome acessível (PageSpeed / Agentic Browsing)", s155)

    def s156():
        # Onda 60. Duas folhas de plugin do WordPress eram carregadas nas 109 páginas
        # sem serem usadas (dashicons 36 KiB e formidableforms 23 KiB), bloqueando o
        # desenho por ~3 s somados. A asserção mede o EFEITO na página, não a lista de
        # arquivos: se a folha está declarada, alguma marca de uso dela tem de existir
        # ali. Impede que outro CSS de plugin volte sorrateiro.
        FOLHAS = {
            "dashicons-css": ("dashicons-",),
            "formidable-css": ("frm_forms", "frm_form_field", "frm-show-form"),
            # onda 62d: o pior bloqueador isolado do render na home (36 KB, 283 ms).
            # 109 páginas carregavam, 55 usam o botão de compartilhar.
            "addtoany-css": ("a2a_kit", "addtoany_shortcode", "a2a_button"),
        }
        det = []
        for rel, h in s.todas():
            for css_id, provas in FOLHAS.items():
                m = re.search(r"<link[^>]*id='%s'[^>]*>" % re.escape(css_id), h)
                if not m:
                    continue
                sem_tag = h[:m.start()] + h[m.end():]
                if not any(p in sem_tag for p in provas):
                    det.append(u"%s carrega %s sem usar" % (rel, css_id))
        return (not det, u"; ".join(det[:4]) or u"nenhuma folha de plugin carregada sem uso")
    s.check("S156", u"nenhum CSS de plugin carregado sem uso na página (PageSpeed)", s156)

    def s164():
        # Onda 62d. `onda31-medicao.js` entrava sem defer/async e o PageSpeed o
        # cobrava em 236 ms de bloqueio do render. Como o LCP da home é TEXTO
        # (o relatório nomeia `div.hero-texto > p`), não há imagem no caminho
        # crítico: o que atrasa aquele parágrafo é o que bloqueia o desenho.
        #
        # Mede a DECLARAÇÃO no HTML das 282 páginas — a V-nova mede o computado.
        det = []
        n = 0
        for rel, h in s.todas():
            for m in re.finditer(r'<script([^>]*\bsrc="[^"]*onda31-medicao\.js[^"]*")([^>]*)>', h):
                n += 1
                tag = m.group(0)
                if "defer" not in tag and "async" not in tag:
                    det.append(u"%s carrega a medição bloqueando o render" % rel)
        return (not det, u"%d tag(s) de medição; %s"
                % (n, u"; ".join(det[:4]) or u"todas com defer"))
    s.check("S164", u"medição não bloqueia o desenho (onda 62d)", s164)

    def s157():
        # Onda 60. Generaliza a S123 para DENTRO do CSS: o único erro de console do
        # relatório era um 404 de texture-7.png, pedido em 22 seletores do tema. A S123
        # não pegava porque olha o HTML, e a referência morava num url() de CSS.
        #
        # Mede o que o NAVEGADOR buscaria, não o que existe num arquivo em disco —
        # senão acusa referência que ninguém pede. Dois filtros, ambos medidos:
        #   1. só CSS que alguma página realmente carrega (o dashicons.min.css ficou
        #      órfão nesta onda: continua no disco, e nenhuma página o pede);
        #   2. só regra cujo seletor tem chance de casar — se nenhuma das classes do
        #      seletor aparece em página nenhuma, aquela regra nunca é aplicada e o
        #      url() dela nunca é buscado (caso do chosen-sprite e dos mundi-*.jpg,
        #      restos de componentes que o espelho não tem).
        # LIMITE DECLARADO: classe criada em tempo de execução por JS (ex.: frm_message,
        # que o plugin de formulário insere depois do envio) não aparece no HTML
        # estático, então cai no filtro 2 e não é coberta aqui.
        linkados = set()
        classes_html = set()
        for _rel, h in s.todas():
            for m in re.finditer(r'<link[^>]+href=[\'"]([^\'"]+\.css)[^\'"]*[\'"]', h):
                linkados.add(m.group(1).split("?")[0].lstrip("/"))
            for m in re.finditer(r'class=[\'"]([^\'"]+)[\'"]', h):
                classes_html.update(m.group(1).split())
        det = []
        checados = 0
        for ref_css in sorted(linkados):
            fp = os.path.join(pub, ref_css.replace("/", os.sep))
            if not os.path.exists(fp):
                det.append(u"CSS linkado não existe: %s" % ref_css)
                continue
            with io.open(fp, encoding="utf-8", errors="ignore") as f:
                css = f.read()
            # tira comentários: `texture-7` aparecia num comentário do onda6.css e um
            # grep ingênuo o tomou por declaração viva
            css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
            base = os.path.dirname(fp)
            for m in re.finditer(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""", css):
                ref = m.group(1).strip().split("?")[0].split("#")[0]
                if (not ref or ref.startswith("data:") or ref.startswith("http")
                        or ref.startswith("//")):
                    continue
                # O seletor da regra é o texto ENTRE a fronteira anterior e a chave que
                # abre o bloco onde o url() está. Retroceder só até o `}` anterior erra
                # dentro de @media: pega a linha do media query em vez do seletor.
                abre = css.rfind("{", 0, m.start())
                if abre < 0:
                    seletor = ""
                else:
                    ini = max(css.rfind("}", 0, abre), css.rfind("{", 0, abre)) + 1
                    seletor = css[ini:abre]
                # Um seletor pode ser uma LISTA (a, b, c). Cada grupo casa só se TODAS
                # as classes dele existirem no HTML; a regra é alcançável se ALGUM grupo
                # casar. Testar a união das classes seria permissivo demais: em
                # `.menu__nav-submenu>div.tab_nossarede` a primeira classe existe e a
                # segunda não, e o navegador nunca aplica essa regra.
                grupos = [g for g in seletor.split(",") if g.strip()]
                if grupos:
                    alcancavel = False
                    for g in grupos:
                        cls = set(re.findall(r"\.([A-Za-z0-9_-]+)", g))
                        if not cls or cls <= classes_html:
                            alcancavel = True
                            break
                    if not alcancavel:
                        continue  # nenhuma variante do seletor casa: nada a buscar
                checados += 1
                if ref.startswith("/"):
                    alvo = os.path.join(pub, ref.lstrip("/").replace("/", os.sep))
                else:
                    alvo = os.path.normpath(os.path.join(base, ref.replace("/", os.sep)))
                if not os.path.exists(alvo):
                    det.append(u"%s pede %s (não existe)" % (ref_css, ref[:44]))
        vistos, unicos = set(), []
        for d in det:
            if d not in vistos:
                vistos.add(d)
                unicos.append(d)
        return (not unicos, u"%d url() alcançáveis em %d CSS; %s" % (
            checados, len(linkados), u"; ".join(unicos[:3]) or u"todas resolvem no disco"))
    s.check("S157", u"todo url() alcançável de CSS resolve no disco (404 no console)", s157)

    def s158():
        # Onda 60, e esta nasceu de um bug MEU. Ao escrever <h4 aria-level="3"> nos
        # cards, o reconhecedor do 06_quadro_lideres.py (`<h4>(.*?)</h4>`) deixou de
        # casar, o gerador concluiu que os cards não existiam, trocou os <button> por
        # <div> e os 4 modais de bio da home sumiram sem ninguém ver. A asserção mede o
        # EFEITO no HTML: os cards de líder da home continuam sendo botões que abrem um
        # modal que existe na própria página.
        det = []
        for rel in ("pt/index.html", "en/index.html", "de/index.html"):
            h = s.ler(rel)
            botoes = re.findall(r'<button class="home-leaders__card"[^>]*'
                                r'data-bs-target="#(modal_[^"]+)"', h)
            divs = len(re.findall(r'<div class="home-leaders__card"', h))
            if len(botoes) != 4:
                det.append(u"%s: %d card(s) com modal (esperado 4)" % (rel, len(botoes)))
            if divs:
                det.append(u"%s: %d card(s) viraram <div> sem modal" % (rel, divs))
            for mid in botoes:
                if ('id="%s"' % mid) not in h:
                    det.append(u"%s: card aponta para %s inexistente" % (rel, mid))
        return (not det, u"; ".join(det[:4]) or u"12 cards de líder abrem modal nas 3 homes")
    s.check("S158", u"cards de líder da home continuam abrindo modal de bio", s158)

    def s159():
        # Onda 60b. Esta asserção existe por causa de um bug MEU que foi para producao:
        # o placeholder de texture-7.png era um pixel VERMELHO com alfa 127, e como os
        # 22 seletores do tema usam `background-size:cover`, esse 1x1 se esticou e pintou
        # a home, os insights, as paginas de lider e o menu de VERMELHO. A S157 nao pegou
        # porque cobrava que o arquivo EXISTISSE — mediu a existencia, nao o efeito.
        # Aqui o pixel de todo placeholder de 1x1 e DECODIFICADO e tem de ser
        # completamente transparente. Se um dia entrar o asset real (maior que 1x1), a
        # asserção sai do caminho.
        import zlib as _zlib
        det = []
        conferidos = 0
        for rel in ("wp-content/themes/mirow/resources/images/texture-7.png",
                    "wp-content/themes/mirow/resources/images/form-success.gif",
                    "wp-content/themes/mirow/resources/images/form-select-arrow.svg",
                    "wp-content/plugins/formidable/images/ajax_loader.gif"):
            fp = os.path.join(pub, rel.replace("/", os.sep))
            if not os.path.exists(fp):
                det.append(u"%s ausente" % rel)
                continue
            with io.open(fp, "rb") as f:
                d = f.read()
            conferidos += 1
            if rel.endswith(".png"):
                if d[:8] != bytes([137, 80, 78, 71, 13, 10, 26, 10]):
                    det.append(u"%s nao e PNG" % rel)
                    continue
                w, h = struct.unpack(">II", d[16:24])
                ct = d[25]
                if (w, h) != (1, 1):
                    continue  # asset real; nada a cobrar
                if ct != 6:
                    det.append(u"%s e 1x1 mas sem canal alfa (colortype=%d)" % (rel, ct))
                    continue
                i, pix = 8, None
                while i < len(d):
                    ln = struct.unpack(">I", d[i:i + 4])[0]
                    if d[i + 4:i + 8] == b"IDAT":
                        pix = tuple(_zlib.decompress(d[i + 8:i + 8 + ln])[1:5])
                        break
                    i += 12 + ln
                if pix is None:
                    det.append(u"%s sem IDAT legivel" % rel)
                elif pix[3] != 0:
                    det.append(u"%s PINTA: rgba%s (alfa tem de ser 0)" % (rel, pix,))
            elif rel.endswith(".gif"):
                if d[:6] not in (b"GIF87a", b"GIF89a"):
                    det.append(u"%s nao e GIF" % rel)
                elif len(d) < 200:  # 1x1 placeholder
                    k = d.find(bytes([0x21, 0xF9, 0x04]))
                    if k < 0 or not (d[k + 3] & 1):
                        det.append(u"%s e placeholder sem transparencia declarada" % rel)
            elif rel.endswith(".svg"):
                txt = d.decode("utf-8", "ignore")
                if re.search(r"<(path|rect|circle|ellipse|polygon|line|image)[ />]", txt):
                    det.append(u"%s desenha forma (deveria ser vazio)" % rel)
        return (not det, u"%d placeholder(es); %s" % (
            conferidos, u"; ".join(det[:3]) or u"nenhum pinta pixel"))
    s.check("S159", u"placeholder de asset faltante nao pinta nada (pixel decodificado)", s159)

    def s160():
        # Onda 61. DOIS invariantes, e a distincao entre eles e o ponto:
        #
        # (a) nenhuma imagem que a HOME pede passa de 120 KB. E a pagina que o
        #     PageSpeed audita e a que todo visitante abre. O caso que originou:
        #     `clientes/edp.svg` tinha 414 KB (QUATRO bitmaps embutidos num wrapper
        #     SVG) para um logo exibido a 81x30 px; `mercedes-benz.svg`, 298 KB em 489
        #     paths. Viraram WebP com a razao EXATA do original.
        #
        # (b) nenhuma imagem ORFA acima de 120 KB. Em 18/08 o espelho carregava 181
        #     imagens que NENHUMA pagina referenciava — 25,9 MB de peso morto vindo do
        #     WordPress. Foram removidas; esta metade impede que voltem.
        #
        # O QUE ESTA ASSERÇÃO **NAO** COBRE, de proposito: as imagens grandes de
        # ARTIGO que estao referenciadas (banners de 822-915 KB, um PNG de 3,5 MB).
        # Sao reais e continuam no `docs/BACKLOG-TECNICO.md` como onda 62 — nao entram
        # aqui para a asserção nao virar um alarme cronico que se aprende a ignorar.
        TETO = 120 * 1024
        EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")
        det = []

        # (a) o que a home pede
        da_home = set()
        for rel in HOMES:
            h = s.ler(rel)
            for m in re.finditer(r'(?:src|href)="(/[^"]+\.(?:png|jpg|jpeg|webp|gif|svg))', h):
                da_home.add(m.group(1).split("?")[0].lstrip("/"))
        for ref in sorted(da_home):
            fp = os.path.join(pub, ref.replace("/", os.sep))
            if os.path.exists(fp) and os.path.getsize(fp) > TETO:
                det.append(u"a home pede %s (%.0f KB)"
                           % (ref.split("/")[-1], os.path.getsize(fp) / 1024.0))

        # (b) orfas grandes
        #
        # Onda 68: a varredura abaixo junta o TEXTO das paginas e procura o basename,
        # entao referencia em `content=` conta igual -- e bom que conte, porque as 20
        # derivadas de `og:image` da onda 68 sao citadas SO em
        # `<meta property="og:image" content="...">`. Se um dia esta metade passar a
        # extrair referencias por regex de `src|href` (como a metade (a) faz), as
        # derivadas viram orfas falsas na hora. Fica registrado aqui porque o proximo
        # a mexer nao tem como adivinhar.
        texto = []
        for dp, _d, fs in os.walk(pub):
            if os.sep + ".git" in dp:
                continue
            for nome in fs:
                if nome.endswith((".html", ".css", ".xml", ".js", ".txt")):
                    with io.open(os.path.join(dp, nome), encoding="utf-8",
                                 errors="ignore") as f:
                        texto.append(f.read())
        tudo = chr(10).join(texto)
        orfas = []
        for dp, _d, fs in os.walk(pub):
            if os.sep + ".git" in dp:
                continue
            for nome in fs:
                if not nome.lower().endswith(EXT):
                    continue
                fp = os.path.join(dp, nome)
                if os.path.getsize(fp) <= TETO:
                    continue
                rel = os.path.relpath(fp, pub).replace(os.sep, "/")
                if rel not in tudo and nome not in tudo:
                    orfas.append((os.path.getsize(fp), rel))
        orfas.sort(reverse=True)
        for t, r in orfas[:3]:
            det.append(u"órfã %s (%.0f KB)" % (r.split("/")[-1], t / 1024.0))
        if len(orfas) > 3:
            det.append(u"… e %d outra(s) órfã(s) grandes" % (len(orfas) - 3))
        return (not det, u"%d imagem(ns) na home, %d órfã(s) grande(s); %s"
                % (len(da_home), len(orfas), u"; ".join(det[:4]) or u"tudo sob 120 KB"))
    s.check("S160", u"home sem imagem acima de 120 KB, e nenhuma órfã grande (onda 61)", s160)

    def s161():
        # Onda 61. As referencias trocadas para WebP tem de resolver, e o PNG/SVG antigo
        # nao pode voltar a ser referenciado por descuido num script futuro.
        CONVERTIDOS = ("clientes/edp", "clientes/mercedes-benz", "clientes/taesa",
                       "02/Andreas-Mirow", "02/Felipe-Diniz-1", "02/prof",
                       "02/Elmar-Gans-1", "certificate-cdp", "certificate-basedtargets",
                       "certificate-seventowatch", "certificate-growingfirms",
                       "certificate-globalimpact", "image-52")
        det = []
        webps = set()
        for rel, h in s.todas():
            for m in re.finditer(r'(?:src|href)="([^"]*?/(?:uploads)/[^"]*?)"', h):
                ref = m.group(1).split("?")[0]
                if not any(c in ref for c in CONVERTIDOS):
                    continue
                if ref.endswith((".png", ".svg")):
                    det.append(u"%s ainda pede %s" % (rel, ref.split("/")[-1]))
                elif ref.endswith(".webp"):
                    webps.add(ref)
        for ref in sorted(webps):
            fp = os.path.join(pub, ref.lstrip("/").replace("/", os.sep))
            if not os.path.exists(fp):
                det.append(u"%s referenciado e ausente no disco" % ref.split("/")[-1])
        return (not det, u"%d webp referenciado(s); %s"
                % (len(webps), u"; ".join(det[:4]) or u"todos resolvem, nenhum PNG/SVG velho"))
    s.check("S161", u"imagens convertidas: só WebP referenciado e existente (onda 61)", s161)

    def s162():
        # Onda 62 (vídeo). A S160 e a varredura de órfãs da onda 61 só olham extensão
        # de IMAGEM — então 185 MB de MP4 nunca foram vistos: 87 MB que NENHUMA página
        # pedia e 49 MB de cópia byte-idêntica de arquivo em uso. `public/` caiu de
        # 262 MB para 132 MB removendo isso, sem mudar um pixel.
        #
        # Esta asserção cobra a CLASSE, não os 5 arquivos daquela limpeza:
        #   (a) nenhum vídeo/áudio órfão — ninguém referencia, nem por caminho nem por nome
        #   (b) nenhum par de vídeos byte-a-byte idênticos (md5), mesmo os dois em uso
        #   (c) todo <source>/<video> referenciado resolve num arquivo que existe
        #
        # Por que md5 e não tamanho: dois arquivos de mesmo peso podem ser cortes
        # diferentes; o que autoriza consolidar é o conteúdo ser o MESMO.
        MIDIA = (".mp4", ".webm", ".mov", ".m4v", ".ogv", ".mp3", ".wav")
        det = []

        textos = []
        for dp, _d, fs in os.walk(pub):
            if os.sep + ".git" in dp:
                continue
            for nome in fs:
                if nome.endswith((".html", ".css", ".js", ".xml", ".txt", ".json")):
                    with io.open(os.path.join(dp, nome), encoding="utf-8",
                                 errors="ignore") as f:
                        textos.append(f.read())
        tudo = chr(10).join(textos)

        achados = []
        for dp, _d, fs in os.walk(pub):
            if os.sep + ".git" in dp:
                continue
            for nome in fs:
                if nome.lower().endswith(MIDIA):
                    fp = os.path.join(dp, nome)
                    achados.append((os.path.relpath(fp, pub).replace(os.sep, "/"),
                                    fp, os.path.getsize(fp)))

        # (a) órfãos
        for rel, fp, tam in achados:
            nome = rel.split("/")[-1]
            if rel not in tudo and nome not in tudo:
                det.append(u"órfão %s (%.1f MB)" % (nome, tam / 1048576.0))

        # (b) idênticos
        porhash = {}
        for rel, fp, tam in achados:
            h = hashlib.md5()
            with open(fp, "rb") as f:
                for bloco in iter(lambda: f.read(1 << 20), b""):
                    h.update(bloco)
            porhash.setdefault(h.hexdigest(), []).append((rel, tam))
        for h, grupo in porhash.items():
            if len(grupo) > 1:
                det.append(u"%d cópias idênticas de %s (%.1f MB desperdiçados)"
                           % (len(grupo), grupo[0][0].split("/")[-1],
                              grupo[0][1] * (len(grupo) - 1) / 1048576.0))

        # (c) referência resolve
        pedidos = set()
        for rel, h in s.todas():
            for m in re.finditer(r'<(?:source|video|audio)\b[^>]*?src="([^"]+)"', h):
                ref = m.group(1).split("?")[0]
                if ref.lower().endswith(MIDIA):
                    pedidos.add(ref)
        for ref in sorted(pedidos):
            r = ref[len("/mirow-site/"):] if ref.startswith("/mirow-site/") else ref.lstrip("/")
            if not os.path.exists(os.path.join(pub, r.replace("/", os.sep))):
                det.append(u"%s referenciado e ausente no disco" % ref.split("/")[-1])

        # (d) teto de peso. Onda 62b: o vídeo de carreiras estava a 13.115 kb/s —
        # 40 MB para um loop de fundo MUDO de 25 s. Recomprimido a 1.408 kb/s
        # (4,3 MB) sem tocar no que a página mostra. O teto impede a volta: nenhum
        # arquivo de mídia acima de 8 MB (o maior legítimo hoje é o
        # video-porque-mirow.mp4, com 6,8 MB).
        TETO_MIDIA = 8 * 1024 * 1024
        for rel, _fp, tam in achados:
            if tam > TETO_MIDIA:
                det.append(u"%s tem %.1f MB (teto 8 MB)"
                           % (rel.split("/")[-1], tam / 1048576.0))

        peso = sum(t for _r, _f, t in achados)
        return (not det, u"%d arquivo(s) de mídia, %.1f MB, %d referência(s); %s"
                % (len(achados), peso / 1048576.0, len(pedidos),
                   u"; ".join(det[:4]) or u"nenhum órfão, nenhuma cópia idêntica"))
    s.check("S162", u"vídeo: nenhum órfão, nenhuma cópia idêntica, referência resolve (onda 62)",
            s162)

    def s163():
        # Onda 62c. A S161 lista os arquivos convertidos na onda 61 pelo nome — não
        # escala para 155. Esta cobra a CLASSE, e por isso se mantém sozinha:
        #   (a) NENHUM PNG referenciado passa de 120 KB. É o invariante que a onda
        #       estabeleceu: PNG pesado no espelho é peso morto, porque WebP na
        #       MESMA dimensão corta 72-97% sem mexer em layout.
        #   (b) todo .webp referenciado existe no disco.
        # O piso de 120 KB é o mesmo da S160, de propósito: um número só.
        TETO = 120 * 1024
        det = []
        citados = set()
        fim = re.compile(r'\.(png|webp)(?![a-z0-9])', re.I)
        # sem ':' de propósito — com ele, "https://host/x.webp" era partido no
        # "https:" e virava "//host/x.webp", um caminho que nunca existe no disco,
        # e a asserção acusava ausente um arquivo que estava lá
        PARA = set(' "\'(),\\\n\t{}[];=|<>')
        for _rel, h in s.todas():
            t = h.replace("\\/", "/")
            for m in fim.finditer(t):
                i, j = m.start(), m.end()
                while i > 0 and t[i - 1] not in PARA:
                    i -= 1
                ref = t[i:j].split("?")[0]
                if not ref or ref.startswith("."):
                    continue
                if ref.startswith("/mirow-site/"):
                    ref = ref[len("/mirow-site/"):]
                elif ref.startswith("http"):
                    mm = re.match(r'https?://[^/]+/(.*)$', ref)
                    if not mm:
                        continue
                    ref = mm.group(1)
                    if ref.startswith("mirow-site/"):
                        ref = ref[len("mirow-site/"):]
                citados.add(ref.lstrip("/"))

        gordos, webps = [], 0
        for ref in sorted(citados):
            fp = os.path.join(pub, ref.replace("/", os.sep))
            if ref.lower().endswith(".webp"):
                webps += 1
                if not os.path.exists(fp):
                    det.append(u"%s referenciado e ausente" % ref.split("/")[-1])
            elif os.path.exists(fp) and os.path.getsize(fp) > TETO:
                gordos.append((os.path.getsize(fp), ref))
        gordos.sort(reverse=True)
        for t, r in gordos[:3]:
            det.append(u"PNG %s tem %.0f KB" % (r.split("/")[-1], t / 1024.0))
        if len(gordos) > 3:
            det.append(u"… e mais %d PNG acima de 120 KB" % (len(gordos) - 3))
        return (not det, u"%d referência(s), %d webp; %s"
                % (len(citados), webps,
                   u"; ".join(det[:4]) or u"nenhum PNG acima de 120 KB, todo webp resolve"))
    s.check("S163", u"PNG pesado não volta: nenhum acima de 120 KB, webp resolve (onda 62c)",
            s163)

    # ------------------------------------------------------------------ onda 65
    def s165():
        # Onda 65 / issue #238. DOIS itens ficaram no ar por mais de doze meses com
        # o veículo errado:
        #
        #   28/05/2024 "Armazenamento de energia trava aportes consistentes"
        #       rótulo Estadão + logo do Estadão + data 28/05 — e o link é do VALOR
        #       (Revista Energia), cujo datePublished é 2024-05-10.
        #   02/03/2024 "Descarbonização: onde investir…"
        #       rótulo Folha de S.Paulo + logo da Folha — e o link é do jornal
        #       EMPRESAS & NEGÓCIOS.
        #
        # E havia asserção contra isso. A S57b cobra literalmente "o logo segue o
        # veículo, não o link" — e passava VERDE nos dois, porque o logo batia com o
        # rótulo, e o rótulo é que estava errado. Ela compara dois campos NOSSOS
        # entre si e nunca comparou nenhum deles com o host do link, que é o único
        # dado da linha que não escrevemos. P2.1: medir o efeito, não a declaração.
        #
        # Dois braços, e o primeiro é o que pega a CLASSE:
        #
        #   (a) UM HOST, UM VEÍCULO. Invariante derivado do próprio dado, sem mapa
        #       hardcoded: se o mesmo host aparece rotulado com dois veículos
        #       diferentes, um dos dois está errado por construção. Era exatamente o
        #       caso — valor.globo.com aparecia como "Valor Econômico" E "Estadão";
        #       jornalempresasenegocios.com.br como "Empresas & Negócios" E "Folha
        #       de S.Paulo".
        #   (b) O NOME TEM DE APARECER NO HOST. Algum token de 3+ letras do veículo
        #       (sem acento, só letras) está presente no host — ou o par é exceção
        #       DECLARADA aqui, com o motivo. Isto pega o caso em que o erro é
        #       consistente (um host novo rotulado errado desde o primeiro item, que
        #       o braço (a) não vê).
        EXCECOES = {
            # veículo -> host, e por que host e marca não se parecem
            u"iG": ("ig.com.br", u"a marca tem 2 letras; token de 3+ não existe"),
            u"CZ Insights": ("czapp.com", u"o veículo publica em czapp.com, "
                                          u"domínio da Czarnikow"),
        }
        det = []
        por_host = {}
        for rel in IMPRENSA:
            h = s.ler(rel)
            itens = re.findall(r'<li class="onda18-imprensa__item">(.*?)</li>', h, re.S)
            for it in itens:
                mu = re.search(r'href="(https?://[^"]+)"', it)
                mv = re.search(r'class="onda18-imprensa__veiculo">([^<]*)<', it)
                if not (mu and mv):
                    det.append(u"%s: item sem url ou sem veículo" % rel)
                    continue
                url = mu.group(1)
                # Onda 75: link arquivado no Wayback. O host do link passa a ser
                # web.archive.org, e o veículo continua sendo o ORIGINAL — a URL
                # original vem embutida depois do carimbo de data. Sem isto, a
                # asserção acusaria "IstoÉ Dinheiro não bate com web.archive.org",
                # que é verdade sobre a string e mentira sobre o fato.
                m_arq = re.match(r"https?://web\.archive\.org/web/\d+(?:id_)?/(https?://.+)$", url)
                if m_arq:
                    url = m_arq.group(1)
                host = url.split("/")[2].lower()
                if host.startswith("www."):
                    host = host[4:]
                veic = mv.group(1).replace("&amp;", "&")
                por_host.setdefault(host, set()).add(veic)

        # (a) um host, um veículo
        for host, veics in sorted(por_host.items()):
            if len(veics) > 1:
                det.append(u"host %s rotulado com %d veículos: %s"
                           % (host, len(veics), u" / ".join(sorted(veics))))

        # (b) o nome do veículo aparece no host
        def tokens(nome):
            limpo = unicodedata.normalize("NFKD", nome)
            limpo = u"".join(c for c in limpo if not unicodedata.combining(c))
            return [t for t in re.split(r"[^A-Za-z]+", limpo.lower()) if len(t) >= 3]

        for host, veics in sorted(por_host.items()):
            for veic in sorted(veics):
                if any(t in host for t in tokens(veic)):
                    continue
                esperado = EXCECOES.get(veic)
                if esperado and host.endswith(esperado[0]):
                    continue
                det.append(u"%s: nenhum token do nome aparece no host %s "
                           u"(e não é exceção declarada)" % (veic, host))
        return (not det, u"%d host(s) distinto(s); %s"
                % (len(por_host),
                   u"; ".join(det[:4]) or u"cada host com um veículo só, "
                                          u"e o nome bate com o host"))
    s.check("S165", u"imprensa: o veículo bate com o host do link (#238)", s165)

    def s166():
        # Onda 65 / issue #239. A lista deixou de ser HTML à mão em três arquivos e
        # passou a ser GERADA do mestre P3 (tools/gen_imprensa.py). Esta asserção
        # RECALCULA a lista a partir de tools/imprensa-publicada.json — a lista que
        # o gerador emite — e compara com o HTML das três páginas.
        #
        # É o padrão da S116 (reprojeta os pins da Nossa Rede e compara) e da S120
        # (regera o sitemap inteiro): a forma mais forte de P2.1, porque não confere
        # se o HTML "parece certo" — refaz a conta e exige igualdade. Com isso, a
        # lista não pode divergir do dado curado nem por edição à mão nem por script
        # futuro que mexa nas páginas.
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "imprensa-publicada.json")
        if not os.path.exists(p):
            return (False, u"falta tools/imprensa-publicada.json — rode "
                           u"tools/gen_imprensa.py")
        with io.open(p, encoding="utf-8") as f:
            esperado = json.load(f)
        det = []

        if len(esperado) < 40:
            det.append(u"a lista publicada tem só %d matérias" % len(esperado))

        # ordem: data decrescente
        datas = [m["data"] for m in esperado]
        if datas != sorted(datas, reverse=True):
            det.append(u"a lista publicada não está em data decrescente")

        # url única
        urls = [m["url"] for m in esperado]
        if len(set(urls)) != len(urls):
            dup = sorted(set(u for u in urls if urls.count(u) > 1))
            det.append(u"URL duplicada: %s" % u", ".join(dup[:3]))

        # logo declarado existe no disco
        for m in esperado:
            if m["logo"]:
                fp = os.path.join(pub, "wp-content", "uploads", "2026", "08",
                                  "imprensa-logos", m["logo"])
                if not os.path.exists(fp):
                    det.append(u"logo ausente do disco: %s" % m["logo"])

        # o HTML de cada página é o que o mestre manda — e as três são iguais
        assinaturas = {}
        for rel in IMPRENSA:
            h = s.ler(rel)
            itens = re.findall(r'<li class="onda18-imprensa__item">(.*?)</li>', h, re.S)
            if len(itens) != len(esperado):
                det.append(u"%s tem %d itens, o mestre manda %d"
                           % (rel, len(itens), len(esperado)))
                continue
            achado = []
            for it in itens:
                mu = re.search(r'href="([^"]+)"', it)
                mv = re.search(r'class="onda18-imprensa__veiculo">([^<]*)<', it)
                md = re.search(r'datetime="([^"]+)"', it)
                mt = re.search(r'class="onda18-imprensa__titulo">([^<]*)<', it)
                ml = re.search(r'class="onda41-imprensa__logo"[^>]*src="[^"?]*/'
                               r'([^"/?]+)', it)
                achado.append((md.group(1) if md else u"",
                               (mv.group(1) if mv else u"").replace("&amp;", "&"),
                               (mt.group(1) if mt else u"").replace("&amp;", "&"),
                               mu.group(1).replace("&amp;", "&") if mu else u"",
                               ml.group(1) if ml else None))
            assinaturas[rel] = achado
            for i, (esp, got) in enumerate(zip(esperado, achado)):
                alvo = (esp["data"], esp["veiculo"], esp["titulo"], esp["url"],
                        esp["logo"])
                if got != alvo:
                    campos = [n for n, a, b in zip(
                        ("data", "veículo", "título", "url", "logo"), alvo, got)
                        if a != b]
                    det.append(u"%s item %d divergente em %s"
                               % (rel, i + 1, u"/".join(campos)))
                    break
        vistas = list(assinaturas.values())
        if len(vistas) == 3 and not (vistas[0] == vistas[1] == vistas[2]):
            det.append(u"as três páginas não listam a mesma coisa")
        com_logo = sum(1 for m in esperado if m["logo"])
        return (not det, u"%d matéria(s) recalculada(s) do mestre (%d com logo, "
                         u"%d com wordmark de texto); %s"
                % (len(esperado), com_logo, len(esperado) - com_logo,
                   u"; ".join(det[:4]) or u"as 3 páginas idênticas ao mestre"))
    s.check("S166", u"imprensa recalculada do mestre P3, 3 páginas idênticas (#239)", s166)

    # ------------------------------------------------------------------ onda 67
    def s167():
        # #104 / S-47. O campo de busca do tema postava `?s=` para `action="/"`.
        # Num WordPress o servidor responde; no espelho estatico do Pages nao ha
        # quem responda -- medido em 19/08, `/?s=pricing` devolvia o STUB da raiz e
        # jogava o visitante em /pt/. Era o unico dos tres caminhos de conversao
        # mortos que o visitante ACIONA de proposito.
        #
        # Esta assercao cobra a parte estatica; quem mede o EFEITO (buscar e
        # receber resultado) e a V38, no render.
        BUSCA = {"pt": ("pt/insights/index.html", u"Buscar no site"),
                 "en": ("en/insights/index.html", u"Search the site"),
                 "de": ("de/insights/index.html", u"Website durchsuchen")}
        det = []
        for lang, (rel, rotulo) in sorted(BUSCA.items()):
            h = s.ler(rel)
            m = re.search(r'<form class="search-form"[^>]*action="([^"]*)"', h)
            if not m:
                det.append(u"%s: sem <form class=\"search-form\">" % rel)
                continue
            alvo = "/" + rel[:-len("index.html")]
            if m.group(1) != alvo:
                det.append(u"%s: form posta para %r (esperado %r)"
                           % (rel, m.group(1), alvo))
            if "post_type" in h:
                det.append(u"%s: campo oculto post_type do WordPress ainda la" % rel)
            if rotulo not in h:
                det.append(u"%s: rotulo da busca nao esta no idioma da pagina" % rel)
            if 'id="onda67-busca-resultados"' not in h:
                det.append(u"%s: sem contentor de resultados" % rel)
            if not re.search(r'onda67/busca\.js\?v=\d+', h):
                det.append(u"%s: busca.js ausente ou sem ?v=" % rel)
        # o indice: existe, parseia, e toda URL dele resolve e NAO e stub
        pj = os.path.join(pub, "busca-indice.json")
        if not os.path.exists(pj):
            det.append(u"falta public/busca-indice.json")
        else:
            try:
                idx = json.load(io.open(pj, encoding="utf-8"))["itens"]
            except (ValueError, KeyError) as e:
                idx = []
                det.append(u"busca-indice.json invalido (%s)" % e)
            if len(idx) < 100:
                det.append(u"indice com so %d pagina(s)" % len(idx))
            sem_t = [d["u"] for d in idx if not d.get("t")]
            if sem_t:
                det.append(u"%d item(ns) sem titulo: %s" % (len(sem_t), sem_t[:3]))
            langs = set(d.get("l") for d in idx)
            if not {"pt", "en", "de"} <= langs:
                det.append(u"indice sem os 3 idiomas: %s" % sorted(langs))
            for d in idx[:400]:
                rel2 = d["u"].strip("/").replace("/", os.sep)
                fp = os.path.join(pub, rel2, "index.html") if rel2 \
                    else os.path.join(pub, "index.html")
                if not os.path.exists(fp):
                    det.append(u"indice aponta para %s, que nao existe" % d["u"])
                    break
                hh = io.open(fp, encoding="utf-8", errors="ignore").read()
                if 'http-equiv="refresh"' in hh or "window.location.replace" in hh:
                    det.append(u"indice aponta para %s, que e STUB" % d["u"])
                    break
        return (not det, u"; ".join(det[:4]) or u"3 formularios ligados, indice resolve")
    s.check("S167", u"busca estática: o campo posta na própria página e o índice resolve (#104)",
            s167)

    def s168():
        # #215. A camada que os LLMs leem (llms.txt) nao dizia uma palavra sobre IA,
        # enquanto a home abre com o selo AI Powered desde a onda 58. E, medido ao
        # escrever isto, ela mandava o robo para /pt/contato/ anunciando
        # "formulario" -- aquela pagina e STUB e nao tem formulario nenhum.
        p = os.path.join(pub, "llms.txt")
        if not os.path.exists(p):
            return (False, u"nao existe public/llms.txt")
        t = io.open(p, encoding="utf-8").read()
        det = []
        if not re.search(r"(?i)intelig[eê]ncia artificial|AI Powered|\bIA\b", t):
            det.append(u"nao menciona IA")
        if u"São Paulo" not in t:
            det.append(u"nao cita o escritorio de Sao Paulo")
        if u"formulário" in t and u"Não há formulário" not in t:
            det.append(u"promete formulario de contato, que nao existe")
        # nenhum link interno pode faltar nem ser stub (o caso do /pt/contato/)
        for m in re.finditer(r"\]\((/[^)]+)\)", t):
            rel = m.group(1).strip("/").replace("/", os.sep)
            fp = os.path.join(pub, rel, "index.html")
            if not os.path.exists(fp):
                det.append(u"link %s nao existe" % m.group(1))
                continue
            hh = io.open(fp, encoding="utf-8", errors="ignore").read()
            if 'http-equiv="refresh"' in hh or "window.location.replace" in hh:
                det.append(u"link %s e stub de redirect" % m.group(1))
        # o invisivel nao pode prometer o que o visivel nao diz: se o llms.txt
        # afirma IA, a home tem de afirmar tambem
        if re.search(r"(?i)AI Powered", t):
            if "AI Powered" not in s.ler("pt/index.html"):
                det.append(u"llms.txt diz AI Powered e a home pt nao")
        return (not det, u"; ".join(det[:4]) or u"IA declarada, todo link resolve")
    s.check("S168", u"llms.txt declara IA e não manda o robô para stub (#215)", s168)

    # ------------------------------------------------------------------ onda 68
    def s169():
        # #212/#213/#214: "Na pagina de estrategia precisamos falar como usamos IA
        # nesses tipos de projetos" / "na pagina de compras a mesma coisa" / "na
        # outra pagina a mesma coisa" (Andreas/Mario/Luciana, 12/08).
        #
        # O criterio das issues pede exemplos CONCRETOS e tom de fato, nao de
        # autopromocao. Dois desses criterios dao para medir, e sao os que mais
        # doem se quebrarem:
        #
        #   (a) NENHUM NOME DE CLIENTE dentro do bloco. A lista de clientes vem do
        #       proprio mestre publicado (tools/clients-publicados.json), entao a
        #       assercao acompanha a curadoria em vez de ter lista hardcoded que
        #       envelhece. Citar cliente em texto de metodo, sem autorizacao por
        #       contrato, e problema de confidencialidade -- nao de estilo.
        #   (b) NENHUM PERCENTUAL nem numero de resultado atribuido a IA. Nao ha
        #       medicao isolada do efeito da IA sobre o resultado dos projetos;
        #       "reduz 30%" seria invencao. Os numeros das paginas continuam sendo
        #       dos CASOS, no bloco de Cases, que e outro lugar.
        #
        # Mais o basico: as 9 paginas tem o bloco, 3 itens cada, titulo no idioma
        # da pagina, e o bloco vem ANTES do bloco de Cases (o leitor conhece o
        # metodo, depois como a IA entra nele, depois os exemplos).
        ALVOS = {
            "pt": ["pt/pratica/estrategia/index.html",
                   "pt/pratica/operacoes/index.html",
                   "pt/pratica/marketing-vendas-e-pricing/index.html"],
            "en": ["en/practice/strategy/index.html",
                   "en/practice/operations/index.html",
                   "en/practice/marketing-sales-and-pricing/index.html"],
            "de": ["de/branchen/strategie/index.html",
                   "de/branchen/betrieb/index.html",
                   "de/branchen/marketing-vertrieb-und-preisgestaltung/index.html"],
        }
        TITULO = {"pt": u"Como usamos IA", "en": u"How we use AI",
                  "de": u"Wie wir KI einsetzen"}
        det = []

        # os clientes, do mestre publicado (nao lista hardcoded)
        clientes = []
        pc = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "clients-publicados.json")
        if os.path.exists(pc):
            try:
                clientes = [c["wordmark"] for c in json.load(io.open(pc, encoding="utf-8"))]
            except (ValueError, KeyError):
                det.append(u"clients-publicados.json ilegivel")

        for lang, rels in sorted(ALVOS.items()):
            for rel in rels:
                h = s.ler(rel)
                m = re.search(r'<div class="onda68-ia">(.*?)</div>\s*<div class='
                              r'"experience-single__cases">', h, re.S)
                if not m:
                    # ou o bloco falta, ou nao esta antes dos Cases
                    if 'class="onda68-ia"' not in h:
                        det.append(u"%s sem o bloco de IA" % rel)
                    else:
                        det.append(u"%s: o bloco de IA nao esta antes dos Cases" % rel)
                    continue
                bloco = m.group(1)
                if TITULO[lang] not in bloco:
                    det.append(u"%s: titulo fora do idioma (esperado %r)"
                               % (rel, TITULO[lang]))
                n = bloco.count('class="onda68-ia__item"')
                if n != 3:
                    det.append(u"%s: %d item(ns) no bloco (esperado 3)" % (rel, n))
                # (a) nenhum nome de cliente
                texto = re.sub(r"<[^>]+>", u" ", bloco)
                for c in clientes:
                    if c and re.search(r"(?i)\b" + re.escape(c) + r"\b", texto):
                        det.append(u"%s: o bloco de IA cita o cliente %r" % (rel, c))
                # (b) nenhum percentual nem R$ atribuido a IA
                for mm in re.finditer(r"\d+\s*%|R\$\s*\d", texto):
                    det.append(u"%s: o bloco de IA traz numero de resultado (%r)"
                               % (rel, mm.group(0)))
                    break
        # o css_o18 nao esta em escopo aqui (e definido mais adiante na funcao);
        # ler o arquivo direto e o que mede a mesma coisa sem depender da ordem
        _pcss = os.path.join(pub, "wp-content", "uploads", "2026", "07", "onda6",
                             "onda6.css")
        _css = io.open(_pcss, encoding="utf-8").read() if os.path.exists(_pcss) else u""
        if ".onda68-ia__item{border-left:3px solid #00ADEC" not in _css:
            det.append(u"o bloco de IA perdeu o acento ciano no CSS")
        return (not det, u"; ".join(det[:4])
                or u"9 paginas, 3 itens cada, 0 cliente citado, 0 numero atribuido a IA")
    s.check("S169", u'"Como usamos IA" nas 3 práticas core × 3 idiomas, sem citar cliente (#212/#213/#214)',
            s169)

    def s170():
        # #68 (S-19). O criterio de aceite pedia validacao do FATO e assercao. O
        # Mario validou os marcos 2024-2026 em 19/08 ("#68 ok"), e daqui em diante
        # eles nao mudam em silencio: a pagina de historia e conteudo editorial que
        # 137 scripts de onda podem tocar de raspao.
        #
        # Trava o NUCLEO de cada marco, nao o paragrafo inteiro -- exigir o texto
        # literal completo transformaria qualquer ajuste de virgula em falha de
        # gate, e assercao que grita por virgula e assercao que se aprende a
        # ignorar. O que fica travado e o fato: qual e o ano e o que aconteceu.
        MARCOS = {
            "2024": [u"prática de Energia se consolida",
                     u"setor elétrico brasileiro"],
            "2025": [u"fora da América Latina", u"África Austral"],
            "2026": [u"programa de inteligência artificial aplicada",
                     u"julgamento estratégico"],
        }
        rel = "pt/sobre-nos/nossa-historia/index.html"
        # A pagina de historia escreve acento como ENTIDADE HTML
        # (`pr&aacute;tica`, `el&eacute;trico`) -- comparar o texto acentuado direto
        # nao casa. Decodificar e o que mede a mesma coisa sem depender de como o
        # WordPress serializou o caractere.
        import html as _html
        h = _html.unescape(s.ler(rel))
        det = []
        for ano, pedacos in sorted(MARCOS.items()):
            if (">%s<" % ano) not in h:
                det.append(u"o marco de %s desapareceu da linha do tempo" % ano)
                continue
            for p in pedacos:
                if p not in h:
                    det.append(u"marco de %s sem %r" % (ano, p))
        # A linha do tempo pula 2023, e o texto de 2024 cita "2023 e 2024". Isso foi
        # levantado com o Mario em 19/08 e ele validou os marcos como estao -- entao
        # nao e defeito, e escolha editorial. Fica REGISTRADO aqui para o proximo
        # agente nao "consertar" por conta propria; se um dia 2023 ganhar marco
        # proprio, esta linha sai junto.
        if u"projetos consecutivos em 2023 e 2024" not in h:
            det.append(u"o marco de 2024 deixou de citar 2023 — se 2023 ganhou "
                       u"marco proprio, atualize a S170")
        return (not det, u"; ".join(det[:3])
                or u"marcos 2024/2025/2026 como o Mario validou em 19/08")
    s.check("S170", u"marcos 2024-2026 da história como validados (#68)", s170)

    def s171():
        # Onda 68 (#246). O favicon era a WORDMARK inteira -- "MIROW & CO." com 11
        # caracteres -- espremida no quadro do icone. Medido antes da troca:
        #
        #     cropped-favicon-mirow-192x192.png   tinta branca 0,29%  (caixa 125x11 px)
        #     cropped-favicon-mirow-32x32.png     tinta branca 0,00%
        #     themes/mirow/favicon.ico            16x16, abaixo do minimo do Google
        #
        # ZERO por cento. A 32px cada caractere recebe ~3px e o antialias apaga
        # tudo: o icone servido era um quadrado navy VAZIO, que o Google ainda
        # recorta em circulo. Quem abriu o caso foi o proprio Mario, perguntando
        # "que simbolo e esse que aparece do lado do nosso site no google?" -- o
        # dono da marca nao reconhecia o icone do proprio site. A marca ("m" do
        # LogoNeg.png) da 10,67% de tinta, 37x mais.
        #
        # POR QUE ESTA ASSERÇÃO MEDE TINTA, E NAO O NOME DO ARQUIVO. Cobrar o
        # nome (ou o md5) passaria verde no dia em que alguem regenerasse os
        # icones a partir da wordmark outra vez -- e e justamente esse o erro que
        # se repete, porque "poe o logo no favicon" soa correto. O invariante da
        # CLASSE e: todo icone que declaramos tem de ter tinta suficiente para
        # ser VISTO no tamanho em que e servido. E a lista de icones e lida do
        # PROPRIO HTML (padrao da S127, que le os pesos do <head>), entao a
        # asserção acompanha se as tags mudarem em vez de envelhecer calada.
        TINTA_MIN = 4.0
        det = []

        def medir(dados, area):
            """(% de pixel claro) de um PNG, ou None se nao der para decodificar."""
            dec = _png_rgb(dados)
            if dec is None:
                return None
            larg, alt, canais, linhas = dec
            claros = 0
            for ln in linhas:
                for x in range(0, len(ln), canais):
                    if canais == 4 and ln[x + 3] < 128:
                        continue
                    if ln[x] > 200 and ln[x + 1] > 200 and ln[x + 2] > 200:
                        claros += 1
            return 100.0 * claros / float(larg * alt) if area is None else \
                100.0 * claros / float(area)

        def frames_ico(dados):
            """[(w, h, offset, tamanho)] do diretorio do .ico."""
            if len(dados) < 6:
                return []
            _res, tipo, n = struct.unpack("<HHH", dados[:6])
            if tipo != 1:
                return []
            saida = []
            for i in range(n):
                e = dados[6 + i * 16:6 + (i + 1) * 16]
                if len(e) < 16:
                    break
                w, h, _c, _r, _pl, _bpp, tam, off = struct.unpack("<BBBBHHII", e)
                saida.append((w or 256, h or 256, off, tam))
            return saida

        # --- a lista de icones sai do HTML, nao de constante ---
        refs = set()
        for rel in HOMES:
            h = s.ler(rel)
            for m in re.finditer(r'<link[^>]*rel="[^"]*icon[^"]*"[^>]*>', h):
                mh = re.search(r'href="([^"]+)"', m.group(0))
                if mh:
                    refs.add(mh.group(1).split("?")[0])
            for m in re.finditer(r'name="msapplication-TileImage"[^>]*'
                                 r'content="([^"]+)"', h):
                refs.add(m.group(1).split("?")[0])
        if len(refs) < 4:
            det.append(u"as homes declaram só %d ícone(s); esperado >= 4" % len(refs))

        # `/favicon.ico` da raiz nao e declarado por tag nenhuma: navegador e
        # crawler batem nele por convencao. Antes da onda 68 ele nao existia no
        # espelho, ou seja respondia 404 em producao.
        refs.add("/favicon.ico")

        for ref in sorted(refs):
            fp = os.path.join(pub, ref.lstrip("/").replace("/", os.sep))
            if not os.path.exists(fp):
                det.append(u"%s declarado e AUSENTE no disco" % ref)
                continue
            with io.open(fp, "rb") as f:
                dados = f.read()
            nome = ref.split("/")[-1]

            if nome.endswith(".ico"):
                fr = frames_ico(dados)
                if not fr:
                    det.append(u"%s não é um .ico legível" % nome)
                    continue
                lados = sorted(set(w for w, _h, _o, _t in fr))
                if 48 not in lados:
                    det.append(u"%s sem o frame de 48px (tem %s) — 48 é o mínimo "
                               u"que o Google documenta para o ícone do resultado"
                               % (nome, lados))
                maior = max(fr, key=lambda t: t[0])
                corpo = dados[maior[2]:maior[2] + maior[3]]
                pct = medir(corpo, None)
                if pct is None:
                    det.append(u"%s: frame de %dpx não decodificou" % (nome, maior[0]))
                elif pct < TINTA_MIN:
                    det.append(u"%s tem só %.2f%% de tinta no frame de %dpx "
                               u"(mínimo %.1f%%) — é wordmark, não marca"
                               % (nome, pct, maior[0], TINTA_MIN))
                continue

            if not nome.endswith(".png"):
                continue  # svg/outro formato: nada a medir por pixel aqui
            pct = medir(dados, None)
            if pct is None:
                det.append(u"%s não decodificou como PNG truecolor" % nome)
            elif pct < TINTA_MIN:
                det.append(u"%s tem só %.2f%% de tinta (mínimo %.1f%%) — "
                           u"ícone assim sai como quadrado vazio no tamanho servido"
                           % (nome, pct, TINTA_MIN))

        # O `det` volta JUNTO numa string, nao como lista: o `_imprime` da suite
        # concatena o detalhe direto no texto. Escrevi `return (not det), det` na
        # primeira versao e a asserção ficou VERDE no caso bom (com det vazio o
        # caminho do detalhe nunca roda) e QUEBROU o gate inteiro com TypeError no
        # primeiro caso ruim. Quem pegou foi o teste negativo, nao o positivo --
        # e o motivo pelo qual asserção nova sem cenario negativo exercitado nao
        # vale nada (licao da V37, onda 64).
        return (not det, u"; ".join(det[:6])
                + (u" (+%d)" % (len(det) - 6) if len(det) > 6 else u""))

    s.check("S171", u"ícones expostos têm tinta para serem vistos, e o /favicon.ico "
                    u"da raiz existe (#246)", s171)

    def s172():
        # Onda 68 (#247). O cartao de preview de link -- WhatsApp, LinkedIn, Slack,
        # Telegram, iMessage. Tres defeitos medidos, e o do meio e o instrutivo:
        #
        #   6 paginas sem `og:image` NENHUMA (as 3 de imprensa e as 3 de politica)
        #  58 paginas com metadado MENTINDO sobre o proprio arquivo
        #   0 de 109 com `og:image:alt` ou `twitter:image`
        #
        # As 58: quase todas declaravam `og:image:type = image/png` para arquivo que
        # hoje e WebP -- residuo das ondas 61/62c, que converteram a imagem e nao
        # mexeram na tag. E as 3 homes diziam `width 663 / height 394` para o
        # `og-mirow.png`, que e 1200x630, com `type image/jpeg` para um PNG. Valor
        # gemeo classico: a dimensao vivia em dois lugares e divergiu calada.
        #
        # POR QUE ESTA ASSERÇÃO RECALCULA em vez de conferir presenca: o defeito nao
        # era tag AUSENTE, era tag PRESENTE E ERRADA. Cobrar existencia passaria
        # verde nas 58. Aqui cada width/height/type e comparado com o arquivo ABERTO,
        # no padrao da S116/S120/S166.
        det = []
        MIME = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp",
                "GIF": "image/gif"}
        conferidas = 0
        for rel, h in s.conteudo():
            m = re.search(r'<meta property="og:image" content="([^"]+)"', h)
            if not m:
                det.append(u"%s sem og:image (o preview sai sem imagem)" % rel)
                continue
            ref = m.group(1).replace("https://mirow.com.br/", "").lstrip("/")
            fp = os.path.join(pub, ref.replace("/", os.sep))
            if not os.path.exists(fp):
                det.append(u"%s: og:image aponta para %s, que nao existe" % (rel, ref))
                continue
            conferidas += 1
            dec = _dim_imagem(fp)
            if dec is None:
                det.append(u"%s: nao consegui medir %s" % (rel, ref))
                continue
            larg, altura, fmt = dec
            for prop, real in (("og:image:width", larg), ("og:image:height", altura)):
                mm = re.search(r'<meta property="%s" content="(\d+)"' % prop, h)
                if not mm:
                    det.append(u"%s sem %s" % (rel, prop))
                elif int(mm.group(1)) != real:
                    det.append(u"%s: %s diz %s, o arquivo tem %d"
                               % (rel, prop, mm.group(1), real))
            mt = re.search(r'<meta property="og:image:type" content="([^"]+)"', h)
            esperado = MIME.get(fmt)
            if not mt:
                det.append(u"%s sem og:image:type" % rel)
            elif esperado and mt.group(1) != esperado:
                det.append(u"%s: og:image:type diz %s, o arquivo e %s"
                           % (rel, mt.group(1), esperado))
            if not re.search(r'<meta property="og:image:alt" content="[^"]', h):
                det.append(u"%s sem og:image:alt" % rel)
            # summary_large_image sem imagem e promessa vazia
            if re.search(r'twitter:card" content="summary_large_image"', h) \
                    and not re.search(r'<meta name="twitter:image" content="[^"]', h):
                det.append(u"%s promete summary_large_image e nao tem twitter:image" % rel)
            if larg < 600 or altura < 315:
                det.append(u"%s: %s tem %dx%d, abaixo do minimo de cartao"
                           % (rel, ref.split("/")[-1], larg, altura))
        if conferidas < 100:
            det.append(u"so %d pagina(s) conferida(s); esperado ~109" % conferidas)
        return (not det, u"; ".join(det[:6])
                + (u" (+%d)" % (len(det) - 6) if len(det) > 6 else u""))

    s.check("S172", u"cartão de link coerente: og:image existe e width/height/type "
                    u"batem com o arquivo (#247)", s172)

    def s173():
        # Onda 68 (#247). As 4 superficies de identidade que o site nao tinha em
        # NENHUMA das 109 paginas: theme-color (barra do Chrome no Android),
        # msapplication-TileColor (fundo do bloco do Windows), mask-icon (aba fixada
        # do Safari) e manifest (nome e icone ao instalar no Android).
        #
        # A asserção cobra as tags E resolve o que elas prometem: o manifest tem de
        # parsear e cada icone dele existir no disco -- manifest que aponta para
        # arquivo ausente e pior que manifest nenhum, porque o Android mostra um
        # quadrado vazio no lugar da marca.
        NAVY = "#020E66"
        det = []
        for rel, h in s.conteudo():
            for nome, rex in (
                ("theme-color",
                 r'<meta name="theme-color" content="%s"' % NAVY),
                ("msapplication-TileColor",
                 r'<meta name="msapplication-TileColor" content="%s"' % NAVY),
                ("mask-icon", r'<link rel="mask-icon"[^>]*color="%s"' % NAVY),
                ("manifest", r'<link rel="manifest" href="[^"]+"'),
            ):
                if not re.search(rex, h):
                    det.append(u"%s sem %s (ou fora do navy)" % (rel, nome))
        man = os.path.join(pub, "site.webmanifest")
        if not os.path.exists(man):
            det.append(u"site.webmanifest ausente")
        else:
            try:
                with io.open(man, encoding="utf-8") as f:
                    j = json.load(f)
                if j.get("theme_color") != NAVY:
                    det.append(u"manifest com theme_color %s" % j.get("theme_color"))
                if not j.get("icons"):
                    det.append(u"manifest sem icones")
                for ic in j.get("icons", []):
                    fp = os.path.join(pub, ic["src"].lstrip("/").replace("/", os.sep))
                    if not os.path.exists(fp):
                        det.append(u"manifest aponta para %s, que nao existe" % ic["src"])
                    else:
                        dec = _dim_imagem(fp)
                        if dec and "%dx%d" % (dec[0], dec[1]) != ic.get("sizes"):
                            det.append(u"manifest diz %s para %s, que e %dx%d"
                                       % (ic.get("sizes"), ic["src"], dec[0], dec[1]))
            except Exception as e:
                det.append(u"site.webmanifest nao parseia: %s" % e)
        return (not det, u"; ".join(det[:6])
                + (u" (+%d)" % (len(det) - 6) if len(det) > 6 else u""))

    s.check("S173", u"identidade do navegador: theme-color, TileColor, mask-icon e "
                    u"manifest que resolve (#247)", s173)

    def s174():
        # Onda 68 (#247). O site declarava QUATRO Organization ao Google: as 3 do
        # Yoast, com @id relativo/por-idioma, com logo e sem endereco, e a da onda 59,
        # com endereco/descricao/fundacao e SEM logo. Quatro @id sao quatro entidades,
        # nao uma vista de quatro angulos -- nenhuma dizia ao mesmo tempo quem somos e
        # qual e a nossa marca, que e o que o painel de conhecimento precisa.
        #
        # DUAS NOTAS DE METODO, porque as duas me pegaram na mesma onda:
        #
        # 1. A primeira versao do 143 corrigiu 3 de 109 e a verificacao DELE passou
        #    verde, porque procurava a string relativa `/pt/#organization` enquanto as
        #    outras 106 usavam a absoluta por idioma. No HTML os ids vem com barra
        #    escapada (`https:\/\/`), o que ajudou a esconder. Por isso aqui o JSON e
        #    RE-PARSEADO e se olha o valor, nunca a string no arquivo.
        #
        # 2. A primeira versao DESTA assercao procurava o ImageObject do logo apenas
        #    nos nos de TOPO de `@graph`. O Yoast escreve esse no ANINHADO dentro de
        #    `Organization.logo`, entao a checagem de existencia do arquivo nunca
        #    rodava: apaguei o PNG do logo e a assercao continuou verde. Foi o teste
        #    negativo que mostrou. Agora a varredura e recursiva, pela arvore inteira.
        ORG_CANON = "https://mirow.com.br/#organization"
        det = []

        def _achar(no, tipo=None, saida=None):
            """Todos os dicts da arvore, opcionalmente filtrando por @type."""
            if saida is None:
                saida = []
            if isinstance(no, dict):
                t = no.get("@type")
                t = t if isinstance(t, list) else [t]
                if tipo is None or tipo in t:
                    saida.append(no)
                for v in no.values():
                    _achar(v, tipo, saida)
            elif isinstance(no, list):
                for v in no:
                    _achar(v, tipo, saida)
            return saida

        for rel, h in s.conteudo():
            ids, urls_logo = set(), set()
            vistos_logo = 0
            for m in re.finditer(
                    r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', h, re.S):
                try:
                    d = json.loads(m.group(1))
                except Exception:
                    det.append(u"%s tem json-ld ilegível" % rel)
                    continue
                # Onda 73: o grafo passou a ter Organization de TERCEIRO -- os
                # empregadores anteriores de cada lider, pendurados no padrao
                # Role (OrganizationRole -> worksFor -> Organization). McKinsey e
                # Aracruz nao somos nos: nao levam o nosso @id, e cobrar deles o
                # canonico faria a assercao exigir uma mentira. O invariante
                # segue igual para o que E a Mirow, e por isso o filtro e por
                # PROVENIENCIA (estar dentro de um OrganizationRole), nunca por
                # "@id ausente" -- essa era exatamente a brecha original.
                terceiros = set()
                for papel in _achar(d, "OrganizationRole"):
                    empregador = papel.get("worksFor")
                    if isinstance(empregador, dict):
                        terceiros.add(id(empregador))
                for org in _achar(d, "Organization"):
                    if id(org) in terceiros:
                        # o inverso tambem e defeito: empregador de terceiro
                        # carregando o NOSSO @id funde as duas entidades
                        if org.get("@id") == ORG_CANON:
                            det.append(u"%s: %r usa o @id canônico da Mirow"
                                       % (rel, org.get("name")))
                        continue
                    ids.add(org.get("@id"))
                for img in _achar(d, "ImageObject"):
                    if not str(img.get("@id", "")).endswith("#logo"):
                        continue
                    vistos_logo += 1
                    url = img.get("url")
                    urls_logo.add(url)
                    ref = str(url or "").replace("https://mirow.com.br/", "")
                    fp = os.path.join(pub, ref.lstrip("/").replace("/", os.sep))
                    if not ref or not os.path.exists(fp):
                        det.append(u"%s: logo aponta para %s, que não existe"
                                   % (rel, url))
                        continue
                    dec = _dim_imagem(fp)
                    if dec and (img.get("width") != dec[0]
                                or img.get("height") != dec[1]):
                        det.append(u"%s: logo declara %sx%s, o arquivo é %dx%d"
                                   % (rel, img.get("width"), img.get("height"),
                                      dec[0], dec[1]))
            # Cobrar "um @id por pagina" NAO basta, e o cenario negativo mostrou:
            # troquei as 2 ocorrencias de uma pagina para o @id por idioma e ela
            # seguiu com UM id -- outro -- e a assercao passou verde. O invariante
            # de verdade e que todas as 109 usem O MESMO id, o canonico; e isso que
            # faz o site descrever uma entidade so em vez de 109 consistentes entre
            # si e discordantes entre paginas.
            if not ids:
                det.append(u"%s sem nenhum nó Organization" % rel)
            elif ids != {ORG_CANON}:
                det.append(u"%s usa @id de Organization fora do canônico: %s"
                           % (rel, sorted(str(i) for i in ids)))
            if not vistos_logo:
                det.append(u"%s sem nó de logo" % rel)
            if len(urls_logo) > 1:
                det.append(u"%s declara %d URLs de logo diferentes"
                           % (rel, len(urls_logo)))

        # o nó rico tem de estar nas 3 homes E nas 3 listagens de líder
        for rel in list(HOMES) + ["pt/sobre-nos/lideres/index.html",
                                  "en/about-us/leaders/index.html",
                                  "de/ueber-uns/fuehrungskraefte/index.html"]:
            h = s.ler(rel)
            if '"addressLocality"' not in h or '"foundingDate"' not in h:
                det.append(u"%s sem o nó rico (endereço/fundação)" % rel)
        return (not det, u"; ".join(det[:6])
                + (u" (+%d)" % (len(det) - 6) if len(det) > 6 else u""))

    s.check("S174", u"uma Organization só no grafo, com logo que resolve, e o nó rico "
                    u"nas homes (#247)", s174)

    def s175():
        # Onda 72 (#249, #250, #251 — e-mail do Felipe de 24/08/2026). Quatro
        # invariantes, medidos no efeito (JSON re-parseado, nunca a string):
        #  a) a ficha do Felipe declara alumniOf com Chicago (o contrapeso ao único
        #     diploma alemão que fazia a máquina deduzir "consultoria alemã") e
        #     knowsAbout com os 10 termos do anexo;
        #  b) "15 anos/years/Jahre de experiência" sumiu do site inteiro — são 18;
        #  c) toda página individual de líder do cadastro (PAGINAS do 110, piso
        #     vivo, nunca número literal) tem <meta name="description"> não-vazia
        #     com o nome do líder;
        #  d) a bio média e os 8 exemplos rebalanceados estão nas 3 línguas
        #     (medido por strings distintivas: Booth School / estaleiro; e o item
        #     velho "man power planing" não pode voltar).
        det = []
        VELHO_15 = {"pt": u"15 anos de experiência", "en": u"15 years of experience",
                    "de": u"15 Jahre Erfahrung"}
        for rel, h in s.todas():
            for t in VELHO_15.values():
                if t in h:
                    det.append(u"%s ainda diz '%s'" % (rel, t))
        for lang, home in (("pt", "pt/index.html"), ("en", "en/index.html"),
                           ("de", "de/index.html")):
            h = s.ler(home)
            m = re.search(r'<script type="application/ld\+json" id="onda59-geo">'
                          r'(.*?)</script>', h, re.S)
            if not m:
                det.append(u"%s sem bloco onda59-geo" % home)
                continue
            try:
                g = json.loads(m.group(1))["@graph"]
            except (ValueError, KeyError) as e:
                det.append(u"%s: JSON inválido (%s)" % (home, e))
                continue
            # Onda 72b (#249, confirmação do Mario em 24/08): TODO líder do grafo tem
            # alumniOf não-vazio — era exatamente a assimetria (só diploma alemão
            # legível) que fazia a máquina deduzir "consultoria alemã".
            for p in g:
                if p.get("@type") == "Person" and not p.get("alumniOf"):
                    det.append(u"%s: %s sem alumniOf" % (lang, p.get("name")))
            fel = [p for p in g if p.get("name") == u"Felipe Diniz"]
            if not fel:
                det.append(u"%s sem o Person do Felipe" % home)
                continue
            p = fel[0]
            alumni = [a.get("name", "") for a in p.get("alumniOf", [])]
            if u"University of Chicago" not in alumni or not any(u"EPGE" in a for a in alumni):
                det.append(u"%s: alumniOf do Felipe = %r (falta Chicago/EPGE)" % (lang, alumni))
            if len(p.get("knowsAbout", [])) < 10:
                det.append(u"%s: knowsAbout do Felipe com %d termos (< 10)"
                           % (lang, len(p.get("knowsAbout", []))))
            if "18" not in p.get("description", ""):
                det.append(u"%s: descrição do Felipe sem os 18 anos" % lang)
        DISTINTIVAS = {"pt": (u"estaleiro de reparação naval", u"Booth School of Business"),
                       "en": (u"ship repair yard", u"Booth School of Business"),
                       "de": (u"Schiffsreparaturwerft", u"Booth School of Business")}
        VELHOS = (u"man power planing", u"manpower planning model",
                  u"Modells für das Personalmanagement")
        for nome, paginas in _mod110().PAGINAS.items():
            for lang, rel in paginas.items():
                h = s.ler(rel + "/index.html")
                m = re.search(r'<meta name="description"[^>]*content="([^"]+)"', h)
                primeiro = nome.split()[-2] if nome.startswith(u"Prof") else nome.split()[0]
                if not m or primeiro not in m.group(1):
                    det.append(u"%s sem meta description com o nome" % rel)
                if nome == u"Felipe Diniz" and DISTINTIVAS[lang][1] not in h:
                    det.append(u"%s sem a bio média (Booth ausente)" % rel)
        for lang, home in (("pt", "pt/index.html"), ("en", "en/index.html"),
                           ("de", "de/index.html")):
            h = s.ler(home)
            if DISTINTIVAS[lang][0] not in h:
                det.append(u"%s sem os 8 exemplos novos (estaleiro ausente)" % home)
            for v in VELHOS:
                if v in h:
                    det.append(u"%s ainda tem exemplo velho: %s" % (home, v))
        return (not det, u"; ".join(det[:6])
                + (u" (+%d)" % (len(det) - 6) if len(det) > 6 else u""))

    s.check("S175", u"bio nova do Felipe: alumniOf+knowsAbout na ficha, 18 anos em vez "
                    u"de 15, meta description nos líderes, bio média e 8 exemplos (#249-#251)", s175)

    def s176():
        # Onda 73 (#254): o LinkedIn do Stephan que o site publicava caía em
        # `linkedin.com/404/` -- medido no navegador em 25/08/2026. A asserção
        # tem DUAS pernas, e a segunda é a que importa:
        #  a) todo link de LinkedIn de líder que aparece em qualquer página é um
        #     dos do mestre `LINKEDIN` do 148 (fonte única, P3) -- URL de líder
        #     fora do mestre é erro, mesmo que pareça plausível;
        #  b) nenhum slug da tabela `MORTOS` sobrevive em página nenhuma -- é o
        #     cenário negativo, e é o que pega a reintrodução do link morto por
        #     um script antigo que ninguém lembrou de atualizar (erro 11).
        # O que esta asserção NÃO prova: que o link está vivo. Isso se mede no
        # navegador, porque o LinkedIn responde 999 a cliente que não é
        # navegador e 999 não distingue perfil vivo de 404. O mestre carrega a
        # data em que cada URL foi verificada de verdade -- o gate garante que o
        # site concorda com o mestre, não que o mundo não mudou desde então.
        mestre = set(_mod148().LINKEDIN.values()) | set(_mod148().OUTROS.values())
        # o mestre traz a forma canônica com barra final; o HTML pode não ter
        canon = set(u.rstrip("/") for u in mestre)
        mortos = _mod148().MORTOS
        det = []
        for rel, h in s.todas():
            for morto in mortos:
                if morto in h:
                    det.append(u"%s ainda tem o slug morto %s" % (rel, morto))
            for m in re.finditer(r'https://www\.linkedin\.com/in/([A-Za-z0-9._%-]+)', h):
                url = "https://www.linkedin.com/in/" + m.group(1)
                if url.rstrip("/") not in canon:
                    det.append(u"%s: LinkedIn fora do mestre: %s" % (rel, url))
        # e cada líder do cadastro tem o seu, na página individual dos 3 idiomas
        for nome, paginas in _mod110().PAGINAS.items():
            alvo = _mod148().LINKEDIN.get(nome, "").rstrip("/")
            if not alvo:
                det.append(u"%s sem URL no mestre LINKEDIN" % nome)
                continue
            for lang, rel in paginas.items():
                if alvo not in s.ler(rel + "/index.html"):
                    det.append(u"%s (%s) sem o LinkedIn do mestre" % (rel, lang))
        det = sorted(set(det))
        return (not det, u"; ".join(det[:6])
                + (u" (+%d)" % (len(det) - 6) if len(det) > 6 else u""))

    s.check("S176", u"LinkedIn dos líderes igual ao mestre do 148; 0 slug morto no site (#254)",
            s176)

    def s177():
        # Onda 73: a experiência anterior de cada líder no JSON-LD das 3 homes e
        # das 3 listagens. Antes daqui o grafo dizia só "worksFor: Mirow & Co." --
        # cinco pessoas sem passado, para quem lê por máquina.
        # Medido contra a constante `EXPERIENCIA` do 111 (nunca um número escrito
        # aqui: erro 18), e o que se cobra é a FORMA que o schema.org exige para
        # datar um vínculo -- o padrão Role (worksFor -> OrganizationRole ->
        # worksFor -> Organization). Cargo sem organização, ou sem startDate,
        # não é vínculo: é ruído.
        exp = _mod111().EXPERIENCIA
        det = []
        alvos = [("pt", "pt/index.html"), ("en", "en/index.html"), ("de", "de/index.html"),
                 ("pt", "pt/sobre-nos/lideres/index.html"),
                 ("en", "en/about-us/leaders/index.html"),
                 ("de", "de/ueber-uns/fuehrungskraefte/index.html")]
        for lang, rel in alvos:
            h = s.ler(rel)
            m = re.search(r'<script type="application/ld\+json" id="onda59-geo">'
                          r'(.*?)</script>', h, re.S)
            if not m:
                det.append(u"%s sem bloco onda59-geo" % rel)
                continue
            try:
                grafo = json.loads(m.group(1))["@graph"]
            except (ValueError, KeyError) as e:
                det.append(u"%s: JSON inválido (%s)" % (rel, e))
                continue
            pessoas = dict((p.get("name"), p) for p in grafo if p.get("@type") == "Person")
            for nome, vinculos in exp.items():
                # o nome no grafo leva o ponto depois de "Dr" (normalização do 111)
                chave = nome.replace(u"Prof. Dr Stephan Friedrich",
                                     u"Prof. Dr. Stephan Friedrich")
                p = pessoas.get(chave)
                if p is None:
                    det.append(u"%s: sem o Person de %s" % (rel, chave))
                    continue
                w = p.get("worksFor")
                if not isinstance(w, list):
                    det.append(u"%s: worksFor de %s não é lista" % (rel, chave))
                    continue
                if not any(isinstance(x, dict) and x.get("@id") for x in w):
                    det.append(u"%s: %s sem o vínculo corrente com a Mirow" % (rel, chave))
                papeis = [x for x in w if isinstance(x, dict)
                          and x.get("@type") == "OrganizationRole"]
                if len(papeis) != len(vinculos):
                    det.append(u"%s: %s com %d vínculo(s) passado(s), esperados %d"
                               % (rel, chave, len(papeis), len(vinculos)))
                orgs_esperadas = set(o for _c, o, _i, _f in vinculos)
                for r in papeis:
                    org = (r.get("worksFor") or {}).get("name")
                    if not org:
                        det.append(u"%s: %s tem papel sem organização" % (rel, chave))
                    elif org not in orgs_esperadas:
                        det.append(u"%s: %s com organização inesperada %r"
                                   % (rel, chave, org))
                    if not r.get("startDate"):
                        det.append(u"%s: %s — %s sem startDate" % (rel, chave, org))
                    if not r.get("roleName"):
                        det.append(u"%s: %s — %s sem roleName" % (rel, chave, org))
        det = sorted(set(det))
        return (not det, u"; ".join(det[:6])
                + (u" (+%d)" % (len(det) - 6) if len(det) > 6 else u""))

    s.check("S177", u"experiência anterior dos líderes no JSON-LD, no padrão Role do "
                    u"schema.org (org + cargo + startDate)", s177)

    def s178():
        # Onda 74 (#252): o `sameAs` do Wikidata liga o que o site afirma ao que o
        # Wikidata afirma. Sem ele são duas descrições parecidas de duas entidades;
        # com ele é uma entidade com duas fontes.
        #
        # O que se cobra, contra o mestre `WIKIDATA` do 111 (P3, nunca um QID
        # escrito aqui — valor gêmeo diverge na primeira mudança):
        #  a) a Organization e TODA Person do cadastro têm sameAs de Wikidata;
        #  b) o QID é exatamente o do mestre (o cenário negativo que importa é a
        #     TROCA entre duas pessoas — "tem um QID" passaria verde nela);
        #  c) os QIDs são distintos entre si (copiar-colar é a falha natural aqui);
        #  d) a forma é `https://www.wikidata.org/wiki/Q<dígitos>`.
        #
        # O que esta asserção NÃO prova: que o QID existe no Wikidata e descreve
        # quem dizemos. Isso foi medido na API em 31/08/2026, quando os 6 itens
        # foram criados, e o par site↔Wikidata é bidirecional lá (P108 de cada
        # pessoa aponta para a empresa; a empresa tem P112 → Andreas).
        mestre = _mod111().WIKIDATA
        forma = re.compile(r"^https://www\.wikidata\.org/wiki/Q[0-9]+$")
        vistos = {}
        det = []
        for chave, qid in mestre.items():
            if not qid.startswith("Q") or not qid[1:].isdigit():
                det.append(u"QID malformado no mestre: %s -> %r" % (chave, qid))
            if qid in vistos:
                det.append(u"QID repetido no mestre: %s e %s usam %s"
                           % (vistos[qid], chave, qid))
            vistos[qid] = chave
        alvos = [("pt", "pt/index.html"), ("en", "en/index.html"), ("de", "de/index.html"),
                 ("pt", "pt/sobre-nos/lideres/index.html"),
                 ("en", "en/about-us/leaders/index.html"),
                 ("de", "de/ueber-uns/fuehrungskraefte/index.html")]
        for lang, rel in alvos:
            m = re.search(r'<script type="application/ld\+json" id="onda59-geo">'
                          r'(.*?)</script>', s.ler(rel), re.S)
            if not m:
                det.append(u"%s sem bloco onda59-geo" % rel)
                continue
            try:
                grafo = json.loads(m.group(1))["@graph"]
            except (ValueError, KeyError) as e:
                det.append(u"%s: JSON inválido (%s)" % (rel, e))
                continue
            achados = {}
            for no in grafo:
                tipos = no.get("@type")
                tipos = tipos if isinstance(tipos, list) else [tipos]
                if "Person" not in tipos and "Organization" not in tipos:
                    continue
                nome = no.get("name")
                wd = [x for x in (no.get("sameAs") or []) if "wikidata.org" in x]
                if not wd:
                    det.append(u"%s: %s sem sameAs de Wikidata" % (rel, nome))
                    continue
                if len(wd) > 1:
                    det.append(u"%s: %s com %d sameAs de Wikidata" % (rel, nome, len(wd)))
                if not forma.match(wd[0]):
                    det.append(u"%s: %s com URL fora do padrão: %s" % (rel, nome, wd[0]))
                    continue
                achados[nome] = wd[0].rsplit("/", 1)[-1]
            # o nome no grafo leva o ponto depois de "Dr" (normalização do 111)
            for chave, qid in mestre.items():
                nome = chave.replace(u"Prof. Dr Stephan Friedrich",
                                     u"Prof. Dr. Stephan Friedrich")
                if nome not in achados:
                    det.append(u"%s: %s ausente do grafo (ou sem sameAs)" % (rel, nome))
                elif achados[nome] != qid:
                    det.append(u"%s: %s aponta para %s, o mestre diz %s"
                               % (rel, nome, achados[nome], qid))
            if len(set(achados.values())) != len(achados):
                det.append(u"%s: dois nós apontam para o MESMO QID" % rel)
        det = sorted(set(det))
        return (not det, u"; ".join(det[:6])
                + (u" (+%d)" % (len(det) - 6) if len(det) > 6 else u""))

    s.check("S178", u"sameAs do Wikidata na firma e em cada líder, igual ao mestre de QIDs (#252)",
            s178)

    def s179():
        # Onda 75: a matéria da IstoÉ Dinheiro saiu do ar (301 → 404, com o domínio
        # vivo) e o link passou a apontar para o snapshot do Wayback.
        #
        # Duas coisas, e a segunda é um defeito que eu mesmo criei e consertei:
        #  a) a URL morta não pode voltar. Ela volta sozinha se alguém rodar o
        #     `tools/gen_imprensa.py` antes de o mestre ser corrigido no repo
        #     PRIVADO — o gerador é a fonte, e este site é só o artefato;
        #  b) nenhuma URL de arquivo pode estar ANINHADA. A URL do Wayback contém a
        #     original como sufixo, então um replace cego re-embrulha o link a cada
        #     execução: `.../web/DATA/https://web.archive.org/web/DATA/https://…`.
        #     Aconteceu na 2ª execução do 149, e o link ainda "funcionava" —
        #     defeito que só aparece se alguém medir a forma.
        MORTAS = ["https://istoedinheiro.com.br/com-white-martins-brasil-entra-na-trilha-"
                  "do-hidrogenio-verde/"]
        det = []
        for rel, h in s.todas():
            for u in MORTAS:
                # a URL morta é sufixo da arquivada; só é defeito quando aparece SEM
                # o prefixo do Wayback na frente
                if u in h.replace("https://web.archive.org/web/20231206004028/" + u, ""):
                    det.append(u"%s traz a URL morta da IstoÉ" % rel)
            if re.search(r"web\.archive\.org/web/\d+/https://web\.archive\.org", h):
                det.append(u"%s tem URL de arquivo aninhada" % rel)
        pj = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "imprensa-publicada.json")
        if os.path.exists(pj):
            bruto = io.open(pj, encoding="utf-8").read()
            for u in MORTAS:
                if u in bruto.replace("https://web.archive.org/web/20231206004028/" + u, ""):
                    det.append(u"tools/imprensa-publicada.json traz a URL morta")
            if re.search(r"web\.archive\.org/web/\d+/https://web\.archive\.org", bruto):
                det.append(u"tools/imprensa-publicada.json tem URL de arquivo aninhada")
        det = sorted(set(det))
        return (not det, u"; ".join(det[:6])
                + (u" (+%d)" % (len(det) - 6) if len(det) > 6 else u""))

    s.check("S179", u"0 link de imprensa morto e 0 URL de arquivo aninhada", s179)

    def s180():
        # Onda 77 (31/08/2026). O Mario mandou tirar da PAGINA INICIAL a frase
        # "A Mirow & Co. e uma consultoria estrategica brasileira, com sede no Rio
        # de Janeiro", nas palavras dele: "nunca te pedi para colocar isso".
        #
        # A asserção cobra o EFEITO em duas frentes, porque tirar o texto uma vez
        # não basta: o `113_geo_frase_sede.py` existe e sabe reinserir. Se alguém
        # rodar a onda 59-sede de novo, ou reativar o HOMES dele, a frase volta
        # sozinha — e é isso que esta sentinela pega.
        #   (a) nenhuma das 3 homes traz a frase, em nenhum dos 3 idiomas;
        #   (b) nenhuma das 3 homes traz a classe `onda59-sede`, que é a casca —
        #       parágrafo vazio guardaria o espaçamento e um nó sem conteúdo.
        FRASES = [
            u"consultoria estratégica brasileira, com sede no Rio de Janeiro",
            u"Brazilian strategy consulting firm headquartered in Rio de Janeiro",
            u"brasilianische Strategieberatung mit Sitz in Rio de Janeiro",
        ]
        # ALCANCE, dito na cara: esta asserção mede o CORPO da página — o texto que
        # o visitante lê. As mesmas palavras seguem no <head> das 3 homes, na
        # `meta description` e na `description` do JSON-LD, que não são texto
        # visível e são a munição do trabalho de GEO. Tirar de lá é decisão
        # editorial do Mario, perguntada em 31/08 e ainda sem resposta — enquanto
        # não houver, a asserção não pode fingir que cobre o que não cobre.
        det = []
        for rel in ("pt/index.html", "en/index.html", "de/index.html"):
            h = s.ler(rel)
            corpo = h.split("</head>", 1)[-1]
            for f in FRASES:
                if f in corpo:
                    det.append(u"%s ainda traz a frase de sede no corpo" % rel)
            if "onda59-sede" in corpo:
                det.append(u"%s ainda tem a casca .onda59-sede" % rel)
        det = sorted(set(det))
        return (not det, u"; ".join(det) or u"as 3 homes sem a frase no corpo e sem a casca (o <head> nao e coberto)")

    s.check("S180", u"frase de sede fora do CORPO da página inicial, nos 3 idiomas (Mario, 31/08)",
            s180)

    def s181():
        # Onda 78 (pedido do Mario, 31/08): cada card de líder mostra as
        # instituições por onde ele passou, com ícone de tipo.
        #
        # O que se cobra é a PARIDADE com a fonte: a quantidade de chips de cada
        # pessoa tem de bater com `ALUMNI` + `EXPERIENCIA` do 111 — as mesmas
        # constantes que alimentam o JSON-LD. Se o card e a ficha da máquina
        # discordarem, um dos dois está mentindo e ninguém sabe qual. Número de
        # chip nunca é escrito aqui (erro 18): sai da constante, em runtime.
        m111, m152 = _mod111(), _mod152()
        det = []
        for rel in ("pt/sobre-nos/lideres/index.html",
                    "en/about-us/leaders/index.html",
                    "de/ueber-uns/fuehrungskraefte/index.html"):
            h = s.ler(rel)
            for nome in _mod110().PAGINAS:
                esperado = []
                vistos = set()
                for inst in m111.ALUMNI.get(nome, []):
                    c = m152.CURTO.get(inst, inst)
                    if c not in vistos:
                        vistos.add(c)
                        esperado.append(c)
                for _cg, org, _i, _f in m111.EXPERIENCIA.get(nome, []):
                    c = m152.CURTO.get(org, org)
                    if c not in vistos:
                        vistos.add(c)
                        esperado.append(c)
                if not esperado:
                    continue
                # recorta o card da pessoa e conta os chips DELE
                curto = nome.replace(u"Prof. Dr Stephan Friedrich",
                                     u"Prof. Dr Stephan Friedrich")
                i = h.find(u">%s<" % curto)
                if i < 0:
                    det.append(u"%s: card de %s não encontrado" % (rel, nome))
                    continue
                fim = h.find(u'page-leaders__list-item-more', i)
                card = h[i:fim if fim > i else i + 6000]
                achados = re.findall(r'onda78-inst__item[^>]*>.*?<span>([^<]+)</span>',
                                     card, re.S)
                if len(achados) != len(esperado):
                    det.append(u"%s: %s tem %d chip(s), esperados %d"
                               % (rel, nome, len(achados), len(esperado)))
                faltam = [e for e in esperado if e not in achados]
                if faltam:
                    det.append(u"%s: %s sem os chips %s"
                               % (rel, nome, ", ".join(faltam[:3])))
        det = sorted(set(det))
        return (not det, u"; ".join(det[:5])
                or u"chips de instituição batem com ALUMNI+EXPERIENCIA nos 3 idiomas")

    s.check("S181", u"cards de líder mostram as instituições, iguais à fonte do JSON-LD (onda 78)",
            s181)

    def s28():
        # S-28 (#80): "Private:" é artefato do WordPress (post de perfil marcado
        # privado) e não pode aparecer em página nenhuma; o Elmar é Senior
        # Expert (decisão da onda 6) — nunca mais Managing Partner.
        ruins = [rel for rel, h in s.todas() if "Private:" in h]
        elmar = [rel for rel, h in s.todas()
                 if re.search(r'Elmar Gans</(?:strong|h4)>(?:<[^>]*>)?Managing Partner', h)]
        det = []
        if ruins:
            det.append(u'"Private:" em %d página(s): %s' % (len(ruins), ", ".join(ruins[:3])))
        if elmar:
            det.append(u"Elmar como Managing Partner em: %s" % ", ".join(elmar[:3]))
        return (not ruins and not elmar, u"; ".join(det))
    s.check("S28", u'0 "Private:" no site; Elmar sempre Senior Expert', s28)

    def s03():
        # S-03 (#53): a Sotreq — o caso que originou o P3 — na barra das 4
        # homes. H03/H04 já cobrem contagem e paridade com o mestre; esta
        # asserção grava o pedido nominal que ficou 2 ondas bloqueado.
        ruins = [rel for rel in HOMES if "/clientes/sotreq.svg" not in s.ler(rel)]
        return (not ruins, u"Sotreq ausente de: %s" % ", ".join(ruins))
    s.check("S03", u"Sotreq na barra de clientes das 4 homes", s03)

    def s23():
        # Historico: #73 (malha animada) -> S-37/#92 (31/07: volta do video)
        # -> S-49/#107 (03/08: o Mario pediu fundo dinamico futurista, viu 3
        # sugestoes prototipadas e ESCOLHEU o "Horizonte 2050" com convite ao
        # scroll — decisao do dono, reverte a S-37). O hero das 4 homes usa os
        # 2 canvases da onda17 + JS; o MP4 de 22,8 MB NAO pode voltar, nem os
        # restos da malha antiga.
        ruins = []
        for rel in HOMES:
            h = s.ler(rel)
            for vivo in ("hero-horizonte__cena", "hero-horizonte__convite",
                         "onda17-horizonte.js"):
                if vivo not in h:
                    ruins.append("%s sem %s" % (rel, vivo))
            for morto in ("video-bg-home-1.mp4", "hero-malha__img",
                          "hero-malha__canvas", "onda13-hero-plexus.js"):
                if morto in h:
                    ruins.append("%s ainda tem %s" % (rel, morto))
        return (not ruins, u"; ".join(ruins[:4]))
    s.check("S23", u"hero Horizonte 2050 (canvas, S-49); 0 vídeo de 22,8 MB", s23)

    def s30():
        # S-30 (#82): a malha preenche o quadro — a classe que desliga a
        # máscara vertical do tema tem que estar no div do hero das 4 homes.
        ruins = [rel for rel in HOMES
                 if 'banner__background banner__background--malha' not in s.ler(rel)]
        return (not ruins, u"classe da malha cheia ausente de: %s" % ", ".join(ruins))
    s.check("S30", u"malha do hero sem a máscara do tema (borda esmaecida)", s30)

    def s31():
        # S-31 (#83): a seção "nossos números" saiu da home (números no hero).
        ruins = [rel for rel in HOMES if "our-numbers" in s.ler(rel)]
        return (not ruins, u'seção "nossos números" ainda em: %s' % ", ".join(ruins))
    s.check("S31", u'0 seções "nossos números" nas 4 homes', s31)

    def s05():
        # S-05 (#54): cards de expertise curtos e executivos — o corpo de cada
        # card cabe em 1 frase (~140 chars). Antes tinham 300-400.
        ruins = []
        for rel in HOMES:
            h = s.ler(rel)
            for m in re.finditer(
                    r'home-experience__list-item-content"><p>(.*?)</p>', h, re.S):
                txt = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                if len(txt) > 160:
                    ruins.append("%s: %d chars (%r...)" % (rel, len(txt), txt[:40]))
        return (not ruins, u"; ".join(ruins))
    s.check("S05", u"cards de expertise com texto curto (1 frase executiva)", s05)

    def s32():
        # S-32 (#84): dropdown do menu com a altura do conteúdo (o min-height
        # de tela inteira do tema anulado no bloco) + nav no rodapé (marcador
        # coberto pela M-assertion onda14:rodape-menu).
        css = s.ler("wp-content/uploads/2026/07/onda6/onda6.css")
        ini = css.find("/* onda14:menu-executivo:ini */")
        fim = css.find("/* onda14:menu-executivo:fim */")
        if ini < 0 or fim < 0:
            return (False, u"bloco onda14:menu-executivo ausente")
        bloco = css[ini:fim]
        faltam = [ag for ag in ("min-height:0", ".rodape-menu") if ag not in bloco]
        return (not faltam, u"bloco sem: %s" % ", ".join(faltam))
    s.check("S32", u"dropdown do menu ajustado ao conteúdo; nav do rodapé estilizada", s32)

    def s34():
        # S-34: os painéis de vidro de leitura ficam (texto + números), o
        # fundo é o vídeo (S23) — imagens da fase de teste não voltam.
        ruins = []
        for rel in HOMES:
            h = s.ler(rel)
            if "hero-texto" not in h:
                ruins.append("%s sem o painel de leitura do texto" % rel)
            for morto in ("onda6/malha-hero.jpg", "onda6/lampada-hero.jpg"):
                if morto in h:
                    ruins.append("%s ainda referencia %s" % (rel, morto))
        return (not ruins, u"; ".join(ruins))
    s.check("S34", u"painéis de leitura no hero; 0 imagem da fase de teste", s34)

    def s38():
        # S-38: linha legal enxuta — o logo grande e o LinkedIn saíram (já
        # moram na barra clonada); sobra só o link pequeno da política.
        ruins = [rel for rel, h in s.conteudo()
                 if '<footer class="footer">' in h and "footer__brand" in h]
        sem = [rel for rel, h in s.conteudo()
               if '<footer class="footer">' in h and "onda15:rodape-legal" not in h]
        det = []
        if ruins:
            det.append(u"logo antigo ainda em %d página(s): %s" % (len(ruins), ", ".join(ruins[:3])))
        if sem:
            det.append(u"%d página(s) sem a linha enxuta" % len(sem))
        return (not ruins and not sem, u"; ".join(det))
    s.check("S38", u"linha legal do rodapé enxuta (só o link da política)", s38)

    def s40():
        # S-40: preview de link (WhatsApp/OG). og:image/og:url absolutas em
        # toda página; as homes usam o cartão com o logo. ATENÇÃO: o host é o
        # do Pages — na migração de DNS, rodar o script 60 com o host novo e
        # atualizar aqui.
        rex = re.compile(r'<meta (?:property|name)="(?:og:image|og:url|twitter:image)" '
                         r'content="([^"]*)"')
        relativas = []
        for rel, h in s.conteudo():
            for v in rex.findall(h):
                if v.startswith("/"):
                    relativas.append("%s -> %s" % (rel, v[:40]))
                    break
        sem_cartao = [rel for rel in HOMES
                      if "onda6/og-mirow.png" not in s.ler(rel)]
        det = []
        if relativas:
            det.append(u"%d página(s) com OG relativa: %s" % (len(relativas), "; ".join(relativas[:3])))
        if sem_cartao:
            det.append(u"homes sem o cartão do logo: %s" % ", ".join(sem_cartao))
        return (not relativas and not sem_cartao, u"; ".join(det))
    s.check("S40", u"preview de link: OG absoluto; cartão do logo nas homes", s40)

    def s36():
        # S-36 v3 — APOSENTADA a barra do rodape (onda 42, #191, decisao
        # explicita do Mario 06/08: "aposentar a barra inferior... gostei da
        # ideia"). Com a barra superior fixa (S-137), o clone perdeu a funcao.
        # A assercao INVERTE: nenhuma pagina de conteudo pode voltar a ter o
        # clone; a linha legal (politica de privacidade) tem que continuar.
        ruins = []
        for rel, h in s.conteudo():
            if '<footer class="footer">' not in h:
                continue
            if 'class="rodape-barra"' in h:
                ruins.append(u"%s com a barra do rodape de volta" % rel)
            if 'rodape-legal' not in h:
                ruins.append(u"%s sem a linha legal" % rel)
        return (not ruins, u"%d página(s): %s" % (len(ruins), "; ".join(ruins[:3])))
    s.check("S36", u"barra do rodapé aposentada (não volta) e linha legal presente (#191)", s36)

    def s41():
        # S-41 (#97): big numbers perto da borda direita do viewport (calc
        # com 100vw no CSS) e painel do hero puxado para a esquerda (min()).
        css = s.ler("wp-content/uploads/2026/07/onda6/onda6.css")
        det = []
        if "onda16:hero-layout-s41:ini" not in css:
            det.append(u"bloco onda16:hero-layout-s41 ausente do onda6.css")
        else:
            bloco = css.split("onda16:hero-layout-s41:ini")[1].split(
                "onda16:hero-layout-s41:fim")[0]
            if "100vw" not in bloco or ".hero-numeros" not in bloco:
                det.append(u"pilha de números sem o calc de viewport")
            if "min(-30px" not in bloco or ".hero-texto" not in bloco:
                det.append(u"painel do hero sem o deslocamento à esquerda")
        return (not det, u"; ".join(det))
    s.check("S41", u"hero: números na borda direita; painel à esquerda (CSS)", s41)

    def s42():
        # S-42 (#98): hover com a cor da marca. Classes --in/--ig/--mail nos
        # links de contato (hero das homes + barras de toda página) e regras
        # de cor no onda6.css.
        css = s.ler("wp-content/uploads/2026/07/onda6/onda6.css")
        det = []
        bloco = ""
        if "onda16:hover-marcas-s42:ini" in css:
            bloco = css.split("onda16:hover-marcas-s42:ini")[1].split(
                "onda16:hover-marcas-s42:fim")[0]
        for cor, quem in (("#0A66C2", "LinkedIn"), ("#E1306C", "Instagram"),
                          ("#00ADEC", "e-mail")):
            if cor not in bloco:
                det.append(u"cor de %s ausente do bloco S-42" % quem)
        for rel in HOMES:
            h = s.ler(rel)
            for cls in ("hero-contatos__link--in", "hero-contatos__link--ig",
                        "hero-contatos__link--mail"):
                if cls not in h:
                    det.append(u"%s sem %s" % (rel, cls))
        sem_mod = []
        for rel, h in s.conteudo():
            for m in re.finditer(r'<a\b[^>]*menu__contatos-link[^>]*>', h):
                tag = m.group(0)
                if "menu__contatos-link--" in tag:
                    continue
                if "mailto:" in tag or "linkedin.com" in tag or "instagram.com" in tag:
                    sem_mod.append(rel)
                    break
        if sem_mod:
            det.append(u"%d página(s) com ícone de barra sem modificador: %s"
                       % (len(sem_mod), ", ".join(sem_mod[:3])))
        return (not det, u"; ".join(det[:5]))
    s.check("S42", u"hover na cor da marca (classes + cores no CSS)", s42)

    # ------------------------------------------------------------------ onda 18
    # 22 pedidos do Mario de 03/08 (S-50..S-71, issues #108..#129). Uma asserção
    # por pedido — id S50..S71, na mesma numeração das issues.
    css_o18 = s.ler("wp-content/uploads/2026/07/onda6/onda6.css")

    def s50():
        # o ícone "in" do card de líder tem que ser <a> para o LinkedIn real,
        # nunca o SVG decorativo dentro do <button> (que abria a bio)
        det = []
        for rel in HOMES:
            h = s.ler(rel)
            n_cards = h.count('class="home-leaders__card"')
            n_links = len(re.findall(
                r'class="onda18-lider__in" href="https://[^"]*linkedin\.com/in/', h))
            if n_cards != n_links:
                det.append(u"%s: %d card(s) e %d link(s) de LinkedIn"
                           % (rel, n_cards, n_links))
        return (not det, u"; ".join(det))
    s.check("S50", u"card de líder com link real do LinkedIn (#108)", s50)

    def s51():
        faltam = [rel for rel, h in s.conteudo()
                  if 'class="onda19-lateral__link onda19-lateral__link--topo"' not in h]
        semanc = [rel for rel, h in s.conteudo() if 'id="topo"' not in h]
        det = []
        if faltam:
            det.append(u"%d página(s) sem botão de voltar ao topo: %s"
                       % (len(faltam), ", ".join(faltam[:3])))
        if semanc:
            det.append(u"%d página(s) sem a âncora id=topo: %s"
                       % (len(semanc), ", ".join(semanc[:3])))
        return (not det, u"; ".join(det))
    s.check("S51", u"botão de voltar ao topo em todas as páginas (#109)", s51)

    def s52():
        # no rodapé a lista de idiomas tem que subir (bottom), não descer (top)
        ok = (".rodape-barra .menu__languages-list" in css_o18
              and "bottom:calc(100% - 2px)" in css_o18)
        return (ok, u"falta a regra que abre o seletor de idiomas para cima")
    s.check("S52", u"idiomas do rodapé abrem para cima (#110)", s52)

    def s53():
        ok = ("margin-bottom:8px !important" in css_o18
              and ".rodape-legal{padding-top:0 !important}" in css_o18)
        return (ok, u"falta a redução de espaço entre a linha e a política")
    s.check("S53", u"menos espaco linha -> politica de privacidade (#111)", s53)

    def s54():
        # texto e ícones maiores que o estado da onda 15 (15px / 22px)
        det = []
        if ".menu__nav-link{font-size:17px !important}" not in css_o18:
            det.append(u"menu não está em 17px")
        if ".menu__contatos svg{width:26px !important;height:26px !important}" not in css_o18:
            det.append(u"ícones de contato não estão em 26px")
        if ".rodape-menu a{font-size:17px}" not in css_o18:
            det.append(u"nav do rodapé não está em 17px")
        return (not det, u"; ".join(det))
    s.check("S54", u"texto e ícones maiores nas duas barras (#112)", s54)

    def s55():
        ok = ".job-contact--topo .job-contact__title{color:#fff !important}" in css_o18
        return (ok, u'falta o branco no título "Trabalhe Conosco"')
    s.check("S55", u'"Trabalhe Conosco" legível em carreiras (#113)', s55)

    def s56():
        # o card de insight não pode começar em grayscale(100%). Onda 41 (#187)
        # subiu o brightness de 0.38 para 0.9; onda 42 (#193) foi a cor plena
        # (1.0) com scrim só na base — o efeito renderizado é a V24.
        ok = (".page-insights__list-image{filter:grayscale(0%) brightness(1) !important}"
              in css_o18)
        return (ok, u"falta a regra que tira o grayscale inicial dos insights")
    s.check("S56", u"insights começam coloridos (#114)", s56)

    def s57():
        alvos = IMPRENSA
        det = []
        for rel in alvos:
            h = s.ler(rel)
            if 'class="onda18-imprensa"' not in h:
                det.append(u"%s sem a lista nova" % rel)
                continue
            n = h.count('class="onda18-imprensa__item"')
            if n < 20:
                det.append(u"%s com só %d item(ns)" % (rel, n))
            for campo in ("__veiculo", "__data", "__titulo"):
                if ("onda18-imprensa%s" % campo) not in h:
                    det.append(u"%s sem %s" % (rel, campo))
        if ".onda18-imprensa{list-style:none;margin:0 0 60px;padding:0;background:#fff}" \
                not in css_o18:
            det.append(u"lista de imprensa sem fundo branco no CSS")
        return (not det, u"; ".join(det[:5]))
    s.check("S57", u"imprensa em lista branca com veículo/data/link (#115)", s57)



    def s60():
        det = []
        for rel, h in s.todas():
            if 'id="form_contact-form"' not in h:
                continue
            m = re.search(r'<div id="frm_field_6_container"[^>]*>.*?</div>', h, re.S)
            bloco = m.group(0) if m else ""
            if "frm_required_field" in bloco or 'aria-required="true"' in bloco:
                det.append(rel)
        return (not det, u"%d página(s) ainda exigindo telefone: %s"
                % (len(det), ", ".join(det[:3])))
    s.check("S60", u"contato: telefone não obrigatório (#118)", s60)

    def s61():
        det = []
        for rel, h in s.todas():
            if 'id="form_contact-form"' not in h:
                continue
            m = re.search(r'<textarea name="item_meta\[5\]"[^>]*>(.*?)</textarea>', h, re.S)
            if not m or len(m.group(1).strip()) < 30:
                det.append(rel)
        return (not det, u"%d página(s) sem mensagem-padrão: %s"
                % (len(det), ", ".join(det[:3])))
    s.check("S61", u"contato: mensagem-padrão pré-preenchida (#119)", s61)

    def s62():
        # a regra tem que bater a especificidade do tema
        # (.contact__form .frm_pro_form .frm_button_submit, com !important)
        ok = ("background:#00ADEC !important" in css_o18
              and ".contact .contact__form .frm_pro_form .frm_button_submit" in css_o18)
        return (ok, u"botão de envio segue sem contraste próprio")
    s.check("S62", u'contato: botão "Enviar mensagem" visível (#120)', s62)

    def s63():
        det = []
        for rel in CARREIRAS:
            h = s.ler(rel)
            if "onda11:s12-cta-cliente" in h:
                det.append(u'%s ainda tem o bloco "já é cliente?"' % rel)
            m = re.search(r'value-offer__title">([^<]*)', h)
            if m and (u"para você" in m.group(1) or u"for you" in m.group(1)
                      or u"für Sie" in m.group(1)):
                det.append(u'%s: título ainda diz "para você"' % rel)
        return (not det, u"; ".join(det[:4]))
    s.check("S63", u'carreiras: sem "já é cliente?" e sem "para você" (#121)', s63)

    def s64():
        det = []
        for rel in CARREIRAS:
            h = s.ler(rel)
            if 'class="onda18-inscrever__link" href="#inscricao"' not in h:
                det.append(u"%s sem botão de inscrição no fim" % rel)
            if 'id="inscricao"' not in h:
                det.append(u"%s sem a âncora do formulário" % rel)
        return (not det, u"; ".join(det[:4]))
    s.check("S64", u"carreiras: botão de inscrição no fim da página (#122)", s64)

    def s65():
        det = []
        faltam = [rel for rel, h in s.conteudo() if "onda18-praticas" not in h]
        if faltam:
            det.append(u"%d página(s) sem a classe no <ul> das práticas: %s"
                       % (len(faltam), ", ".join(faltam[:3])))
        if ".menu__nav-sublinks.onda18-praticas{display:flex" not in css_o18:
            det.append(u"CSS não põe as práticas em linha")
        if 'content:"|";color:#7F7F7F' not in css_o18:
            det.append(u"CSS sem o separador | cinza")
        return (not det, u"; ".join(det[:4]))
    s.check("S65", u'menu "Práticas" horizontal com "|" cinza (#123)', s65)

    def s66():
        # "Sobre nós" continua vertical (nunca ganha a classe das práticas) e
        # com fonte maior
        det = []
        for rel in HOMES:
            h = s.ler(rel)
            m = re.search(r'<!-- onda7:menu-sobre -->.*?<!-- /onda7:menu-sobre -->', h, re.S)
            if m and "onda18-praticas" in m.group(0):
                det.append(u"%s: submenu de Sobre nós virou horizontal" % rel)
        if ".menu__nav-sublink{font-size:19px !important}" not in css_o18:
            det.append(u"sublinks não estão em 19px")
        return (not det, u"; ".join(det[:4]))
    s.check("S66", u'menu "Sobre nós" vertical e com texto maior (#124)', s66)

    def s67():
        novas = ["pt/sobre-nos/nossos-valores", "sobre-nos/nossos-valores",
                 "en/about-us/our-values", "de/ueber-uns/unsere-werte",
                 "de/unsere-werte"]
        det = []
        for d in novas:
            if not os.path.exists(os.path.join(pub, d.replace("/", os.sep), "index.html")):
                det.append(u"falta %s/" % d)
        # o caminho antigo tem que existir, mas só como redirect
        for antigo in ["pt/sobre-nos/nosso-trabalho", "en/about-us/our-work",
                       "de/ueber-uns/unsere-arbeit"]:
            p = os.path.join(pub, antigo.replace("/", os.sep), "index.html")
            if not os.path.exists(p):
                det.append(u"%s/ sem redirect" % antigo)
            elif "onda18:redirect-s67" not in s.ler(antigo + "/index.html"):
                det.append(u"%s/ não é o stub de redirect" % antigo)
        # e nenhum link interno pode continuar apontando para o caminho velho
        vivos = [rel for rel, h in s.todas()
                 if "onda18:redirect-s67" not in h
                 and re.search(r'/(sobre-nos/nosso-trabalho|about-us/our-work|'
                               r'ueber-uns/unsere-arbeit)/', h)]
        if vivos:
            det.append(u"%d página(s) com link para a URL antiga: %s"
                       % (len(vivos), ", ".join(vivos[:3])))
        return (not det, u"; ".join(det[:5]))
    s.check("S67", u"URL nossos-valores no ar, com redirect da antiga (#125)", s67)

    def s68():
        det = []
        for rel in ["pt/sobre-nos/nossos-valores/index.html",
                    "en/about-us/our-values/index.html",
                    "de/ueber-uns/unsere-werte/index.html"]:
            h = s.ler(rel)
            if '<section class="internal-banner"' in h:
                det.append(u"%s ainda tem o banner de topo" % rel)
            if '<section class="culture"' not in h or '<section class="reasons"' not in h:
                det.append(u"%s perdeu cultura ou 'por que a Mirow'" % rel)
            elif h.index('<section class="culture"') > h.index('<section class="reasons"'):
                det.append(u"%s: cultura depois de 'por que a Mirow'" % rel)
        return (not det, u"; ".join(det[:4]))
    s.check("S68", u"nossos-valores: sem banner, cultura -> por que (#126)", s68)

    def s69():
        det = [rel for rel in ["pt/sobre-nos/nossos-valores/index.html",
                               "en/about-us/our-values/index.html",
                               "de/ueber-uns/unsere-werte/index.html"]
               if '<section class="segments"' in s.ler(rel)]
        return (not det, u"página(s) com o bloco de setores: %s" % ", ".join(det))
    s.check("S69", u'nossos-valores sem "soluções para vários setores" (#127)', s69)

    def s70():
        # v4 (#128 / S-77): o Mario encerrou a metafora visual — "remova isso e
        # coloque ... 5 cards com cada grupo de industrias listado, sem planeta nem
        # nada disso. faca no tema do resto da pagina."
        # v5 (onda 42, #194): recategorizados em 6 cards / 24 setores (industria
        # pesada, energia, base florestal etc.) — os nomes exatos sao da S132.
        det = []
        for rel in HOMES:
            h = s.ler(rel)
            cards = h.count('class="onda18-const"')
            itens = h.count('class="onda18-const__item"')
            if cards != 6:
                det.append(u"%s com %d card(s) de grupo (esperado 6)" % (rel, cards))
            if itens != 24:
                det.append(u"%s com %d setor(es) (esperado 24)" % (rel, itens))
            # nada de planeta/esfera/ceu: as 3 versoes anteriores estao aposentadas
            for morto in ("onda18-orbe__mapa", "o18hub", "onda18-orbe__ceu",
                          "onda18-orbe__planeta", "onda18-const__lista::before"):
                if morto in h:
                    det.append(u"%s ainda tem resto de versao antiga (%s)" % (rel, morto))
        # S-84: sem a contagem "5 setores", sem o subtexto, titulo branco tipo
        # "Lideres", e os setores na ordem de frequencia do acervo (mirow-rag)
        for rel in HOMES:
            hh = s.ler(rel)
            if "onda18-const__conta" in hh:
                det.append(u'%s ainda mostra a contagem "N setores"' % rel)
            if "onda18-orbe__sub" in hh:
                det.append(u"%s ainda tem o subtexto das 19 indústrias" % rel)
        # A checagem de "ordem por frequência" (calculada pelo script 71) foi
        # APOSENTADA na onda 42 (#194): a taxonomia passou a ser CURADA — o
        # Mario definiu as categorias (indústria pesada, energia, base
        # florestal...) e a S132 crava nomes e ordem byte a byte.
        if ".onda18-orbe__titulo{color:#e9f0ff" not in css_o18:
            det.append(u'título não está no branco do estilo "Líderes"')
        if ".onda18-orbe__cards{display:grid" not in css_o18:
            det.append(u"CSS sem a grade dos 5 cards")
        for morto in ("@keyframes onda18-orbita", "@keyframes onda18-flutua",
                      "@keyframes onda18-pulso"):
            if morto in css_o18:
                det.append(u"%s voltou (versao aposentada)" % morto)
        return (not det, u"; ".join(det[:4]))
    s.check("S70", u"home: 5 cards de grupos de setores, sem planeta (#128/S-77)", s70)

    def s71():
        det = []
        if ".home-leaders .container .row__content .col{padding-bottom:40px !important}" \
                not in css_o18:
            det.append(u"grade de líderes sem a redução de padding")
        if ".certificates{padding-top:48px !important}" not in css_o18:
            det.append(u"seção de reconhecimentos sem a redução de padding")
        return (not det, u"; ".join(det))
    s.check("S71", u"home: menos vão entre líderes e reconhecimentos (#129)", s71)

    def s72():
        det = []
        for rel, hh in s.conteudo():
            for m in re.finditer(r'<a[ ][^>]*href="mailto:[^"]*"[^>]*>', hh):
                tag = m.group(0)
                if not ("menu__contatos-link--mail" in tag
                        or "hero-contatos__link--mail" in tag):
                    continue  # e-mail pessoal de líder: não entra no pedido
                if "subject=" not in tag or "body=" not in tag:
                    det.append(rel)
                    break
        return (not det, u"%d página(s) com e-mail de canal sem assunto/texto: %s"
                % (len(det), ", ".join(det[:3])))
    s.check("S72", u"e-mail dos canais abre com assunto e texto-padrão (#130)", s72)

    def s73():
        # os tamanhos têm que ser os MESMOS tokens do hero do tema:
        # .banner h2 = 62px (slogan) e .banner p = 18px (parágrafo)
        det = []
        if ".hero-numeros__valor{font-size:62px !important;line-height:1}" not in css_o18:
            det.append(u"big number não está em 62px (tamanho do slogan)")
        if ".hero-numeros__texto{font-size:18px !important;line-height:1.35;margin-top:6px}"                 not in css_o18:
            det.append(u"texto do número não está em 18px (tamanho do parágrafo)")
        tema = s.ler("wp-content/themes/mirow/public/bundle-css.css")
        if "font-size:62px;font-size:3.875rem" not in tema:
            det.append(u"o slogan do tema deixou de ser 62px — reveja o pedido")
        return (not det, u"; ".join(det))
    s.check("S73", u"hero: números no tamanho do slogan, texto no do parágrafo (#131)", s73)

    # ------------------------------------------------------------------ onda 19
    css_o19 = css_o18   # mesmo arquivo, blocos onda19:*

    def s74():
        # a lista de idiomas do rodape abre para cima (S-52) e nao pode ficar
        # atras da secao anterior — foi por isso que o Mario nao via as linguas
        det = []
        for regra in (".footer{position:relative;z-index:20}",
                      ".rodape-barra .menu__languages{z-index:30}",
                      ".rodape-barra .menu__languages-list{z-index:40}"):
            if regra not in css_o19:
                det.append(u"falta a regra %s" % regra)
        return (not det, u"; ".join(det))
    s.check("S74", u"as 3 línguas do rodapé aparecem inteiras (#132)", s74)

    def s75():
        sobrou = [rel for rel, h in s.todas() if '<section class="links">' in h]
        return (not sobrou, u'%d página(s) ainda com o bloco "Como podemos ajudar?": %s'
                % (len(sobrou), ", ".join(sobrou[:3])))
    s.check("S75", u'0 blocos "Como podemos ajudar? / Transforme sua carreira" (#133)', s75)

    def s76():
        det = []
        sem = [rel for rel, h in s.conteudo() if 'class="onda19-lateral"' not in h]
        if sem:
            det.append(u"%d página(s) sem a coluna lateral: %s"
                       % (len(sem), ", ".join(sem[:3])))
        # os 3 atalhos, com o e-mail levando assunto/corpo (S-72)
        ruins = []
        for rel, h in s.conteudo():
            if ("onda19-lateral__link--wa" not in h
                    or "onda19-lateral__link--mail" not in h
                    or "onda19-lateral__link--topo" not in h):
                ruins.append(rel)
                continue
            m = re.search(r'onda19-lateral__link--mail" href="mailto:([^"]+)"', h)
            if not m or "subject=" not in m.group(1) or "body=" not in m.group(1):
                ruins.append(rel)
        if ruins:
            det.append(u"%d página(s) sem os 3 atalhos (ou e-mail sem assunto): %s"
                       % (len(ruins), ", ".join(ruins[:3])))
        return (not det, u"; ".join(det))
    s.check("S76", u"coluna lateral com WhatsApp, e-mail e voltar ao topo (#134)", s76)

    def s67b():
        # ajuste do #125: o ROTULO tambem mudou, nao so a URL
        det = []
        for rel, h in s.conteudo():
            for antigo in (u">Nosso Trabalho<", u">Our Work<", u">Unsere Arbeit<"):
                if antigo in h:
                    det.append(u"%s com %s" % (rel, antigo))
                    break
        alvos = {"pt/index.html": u">Nossos Valores<", "en/index.html": u">Our Values<",
                 "de/index.html": u">Unsere Werte<"}
        for rel, txt in alvos.items():
            if txt not in s.ler(rel):
                det.append(u"%s sem o rótulo novo" % rel)
        return (not det, u"%d problema(s): %s" % (len(det), "; ".join(det[:3])))
    s.check("S67b", u'menu diz "Nossos Valores" em toda parte (#125)', s67b)

    def s57b():
        # ajuste do #115: o icone segue o VEICULO, nao o dominio do link — os 2
        # itens com veiculo e link divergentes saiam com o logo de outro jornal
        det = []
        for rel in IMPRENSA:
            h = s.ler(rel)
            # Onda 41 (#190): os favicons viraram wordmarks em imprensa-logos/;
            # o invariante segue o mesmo — o logo pertence ao VEÍCULO da linha.
            for veic, dom in ((u"Estadão", "imprensa-logos/estadao.svg"),
                              (u"Folha de S.Paulo", "imprensa-logos/folha.svg"),
                              (u"Valor Econômico", "imprensa-logos/valor.svg")):
                itens = re.findall(
                    r'<img class="onda41-imprensa__logo" src="([^"]+)"[^>]*>'
                    r'<span class="onda18-imprensa__veiculo">' + re.escape(veic) + '</span>', h)
                if not itens:
                    det.append(u"%s: nenhum item de %s" % (rel, veic))
                ruins = [i for i in itens if dom not in i]
                if ruins:
                    det.append(u"%s: %d item(ns) de %s com logo de outro veículo"
                               % (rel, len(ruins), veic))
        return (not det, u"; ".join(det[:4]))
    s.check("S57b", u"imprensa: logo segue o veículo, não o link (#115)", s57b)

    # ------------------------------------------------------------------ onda 21
    def s78():
        alvos = {"pt/index.html": u"dos nossos clientes<br>nos contratam novamente",
                 "de/index.html": u"unserer Kunden<br>beauftragen uns erneut"}
        det = [rel for rel, txt in alvos.items() if txt not in s.ler(rel)]
        # EN nao entra: a frase la e "of client re-engagement rate", sem o mesmo
        # ponto de quebra (registrado na #136)
        return (not det, u"página(s) sem a quebra: %s" % ", ".join(det))
    s.check("S78", u'hero: "nos contratam novamente" em linha própria (#136)', s78)

    def s79():
        ok = (".rodape-barra{width:100vw" in css_o18
              and "margin-left:calc(50% - 50vw) !important" in css_o18)
        return (ok, u"a barra do rodapé não sangra 100vw como a de cima")
    s.check("S79", u"barra do rodapé com branco até os cantos (#137)", s79)

    def s80():
        det = []
        if ".menu__nav-sublinks.onda18-praticas{display:grid !important" not in css_o18:
            det.append(u"práticas não estão em grade")
        # a S-88 trocou o MECANISMO: colunas iguais nao cabiam "Sourcing, Compras e
        # Estoques" em 1 linha, entao virou coluna do tamanho do conteudo espalhada
        # (mesmo pedido — ocupar a largura da caixa — outra tecnica)
        if "grid-template-columns:repeat(3,max-content);justify-content:space-between"                 not in css_o18:
            det.append(u"as práticas não ocupam a largura da caixa")
        if ".menu__nav-submenu .row>.col{flex:0 0 100%" not in css_o18:
            det.append(u"a coluna do painel não ocupa a largura (grade ficava em 1/3)")
        return (not det, u"; ".join(det))
    s.check("S80", u"práticas distribuídas na largura da caixa (#138)", s80)

    def s81():
        # slug e rotulo mudam por idioma; a ordem pedida e a mesma nos tres
        POR_IDIOMA = {
            "pt": (["nossos-valores", "lideres", "nossa-historia", "reconhecimentos",
                    "nossa-rede"], [u">Nossos Líderes<", u">Nossa História<"]),
            "en": (["our-values", "leaders", "our-history", "recognitions",
                    "our-network"], [u">Our Leaders<"]),
            "de": (["unsere-werte", "fuehrungskraefte", "unsere-geschichte",
                    "anerkennungen", "unser-netzwerk"], [u">Unsere Führungskräfte<"]),
        }
        det = []
        for rel in HOMES:   # onda 57: as de contato viraram stub (#228)
            hh = s.ler(rel)
            idioma = "de" if "/de/" in ("/" + rel) else ("en" if "/en/" in ("/" + rel)
                                                        else "pt")
            if rel.startswith("en/"):
                idioma = "en"
            elif rel.startswith("de/"):
                idioma = "de"
            ordem, rotulos = POR_IDIOMA[idioma]
            m = re.search(r'<!-- onda7:menu-sobre -->(.*?)<!-- /onda7:menu-sobre -->',
                          hh, re.S)
            if not m:
                det.append(u"%s sem o marcador do submenu" % rel)
                continue
            achados = re.findall(r'/(?:sobre-nos|about-us|ueber-uns)/([a-z-]+)/',
                                 m.group(1))
            vistos = [a for a in achados if a in ordem]
            if vistos != ordem:
                det.append(u"%s (%s) com ordem %s" % (rel, idioma, vistos))
            for rot in rotulos:
                if rot not in m.group(1):
                    det.append(u"%s sem o rótulo %s" % (rel, rot.strip("><")))
        return (not det, u"; ".join(det[:3]))
    s.check("S81", u'submenu "Sobre nós" na ordem e rótulos pedidos (#139)', s81)

    def s82():
        # ATUALIZADA na onda 31 (S-111..S-116): os mapas deixaram de ser desenho a
        # mao e a pagina passou a ser GERADA do arquivo mestre (tools/gen_rede.py).
        # O que a S-82 protegia continua protegido: 2 mapas, 6 parceiros, logo no
        # proprio pin, sem escritorio da Mirow e sem a Virtus.
        det = []
        for rel in REDE:
            h = s.ler(rel)
            mapas = h.count('class="onda31-mapa"')
            pins = h.count('class="onda31-pin"')
            logos_no_pin = len(re.findall(
                r'class="onda31-pin__chip"[^>]*>\s*<img ', h))
            if mapas != 2:
                det.append(u"%s com %d mapa(s) (esperado 2)" % (rel, mapas))
            if pins != 6:
                det.append(u"%s com %d pin(s) de parceiro (esperado 6)" % (rel, pins))
            if logos_no_pin != 6:
                det.append(u"%s com %d logo(s) dentro do pin (esperado 6)"
                           % (rel, logos_no_pin))
            if "onda21-pin--mirow" in h:
                det.append(u"%s ainda marca escritórios da Mirow no mapa" % rel)
            if u"Virtus" in h:
                det.append(u"%s cita a Virtus (comprada pela Deloitte, não é parceira)" % rel)
            if 'class="rede-mapa__svg"' in h:
                det.append(u"%s ainda tem o mapa-múndi único da onda 9" % rel)
        return (not det, u"; ".join(det[:4]))
    s.check("S82", u"rede: 2 mapas, 6 parceiros com logo no pin (#140)", s82)
    def s83():
        # o painel do menu no modelo Bain: branco no >div INTERNO (o tema pinta
        # navy justamente ali), filete ciano e sombra
        det = []
        if ".menu__nav-submenu>div{background:#fff !important" not in css_o18:
            det.append(u"o painel branco não está no >div interno")
        if "border-bottom:3px solid #00ADEC" not in css_o18:
            det.append(u"falta o filete ciano do painel")
        if ".menu__nav-sublink{color:#020E66 !important;font-weight:400}" not in css_o18:
            det.append(u"os itens do painel não estão em navy sobre o branco")
        return (not det, u"; ".join(det))
    s.check("S83", u"painel do menu branco e destacado do fundo (#141)", s83)

    # ------------------------------------------------------------------ onda 23
    def s85():
        det = []
        for rel in HOMES:
            hh = s.ler(rel)
            # o framework: uma marca por secao, 1 a 4, descendo a home
            for n in range(1, 5):
                c = hh.count("onda22-marca--%d" % n)
                if c != 1:
                    det.append(u"%s com %d marca(s) --%d (esperado 1)" % (rel, c, n))
            # a ordem das marcas na pagina tem que ser 1,2,3,4
            achadas = [int(x) for x in re.findall(r'onda22-marca onda22-marca--(\d)', hh)]
            if achadas != [1, 2, 3, 4]:
                det.append(u"%s com as marcas fora de ordem: %s" % (rel, achadas))
            # os dois textos que saem
            for classe, nome in (("home-experience__title", u'"Práticas"'),
                                 ("home-leaders__title", u'super título "Líderes"')):
                m = re.search(r'<h[1-6][^>]*class="%s"[^>]*>(.*?)</h[1-6]>' % classe,
                              hh, re.S)
                if m and m.group(1).strip():
                    det.append(u"%s ainda tem o %s" % (rel, nome))
        # ATUALIZADA na onda 30 (S-110): a tipografia dos 4 títulos saiu da regra
        # de 4 seletores e virou UMA classe compartilhada — ver S110.
        m = re.search(r'\.onda30-titulo-secao\{([^}]*)\}', css_o18)
        if not m:
            det.append(u"a classe única dos títulos (.onda30-titulo-secao) não existe")
        else:
            for prop in ("font-weight:700 !important",
                         "text-transform:none !important", "text-align:left !important"):
                if prop not in m.group(1):
                    det.append(u"a classe dos títulos sem %s" % prop)
            # ONDA 66: aqui se cobrava a string literal `font-size:48px !important`.
            # A migração fluida trocou o 48px fixo por
            # `clamp(28px, 17.6px + 2.17vw, 48px)` — mesma tipografia nas larguras
            # aprovadas, sem o salto de 41% em 992px — e a asserção quebrou o gate
            # por MOTIVO CERTO, ALVO ERRADO: ela media a declaração, não o efeito.
            # Quarta vez nesta classe em dois dias (S125 na onda 33b, S119 na 62c,
            # S146 na 65). O invariante que interessa é "os 4 títulos são parelhos",
            # e quem o mede de verdade é a V17, no render. Aqui fica o que é estático:
            # a classe declara UM tamanho, seja ele qual for — se alguém voltar a
            # espalhar tamanho por seletor, isto acusa.
            tam = re.findall(r"font-size:\s*([^;}]+)", m.group(1))
            if len(tam) != 1:
                det.append(u"a classe dos títulos declara %d font-size (esperado 1): %s"
                           % (len(tam), tam))
            elif "!important" not in tam[0]:
                det.append(u"o font-size da classe dos títulos perdeu o !important")
        # v2 do marcador (S-86): grade 2x2, navy fixo, a esquerda do titulo
        if ".onda22-marca{float:left;display:grid" not in css_o18:
            det.append(u"marca não é grade 2x2 flutuando à esquerda do título")
        if "width:7px;height:7px;background:#020E66;opacity:.42" not in css_o18:
            det.append(u"os 3 blocos pequenos não estão navy/discretos")
        if ".onda22-marca--4 i:nth-child(4){width:12px;height:12px;opacity:1}" not in css_o18:
            det.append(u"o quadrante da seção não fica maior/opaco")
        if "currentColor" in css_o18.split("onda22:marca-secoes:ini")[-1].split(
                "onda22:marca-secoes:fim")[0]:
            det.append(u"a marca voltou a usar currentColor (o pedido é navy sempre)")
        # cada marca tem os 4 quadrantes no HTML
        for rel in HOMES:
            hh = s.ler(rel)
            for n in range(1, 5):
                esperado = ('<span class="onda22-marca onda22-marca--%d" '
                            'aria-hidden="true"><i></i><i></i><i></i><i></i></span>' % n)
                if esperado not in hh:
                    det.append(u"%s: marca --%d sem os 4 quadrantes" % (rel, n))
        return (not det, u"; ".join(det[:4]))
    s.check("S85", u"marca de seção 1-4 como framework da home; títulos parelhos", s85)

    # ------------------------------------------------------------------ onda 24
    def s87():
        # ATUALIZADA na onda 25 (S-91): na onda 24 a solucao era deixar o titulo
        # claro no dark-mode; o Mario pediu o inverso — os 4 titulos em navy e o
        # darken fora de cena. O pedido protegido e o mesmo: o titulo nao apaga.
        det = []
        if ".home-experience--dark-mode::after{opacity:1 !important}" not in css_o18:
            det.append(u"o darken ao rolar voltou (o véu claro do tema é removido)")
        # ATUALIZADA na onda 30 (S-110): o navy é propriedade da classe única
        m = re.search(r'\.onda30-titulo-secao\{[^}]*color:#020E66 !important', css_o18)
        if not m:
            det.append(u"o navy saiu da classe única dos títulos")
        if "color:#e9f0ff !important" in css_o18:
            det.append(u"sobrou título claro (o pedido é navy nos quatro)")
        return (not det, u"; ".join(det))
    s.check("S87", u"4 títulos da home em navy, sem darken ao rolar (#145/#149)", s87)

    def s88():
        det = []
        if "grid-template-columns:repeat(3,max-content);justify-content:space-between"                 not in css_o18:
            det.append(u"práticas sem colunas de conteúdo espalhadas")
        if ".menu__nav-sublinks.onda18-praticas .menu__nav-sublink{white-space:nowrap}"                 not in css_o18:
            det.append(u"práticas sem nowrap (podem voltar a quebrar em 2 linhas)")
        return (not det, u"; ".join(det))
    s.check("S88", u'"Sourcing, Compras e Estoques" em uma linha só (#146)', s88)

    def s89():
        det = []
        if "grid-template-columns:repeat(5,max-content);justify-content:space-between"                 not in css_o18:
            det.append(u"Sobre nós não está espalhado na largura")
        # as DUAS camadas de largura do painel (medidas via CDP)
        if ".menu__nav-submenu .container>.row{flex:1 1 100%;width:100%}" not in css_o18:
            det.append(u"falta a largura do .row (ele encolhia no conteúdo)")
        if ".menu__nav-submenu .row>.col{flex:0 0 100%" not in css_o18:
            det.append(u"falta a largura do .col")
        return (not det, u"; ".join(det))
    s.check("S89", u'submenu "Sobre nós" esticado até a direita (#147)', s89)

    def s90():
        det = []
        if ".menu__languages-list{background:#020E66 !important" not in css_o18:
            det.append(u"balão de idiomas não está no navy Mirow")
        for regra in (".menu__languages-list::after{border-bottom-color:#020E66 !important}",
                      ".rodape-barra .menu__languages-list::after"
                      "{border-top-color:#020E66 !important}"):
            if regra not in css_o18:
                det.append(u"a setinha do balão não acompanha o navy")
        return (not det, u"; ".join(det[:2]))
    s.check("S90", u"balão de idiomas no azul Mirow, não preto (#148)", s90)

    # ------------------------------------------------------------------ onda 25
    def s94():
        # mesmo peso nos dois submenus (Praticas estava 700, Sobre nos 400)
        ok = (".menu__nav-sublink{font-weight:600 !important}" in css_o18
              and ".menu__nav-sublinks.onda18-praticas .menu__nav-sublink"
                  "{font-weight:600 !important}" in css_o18)
        return (ok, u"os dois submenus não estão no mesmo peso de fonte")
    s.check("S94", u"peso do texto igual nos dois submenus (#152)", s94)

    def s95():
        det = []
        for d in ("pt/insights", "insights"):
            if not os.path.exists(os.path.join(pub, d.replace("/", os.sep), "index.html")):
                det.append(u"falta %s/" % d)
        for antigo_dir in ("pt/analises", "analises"):
            p2 = os.path.join(pub, antigo_dir.replace("/", os.sep), "index.html")
            if not os.path.exists(p2):
                det.append(u"%s/ sem redirect" % antigo_dir)
            elif "onda25:redirect-s95" not in s.ler(antigo_dir + "/index.html"):
                det.append(u"%s/ não é o stub de redirect" % antigo_dir)
        vivos = [rel for rel, hh in s.todas()
                 if "onda25:redirect-s95" not in hh and re.search(r'/analises/', hh)]
        if vivos:
            det.append(u"%d página(s) com link para /analises/: %s"
                       % (len(vivos), ", ".join(vivos[:3])))
        return (not det, u"; ".join(det[:4]))
    s.check("S95", u"insights em /insights/, com redirect de /analises/ (#153)", s95)

    def s96():
        # a agencia de imprensa nao atende mais a Mirow: nenhuma pagina pode citar
        det = [rel for rel, hh in s.todas() if "agenciaecomunica" in hh]
        # e o marcador da onda 12, que fechava DENTRO daquele <h5>, tem de sobrar
        # o marcador da onda 12 nasceu no <h1> da página PT; as páginas EN/DE
        # (S-106) têm o título próprio, sem esse marcador
        for rel in ("pt/imprensa/index.html",):
            if "onda12:imprensa-formatacao" not in s.ler(rel):
                det.append(u"%s perdeu o marcador da onda 12" % rel)
        return (not det, u"%d problema(s): %s" % (len(det), ", ".join(det[:3])))
    s.check("S96", u"0 menção à agência de imprensa antiga (#154)", s96)

    # ------------------------------------------------------------------ onda 26
    def s97():
        # o link nasceu branco (onda 7, seção escura); depois da S-91 o fundo é
        # claro e ele tem de ser navy
        det = []
        if ".onda7-vertodos{color:#020E66 !important}" not in css_o18:
            det.append(u'"Ver todos os líderes" não está em navy')
        if ".onda7-vertodos:hover,.onda7-vertodos:focus-visible{color:#00ADEC" not in css_o18:
            det.append(u"o hover do link não é ciano")
        for rel in HOMES:
            if "onda7-vertodos" not in s.ler(rel):
                det.append(u"%s sem o link Ver todos os líderes" % rel)
        return (not det, u"; ".join(det[:3]))
    s.check("S97", u'home: "Ver todos os líderes" em azul (#155)', s97)

    def s98():
        # UMA fonte no site inteiro. O tema pede 3 famílias por variável e nenhuma
        # é carregada — só o Titillium Web está no <head>. As variáveis apontam
        # para ela; a checagem do render em si é a V08 (fontes computadas).
        det = []
        for var in ("--fontFamily", "--secondaryFontFamily", "--tertiaryFontFamily",
                    "--bs-font-sans-serif", "--bs-body-font-family"):
            if '%s:"Titillium Web",sans-serif;' % var not in css_o18:
                det.append(u"%s não aponta para Titillium Web" % var)
        # e nenhuma página pode carregar webfont novo (Titillium é o único)
        familias = set()
        for rel, hh in s.todas():
            familias.update(re.findall(r'fonts\.googleapis\.com/css2\?family=([^:"\'&]+)',
                                       hh))
        if familias - {"Titillium+Web"}:
            det.append(u"webfont(s) além do Titillium: %s"
                       % ", ".join(sorted(familias - {"Titillium+Web"})))
        return (not det, u"; ".join(det[:3]))
    s.check("S98", u"uma fonte só declarada em todo o site (#156)", s98)

    def s99():
        # Práticas no mesmo tamanho de Sobre nós (19px), em toda a largura.
        # Revoga o tamanho maior da S-65/S-88 — decisão do Mario em 04/08.
        bloco = css_o18.split("onda26:ajustes-s97-s100:ini")[-1].split(
            "onda26:ajustes-s97-s100:fim")[0]
        det = []
        if "font-size:19px !important" not in bloco:
            det.append(u"o submenu de Práticas não foi igualado a 19px")
        if re.search(r'onda18-praticas .menu__nav-sublink\{font-size:(?!19px)', bloco):
            det.append(u"sobrou tamanho diferente de 19px no bloco da onda 26")
        return (not det, u"; ".join(det[:2]))
    s.check("S99", u"submenu Práticas no tamanho de Sobre nós (#157)", s99)

    def s100():
        ok = ".rodape-barra{border-bottom:0 !important}" in css_o18
        return (ok, u"a barra do rodapé ainda tem filete separando a política")
    s.check("S100", u"rodapé sem linha antes da política de privacidade (#158)", s100)

    def s101():
        # e-mail no card de Andreas e Felipe; Stephan e Elmar ficam sem
        det = []
        esperado = {u"Andreas Mirow": "andreas.mirow@mirow.com.br",
                    u"Felipe Diniz": "felipe.diniz@mirow.com.br"}
        for rel in HOMES:
            hh = s.ler(rel)
            for bloco in re.findall(r'<div class="onda18-lider.*?</div>', hh, re.S):
                # `<h4[^>]*>` e nao `<h4>`: a onda 60 escreveu <h4 aria-level="3"> nos
                # cards, e a versao literal deixava o nome como "?" — o que fazia esta
                # assercao acusar "nao devia ter e-mail" para um card que estava certo.
                # Terceira vez que a mesma classe apareceu na sessao de 18/08 (as outras
                # foram o reconhecedor do 06_quadro_lideres.py e a S128): regex de
                # markup PROPRIO tolera atributo novo na tag.
                mn = re.search(r'<h4[^>]*>([^<]*)</h4>', bloco)
                nome = mn.group(1).strip() if mn else "?"
                tem = "onda26-lider__mail" in bloco
                if nome in esperado:
                    if not tem:
                        det.append(u"%s: %s sem e-mail" % (rel, nome))
                    elif ("mailto:%s?subject=" % esperado[nome]) not in bloco:
                        det.append(u"%s: e-mail de %s errado ou sem assunto"
                                   % (rel, nome))
                elif tem:
                    det.append(u"%s: %s não devia ter e-mail" % (rel, nome))
        if ".onda26-lider__mail{position:absolute" not in css_o18:
            det.append(u"o link de e-mail não está posicionado sobre o card")
        return (not det, u"; ".join(det[:3]))
    s.check("S101", u"e-mail de Andreas e Felipe nos cards da home (#159)", s101)

    def s102():
        det = []
        for rel in IMPRENSA:
            hh = s.ler(rel)
            itens = re.findall(r'<li class="onda18-imprensa__item">(.*?)</li>', hh, re.S)
            if not itens:
                det.append(u"%s sem itens de imprensa" % rel)
                continue
            for i, it in enumerate(itens):
                if not it.startswith('<a class="onda26-imprensa__link" href="http'):
                    det.append(u"%s item %d não é uma linha-link" % (rel, i + 1))
                    break
                # um link por linha: o título deixou de ser <a>
                if it.count("<a ") != 1:
                    det.append(u"%s item %d com %d links (esperado 1)"
                               % (rel, i + 1, it.count("<a ")))
                    break
        if ".onda26-imprensa__link{display:grid" not in css_o18:
            det.append(u"a grade não migrou para o link da linha")
        return (not det, u"; ".join(det[:3]))
    s.check("S102", u"imprensa: a linha inteira é link (#160)", s102)

    def s103():
        det = []
        praticas = [(rel, hh) for rel, hh in s.todas()
                    if 'class="experience-single__banner-owner-list"' in hh]
        # 88 -> 21: depois da S-107 (#165) cada prática tem UMA URL
        if len(praticas) < 20:
            det.append(u"só %d páginas de prática encontradas (esperado 21)"
                       % len(praticas))
        for rel, hh in praticas:
            donos = re.findall(r'experience-single__banner-owner" data-bs-toggle='
                               r'"modal"\s*data-bs-target="[^"]*"><img[^>]*>'
                               r'<p><strong>([^<]*)</strong>', hh)
            if any(u"Elmar" in d for d in donos):
                det.append(u"%s ainda mostra Elmar" % rel)
            elif not ({u"Andreas Mirow", u"Felipe Diniz"} & set(donos)):
                det.append(u"%s sem Andreas nem Felipe: %s" % (rel, donos))
        return (not det, u"%d problema(s): %s" % (len(det), "; ".join(det[:3])))
    s.check("S103", u"práticas sem Elmar, com Andreas e Felipe (#161)", s103)

    # ------------------------------------------------------------------ onda 27
    # Onda 57 (#228): o item de Contato saiu do menu junto com a página. Eram 6
    # itens desde a S-106; agora são 5. O contato passou a viver só nas pílulas do
    # hero e nos ícones do header, que a V23 e a V14 já medem.
    ORDEM_MENU = {
        "pt": [u"Sobre nós", u"Práticas", u"Insights", u"Imprensa", u"Carreiras"],
        "en": [u"About us", u"Practices", u"Insights", u"Press", u"Careers"],
        "de": [u"Über uns", u"Branchen", u"Insights", u"Presse", u"Karrieren"],
    }

    def s104():
        # a ordem pedida pelo Mario, página a página, nas DUAS barras (a do rodapé
        # é clone byte a byte — a S36 garante a igualdade, aqui se cobra a ordem)
        det = []
        for rel, hh in s.conteudo():
            # a barra do header é o PRIMEIRO <nav class="menu"> da página (o
            # segundo é o clone do rodapé — ver S36)
            i = hh.find('<nav class="menu"')
            j = hh.find("</nav>", i)
            if i < 0 or j < 0:
                det.append(u"%s sem header" % rel)
                continue
            itens = [x.strip() for x in re.findall(
                r'class="menu__nav-link[^"]*" href="[^"]*"[^>]*>([^<]+)<', hh[i:j])]
            lang = re.search(r'pll_language=([a-z]{2})', hh)
            lang = lang.group(1) if lang else "pt"
            esperado = ORDEM_MENU.get(lang)
            if esperado and itens != esperado:
                det.append(u"%s: %s" % (rel, " > ".join(itens)))
        return (not det, u"%d página(s) fora da ordem: %s"
                % (len(det), "; ".join(det[:2])))
    s.check("S104", u"menu na ordem Insights > Imprensa > Carreiras (#162)", s104)

    def s105():
        # o repouso da barra não pode voltar a depender do que está atrás dela
        det = []
        for regra in (".header .menu{background:#020E66 !important",
                      ".rodape-barra .menu{background:#020E66 !important}"):
            if regra not in css_o18:
                det.append(u"falta a regra de fundo sólido: %s" % regra[:40])
        # o hover branco (painel do menu, S-83) tem de continuar vencendo
        if ".header .menu:hover" not in css_o18:
            det.append(u"o hover branco da barra foi perdido")
        return (not det, u"; ".join(det[:2]))
    s.check("S105", u"barra com fundo sólido igual em toda página (#163)", s105)

    # ------------------------------------------------------------------ onda 29
    def s106():
        # #164: Imprensa passa a existir em EN e DE, e o menu tem 6 itens nas três
        det = []
        for rel in IMPRENSA:
            p = os.path.join(pub, rel.replace("/", os.sep))
            if not os.path.exists(p):
                det.append(u"falta %s" % rel)
                continue
            hh = s.ler(rel)
            n = len(re.findall(r'class="onda18-imprensa__item"', hh))
            if n < 20:
                det.append(u"%s com só %d itens de imprensa" % (rel, n))
            can = re.search(r'rel="canonical" href="([^"]+)"', hh)
            propria = HOST + "/" + rel[:-len("index.html")]
            if not can or can.group(1).rstrip("/") + "/" != propria:
                det.append(u"%s com canonical errado: %s"
                           % (rel, can.group(1) if can else "-"))
        # o seletor de idiomas das três aponta uma para a outra (era home antes)
        urls = ["/pt/imprensa/", "/en/press/", "/de/presse/"]
        for rel in IMPRENSA:
            hh = s.ler(rel)
            m = re.search(r'<ul class="menu__languages-list">(.*?)</ul>', hh, re.S)
            achou = re.findall(r'<a href="([^"]+)"', m.group(1)) if m else []
            if achou[:3] != urls:
                det.append(u"%s: seletor de idiomas não liga as três (%s)"
                           % (rel, achou[:3]))
        return (not det, u"; ".join(det[:3]))
    s.check("S106", u"imprensa existe em pt/en/de, ligadas entre si (#164)", s106)

    def s107():
        # #165: UMA URL por página. Toda página de conteúdo se autocanonicaliza, e
        # nenhum link interno leva a uma URL que virou stub (clique sem 2 saltos).
        det = []
        stubs = set()
        conteudo = []
        for rel, hh in s.todas():
            if not rel.endswith("index.html"):
                continue
            if "menu__nav-item" not in hh:            # é stub de redirect
                if rel != "index.html":
                    stubs.add("/" + rel[:-len("index.html")])
                continue
            conteudo.append((rel, hh))
            if rel == "en/homepage/index.html":
                continue          # home duplicada declarada (S-16)
            can = re.search(r'rel="canonical" href="([^"]+)"', hh)
            propria = HOST + "/" + rel[:-len("index.html")]
            if not can or can.group(1).rstrip("/") + "/" != propria:
                det.append(u"%s não é a própria canônica (%s)"
                           % (rel, can.group(1) if can else "-"))
        if len(stubs) < 140:
            det.append(u"só %d stubs de redirect (esperado >= 140)" % len(stubs))
        for rel, hh in conteudo:
            for url in re.findall(r'href="(/[^"#?]*/)"', hh):
                if url in stubs:
                    det.append(u"%s ainda linka para o stub %s" % (rel, url))
                    break
        return (not det, u"%d problema(s) em %d páginas de conteúdo: %s"
                % (len(det), len(conteudo), "; ".join(det[:3])))
    s.check("S107", u"uma URL por página; nenhum link para redirect (#165)", s107)

    def s108():
        # #166: nenhuma página de conteúdo abre "nua", e nenhuma fica vazia
        det = []
        for rel, hh in s.conteudo():
            if "menu__nav-item" not in hh:
                continue
            m = re.search(r'<main class="[^"]*">(.*?)</main>', hh, re.S)
            corpo = m.group(1) if m else ""
            texto = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", corpo)).strip()
            if len(texto) < 40:
                det.append(u"%s tem <main> vazio" % rel)
                continue
            tem_abertura = (re.search(r'class="(banner|internal-banner|'
                                      r'experience-single__banner|blog-single__banner)',
                                      hh)
                            or "onda29-abertura" in hh
                            or 'class="culture' in hh)
            if not tem_abertura:
                det.append(u"%s abre sem banner nem faixa" % rel)
        if ".onda29-abertura{background:#020E66" not in css_o18:
            det.append(u"a faixa de abertura não está no CSS")
        return (not det, u"%d página(s): %s" % (len(det), "; ".join(det[:3])))
    s.check("S108", u"toda página abre com banner ou faixa; 0 página vazia (#166)",
            s108)

    # ------------------------------------------------------------------ onda 30
    def s110():
        # #168: os 4 títulos de seção da home são a MESMA coisa — uma classe, a
        # mesma animação e o mesmo nível de heading. O render é medido na V17.
        det = []
        historicas = ["home-experience__subtitle", "onda18-orbe__titulo",
                      "home-leaders__subtitle", "certificates__title"]
        for rel in HOMES:
            hh = s.ler(rel)
            for classe in historicas:
                m = re.search(r'<(h[1-6])([^>]*class="[^"]*' + re.escape(classe)
                              + r'[^"]*"[^>]*)>', hh)
                if not m:
                    det.append(u"%s: não achei o título %s" % (rel, classe))
                    continue
                tag, attrs = m.group(1), m.group(2)
                if "onda30-titulo-secao" not in attrs:
                    det.append(u"%s: %s sem a classe compartilhada" % (rel, classe))
                if 'data-aos="fade-up"' not in attrs:
                    det.append(u"%s: %s sem a animação fade-up" % (rel, classe))
                if tag != "h2":
                    det.append(u"%s: %s é <%s>, esperado <h2>" % (rel, classe, tag))
        # e a tipografia não pode voltar a ser escrita por seletor de seção
        bloco22 = css_o18.split("onda22:marca-secoes:ini")[-1].split(
            "onda22:marca-secoes:fim")[0]
        if "font-size:48px" in bloco22:
            det.append(u"a tipografia dos títulos voltou para o bloco da onda 22")
        return (not det, u"%d problema(s): %s" % (len(det), "; ".join(det[:3])))
    s.check("S110", u"4 títulos da home numa classe só, com a mesma animação (#168)",
            s110)

    # ------------------------------------------------------------------ onda 31
    def s111():
        # #169: logo de verdade no pin, não mais o favicon de 128px que a S-82 pegou
        det = []
        dir_logos = os.path.join(pub, "wp-content", "uploads", "2026", "08", "rede")
        try:
            arquivos = os.listdir(dir_logos)
        except OSError:
            return (False, u"pasta de logos da rede não existe")
        favicons = [a for a in arquivos
                    if not (a.endswith("-logo.svg") or a.endswith("-logo.png")
                            or a.startswith("mapa-"))]
        if favicons:
            det.append(u"favicon(s) antigo(s) ainda na pasta: %s"
                       % ", ".join(favicons[:3]))
        logos = [a for a in arquivos if a.endswith(("-logo.svg", "-logo.png"))]
        if len(logos) < 6:
            det.append(u"só %d logo(s) de parceiro (esperado 6)" % len(logos))
        for a in logos:
            tam = os.path.getsize(os.path.join(dir_logos, a))
            if tam < 1500:
                det.append(u"%s tem só %d bytes (parece favicon)" % (a, tam))
        for rel in REDE:
            hh = s.ler(rel)
            for a in logos:
                pass
            if re.search(r'onda31-pin__chip[^>]*>\s*<img src="[^"]*/(?:www\.)?[a-z0-9.-]+\.com',
                         hh):
                det.append(u"%s ainda usa favicon por domínio no pin" % rel)
        return (not det, u"; ".join(det[:3]))
    s.check("S111", u"logo de verdade no pin dos parceiros (#169/#140)", s111)

    def s112():
        # #170: o mapa e um SVG GERADO do Natural Earth, servido como arquivo
        det = []
        for chave in ("americas", "europa"):
            p = os.path.join(pub, "wp-content", "uploads", "2026", "08", "rede",
                             "mapa-%s.svg" % chave)
            if not os.path.exists(p):
                det.append(u"falta mapa-%s.svg" % chave)
                continue
            svg = s.ler("wp-content/uploads/2026/08/rede/mapa-%s.svg" % chave)
            # geometria de verdade tem MUITO ponto; o desenho a mao da onda 21
            # cabia em 4 KB
            pontos = svg.count("L")
            if pontos < 800:
                det.append(u"mapa-%s.svg com só %d segmentos (parece desenho à mão)"
                           % (chave, pontos))
            if 'viewBox="0 0 1000' not in svg:
                det.append(u"mapa-%s.svg fora do viewBox de 1000 de largura" % chave)
        for rel in REDE:
            hh = s.ler(rel)
            if hh.count("onda31-mapa__svg") != 2:
                det.append(u"%s não tem os 2 mapas como arquivo" % rel)
            if "<svg" in hh.split('class="onda31-rede"')[-1][:4000]:
                det.append(u"%s voltou a embutir SVG de mapa na página" % rel)
        return (not det, u"; ".join(det[:3]))
    s.check("S112", u"mapas gerados de geometria real, em arquivo (#170)", s112)

    def s113():
        # #171: a lista de parceiros abaixo dos mapas saiu
        det = []
        for rel in REDE:
            hh = s.ler(rel)
            for marca in ("onda21-lista", "onda31-lista"):
                if marca in hh:
                    det.append(u"%s ainda tem a lista de parceiros (%s)" % (rel, marca))
        return (not det, u"; ".join(det[:3]))
    s.check("S113", u"rede sem a lista de parceiros abaixo dos mapas (#171)", s113)

    def s116():
        # #174: a posição de cada pin é a projeção da lat/lon do mestre — o caso do
        # PSE "em Londres" mas desenhado no mar não pode voltar. A suíte RECALCULA
        # a projeção e compara com o que está no HTML: pin editado à mão quebra aqui.
        import math as _m
        publicados = os.path.join(os.path.dirname(AQUI), "tools",
                                  "rede-publicada.json")
        if not os.path.exists(publicados):
            return (False, u"falta tools/rede-publicada.json (gerado por gen_rede.py)")
        with io.open(publicados, encoding="utf-8") as f:
            dados = json.load(f)

        def merc(lat):
            lat = max(min(lat, 84.0), -84.0)
            return _m.log(_m.tan(_m.radians(45.0 + lat / 2.0)))

        det = []
        for chave, mapa in sorted(dados["mapas"].items()):
            lon0, lat0, lon1, lat1 = mapa["bbox"]
            x0, x1 = _m.radians(lon0), _m.radians(lon1)
            y_topo, y_base = merc(lat1), merc(lat0)
            for pa in mapa["pins"]:
                esq = 100.0 * (_m.radians(pa["lon"]) - x0) / (x1 - x0)
                top = 100.0 * (y_topo - merc(pa["lat"])) / (y_topo - y_base)
                if abs(esq - pa["esq"]) > 0.05 or abs(top - pa["top"]) > 0.05:
                    det.append(u"%s: publicado %.2f/%.2f, projeção diz %.2f/%.2f"
                               % (pa["nome"], pa["esq"], pa["top"], esq, top))
                if not (0 < esq < 100 and 0 < top < 100):
                    det.append(u"%s cai fora do mapa (%.1f/%.1f)"
                               % (pa["nome"], esq, top))
                # e o HTML tem de trazer exatamente esses números
                for rel in REDE:
                    hh = s.ler(rel)
                    if 'style="left:%.2f%%;top:%.2f%%"' % (pa["esq"], pa["top"]) not in hh:
                        det.append(u"%s: %s sem o pin na posição projetada"
                                   % (rel, pa["nome"]))
                        break
        return (not det, u"%d problema(s): %s" % (len(det), "; ".join(det[:3])))
    s.check("S116", u"pin de cada parceiro na projeção da sua lat/lon (#174)", s116)

    # ---------------------------------------------------------------- onda 33
    # Lote de limpeza: cinco pedidos antigos, todos verificáveis. Cada um deixa uma
    # asserção para trás, para o problema não voltar em silêncio.

    # Quem saiu da firma e tinha página de perfil no espelho.
    SAIRAM_SLUGS = ["giulia-turcato", "lucas-duarte",
                    "mariana-nakagawa", "matheus-strapasson",
                    # Onda 68: Michael Munch deixou a firma em 19/08/2026 e o
                    # Mario pediu para tira-lo "de tudo". Sao 4 URLs com o slug
                    # (pt/lider, en/leader, de/lider e o duplicado de/leader),
                    # e mais 4 stubs de `591` que a S151 cobra.
                    "michael-munch"]
    # Nomes que não podem aparecer como AUTORIA nem como perfil. Fernando Fabbris
    # não entra: ele é coautor real do artigo da transição climática (evento de
    # out/2024), e apagar o crédito de quem escreveu seria falsear o registro — o
    # que a onda 33 corrigiu ali foi o tempo verbal da bio (era "é", virou "foi").
    EX_AUTORES = [u"Giulia Turcato"]

    def s118():
        # #66 + #81: quem saiu sai do site. Três coisas de uma vez:
        #   a) nenhuma das 28 URLs de perfil serve conteúdo — todas redirecionam
        #      para a página de líderes do idioma, num salto só;
        #   b) nenhuma página de CONTEÚDO traz um ex-autor;
        #   c) os 4 modais órfãos saíram da en/homepage.
        det = []
        alvos = [(rel, h) for rel, h in s.todas()
                 if any(sl in rel.lower() for sl in SAIRAM_SLUGS)]
        # 28 na onda 33 + 4 do Michael na onda 68.
        if len(alvos) != 32:
            det.append(u"esperava 32 URLs de ex-líder, achei %d" % len(alvos))
        lideres = ("/sobre-nos/lideres/", "/about-us/leaders/",
                   "/ueber-uns/fuehrungskraefte/")
        for rel, h in alvos:
            if not s.eh_stub(rel, h):
                det.append(u"%s ainda serve conteúdo" % rel)
                continue
            m = re.search(r'content="0;url=([^"]+)"', h)
            if not m:
                det.append(u"%s sem destino de redirect" % rel)
            elif not any(a in m.group(1) for a in lideres):
                # dois saltos: o stub mandaria para outro stub
                det.append(u"%s redireciona para %s, não para os líderes"
                           % (rel, m.group(1)))
        for rel, h in s.conteudo():
            for nome in EX_AUTORES:
                if nome in h:
                    det.append(u"%s ainda cita %s" % (rel, nome))
        home_en = s.ler("en/homepage/index.html")
        for nome in ("Marcelo Soares", "Marcelo Massarente",
                     "Lucas Santiago", "Fernando Fabbris"):
            if nome in home_en:
                det.append(u"modal de %s de volta na en/homepage" % nome)
        return (not det, u"%d problema(s): %s" % (len(det), "; ".join(det[:4])))
    s.check("S118", u"quem saiu não tem página nem autoria no site (#66/#81)", s118)

    def s119():
        # #69: as 6 imagens das práticas existem no disco de verdade. Antes eram
        # exceção declarada em FALTAS_CONHECIDAS ("S-20"); foram recuperadas do
        # WordPress vivo. A E05 já cobra "todo asset existe" — esta garante que
        # ninguém as devolva para a lista de exceções, e que não sejam placeholder.
        det = []
        for rel, _h in s.conteudo():
            pass
        esperadas = [
            "novo/wp-content/uploads/2023/04/strategic_ideation_formulation_execution-1.png",
            "novo/wp-content/uploads/2023/05/2-inovacao-modelo-de-negocio-radar-de-tendencias-workshop-ecossistema-1024x503.png",
            "novo/wp-content/uploads/2023/05/3-marketing-vendas-pricing-go-to-market-CX-forca-de-vendas-digital-1024x545.png",
            "novo/wp-content/uploads/2023/05/4-operacoes-supply-chain-SOP-CSC-procurement-estoques-1024x435.png",
            "novo/wp-content/uploads/2023/05/7-transformacao-metodologia-agil-gestao-da-mudanca-governanca-quick-wins-1024x521.png",
            "novo/wp-content/uploads/2023/05/8-adaptacao-climatica-sustentabilidade-net-zero-ESG-descarbonizacao-carbono-1024x552.png",
        ]
        # Onda 62c: as 6 viraram WebP na mesma dimensão. A asserção cobra que a
        # IMAGEM exista e não seja placeholder — o formato é incidental, como na
        # H04, que passou a aceitar webp porque cobra o cliente, não a extensão.
        # Sem isto, a S119 quebraria o deploy por motivo certo e alvo errado
        # (o caso da S125 na onda 33b).
        for rel in esperadas:
            candidatos = [rel, rel[:-4] + ".webp"] if rel.endswith(".png") else [rel]
            p = next((os.path.join(pub, c.replace("/", os.sep)) for c in candidatos
                      if os.path.exists(os.path.join(pub, c.replace("/", os.sep)))), None)
            if p is None:
                det.append(u"ausente: %s" % rel.split("/")[-1])
                continue
            if os.path.getsize(p) < 4 * 1024:
                det.append(u"%s tem só %d bytes — não é a imagem"
                           % (os.path.basename(p), os.path.getsize(p)))
            with io.open(p, "rb") as f:
                cab = f.read(12)
            if not (cab[:4] == b"\x89PNG" or (cab[:4] == b"RIFF" and cab[8:12] == b"WEBP")):
                det.append(u"%s não é PNG nem WebP" % os.path.basename(p))
        for rel in esperadas:
            if rel in FALTAS_CONHECIDAS:
                det.append(u"%s voltou para FALTAS_CONHECIDAS" % rel.split("/")[-1])
        return (not det, u"%d problema(s): %s" % (len(det), "; ".join(det[:3])))
    s.check("S119", u"as 6 imagens das práticas existem de verdade (#69)", s119)

    def s120():
        # #70: o sitemap existe, e é EXATAMENTE o que o gerador produz das páginas de
        # conteúdo. A suíte RECALCULA a lista e compara — sitemap editado à mão, ou
        # página nova que ninguém regerou, quebra aqui (mesmo padrão da S116).
        import importlib.util
        p_sitemap = os.path.join(pub, "sitemap.xml")
        if not os.path.exists(p_sitemap):
            return (False, u"public/sitemap.xml ausente — o robots.txt aponta para o vazio")
        p_gen = os.path.join(os.path.dirname(pub), "tools_onda6",
                             "90_sitemap_e_raiz.py")
        spec = importlib.util.spec_from_file_location("gen90", p_gen)
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)

        itens = gen.urls_do_sitemap(pub)
        esperado = gen.xml_do_sitemap(itens)
        atual = s.ler("sitemap.xml")
        det = []
        if atual != esperado:
            det.append(u"sitemap.xml diverge do gerador (%d URLs esperadas)"
                       % len(itens))
        # nenhuma URL do sitemap pode ser noindex nem faltar no disco
        for loc, _lastmod in itens:
            caminho = loc[len(gen.BASE):].lstrip("/") if loc.startswith(gen.BASE) else None
            if caminho is None:
                det.append(u"URL fora do espelho: %s" % loc)
                continue
            rel = caminho.rstrip("/") + "/index.html"
            fp = os.path.join(pub, rel.replace("/", os.sep))
            if not os.path.exists(fp):
                det.append(u"URL sem arquivo: %s" % loc)
            elif "noindex" in s.ler(rel).lower():
                det.append(u"URL noindex no sitemap: %s" % loc)
        # e o robots tem de apontar para ele
        robots = s.ler("robots.txt")
        url = gen.BASE + gen.PREFIXO + "sitemap.xml"
        if ("Sitemap: %s" % url) not in robots:
            det.append(u"robots.txt não aponta para %s" % url)
        return (not det, u"%d problema(s) (%d URLs): %s"
                % (len(det), len(itens), "; ".join(det[:3])))
    s.check("S120", u"sitemap.xml existe, bate com o gerador e o robots aponta (#70)",
            s120)

    def s121():
        # #71: a raiz do Pages vai para /pt/, não para /en/. Firma brasileira,
        # conteúdo principal em PT — decisão do Mario.
        h = s.ler("index.html")
        m = re.search(r'content="0;url=([^"]+)"', h)
        if not m:
            return (False, u"public/index.html não é redirect: %r" % h[:80])
        destino = m.group(1)
        return (destino.rstrip("/").endswith("/pt"),
                u"a raiz manda para %s (esperado terminar em /pt/)" % destino)
    s.check("S121", u"raiz do Pages redireciona para /pt/ (#71)", s121)

    def s122():
        # #106: 0 referência a /feed/ (não existe feed num site estático: eram 37
        # <link rel=alternate rss>, todos 404) e 0 resquício de UI do ChatGPT
        # colada nas páginas alemãs de digital.
        det = []
        comfeed = [rel for rel, h in s.todas() if "/feed/" in h]
        if comfeed:
            det.append(u"%d página(s) com /feed/: %s"
                       % (len(comfeed), ", ".join(comfeed[:3])))
        chat = [rel for rel, h in s.todas() if "ChatGPT" in h]
        if chat:
            det.append(u"%d página(s) com markup do ChatGPT: %s"
                       % (len(chat), ", ".join(chat[:3])))
        return (not det, u"; ".join(det))
    s.check("S122", u"0 referência morta a /feed/ e 0 markup do ChatGPT (#106)", s122)

    def s123():
        # Achado da própria onda 33: 143 páginas referenciavam o asset de medição como
        # "/wp-content/..." — sem o prefixo /mirow-site/ — e portanto 404avam no Pages.
        # A M01 não pegava porque ela procura o NOME do arquivo, não o caminho.
        # Aqui o caminho de TODA referência a asset próprio tem de resolver no disco.
        det = []
        for rel, h in s.todas():
            for m in re.finditer(r'(?:src|href)="([^"]*(?:onda\d+[\w-]*|onda6)\.(?:js|css))(?:\?[^"]*)?"', h):
                caminho = m.group(1)
                if not caminho.startswith("/"):
                    continue
                if caminho.startswith("/mirow-site/"):
                    det.append(u"%s: %s ainda com o prefixo do staging" % (rel, caminho))
                    continue
                fp = os.path.join(pub, caminho.lstrip("/").replace("/", os.sep))
                if not os.path.exists(fp):
                    det.append(u"%s: %s não existe no disco" % (rel, caminho))
        return (not det, u"%d referência(s) quebrada(s): %s"
                % (len(det), "; ".join(det[:3])))
    s.check("S123", u"asset próprio root-relative e existente no disco", s123)

    def s124():
        # Achado da própria onda 33: a S-106 criou en/press e de/presse a partir de
        # outro molde e o hreflang veio com ele — as duas declaravam a POLÍTICA DE
        # PRIVACIDADE como sua versão nos outros idiomas, e pt/imprensa não tinha
        # nenhum. As três têm de apontar umas para as outras.
        esperado = {"pt": HOST + "/pt/imprensa/",
                    "en": HOST + "/en/press/",
                    "de": HOST + "/de/presse/"}
        det = []
        for rel in IMPRENSA:
            h = s.ler(rel)
            achado = dict((lg, hf) for hf, lg in re.findall(
                r'<link rel="alternate" href="([^"]*)" hreflang="([^"]*)"', h))
            if achado != esperado:
                det.append(u"%s: hreflang %s" % (rel, sorted(achado.items())))
        return (not det, u"%d página(s) de imprensa com hreflang errado: %s"
                % (len(det), "; ".join(det[:3])))
    s.check("S124", u"as 3 páginas de imprensa se apontam por hreflang", s124)

    def s125():
        # #178: o "m" da marca no centro do hero. O path desenhado no canvas tem de
        # ser EXATAMENTE o primeiro <path> de marca-mirow-co.svg — fonte única do
        # glifo (P3). Se a marca oficial mudar, a suíte acusa em vez de o hero
        # divergir do resto do site em silêncio.
        js_rel = "wp-content/uploads/2026/07/onda6/onda17-horizonte.js"
        svg_rel = "wp-content/uploads/2024/04/marca-mirow-co.svg"
        for rel in (js_rel, svg_rel):
            if not os.path.exists(os.path.join(pub, rel.replace("/", os.sep))):
                return (False, u"arquivo ausente: %s" % rel)
        js = s.ler(js_rel)
        svg = s.ler(svg_rel)
        oficial = re.findall(r'<path d="([^"]+)"', svg)
        if not oficial:
            return (False, u"nenhum <path> em %s" % svg_rel)
        m = re.search(r"var M_PATH = '([^']+)'", js)
        if not m:
            return (False, u"M_PATH não encontrado em %s" % js_rel)
        if m.group(1) != oficial[0]:
            return (False, u"o M_PATH do canvas divergiu do 1º path de %s "
                           u"(marca %d chars, canvas %d chars)"
                    % (svg_rel, len(oficial[0]), len(m.group(1))))
        # e o logo tem de ser efetivamente construído. ATENÇÃO: até a onda 35 isto
        # cobrava `desenharLogo(` (o m era pintado no canvas). Na onda 36 o glifo saiu
        # do canvas e virou ELEMENTO SVG (`.hero-logo-m`), para poder ficar na frente
        # dos cards — então o que se cobra aqui mudou junto. Não é afrouxamento: a
        # V22 mede o elemento renderizado (sólido, z-index, 0 colisão com texto).
        falta = [t for t in ("garantirLogo(", "hero-logo-m", "medirCentro(",
                             "posicionarLogo(") if t not in js]
        if falta:
            return (False, u"o hero não constrói o logo: falta %s" % ", ".join(falta))
        # o path do elemento SVG tem de ser o M_PATH, não uma cópia colada
        if "p.setAttribute('d', M_PATH)" not in js:
            return (False, u"o <path> do SVG não usa a constante M_PATH — risco de "
                           u"cópia divergente do glifo")
        return (True, u"M_PATH idêntico ao da marca (%d chars)" % len(oficial[0]))
    s.check("S125", u'o "m" do hero vem da marca oficial, sem cópia divergente (#178)',
            s125)

    def s127():
        # #179, causa-raiz: nenhum font-weight do NOSSO css pode pedir um peso que a
        # página não carrega. Era o bug dos big numbers: o CSS pedia 800, o <head>
        # pede wght@200;300;400;600;700;900, e o navegador arredondava para 900 —
        # os números saíam no peso mais gordo da família sem ninguém ter escrito isso.
        # A asserção lê os pesos disponíveis da FONTE DA VERDADE, não de uma lista
        # fixa. Essa fonte mudou de lugar na #227: antes era o `wght@…` do <link>
        # do Google no <head>; agora a Titillium é autohospedada e quem manda são
        # os @font-face do nosso CSS. A asserção quebrou o deploy no ato — motivo
        # certo, alvo errado, como a S125 na onda 36 — e passou a ler o disco, que
        # é ainda melhor: mede o peso que de fato existe em arquivo, não o pedido.
        FONTES = "wp-content/uploads/2026/07/fontes/fontes-mirow.css"
        try:
            disponiveis = set(int(x) for x in
                              re.findall(r"font-weight:\s*(\d+)", s.ler(FONTES)))
        except IOError:
            disponiveis = set()
        if not disponiveis:
            # Fallback ao modelo antigo, caso um dia a fonte volte a ser remota.
            m = re.search(r'family=Titillium\+Web:wght@([0-9;]+)', s.ler("pt/index.html"))
            if not m:
                return (False, u"não achei os pesos nem em %s nem no <head> da home"
                        % FONTES)
            disponiveis = set(int(x) for x in m.group(1).split(";") if x)
        css = s.ler("wp-content/uploads/2026/07/onda6/onda6.css")
        orfaos = {}
        for w in re.findall(r'font-weight:\s*(\d+)', css):
            if int(w) not in disponiveis:
                orfaos[w] = orfaos.get(w, 0) + 1
        return (not orfaos,
                u"peso(s) declarado(s) e não carregado(s): %s — disponíveis: %s"
                % (", ".join("%s (%dx)" % (k, v) for k, v in sorted(orfaos.items())),
                   sorted(disponiveis)))
    s.check("S127", u"nenhum font-weight pede peso que a fonte não carrega (#179)",
            s127)

    # S128 — onda 41 (#187): a caixinha de expertise é "Estratégia e Inovação"
    # nas 3 homes (decisão FD+AM 05/08). A âncora é o ícone do card, para não
    # confundir com o hero nem com o menu Práticas.
    def s128():
        alvo = {"pt/index.html": u"Estratégia e Inovação",
                "en/index.html": u"Strategy &amp; Innovation",
                "de/index.html": u"Strategie &amp; Innovation"}
        det = []
        for rel, txt in alvo.items():
            # `[^>]*` entre o src e o `>`: a onda 60 pôs alt="" no ícone (imagem
            # decorativa), e a versão literal desta asserção quebrou o deploy por
            # motivo certo e alvo errado — o texto da caixinha nunca mudou. O que
            # importa é o ícone de estratégia estar colado no rótulo certo.
            if not re.search(r'icon-strategy\.svg"[^>]*><span>%s</span>' % re.escape(txt),
                             s.ler(rel)):
                det.append(u"%s sem '%s'" % (rel, txt))
        return (not det, u"; ".join(det))
    s.check("S128", u'caixinha de expertise é "Estratégia e Inovação" nas 3 homes (#187)',
            s128)

    # S129 — onda 41: todo logo de veículo/cliente resolve para arquivo existente
    # E todo SVG de logo declara width/height na raiz. Causa-raiz de dois bugs da
    # onda: santos-brasil.svg sem width/height renderizava 0x0 (o navegador não
    # deriva tamanho de viewBox em <img> com max-width/max-height auto), e o jpg
    # antigo apontado depois de removido daria 404 silencioso.
    def s129():
        det = []
        rex = re.compile(r'<img class="(?:clientes-logos__item-img|onda41-imprensa__logo)[^"]*"[^>]*src="([^"?]+)')
        vistos = set()
        for rel in ["pt/index.html", "en/index.html", "de/index.html",
                    "pt/imprensa/index.html", "en/press/index.html",
                    "de/presse/index.html"]:
            h = s.ler(rel)
            for m in re.finditer(r'<img [^>]*src="(/[^"?]+\.(?:svg|png|jpg))[^"]*"[^>]*>', h):
                src = m.group(1)
                if ("clientes/" not in src and "imprensa" not in src) or src in vistos:
                    continue
                vistos.add(src)
                caminho = src.lstrip("/")
                fs = os.path.join(s.pub, caminho.replace("/", os.sep))
                if not os.path.exists(fs):
                    det.append(u"%s não existe (%s)" % (src, rel))
                    continue
                if src.endswith(".svg"):
                    with io.open(fs, encoding="utf-8", errors="ignore") as f:
                        raiz = re.search(r"<svg[^>]*>", f.read())
                    if not raiz or "width=" not in raiz.group(0) or "height=" not in raiz.group(0):
                        det.append(u"%s sem width/height na raiz" % src)
        return (not det, u"%d problema(s): %s" % (len(det), "; ".join(det[:4])))
    s.check("S129", u"logos (clientes+imprensa) existem e todo SVG tem width/height",
            s129)

    # S130 — onda 41 (#65): /en/ é a home EN canônica. A duplicata /en/homepage/
    # é stub noindex com refresh para /en/, e as 3 homes se apontam por hreflang
    # (fecha a pendência da 33b). O sitemap sem a duplicata já é coberto pela
    # S120, que o RECALCULA.
    def s130():
        det = []
        h = s.ler("en/homepage/index.html")
        if "onda41:home-en-canonica" not in h:
            det.append(u"en/homepage não é o stub da onda 41")
        else:
            if 'content="0;url=/en/"' not in h:
                det.append(u"stub não redireciona para /en/")
            if "noindex" not in h:
                det.append(u"stub sem noindex")
        # As homes JÁ tinham hreflang completo do tema (pt/en/de + x-default —
        # medido em 06/08; o registro da 33b sobre "home sem hreflang" era só a
        # en/homepage). Aqui se cobra: o trio aponta as 3 homes, e NENHUMA
        # página do site declara a duplicata /en/homepage/ como alternativa.
        for rel in ["pt/index.html", "en/index.html", "de/index.html"]:
            hh = s.ler(rel)
            pares = re.findall(
                r'<link rel="alternate" href="([^"]*)" hreflang="([^"]*)"', hh)
            por_lang = {}
            for href, lang in pares:
                por_lang.setdefault(lang.split("-")[0], set()).add(href)
            for lang, home in (("pt", HOST + "/pt/"),
                               ("en", HOST + "/en/"),
                               ("de", HOST + "/de/")):
                if home not in por_lang.get(lang, set()):
                    det.append(u"%s: hreflang %s não aponta %s" % (rel, lang, home))
            if any("/en/homepage/" in href for href, _l in pares):
                det.append(u"%s declara /en/homepage/ como alternativa" % rel)
        for rel, hh in s.conteudo():
            if 'hreflang' in hh and '/en/homepage/' in hh and \
               re.search(r'hreflang="[^"]*"[^>]*href="[^"]*/en/homepage/|href="[^"]*/en/homepage/"[^>]*hreflang', hh):
                det.append(u"%s aponta hreflang para a duplicata" % rel)
        return (not det, u"; ".join(det[:4]))
    s.check("S130", u"/en/ canônica: en/homepage é stub e as 3 homes têm hreflang (#65)",
            s130)

    # S131 — onda 41 (#190): toda linha da imprensa tem o logo grande (imagem em
    # imprensa-logos/ ou wordmark tipográfico de fallback) nas 3 línguas.
    def s131():
        det = []
        for rel in ["pt/imprensa/index.html", "en/press/index.html",
                    "de/presse/index.html"]:
            h = s.ler(rel)
            itens = h.count('onda18-imprensa__item')
            logos = h.count('onda41-imprensa__logo')  # img e --texto contam
            sobras = h.count('class="onda18-imprensa__logo')
            if itens == 0:
                det.append(u"%s sem itens" % rel)
            if logos < itens:
                det.append(u"%s: %d itens, %d logos novos" % (rel, itens, logos))
            if sobras:
                det.append(u"%s: %d favicon(s) antigo(s) ainda no markup" % (rel, sobras))
        return (not det, u"; ".join(det[:4]))
    s.check("S131", u"imprensa com logo grande (ou wordmark de texto) em toda linha (#190)",
            s131)

    # S132 — onda 42 (#194): os setores da home recategorizados — 6 cards com
    # os nomes decididos, nas 3 homes, cobrindo o portfólio real.
    def s132():
        esperado = {
            "pt/index.html": [u"Base Florestal", u"Indústria Pesada", u"Energia",
                              u"Logística e Portos", u"Consumo e Agro",
                              u"Serviços e Tecnologia"],
            "en/index.html": [u"Forest-based Industry", u"Heavy Industry",
                              u"Energy", u"Logistics & Ports",
                              u"Consumer & Agri", u"Services & Technology"],
            "de/index.html": [u"Forstbasierte Industrie", u"Schwerindustrie",
                              u"Energie", u"Logistik & Häfen", u"Konsum & Agrar",
                              u"Dienstleistungen & Technologie"],
        }
        det = []
        for rel, nomes in esperado.items():
            h = s.ler(rel)
            seg = h[h.find('onda18-orbe__cards'):h.find('</section>',
                                                        h.find('onda18-orbe__cards'))]
            achado = re.findall(r'onda18-const__nome">([^<]*)<', seg)
            achado = [a.replace("&amp;", "&") for a in achado]
            if achado != nomes:
                det.append(u"%s: %s" % (rel, achado))
        return (not det, u"; ".join(det[:2]))
    s.check("S132", u"setores da home: os 6 cards recategorizados nas 3 homes (#194)",
            s132)

    # S133 — onda 42 (#192): GEO honesto. O llms.txt existe com as práticas, e
    # NEM ele NEM as homes nomeiam consultorias concorrentes (regra do Mario
    # 23/07 — o pedido de texto oculto comparativo foi recusado na #192; esta
    # asserção impede a ideia de voltar por outra porta).
    def s133():
        det = []
        p = os.path.join(s.pub, "llms.txt")
        if not os.path.exists(p):
            det.append(u"llms.txt não existe")
        else:
            with io.open(p, encoding="utf-8") as f:
                t = f.read()
            for pratica in (u"Estratégia e Inovação", u"Go-to-market e Pricing",
                            u"Sourcing, Compras e Estoques"):
                if pratica not in t:
                    det.append(u"llms.txt sem a prática '%s'" % pratica)
            # a checagem de concorrente vale para o MATERIAL GEO (llms.txt),
            # não para as homes: as bios dos líderes citam ex-empregadores
            # (McKinsey etc.), o que é currículo factual e legítimo.
            for nome in ("McKinsey", "Bain", "BCG", "Boston Consulting"):
                if nome in t:
                    det.append(u"concorrente '%s' citado no llms.txt" % nome)
        for rel in ["pt/index.html", "en/index.html", "de/index.html"]:
            if '"knowsAbout"' not in s.ler(rel):
                det.append(u"%s sem Organization.knowsAbout" % rel)
        return (not det, u"; ".join(sorted(set(det))[:4]))
    s.check("S133", u"GEO honesto: llms.txt + knowsAbout, sem concorrente nomeado (#192)",
            s133)

    # S134 — onda 43 (#199). O submenu Práticas diz "Estratégia e Inovação",
    # como o card da home desde a #187 — o rótulo antigo ("Estratégia" seco)
    # não pode voltar em NENHUMA das páginas, nas 3 línguas.
    def s134():
        from _onda7_css import idioma_da_pagina
        certos = {"pt": u">Estratégia e Inovação</a>",
                  "en": u">Strategy &amp; Innovation</a>",
                  "de": u">Strategie &amp; Innovation</a>"}
        errados = {"pt": u">Estratégia</a>",
                   "en": u">Strategy</a>",
                   "de": u">Strategie</a>"}
        det = []
        n = 0
        for rel, h in s.todas():
            i = h.find("<!-- onda7:menu-praticas -->")
            if i < 0:
                continue
            n += 1
            trecho = h[i:h.find("<!-- /onda7:menu-praticas -->", i)]
            idi = idioma_da_pagina(h)
            if certos[idi] not in trecho or errados[idi] in trecho:
                det.append(rel)
        if not n:
            det.append(u"nenhuma página com o marcador do menu")
        return (not det, u"%d página(s) com rótulo velho: %s"
                % (len(det), u", ".join(det[:4])))
    s.check("S134", u"menu Práticas com 'Estratégia e Inovação' nas 3 línguas (#199)",
            s134)

    # S135 — onda 44 (#201). Botões GENÉRICOS de e-mail (pílula do hero, ícone
    # da barra, trilho lateral) com DOIS destinatários (Andreas + Felipe); os
    # mailtos de card/modal de líder seguem pessoais, com um destinatário só.
    def s135():
        generico = re.compile(
            r'<a class="[^"]*(?:hero-contatos__link--mail|'
            r'menu__contatos-link--mail|onda19-lateral__link--mail)[^"]*"'
            r'[^>]*href="(mailto:[^"]*)"')
        lider = re.compile(
            r'class="onda26-lider__mail" href="(mailto:[^?"]*)')
        dupla = "mailto:andreas.mirow@mirow.com.br,felipe.diniz@mirow.com.br?"
        det = []
        n = 0
        for rel, h in s.conteudo():
            for m in generico.finditer(h):
                n += 1
                if not m.group(1).startswith(dupla):
                    det.append(u"%s: botão genérico sem os 2 destinatários" % rel)
                    break
            for m in lider.finditer(h):
                if "," in m.group(1):
                    det.append(u"%s: mailto de líder virou lista" % rel)
                    break
        if not n:
            det.append(u"nenhum botão genérico de e-mail encontrado")
        return (not det, u"; ".join(sorted(set(det))[:4]))
    s.check("S135", u"botões genéricos de e-mail com Andreas E Felipe; líderes intactos (#201)",
            s135)

    def s136():
        # #224: o AddToAny saiu. Mede o EFEITO — nenhuma URL do fornecedor no HTML
        # (era ele quem recebia o IP de todo leitor de artigo, e por onde passava
        # quem clicava em compartilhar) — e a substituição de fato funcionando:
        # cada botão aponta para o destino real e tem ícone próprio.
        det = []
        # O padrão nasceu exigindo `href="https?://` e DEIXOU PASSAR
        # `<link rel='dns-prefetch' href='//static.addtoany.com' />` — aspa simples
        # e URL sem protocolo. Publicamos com ele, e só a conferência AO VIVO pegou.
        # Agora a asserção cobre o que o título promete: QUALQUER referência ao
        # domínio do fornecedor, em qualquer atributo, com qualquer aspa, com ou
        # sem protocolo (P2.1 — o escopo do teste tem de cobrir o escopo do título).
        externo = re.compile(r'addtoany\.com', re.I)
        for rel, h in s.conteudo():
            if externo.search(h):
                det.append(u"%s: ainda referencia addtoany.com" % rel)
                continue
            for kit in re.finditer(r'<div class="a2a_kit[^"]*"[^>]*>(.*?)</div>', h, re.S):
                corpo = kit.group(1)
                ancoras = re.findall(r'<a class="a2a_button_(\w+)" href="([^"]*)"', corpo)
                if not ancoras:
                    det.append(u"%s: kit de compartilhar sem botões" % rel)
                    break
                for rede, href in ancoras:
                    ok = (("mailto:" in href) if rede == "email"
                          else ("wa.me" in href) if rede == "whatsapp"
                          else ("linkedin.com/sharing" in href))
                    if not ok:
                        det.append(u"%s: botão %s aponta para %s" % (rel, rede, href[:40]))
                if corpo.count("<svg") != len(ancoras):
                    det.append(u"%s: %d botão(ões) sem ícone (o script do fornecedor "
                               u"desenhava; agora o SVG tem de estar no HTML)"
                               % (rel, len(ancoras) - corpo.count("<svg")))
                break
        return (not det, u"; ".join(sorted(set(det))[:4]))
    s.check("S136", u"compartilhar sem AddToAny: links diretos e ícone no HTML (#224)", s136)

    def s137():
        # #225: a política v2. A asserção existe porque a v1 afirmava que os dados
        # ficavam "exclusivamente ... no Brasil" enquanto o site era servido pelo
        # GitHub (EUA) — declaração que divergiu da realidade e ninguém mediu.
        # Aqui cobramos o inverso: que a página NOMEIE cada operador que o site
        # realmente carrega, e não volte a afirmar o que é falso.
        PAGS = {"pt": "pt/politica-de-privacidade/index.html",
                "en": "en/privacy-policy/index.html",
                "de": "de/datenschutzrichtlinie/index.html"}
        OPERADORES = ("GitHub", "Google", "Dealfront", "Amazon Web Services")
        det = []
        for lang, rel in PAGS.items():
            try:
                h = s.ler(rel)
            except IOError:
                det.append(u"%s: página ausente" % lang)
                continue
            if "onda57:politica-v2" not in h:
                det.append(u"%s: ainda na versão antiga" % lang)
                continue
            for op in OPERADORES:
                if op not in h:
                    det.append(u"%s: não declara o operador %s" % (lang, op))
            # A frase que era falsa. Se voltar, é regressão de conteúdo.
            if re.search(r"exclusivamente[^<]{0,80}Brasil", h):
                det.append(u"%s: voltou a afirmar armazenamento exclusivo no Brasil" % lang)
            if "pol-optout" not in h:
                det.append(u"%s: sem o botão de oposição ao rastreamento" % lang)
        return (not det, u"; ".join(det[:4]))
    s.check("S137", u"política v2 nas 3 línguas: operadores reais e opt-out (#225)", s137)

    def s138():
        # #227: Google Fonts fora. Mede o efeito em TODO arquivo servido (html E
        # css) — o furo do AddToAny foi justamente uma referência num formato que
        # o padrão não previa, então aqui não se filtra por atributo nem por aspa.
        # Os 3 @import mortos moravam no CSS do TEMA, não no HTML.
        sujos = []
        for dp, _d, fs in os.walk(pub):
            for nome in fs:
                if not nome.lower().endswith((".html", ".css")):
                    continue
                fp = os.path.join(dp, nome)
                with io.open(fp, encoding="utf-8", errors="ignore") as f:
                    if re.search(r"fonts\.(googleapis|gstatic)\.com", f.read()):
                        sujos.append(os.path.relpath(fp, pub).replace(os.sep, "/"))
        if sujos:
            return (False, u"%d arquivo(s) ainda chamam o Google Fonts: %s"
                    % (len(sujos), ", ".join(sujos[:4])))
        # E o substituto tem de existir de verdade (S123 cobre o caminho; aqui,
        # que os arquivos de fonte estejam no disco — CSS sem woff2 é fonte morta).
        d = os.path.join(pub, "wp-content", "uploads", "2026", "07", "fontes")
        if not os.path.isdir(d):
            return (False, u"pasta de fontes locais não existe")
        woff = [f for f in os.listdir(d) if f.endswith(".woff2")]
        if len(woff) < 12:
            return (False, u"só %d woff2 no disco; o CSS declara 12" % len(woff))
        return (True, u"")
    s.check("S138", u"Google Fonts fora; Titillium Web servida do nosso disco (#227)", s138)

    # M — medição (mirow-marketing#3). O snippet de GA4 tinha sido escrito só na
    # camada Astro, que está fora do deploy, e por isso nunca chegou ao ar. As
    # asserções abaixo existem para essa regressão não voltar em silêncio.
    MEDICAO = "wp-content/uploads/2026/07/onda6/onda31-medicao.js"

    def m01():
        # Cobra as páginas de CONTEÚDO. A razão já estava escrita aqui para o
        # public/index.html — "o navegador sai antes de a medição valer, o
        # pageview é contado na página de destino" — e vale para qualquer stub de
        # redirect; a exceção é que estava estreita demais. Ficou explícito na
        # onda 57 (#228), quando as 3 páginas de contato viraram stub.
        sem = [rel for rel, h in s.conteudo() if MEDICAO not in h]
        return (not sem, u"%d página(s) sem o asset de medição: %s"
                % (len(sem), ", ".join(sem[:5])))
    s.check("M01", u"toda página carrega o asset de medição", m01)

    def m02():
        maus = [rel for rel, h in s.todas() if MEDICAO in h and (MEDICAO + "?v=") not in h]
        return (not maus, u"%d página(s) referenciam a medição sem ?v= (cache serve "
                u"versão velha): %s" % (len(maus), ", ".join(maus[:5])))
    s.check("M02", u"asset de medição carimbado com ?v=", m02)

    def m03():
        maus = [rel for rel, h in s.todas() if "gtag('config'" in h or 'gtag("config"' in h]
        return (not maus, u"%d página(s) com gtag inline sobrando — a configuração tem "
                u"que vir só do asset: %s" % (len(maus), ", ".join(maus[:5])))
    s.check("M03", u"nenhum gtag inline sobrando no HTML", m03)

    def m04():
        p = os.path.join(pub, *MEDICAO.split("/"))
        if not os.path.exists(p):
            return (False, u"asset de medição ausente em %s" % MEDICAO)
        js = s.ler(MEDICAO)
        # onda 50 (#207): só a institucional. A herdada saiu por decisão do Mario
        # (11/08); a ausência dela em TODO o public/ é a M06.
        falta = [pid for pid in ("G-5VTS0MZK79",) if pid not in js]
        return (not falta, u"propriedade(s) fora do asset: %s" % ", ".join(falta))
    s.check("M04", u"a propriedade institucional configurada no asset", m04)

    def m06():
        # Onda 50 (#207): 0 referência à tag herdada em qualquer arquivo de texto
        # de public/ — mede o efeito (grep no que o Pages serve), não a declaração.
        herdada = "G-VK4QHHHS5X"
        sujos = []
        for dirpath, _dirs, files in os.walk(pub):
            for nome in files:
                if not nome.lower().endswith((".html", ".css", ".js", ".xml", ".txt", ".json")):
                    continue
                fp = os.path.join(dirpath, nome)
                with io.open(fp, encoding="utf-8", errors="ignore") as f:
                    if herdada in f.read():
                        sujos.append(os.path.relpath(fp, pub).replace(os.sep, "/"))
        return (not sujos, u"%d arquivo(s) ainda citam a tag herdada: %s"
                % (len(sujos), ", ".join(sujos[:5])))
    s.check("M06", u"0 referência à tag GA4 herdada (G-VK4QHHHS5X) em public/ (#207)", m06)

    def m05():
        js = s.ler(MEDICAO)
        i_consent = js.find("'consent', 'default'")
        i_config = js.find("'config'")
        if i_consent < 0:
            return (False, u"sem Consent Mode: o site passaria a gravar cookie sem base legal")
        # Opcao C (decisao Mario 2026-08-12, mirow-marketing#209): analytics
        # liberado por default, TODO o eixo de ads negado. A assercao anterior
        # exigia analytics_storage 'denied'; mudou por decisao explicita.
        if "analytics_storage: 'granted'" not in js:
            return (False, u"analytics_storage não está 'granted' por padrão (opção C, #209)")
        for chave in ("ad_storage", "ad_user_data", "ad_personalization"):
            if "%s: 'denied'" % chave not in js:
                return (False, u"%s não está negado — a opção C proíbe qualquer eixo de ads" % chave)
        if i_config >= 0 and i_consent > i_config:
            return (False, u"consent default vem DEPOIS do config — o GA4 processa a fila "
                    u"na ordem e o consentimento chegaria tarde")
        return (True, u"")
    s.check("M05", u"Consent Mode v2 opção C: analytics granted, ads negado, antes do config (#209)", m05)

    # LF — Leadfeeder Lite, nível empresa (mirow-marketing#222). Entrou depois de o
    # Data Reveal ser REPROVADO no probe: aquele mandava o formulário inteiro sem
    # submit. O Leadfeeder passou no mesmo probe (14/08) — payload em base64
    # legível, sem campo de formulário e sem fingerprint.
    LF = "wp-content/uploads/2026/07/onda6/onda54-leadfeeder.js"

    def lf01():
        sem = [rel for rel, h in s.conteudo() if LF not in h]
        return (not sem, u"%d página(s) de conteúdo sem o asset do Leadfeeder: %s"
                % (len(sem), ", ".join(sem[:5])))
    s.check("LF01", u"toda página de conteúdo carrega o asset do Leadfeeder (#222)", lf01)

    def lf02():
        # Stubs de fora: o plano Lite dá 100 empresas/mês e página de redirect não
        # é lida por ninguém. Critério idêntico ao do injetor 94_leadfeeder.py.
        maus = [rel for rel, h in s.todas() if LF in h and s.eh_stub(rel, h)]
        return (not maus, u"%d stub(s) de redirect carregando o tracker à toa: %s"
                % (len(maus), ", ".join(maus[:5])))
    s.check("LF02", u"stub de redirect NÃO carrega o Leadfeeder (#222)", lf02)

    def lf03():
        maus = [rel for rel, h in s.conteudo() if (LF + "?v=") not in h]
        return (not maus, u"%d página(s) referenciam o Leadfeeder sem ?v= (cache serve "
                u"versão velha): %s" % (len(maus), ", ".join(maus[:5])))
    s.check("LF03", u"asset do Leadfeeder carimbado com ?v= (#222)", lf03)

    def lf04():
        js = s.ler(LF)
        url = re.search(r"var SCRIPT_URL = '([^']*)'", js)
        if not url:
            return (False, u"sumiu o SCRIPT_URL do asset")
        if url.group(1) and "lfeeder.com" not in url.group(1):
            return (False, u"SCRIPT_URL aponta para host que não é do Leadfeeder: %s"
                    % url.group(1))
        # A ordem é o que protege: gate e opt-out TÊM que rodar antes de o script
        # do fornecedor ser criado. Presença sem ordem não protege ninguém (P2.1).
        i_ativo = js.find("if (!ATIVO) return;")
        i_opt = js.find("if (optOut()) return;")
        i_script = js.find("document.createElement('script')")
        if i_ativo < 0 or js.find("var ATIVO") < 0:
            return (False, u"sumiu o interruptor ATIVO — é o kill switch de 1 linha "
                    u"para desligar o tracker sem tocar em 112 páginas")
        if i_opt < 0:
            return (False, u"asset sem opt-out — a única mitigação que não depende do fornecedor")
        if i_script >= 0 and (i_ativo > i_script or i_opt > i_script):
            return (False, u"ATIVO/opt-out rodam DEPOIS de criar o script do fornecedor: "
                    u"quem optou por sair seria rastreado mesmo assim")
        return (True, u"")
    s.check("LF04", u"Leadfeeder: host correto, kill switch e opt-out antes do tracker (#222)",
            lf04)


# ------------------------------------------------------- asserções ao vivo

class ServidorLocal(object):
    """Serve public/ numa porta livre, só durante a suíte.

    Sobe e derruba junto com a suíte de propósito: um `http.server` órfão
    servindo a pasta errada já falseou QA neste projeto.
    """
    def __init__(self, pub):
        self.pub = pub
        self.porta = None
        self.proc = None

    def __enter__(self):
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        self.porta = srv.getsockname()[1]
        srv.close()
        # Onda 47 (#101): as URLs das páginas são root-relative (/pt/, /wp-content/...)
        # como no domínio final — public/ é servido direto na raiz.
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(self.porta), "--bind", "127.0.0.1",
             "--directory", self.pub],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(40):
            try:
                urllib.request.urlopen("http://127.0.0.1:%d/pt/" % self.porta,
                                       timeout=2).read(1)
                return self
            except Exception:
                time.sleep(0.25)
        raise RuntimeError("servidor local não subiu na porta %d" % self.porta)

    def base(self):
        return "http://127.0.0.1:%d" % self.porta

    def __exit__(self, *a):
        if self.proc:
            self.proc.terminate()


class Navegador(object):
    """Chrome headless via CDP, reaproveitando o WS do tools_onda6/qa/shot.py."""
    def __init__(self, largura=1400, altura=900):
        self.largura, self.altura = largura, altura

    def __enter__(self):
        from shot import WS  # noqa: E402  (tools_onda6/qa já está no sys.path)
        self.perfil = tempfile.mkdtemp(prefix="verif")
        # Porta LIVRE, não a fixa 9344 que estava aqui. Com porta fixa, um Chrome
        # de execução anterior que não morreu ainda continua ouvindo nela — e o
        # próximo Navegador se conecta ao browser VELHO, que está numa página
        # velha, de um ServidorLocal de outra porta. O efeito é cruel: as medições
        # SAEM, plausíveis, e são de outra página. Custou um diagnóstico inteiro em
        # 17/08, quase reportado como bug do site (as URLs de redirect pareciam
        # apontar para lugares aleatórios; o HTML estava certo o tempo todo).
        # Mesma família do P2.1: o instrumento respondia sem estar medindo o alvo.
        _s = socket.socket()
        _s.bind(("127.0.0.1", 0))
        self.porta = _s.getsockname()[1]
        _s.close()
        self.proc = subprocess.Popen(
            [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--remote-debugging-port=%d" % self.porta, "--user-data-dir=" + self.perfil,
             "--window-size=%d,%d" % (self.largura, self.altura), "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ws_url = None
        for _ in range(60):
            try:
                tabs = json.load(urllib.request.urlopen(
                    "http://127.0.0.1:%d/json" % self.porta, timeout=5))
                for t in tabs:
                    if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                        ws_url = t["webSocketDebuggerUrl"]
                        break
                if ws_url:
                    break
            except Exception:
                pass
            time.sleep(0.5)
        if not ws_url:
            raise RuntimeError("não consegui falar com o Chrome")
        self.ws = WS(ws_url)
        self.mid = 0
        self.ws.call(self._id(), "Page.enable")
        return self

    def _id(self):
        self.mid += 1
        return self.mid

    # ---- instrumentacao e reuso (onda 60c) -------------------------------------
    # ANTES: todo abrir() dormia 6 s fixos. Com a fase estatica em 1,2 s, era ai
    # que morria o tempo do gate: cada page load custava 6 s, houvesse ou nao o
    # que esperar, e varias assercoes reabrem a MESMA url no MESMO viewport.
    # AGORA: espera a pagina ficar pronta de verdade (readyState + fontes + um
    # frame de animacao) e reaproveita a pagina quando nada mudou.
    # `--espera-fixa` volta ao comportamento antigo, para comparar.
    loads = 0
    tempo_loads = 0.0
    espera_fixa = False

    def _pronto(self, limite=8.0):
        """Bloqueia ate a pagina estar ESTAVEL, ou ate `limite` segundos.

        Nao basta `readyState=complete` + fontes: o tema usa AOS e o
        `onda8-dobra.js` re-mede a dobra em runtime, entao a geometria ainda muda
        depois do load. Medido em 18/08: com so readyState+fontes, a V30 acusava
        que o selo "AI Powered" nao estava acima do slogan — o selo AINDA estava
        animando. Aqui a espera olha uma IMPRESSAO DIGITAL do layout e sai quando
        ela para de mudar em duas amostras seguidas. E o mesmo principio da P2.1:
        esperar o efeito (layout assentado), nao um numero de segundos chutado.
        """
        FP = ("(function(){try{"
              "if(document.readyState!=='complete')return 'x';"
              "if(document.fonts&&document.fonts.status!=='loaded')return 'x';"
              "var p=[document.body.scrollHeight,window.innerHeight];"
              "var e=document.querySelectorAll('[data-aos],.onda53-selo-ia,"
              ".clientes-logos,.hero-texto,.hero-numeros');"
              "for(var i=0;i<e.length && i<14;i++){var r=e[i].getBoundingClientRect();"
              "p.push(Math.round(r.top),Math.round(r.left),Math.round(r.width),"
              "Math.round(r.height),getComputedStyle(e[i]).opacity);}"
              "return p.join(',');}catch(err){return 'x'}})()")
        t0 = time.time()
        anterior, iguais = None, 0
        while time.time() - t0 < limite:
            atual = self.js(FP)
            if atual and atual != "x" and atual == anterior:
                iguais += 1
                if iguais >= 2:      # duas amostras seguidas identicas
                    break
            else:
                iguais = 0
            anterior = atual
            time.sleep(0.2)
        return time.time() - t0

    def abrir(self, url, largura=None, altura=None, forcar=False):
        larg = largura or self.largura
        alt = altura or self.altura
        estado = (url, larg, alt)
        # Reuso: mesma url e mesmo viewport, e ninguem sujou a pagina desde entao
        # (hover e clique marcam `_sujo`, porque deixam estado que a proxima
        # assercao nao espera encontrar).
        if (not forcar and not getattr(self, "_sujo", True)
                and getattr(self, "_estado", None) == estado):
            return
        # trava as métricas do device: sem isso a barra do Chrome come ~98px e
        # qualquer medição de primeira dobra sai errada (bug real da onda 8).
        t0 = time.time()
        self.ws.call(self._id(), "Emulation.setDeviceMetricsOverride", {
            "width": larg, "height": alt,
            "deviceScaleFactor": 1, "mobile": False})
        self.ws.call(self._id(), "Page.navigate", {"url": url})
        if Navegador.espera_fixa:
            time.sleep(6)
        else:
            self._pronto()
        Navegador.loads += 1
        Navegador.tempo_loads += time.time() - t0
        self._estado = estado
        self._sujo = False

    def js(self, expr):
        r = self.ws.call(self._id(), "Runtime.evaluate",
                         {"expression": expr, "returnByValue": True})
        return r.get("result", {}).get("result", {}).get("value")

    def recorte(self, x, y, largura, altura):
        """PNG em base64 de uma regiao da pagina. None se o CDP recusar.

        Existe para assercao que precisa do PIXEL PINTADO, nao do
        getComputedStyle: `background-image` nao devolve cor, e cor declarada nao
        diz se o texto le. Usado pela V39 (contraste do bloco de IA), na mesma
        familia do pixel vermelho da onda 60b.
        """
        r = self.ws.call(self._id(), "Page.captureScreenshot", {
            "format": "png", "captureBeyondViewport": True,
            "clip": {"x": max(0, int(x)), "y": max(0, int(y)),
                     "width": max(1, int(largura)), "height": max(1, int(altura)),
                     "scale": 1}})
        return (r.get("result") or {}).get("data")

    def hover(self, x, y, espera=1.0):
        self._sujo = True  # hover deixa estado; a proxima assercao precisa recarregar
        """Hover de verdade (Input.dispatchMouseEvent), como o mouse do Mario.

        Serve para medir o que só existe em hover — o painel dos submenus. NÃO
        vale conferir cor em hover por screenshot: com `captureBeyondViewport` o
        Chrome repinta e o estado se perde (ver o aviso no shot_menu.py).
        """
        self.ws.call(self._id(), "Input.dispatchMouseEvent",
                     {"type": "mouseMoved", "x": x, "y": y,
                      "button": "none", "clickCount": 0})
        time.sleep(espera)

    def __exit__(self, *a):
        try:
            self.proc.terminate()
        except Exception:
            pass


def ao_vivo(s):
    if not os.path.exists(CHROME):
        s.res.append(("V--", u"asserções ao vivo", "PENDENTE", u"Chrome não encontrado em %s" % CHROME))
        print(u"  PENDENTE V--    asserções ao vivo — Chrome não encontrado")
        return
    with ServidorLocal(s.pub) as srv, Navegador() as nav:
        base = srv.base()

        # V01 — primeira dobra exata (onda 8): hero + barra de logos = 1 tela.
        # Medida em runtime; a sobra tem que ser ~0. Tolerância de 4px para
        # arredondamento de layout.
        def faz_dobra(rel, largura, altura):
            def f():
                url = "%s/%s" % (base, rel.replace("index.html", ""))
                nav.abrir(url, largura, altura)
                v = nav.js(
                    "(function(){var f=document.querySelector('.clientes-logos');"
                    "if(!f)return 'sem faixa de logos';"
                    "var b=Math.round(f.getBoundingClientRect().bottom);"
                    "return b - window.innerHeight;})()")
                if isinstance(v, str):
                    return (False, v)
                if v is None:
                    return (False, u"não deu para medir a dobra")
                return (abs(v) <= 4, u"sobra de %dpx em %dx%d (esperado 0, tolerância 4)"
                        % (v, largura, altura))
            return f
        for i, rel in enumerate(HOMES, 1):
            s.check("V%02d" % i, u"primeira dobra exata em %s (1400x900)" % rel,
                    faz_dobra(rel, 1400, 900))
        # V05 — onda 47: em viewport baixo o banner pode CRESCER (o conteudo
        # nao cabe na dobra) — o que nao pode e sobrar buraco (sobra negativa)
        # nem o titulo sumir sob o menu fixo (V29 cobre o titulo).
        def dobra_sem_buraco(rel, largura, altura):
            def f():
                url = "%s/%s" % (base, rel.replace("index.html", ""))
                nav.abrir(url, largura, altura)
                v = nav.js(
                    "(function(){var f=document.querySelector('.clientes-logos');"
                    "if(!f)return 'sem faixa de logos';"
                    "var b=Math.round(f.getBoundingClientRect().bottom);"
                    "return b - window.innerHeight;})()")
                if isinstance(v, str):
                    return (False, v)
                return (v >= -4, u"buraco de %dpx abaixo dos logos em %dx%d" % (-(v or 0), largura, altura))
            return f
        s.check("V05", u"dobra sem buraco em pt (1366x768; banner pode crescer — onda47)",
                dobra_sem_buraco("pt/index.html", 1366, 768))

        # V29 — onda 47 (achado 11/08): o titulo do hero NUNCA fica sob o menu
        # fixo, em nenhuma altura de viewport. Antes, com height fixo +
        # align-items:center, a 1280x620 o "Estratégia" perdia 82px sob o menu.
        def titulo_livre():
            det = []
            for w, h in [(1920, 730), (1366, 768), (1280, 620)]:
                nav.abrir(base + "/pt/", w, h)
                v = nav.js(
                    "(function(){var t=document.querySelector('.hero-texto h2');"
                    "var m=document.querySelector('.menu, nav, .header');"
                    "if(!t||!m)return 'seletor sumiu';"
                    "return Math.round(t.getBoundingClientRect().top -"
                    " m.getBoundingClientRect().bottom);})()")
                if isinstance(v, str):
                    det.append(u"%dx%d: %s" % (w, h, v))
                elif v is None or v < 4:
                    det.append(u"%dx%d: titulo a %spx do menu (minimo 4)" % (w, h, v))
            return (not det, u"; ".join(det))
        s.check("V29", u"titulo do hero livre do menu fixo em 3 alturas de tela (onda47)",
                titulo_livre)

        # V06 — os 4 contatos do hero recebem o clique de verdade. O bug da
        # onda 8.1 foi exatamente isto: o .banner__background (absolute) ficava
        # por cima e comia o clique, sem nenhum sintoma visual.
        def v06():
            nav.abrir("%s/pt/" % base, 1400, 900)
            v = nav.js(
                "(function(){var ls=document.querySelectorAll('.hero-contatos__link');"
                "if(!ls.length)return 'nenhum link de contato no hero';var ruins=[];"
                "for(var i=0;i<ls.length;i++){var r=ls[i].getBoundingClientRect();"
                "var el=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);"
                "if(!el||!ls[i].contains(el)&&el!==ls[i])ruins.push(i+':'+(el?el.className:'nada'));}"
                "return ruins.length?ruins.join(' '):'ok:'+ls.length;})()")
            if isinstance(v, str) and v.startswith("ok:"):
                return (True, u"%s links clicáveis" % v[3:])
            return (False, u"link(s) do hero com clique bloqueado: %s" % v)
        s.check("V06", u"os 4 contatos do hero recebem clique", v06)

        # V07 — S-41 (#97): nenhum bloquinho da pilha de números com mais de
        # 2 linhas de texto (medido: altura do span / line-height) em desktop.
        def v07():
            # AMPLIADA na onda 37. Antes media só `pt/` em 1920x1080 — e o título
            # dela promete "no máximo 2 linhas" sem qualificar. Resultado: a legenda
            # alemã "der Projekte werden für Kunden mit einem Jahresumsatz..." estava
            # em 3 LINHAS em 1400px, no ar, e a asserção passava verde. É o mesmo
            # padrão do P2.1: a asserção era mais estreita que o invariante que diz
            # proteger. Agora cobre as 4 homes nas larguras onde a pilha existe.
            js = ("(function(){var ts=document.querySelectorAll('.hero-numeros__texto');"
                  "if(!ts.length)return JSON.stringify({vazio:true});var ruins=[];"
                  "for(var i=0;i<ts.length;i++){var cs=getComputedStyle(ts[i]);"
                  "var lh=parseFloat(cs.lineHeight);"
                  "var n=Math.round(ts[i].getBoundingClientRect().height/lh);"
                  "if(n>2)ruins.push(n+'linhas: '+ts[i].textContent.trim().slice(0,34));}"
                  "return JSON.stringify({total:ts.length,ruins:ruins});})()")
            det = []
            medidos = 0
            for rel in HOMES:
                for w, h in [(1920, 1080), (1600, 900), (1400, 900), (1200, 900)]:
                    nav.abrir("%s/%s" % (base, rel.replace("index.html", "")), w, h)
                    try:
                        d = json.loads(nav.js(js))
                    except Exception as e:
                        det.append(u"%s @%d: não deu para medir (%r)" % (rel, w, e))
                        continue
                    if d.get("vazio"):
                        continue      # abaixo de 1200 a pilha não é exibida
                    medidos += 1
                    if d["ruins"]:
                        det.append(u"%s @%dpx — %s" % (rel, w, "; ".join(d["ruins"])))
            if not medidos:
                det.append(u"a pilha não foi encontrada em nenhuma home/largura")
            return (not det, u"%d bloco(s) com mais de 2 linhas: %s"
                    % (len(det), "; ".join(det[:3])))
        # o título não pode ter "≤": o console do Windows é cp1252 e o print explode
        s.check("V07", u"números do hero com no máximo 2 linhas — 4 homes x 4 larguras",
                v07)

        # V08 — S-98 (#156): UMA fonte renderizada por página. Aqui não se olha
        # o CSS, se olha o que o navegador computou em cada elemento visível —
        # era exatamente isso que denunciava expertise (Arial, porque Archivo não
        # existe) x setores (Titillium). Varre as páginas de cada template.
        def faz_fonte_unica(rel):
            def f():
                nav.abrir("%s/%s" % (base, rel.replace("index.html", "")), 1400, 900)
                v = nav.js(
                    "(function(){var m={},es=document.querySelectorAll('body *');"
                    "for(var i=0;i<es.length;i++){var e=es[i];"
                    "if(!e.getClientRects().length)continue;"
                    "var t=e.tagName;"
                    "if(t=='SCRIPT'||t=='STYLE'||t=='SVG'||t=='PATH')continue;"
                    "var f=getComputedStyle(e).fontFamily;"
                    "m[f]=(m[f]||0)+1;}"
                    "return JSON.stringify(m);})()")
                try:
                    mapa = json.loads(v)
                except Exception:
                    return (False, u"não deu para medir as fontes: %r" % v)
                fora = {k: n for k, n in mapa.items() if "Titillium Web" not in k}
                if fora:
                    itens = sorted(fora.items(), key=lambda kv: -kv[1])[:2]
                    return (False, u"%d família(s) fora do Titillium: %s"
                            % (len(fora), "; ".join(u"%s (%d elem.)" % (k, n)
                                                   for k, n in itens)))
                return (True, u"1 família em %d elementos visíveis"
                        % sum(mapa.values()))
            return f
        for i, rel in enumerate(["pt/index.html", "pt/pratica/estrategia/index.html",
                                 "pt/imprensa/index.html", "pt/sobre-nos/lideres/index.html",
                                 # onda 57 (#228): contato saiu; entra a política,
                                 # que é o outro template de texto corrido
                                 "pt/politica-de-privacidade/index.html",
                                 "de/index.html"], 8):
            s.check("V%02d" % i, u"uma fonte só renderizada em %s" % rel,
                    faz_fonte_unica(rel))

        # V14 — S-105 (#163): a barra tem de ser a MESMA coisa medida no navegador,
        # em páginas de templates diferentes (home com hero, prática com foto,
        # imprensa sem banner, post de blog, política de privacidade). Não se
        # compara CSS: compara-se a assinatura renderizada da barra.
        def v14():
            paginas = ["pt/", "pt/insights/", "pt/imprensa/", "pt/carreiras/",
                       "pt/pratica/estrategia/", "pt/sobre-nos/nossos-valores/",
                       "pt/sobre-nos/lideres/", "pt/politica-de-privacidade/"]
            js = ("(function(){var n=document.querySelector('.header .menu');"
                  "if(!n)return 'sem barra';var c=getComputedStyle(n),"
                  "r=n.getBoundingClientRect(),"
                  "l=document.querySelector('.header .menu__nav-link');"
                  "return JSON.stringify({bg:c.backgroundColor,h:Math.round(r.height),"
                  "cor:getComputedStyle(l).color,"
                  "fonte:getComputedStyle(l).fontFamily+'|'+getComputedStyle(l).fontSize,"
                  "itens:[].map.call(document.querySelectorAll("
                  "'.header .menu__nav-link'),function(a){return a.textContent.trim()})"
                  ".join('>'),"
                  "canais:document.querySelectorAll('.header .menu__contatos-link').length,"
                  "idiomas:!!document.querySelector('.header .menu__languages')});})()")
            assinaturas = {}
            for rel in paginas:
                nav.abrir("%s/%s" % (base, rel), 1400, 900)
                v = nav.js(js)
                if not isinstance(v, str) or v.startswith("sem"):
                    return (False, u"%s: %s" % (rel, v))
                assinaturas[rel] = v
            distintas = {}
            for rel, sig in assinaturas.items():
                distintas.setdefault(sig, []).append(rel)
            if len(distintas) > 1:
                pares = sorted(distintas.items(), key=lambda kv: -len(kv[1]))
                fora = pares[1][1]
                d1 = json.loads(pares[0][0])
                d2 = json.loads(pares[1][0])
                difs = [u"%s: %r x %r" % (k, d1.get(k), d2.get(k))
                        for k in d1 if d1.get(k) != d2.get(k)]
                return (False, u"%d barras diferentes — %s difere em %s"
                        % (len(distintas), ", ".join(fora[:2]), "; ".join(difs[:3])))
            d = json.loads(list(distintas)[0])
            return (True, u"1 barra só nas %d páginas (fundo %s, %dpx, %s)"
                    % (len(paginas), d["bg"], d["h"], d["itens"]))
        s.check("V14", u"a mesma barra superior em 8 páginas de templates diferentes",
                v14)

        # V15 — S-109 (#167): o painel do submenu tem de ter a MESMA altura,
        # qualquer que seja o item. "Sobre nós" media 159px e "Práticas" 129px
        # porque a margem da lista (40px do tema x 6px da S-65) e o padding do
        # link (6px x 2px) nunca foram igualados. Medido com hover real.
        def faz_paineis_iguais(largura):
            def f():
                js_pos = ("(function(i){var a=document.querySelectorAll("
                          "'.header .menu__nav-link')[i];if(!a)return null;"
                          "var r=a.getBoundingClientRect();"
                          "return [Math.round(r.left+r.width/2),"
                          "Math.round(r.top+r.height/2)];})(%d)")
                js_h = ("(function(){var sms=document.querySelectorAll("
                        "'.header .menu__nav-submenu');"
                        "for(var i=0;i<sms.length;i++){"
                        "if(getComputedStyle(sms[i]).display!=='none')"
                        "return Math.round(sms[i].getBoundingClientRect().height);}"
                        "return 0;})()")
                nav.abrir("%s/pt/" % base, largura, 900)
                alturas = {}
                for i, nome in ((0, u"Sobre nós"), (1, u"Práticas")):
                    pos = nav.js(js_pos % i)
                    if not pos:
                        return (False, u"não achei o item %d da barra" % i)
                    nav.hover(pos[0], pos[1])
                    alturas[nome] = nav.js(js_h)
                    nav.hover(10, 800, espera=0.6)   # sai do hover
                if not all(alturas.values()):
                    return (False, u"painel não abriu no hover: %r" % alturas)
                dif = abs(alturas[u"Sobre nós"] - alturas[u"Práticas"])
                return (dif <= 2, u"%dpx: Sobre nós=%dpx, Práticas=%dpx (dif %dpx, "
                        u"tolerância 2)" % (largura, alturas[u"Sobre nós"],
                                            alturas[u"Práticas"], dif))
            return f
        for i, largura in enumerate((1400, 1200), 15):
            s.check("V%02d" % i,
                    u"painéis de submenu com a mesma altura em %dpx" % largura,
                    faz_paineis_iguais(largura))

        # V17 — S-110 (#168): os 4 títulos de seção da home têm de sair IGUAIS do
        # navegador (família, tamanho, peso, cor, alinhamento) e com a mesma
        # animação. Não se lê CSS: lê-se o computado de cada um, na home de fato.
        def v17():
            js = ("(function(){var cls=['home-experience__subtitle',"
                  "'onda18-orbe__titulo','home-leaders__subtitle',"
                  "'certificates__title'];var out=[];"
                  "for(var i=0;i<cls.length;i++){var e=document.querySelector('.'+cls[i]);"
                  "if(!e){out.push({classe:cls[i],erro:'não achei'});continue;}"
                  "var c=getComputedStyle(e);"
                  "out.push({classe:cls[i],tag:e.tagName,"
                  "aos:e.getAttribute('data-aos')||'-',"
                  "assinatura:[c.fontFamily,c.fontSize,c.fontWeight,c.color,"
                  "c.textAlign,c.textTransform].join('|')});}"
                  "return JSON.stringify(out);})()")
            nav.abrir("%s/pt/" % base, 1400, 900)
            v = nav.js(js)
            try:
                dados = json.loads(v)
            except Exception:
                return (False, u"não deu para medir os títulos: %r" % v)
            faltando = [d["classe"] for d in dados if d.get("erro")]
            if faltando:
                return (False, u"título(s) ausente(s): %s" % ", ".join(faltando))
            assinaturas = set(d["assinatura"] for d in dados)
            aos = set(d["aos"] for d in dados)
            tags = set(d["tag"] for d in dados)
            det = []
            if len(assinaturas) > 1:
                det.append(u"%d estilos diferentes: %s"
                           % (len(assinaturas),
                              " x ".join(sorted(assinaturas))[:160]))
            if aos != {"fade-up"}:
                det.append(u"animações diferentes: %s" % sorted(aos))
            if len(tags) > 1:
                det.append(u"níveis de heading diferentes: %s" % sorted(tags))
            if det:
                return (False, u"; ".join(det))
            # e a animação tem de RODAR igual nos quatro: o AOS marca aos-init com
            # opacity 0 antes de entrar na viewport e troca para aos-animate depois.
            # Era exatamente o que faltava no título de Setores (#168).
            js_estado = ("(function(){var cls=['home-experience__subtitle',"
                         "'onda18-orbe__titulo','home-leaders__subtitle',"
                         "'certificates__title'];var o=[];"
                         "for(var i=0;i<cls.length;i++){var e="
                         "document.querySelector('.'+cls[i]);"
                         "o.push((e.className.indexOf('aos-animate')>=0)?'anima':"
                         "((e.className.indexOf('aos-init')>=0)?'init':'sem-aos'));}"
                         "return o.join(',');})()")
            antes = nav.js(js_estado)
            if antes != "init,init,init,init":
                return (False, u"antes de rolar, o AOS não armou os quatro igual: %s"
                        % antes)
            # rola até o fim em passos, para o observer do AOS disparar em todos
            for frac in (0.35, 0.6, 0.85, 1.0):
                nav.js("window.scrollTo(0,document.body.scrollHeight*%s);'ok'" % frac)
                time.sleep(1.2)
            depois = nav.js(js_estado)
            if depois != "anima,anima,anima,anima":
                return (False, u"depois de rolar, a animação não rodou nos quatro: %s"
                        % depois)
            return (True, u"4 títulos com o mesmo estilo (%s), o mesmo nível (%s) e a "
                    u"mesma animação — os quatro saem de opacity 0 e animam ao rolar"
                    % (list(assinaturas)[0].split("|")[1], list(tags)[0]))
        s.check("V17", u"os 4 títulos da home saem idênticos e animam igual", v17)

        # V18 — S-114 (#172) e S-115 (#173): o mapa tem de PREENCHER o palco (o da
        # Europa sobrava faixa vazia) e o chip do logo tem de ser o tamanho novo.
        # Medido no render: proporção do SVG contra a do palco e caixa do chip.
        def v18():
            nav.abrir("%s/pt/sobre-nos/nossa-rede/" % base, 1400, 900)
            js = ("(function(){var out={mapas:[],chips:[]};"
                  "var ps=document.querySelectorAll('.onda31-mapa__palco');"
                  "for(var i=0;i<ps.length;i++){var pal=ps[i].getBoundingClientRect();"
                  "var img=ps[i].querySelector('.onda31-mapa__svg');"
                  "var r=img.getBoundingClientRect();"
                  "out.mapas.push({palco:[Math.round(pal.width),Math.round(pal.height)],"
                  "mapa:[Math.round(r.width),Math.round(r.height)],"
                  "cobre:Math.round(100*(r.width*r.height)/(pal.width*pal.height))});}"
                  "var cs=document.querySelectorAll('.onda31-pin__chip');"
                  "for(var j=0;j<cs.length;j++){var c=cs[j].getBoundingClientRect();"
                  "var im=cs[j].querySelector('img').getBoundingClientRect();"
                  "out.chips.push({chip:[Math.round(c.width),Math.round(c.height)],"
                  "logo:Math.round(im.height)});}"
                  "return JSON.stringify(out);})()")
            v = nav.js(js)
            try:
                d = json.loads(v)
            except Exception:
                return (False, u"não deu para medir a rede: %r" % v)
            det = []
            if len(d["mapas"]) != 2:
                det.append(u"%d palco(s) de mapa (esperado 2)" % len(d["mapas"]))
            for i, m in enumerate(d["mapas"]):
                if m["cobre"] < 95:
                    det.append(u"mapa %d cobre só %d%% do palco (S-114 pede ~100%%)"
                               % (i + 1, m["cobre"]))
            if len(d["chips"]) != 6:
                det.append(u"%d chip(s) de parceiro (esperado 6)" % len(d["chips"]))
            baixos = [c for c in d["chips"] if c["logo"] < 24]
            if baixos:
                det.append(u"%d chip(s) com logo abaixo de 24px (S-115 pede 26px)"
                           % len(baixos))
            estreitos = [c for c in d["chips"] if c["chip"][0] < 46]
            if estreitos:
                det.append(u"%d chip(s) mais estreito(s) que 46px" % len(estreitos))
            if det:
                return (False, u"; ".join(det[:3]))
            return (True, u"2 mapas cobrindo %s do palco; 6 chips (logo de %dpx, "
                    u"largura %s)"
                    % ("/".join("%d%%" % m["cobre"] for m in d["mapas"]),
                       d["chips"][0]["logo"],
                       "-".join(str(min(c["chip"][0] for c in d["chips"]))
                                for _ in [0]) + ".."
                       + str(max(c["chip"][0] for c in d["chips"]))))
        s.check("V18", u"mapas preenchendo o palco e chips no tamanho novo", v18)

        # V19 — S-116 (#174) ao vivo: o ponto de cada pin cai DENTRO do mapa e a
        # agulha fica visível no palco. A conferência da coordenada em si é a S116
        # (recalcula a projeção); aqui se prova que nada escapou da caixa.
        def v19():
            nav.abrir("%s/pt/sobre-nos/nossa-rede/" % base, 1400, 900)
            js = ("(function(){var out=[];"
                  "var ps=document.querySelectorAll('.onda31-mapa__palco');"
                  "for(var i=0;i<ps.length;i++){var pal=ps[i].getBoundingClientRect();"
                  "var ag=ps[i].querySelectorAll('.onda31-pin__agulha');"
                  "for(var j=0;j<ag.length;j++){var r=ag[j].getBoundingClientRect();"
                  "var nome=ag[j].parentElement.querySelector('.onda31-pin__nome');"
                  "out.push({nome:nome?nome.textContent:'?',"
                  "dentro:(r.left>=pal.left-2&&r.right<=pal.right+2&&"
                  "r.top>=pal.top-2&&r.bottom<=pal.bottom+2),"
                  "visivel:r.width>0&&r.height>0});}}"
                  "return JSON.stringify(out);})()")
            v = nav.js(js)
            try:
                d = json.loads(v)
            except Exception:
                return (False, u"não deu para medir os pins: %r" % v)
            if len(d) != 6:
                return (False, u"%d agulha(s) de pin no palco (esperado 6)" % len(d))
            fora = [x["nome"] for x in d if not x["dentro"]]
            invisivel = [x["nome"] for x in d if not x["visivel"]]
            if fora:
                return (False, u"pin(s) fora do mapa: %s" % ", ".join(fora))
            if invisivel:
                return (False, u"pin(s) sem marca visível: %s" % ", ".join(invisivel))
            return (True, u"6 pins com o ponto dentro do mapa e visível")
        s.check("V19", u"os 6 pins marcam um ponto dentro do mapa", v19)

        # V20 — S-117 (#175): o chip do logo tem de ficar PERTO do seu ponto e
        # nenhum par pode se sobrepor. Antes do layout em anel, o chip do Batten
        # subia três degraus e ia parar longe da Alemanha (o Mario viu a olho).
        def v20():
            nav.abrir("%s/pt/sobre-nos/nossa-rede/" % base, 1400, 900)
            js = ("(function(){var out=[];"
                  "var ps=document.querySelectorAll('.onda31-mapa__palco');"
                  "for(var i=0;i<ps.length;i++){var pal=ps[i].getBoundingClientRect();"
                  "var pins=ps[i].querySelectorAll('.onda31-pin');"
                  "for(var j=0;j<pins.length;j++){"
                  "var ag=pins[j].querySelector('.onda31-pin__agulha')"
                  ".getBoundingClientRect();"
                  "var ch=pins[j].querySelector('.onda31-pin__chip')"
                  ".getBoundingClientRect();"
                  "var nome=pins[j].querySelector('.onda31-pin__nome');"
                  "out.push({mapa:i,nome:nome?nome.textContent:'?',"
                  "larguraPalco:Math.round(pal.width),"
                  "dist:Math.round(Math.hypot((ch.left+ch.width/2)-(ag.left+ag.width/2),"
                  "(ch.top+ch.height/2)-(ag.top+ag.height/2))),"
                  "caixa:[ch.left,ch.top,ch.right,ch.bottom],"
                  "dentro:(ch.left>=pal.left-1&&ch.right<=pal.right+1&&"
                  "ch.top>=pal.top-1&&ch.bottom<=pal.bottom+1)});}}"
                  "return JSON.stringify(out);})()")
            v = nav.js(js)
            try:
                d = json.loads(v)
            except Exception:
                return (False, u"não deu para medir os chips: %r" % v)
            if len(d) != 6:
                return (False, u"%d chip(s) medido(s) (esperado 6)" % len(d))
            det = []
            # a distância é medida no palco real e normalizada para o palco de
            # referência do gerador (580px), onde o limite RAIO_MAX foi definido
            limite = 96.0 + 42.0 / 2 + 6      # RAIO_MAX + meia altura do chip + folga
            for c in d:
                fator = 580.0 / max(c["larguraPalco"], 1)
                dist_ref = c["dist"] * fator
                if dist_ref > limite:
                    det.append(u"%s a %.0fpx do seu ponto (limite %.0f)"
                               % (c["nome"], dist_ref, limite))
                if not c["dentro"]:
                    det.append(u"%s com o chip fora do mapa" % c["nome"])
            for i in range(len(d)):
                for j in range(i + 1, len(d)):
                    if d[i]["mapa"] != d[j]["mapa"]:
                        continue
                    a, b = d[i]["caixa"], d[j]["caixa"]
                    if not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3]):
                        det.append(u"%s e %s se sobrepõem"
                                   % (d[i]["nome"], d[j]["nome"]))
            if det:
                return (False, u"; ".join(det[:3]))
            longe = max(c["dist"] * (580.0 / max(c["larguraPalco"], 1)) for c in d)
            return (True, u"6 chips sem sobreposição, o mais distante a %.0fpx do seu "
                    u"ponto (limite %.0f)" % (longe, limite))
        s.check("V20", u"chip do logo perto do seu ponto e sem sobrepor vizinho", v20)

        # V21 — S-126 (#179): os big numbers do hero saem SEM bold. Mede o peso
        # COMPUTADO nas 4 homes, não o declarado: era exatamente aí que o bug morava
        # (o CSS dizia 800, o navegador desenhava 900, porque 800 não é carregado).
        # A causa-raiz — peso declarado fora do conjunto carregado — é a S127.
        def v21():
            js = ("(function(){var e=document.querySelectorAll('.hero-numeros__valor');"
                  "var out=[];for(var i=0;i<e.length;i++){var c=getComputedStyle(e[i]);"
                  "out.push({txt:e[i].textContent.trim(),peso:c.fontWeight,"
                  "tam:c.fontSize,cor:c.color});}"
                  "return JSON.stringify(out);})()")
            det = []
            for rel in HOMES:
                nav.abrir("%s/%s" % (base, rel.replace("index.html", "")), 1400, 900)
                try:
                    dados = json.loads(nav.js(js))
                except Exception as e:
                    det.append(u"%s: não deu para medir (%r)" % (rel, e))
                    continue
                if len(dados) != 4:
                    det.append(u"%s tem %d big numbers, esperado 4" % (rel, len(dados)))
                for d in dados:
                    if d["peso"] != "400":
                        det.append(u"%s: %s em peso %s (esperado 400)"
                                   % (rel, d["txt"], d["peso"]))
                    # o pedido foi sobre PESO — tamanho e cor não podem ter mudado
                    if d["cor"] != "rgb(0, 173, 236)":
                        det.append(u"%s: %s mudou de cor para %s"
                                   % (rel, d["txt"], d["cor"]))
            return (not det, u"%d problema(s): %s" % (len(det), "; ".join(det[:4])))
        s.check("V21", u"big numbers do hero sem bold, nas 4 homes (#179)", v21)

        # V22 — S-127 (#180): o "m" sólido e na frente NÃO pode cobrir texto.
        # Enquanto era translúcido e ficava atrás, sobrepor era inofensivo. Opaco e em
        # z-index 10, qualquer sobreposição APAGA o que está embaixo — medido: com
        # 300px fixos ele comia 200px de "Focamos em estratégia, compras e
        # go-to-market..." em 992px. Aqui se medem as caixas TIGHT de cada linha de
        # texto (Range.getClientRects, não a caixa do elemento) contra o retângulo do
        # logo, em 9 larguras. É o P2.1 em ação: mede o efeito, não a declaração.
        def v22():
            js = ("(function(){var lg=document.querySelector('.hero-logo-m');"
                  "if(!lg) return JSON.stringify({erro:'logo nao existe'});"
                  "var cs=getComputedStyle(lg);"
                  "if(cs.display==='none') return JSON.stringify({oculto:true});"
                  "var L=lg.getBoundingClientRect();"
                  "var pc=getComputedStyle(lg.querySelector('path'));"
                  "var hero=document.querySelector('.banner');"
                  "var it=document.createTreeWalker(hero,NodeFilter.SHOW_TEXT,null);"
                  "var n,out=[];"
                  "while(n=it.nextNode()){if(!n.nodeValue.trim())continue;"
                  "var r=document.createRange();r.selectNodeContents(n);"
                  "var rc=r.getClientRects();"
                  "for(var i=0;i<rc.length;i++){var b=rc[i];"
                  "if(!b.width||!b.height)continue;"
                  "var ox=Math.min(L.right,b.right)-Math.max(L.left,b.left);"
                  "var oy=Math.min(L.bottom,b.bottom)-Math.max(L.top,b.top);"
                  "if(ox>0&&oy>0)out.push(n.nodeValue.trim().slice(0,30)+' '"
                  "+Math.round(ox)+'x'+Math.round(oy));}}"
                  "var t=document.querySelector('.hero-texto');"
                  "var nn=document.querySelector('.hero-numeros');"
                  "var fe=null,fd=null;"
                  "if(t&&nn){var rt=t.getBoundingClientRect(),rn=nn.getBoundingClientRect();"
                  "fe=Math.round(L.left-rt.right);fd=Math.round(rn.left-L.right);}"
                  "return JSON.stringify({larg:Math.round(L.width),z:cs.zIndex,"
                  "op:cs.opacity,fill:pc.fill,colisoes:out,fe:fe,fd:fd});})()")
            det = []
            visto = 0
            for w, h in [(2560, 1200), (1920, 1000), (1600, 900), (1400, 900),
                         (1200, 900), (992, 900), (768, 900), (390, 844), (320, 700)]:
                nav.abrir("%s/pt/" % base, w, h)
                try:
                    d = json.loads(nav.js(js))
                except Exception as e:
                    det.append(u"%dpx: não deu para medir (%r)" % (w, e))
                    continue
                if d.get("erro"):
                    det.append(u"%dpx: %s" % (w, d["erro"]))
                    continue
                if d.get("oculto"):
                    continue          # oculto é resposta legítima: não cabe no vão
                visto += 1
                if d["colisoes"]:
                    det.append(u"%dpx cobre texto: %s"
                               % (w, "; ".join(d["colisoes"][:2])))
                if d["op"] != "1":
                    det.append(u"%dpx: opacidade %s (o pedido foi sólido)"
                               % (w, d["op"]))
                if d["fill"].replace(" ", "") != "rgb(255,255,255)":
                    det.append(u"%dpx: fill %s (esperado branco puro)"
                               % (w, d["fill"]))
                if not d["z"].isdigit() or int(d["z"]) <= 4:
                    det.append(u"%dpx: z-index %s não fica na frente dos cards"
                               % (w, d["z"]))
                # onda 38: o M não pode ENCOSTAR nos cards. Com a regra antiga
                # (vão - 16) ele ficava a 10px de cada um em 1400px, e o Mario pediu
                # que respirasse. 24px é o piso; a regra real é a fração de 0,6 do
                # vão, que na prática dá 64px em 1400 e 260px em 1920.
                FOLGA_MIN = 24
                for lado, v in (("esquerda", d.get("fe")), ("direita", d.get("fd"))):
                    if v is None:
                        continue
                    if v < FOLGA_MIN:
                        det.append(u"%dpx: só %dpx de folga do card da %s "
                                   u"(mínimo %dpx)" % (w, v, lado, FOLGA_MIN))
            if not visto:
                det.append(u"o logo não apareceu em NENHUMA largura")
            return (not det, u"%d problema(s): %s" % (len(det), "; ".join(det[:3])))
        s.check("V22", u'o "m" sólido na frente não cobre texto em nenhuma largura (#180)',
                v22)

        # V23 — S-130 (#183): as 4 pílulas de contato em 2 fileiras de 2, e o card dos
        # números sem sobra grande. As duas coisas se medem pelo RENDER, não pelo CSS:
        # as fileiras dependem de onde o grid quebra, e a "sobra" só existe comparando
        # a largura do conteúdo com a LINHA MAIS LARGA de fato desenhada.
        # Antes desta onda as pílulas caíam 3+1 em pt/en e 2+2 em de/ — o alemão
        # acertava por acidente, porque os rótulos dele são mais longos.
        def v23():
            js = ("(function(){var ps=[].slice.call("
                  "document.querySelectorAll('.hero-contatos__link'));"
                  "if(!ps.length) return JSON.stringify({erro:'sem pilulas'});"
                  "var f={};ps.forEach(function(p){"
                  "var t=Math.round(p.getBoundingClientRect().top);f[t]=(f[t]||0)+1;});"
                  "var fil=Object.keys(f).sort(function(a,b){return a-b;})"
                  ".map(function(k){return f[k];});"
                  "var n=document.querySelector('.hero-numeros');var sobra=null;"
                  "if(n&&getComputedStyle(n).display!=='none'){"
                  "var cs=getComputedStyle(n),rn=n.getBoundingClientRect(),mx=0;"
                  "n.querySelectorAll('.hero-numeros__texto').forEach(function(e){"
                  "var r=document.createRange();r.selectNodeContents(e);"
                  "var rc=r.getClientRects();"
                  "for(var i=0;i<rc.length;i++) if(rc[i].width>mx) mx=rc[i].width;});"
                  "sobra=Math.round(rn.width-parseFloat(cs.paddingLeft)"
                  "-parseFloat(cs.paddingRight)-mx);}"
                  "var g1=null,g2=null;"
                  "if(ps.length===4){"
                  "g1=Math.round(ps[1].getBoundingClientRect().left"
                  "-ps[0].getBoundingClientRect().right);"
                  "g2=Math.round(ps[3].getBoundingClientRect().left"
                  "-ps[2].getBoundingClientRect().right);}"
                  "return JSON.stringify({fileiras:fil,total:ps.length,sobra:sobra,"
                  "gap1:g1,gap2:g2});})()")
            det = []
            for rel in HOMES:
                for w, h in [(1920, 1000), (1400, 900), (1200, 900)]:
                    nav.abrir("%s/%s" % (base, rel.replace("index.html", "")), w, h)
                    try:
                        d = json.loads(nav.js(js))
                    except Exception as e:
                        det.append(u"%s @%d: não deu para medir (%r)" % (rel, w, e))
                        continue
                    if d.get("erro"):
                        det.append(u"%s @%d: %s" % (rel, w, d["erro"]))
                        continue
                    if d["total"] != 4:
                        det.append(u"%s @%d: %d pílulas, esperado 4"
                                   % (rel, w, d["total"]))
                    if d["fileiras"] != [2, 2]:
                        det.append(u"%s @%dpx: pílulas em %s, esperado [2, 2]"
                                   % (rel, w, d["fileiras"]))
                    # o alemão precisa de card mais largo (legenda longa), então a
                    # folga dele é naturalmente menor; o teto de 30px vale para todos.
                    if d["sobra"] is not None and d["sobra"] > 30:
                        det.append(u"%s @%dpx: %dpx de sobra no card dos números "
                                   u"(máximo 30px)" % (rel, w, d["sobra"]))
                    # onda 40 (#184): o Instagram fica a UM GAP do LinkedIn, não
                    # alinhado ao E-mail. O grid da onda 39 dava 2+2 mas as colunas
                    # compartilhavam largura, e o Instagram começava na borda da
                    # coluna do "Falar no WhatsApp" — longe do vizinho. Aqui se
                    # compara o gap da 2ª fileira com o da 1ª: se o layout voltar a
                    # ser em colunas, o segundo cresce e isto acusa.
                    if d.get("gap1") is not None and d.get("gap2") is not None:
                        if abs(d["gap2"] - d["gap1"]) > 4:
                            det.append(
                                u"%s @%dpx: gap LinkedIn-Instagram %dpx vs "
                                u"WhatsApp-E-mail %dpx - o Instagram descolou do "
                                u"vizinho" % (rel, w, d["gap2"], d["gap1"]))
            return (not det, u"%d problema(s): %s" % (len(det), "; ".join(det[:3])))
        s.check("V23", u"pílulas 2+2 com Instagram junto do LinkedIn, e card justo (#183/#184)",
                v23)

        # V24 — onda 41 (#187): as fotos dos Insights sem o apagado. O bug era
        # brightness(0.38) na foto inteira (S-56); agora a foto fica quase plena
        # e a legibilidade vem do scrim ::after. Mede o COMPUTADO da foto e a
        # existência do scrim — não o texto do CSS (P2.1).
        def v24():
            nav.abrir("%s/pt/insights/" % base, 1400, 900)
            d = nav.js(
                "(function(){var img=document.querySelector('.page-insights__list-image');"
                "if(!img)return 'sem card de insight';"
                "var cs=getComputedStyle(img),ca=getComputedStyle(img,'::after');"
                "var m=cs.filter.match(/brightness\\(([\\d.]+)\\)/);"
                "return {b:m?parseFloat(m[1]):null,pos:cs.position,"
                "scrim:ca.backgroundImage.indexOf('gradient')>=0&&ca.content!=='none'};})()")
            if isinstance(d, str):
                return (False, d)
            det = []
            # onda 42 (#193): cor plena — brightness 1.0 em repouso
            if d["b"] is None or not (0.98 <= d["b"] <= 1.0):
                det.append(u"brightness computado %s (esperado 1.0)" % d["b"])
            if not d["scrim"]:
                det.append(u"scrim ::after ausente")
            if d["pos"] != "relative":
                det.append(u"imagem sem position:relative (scrim solto)")
            return (not det, u"; ".join(det))
        s.check("V24", u"fotos dos Insights quase plenas, com scrim de legibilidade (#187)",
                v24)

        # V25 — onda 41 (#189): o título "Nossos Líderes" visível em TODA
        # largura, nas 3 homes. O tema o escondia de 320 a 991px (medido) e a
        # correção devolve o display na faixa toda — o teste cobre as duas
        # bordas da faixa e o desktop (P2.1: o escopo do teste cobre o título).
        def v25():
            det = []
            for rel in HOMES:
                url = "%s/%s" % (base, rel.replace("index.html", ""))
                for w in (390, 900, 1400):
                    nav.abrir(url, w, 900)
                    d = nav.js(
                        "(function(){var t=document.querySelector('.home-leaders__subtitle');"
                        "if(!t)return 'sem titulo';var cs=getComputedStyle(t);"
                        "return {d:cs.display,h:Math.round(t.getBoundingClientRect().height)};})()")
                    if isinstance(d, str):
                        det.append(u"%s @%d: %s" % (rel, w, d))
                    elif d["d"] == "none" or d["h"] < 10:
                        det.append(u"%s @%d: display %s, altura %dpx"
                                   % (rel, w, d["d"], d["h"]))
            return (not det, u"%d problema(s): %s" % (len(det), "; ".join(det[:4])))
        s.check("V25", u'título "Nossos Líderes" visível em 390/900/1400 nas 3 homes (#189)',
                v25)

        # V26 — onda 41 (#190): o logo do veículo é GRANDE de fato e carrega.
        # Rola a página inteira (os logos são lazy), exige toda imagem completa
        # com naturalWidth>0, o primeiro logo com >=90px renderizados, e a linha
        # inteira clicável (o grid mora no <a>, S-102).
        def v26():
            # Onda 65: a contagem deixa de ser o "10" hardcoded e passa a vir do
            # mestre (tools/imprensa-publicada.json). Valor gêmeo: com o 10 fixo, a
            # asserção continuaria verde se o gerador emitisse 12 dos 43 itens.
            # Também passa a exigir que os wordmarks de TEXTO (veículo sem asset —
            # hoje epbr, CZ Insights, Money Times e Revista Amazônia) rendereizem
            # com tinta: um <span> vazio ou de altura 0 é logo invisível, e era
            # invisível também para a versão anterior desta asserção.
            esperado_img = esperado_txt = None
            _p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "imprensa-publicada.json")
            if os.path.exists(_p):
                with io.open(_p, encoding="utf-8") as _f:
                    _lista = json.load(_f)
                esperado_img = sum(1 for m in _lista if m["logo"])
                esperado_txt = len(_lista) - esperado_img
            det = []
            for rel in ["pt/imprensa/", "en/press/", "de/presse/"]:
                nav.abrir("%s/%s" % (base, rel), 1400, 900)
                nav.js("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1.2)
                d = nav.js(
                    "(function(){var ruins=[],imgs=document.querySelectorAll('img.onda41-imprensa__logo');"
                    "imgs.forEach(function(i){if(!(i.complete&&i.naturalWidth>0))ruins.push(i.src.split('/').pop());});"
                    "var pequenos=0;imgs.forEach(function(i){var r=i.getBoundingClientRect();"
                    "if(r.width>0&&r.width<90&&r.height<36)pequenos++;});"
                    "var maior=0;imgs.forEach(function(i){maior=Math.max(maior,i.getBoundingClientRect().width);});"
                    "var link=document.querySelector('a.onda26-imprensa__link');"
                    "var lw=link?Math.round(link.getBoundingClientRect().width):0;"
                    "var txts=document.querySelectorAll('span.onda41-imprensa__logo--texto');"
                    "var txtRuins=[];txts.forEach(function(t){var r=t.getBoundingClientRect();"
                    "if(r.width<40||r.height<10||!t.textContent.trim())"
                    "txtRuins.push(t.textContent.trim()||'(vazio)');});"
                    "return {ruins:ruins,imgs:imgs.length,pequenos:pequenos,maior:Math.round(maior),lw:lw,"
                    "txts:txts.length,txtRuins:txtRuins,"
                    "ov:document.documentElement.scrollWidth-document.documentElement.clientWidth};})()")
                if isinstance(d, str):
                    det.append(u"%s: %s" % (rel, d))
                    continue
                if d["ruins"]:
                    det.append(u"%s: logo(s) quebrado(s): %s" % (rel, d["ruins"][:3]))
                # onda 65: a contagem vem do mestre, nao de um 10 hardcoded
                if esperado_img is None:
                    det.append(u"falta tools/imprensa-publicada.json")
                else:
                    if d["imgs"] != esperado_img:
                        det.append(u"%s: %d imagens de logo, o mestre manda %d"
                                   % (rel, d["imgs"], esperado_img))
                    if d["txts"] != esperado_txt:
                        det.append(u"%s: %d wordmark(s) de texto, o mestre manda %d"
                                   % (rel, d["txts"], esperado_txt))
                if d["txtRuins"]:
                    det.append(u"%s: wordmark de texto sem tinta: %s"
                               % (rel, d["txtRuins"][:3]))
                # "grande": todo logo tem >=90px de largura OU >=36px de altura
                # (os quadrados como iG e E&N são altos; os wordmarks, largos —
                # o favicon antigo era 28x28 e falha nos dois critérios), e o
                # maior logo da página é >=140px (há wordmark de verdade).
                if d["pequenos"] > 0:
                    det.append(u"%s: %d logo(s) no tamanho de favicon" % (rel, d["pequenos"]))
                if d["maior"] < 140:
                    det.append(u"%s: maior logo com %dpx (esperado >=140)" % (rel, d["maior"]))
                if d["lw"] < 900:
                    det.append(u"%s: linha clicável com %dpx" % (rel, d["lw"]))
                if d["ov"] > 0:
                    det.append(u"%s: overflow-x de %dpx" % (rel, d["ov"]))
            return (not det, u"%d problema(s): %s" % (len(det), "; ".join(det[:4])))
        s.check("V26", u"imprensa: logos grandes carregando nas 3 línguas, sem overflow (#190)",
                v26)

        # V27 — onda 42 (#191): a barra superior fica no topo DURANTE o scroll.
        # Mede o comportamento, não a declaração: rola 1500px e exige a barra
        # colada no topo do viewport, com fundo navy sólido e acima do conteúdo.
        # Cobre home e uma interna (templates diferentes) em desktop e mobile.
        def v27():
            det = []
            for rel, w in [("pt/", 1400), ("pt/", 390),
                           ("pt/imprensa/", 1400), ("de/", 1400)]:
                nav.abrir("%s/%s" % (base, rel), w, 900)
                d = nav.js(
                    "(function(){var h=document.querySelector('.header');"
                    "if(!h)return 'sem .header';"
                    "window.scrollTo(0,1500);"
                    "var r=h.getBoundingClientRect(),cs=getComputedStyle(h);"
                    "var m=document.querySelector('.header nav.menu');"
                    "var bg=m?getComputedStyle(m).backgroundColor:'';"
                    "return {pos:cs.position,top:Math.round(r.top),op:parseFloat(cs.opacity),"
                    "pe:cs.pointerEvents,z:parseInt(cs.zIndex)||0,bg:bg};})()")
                if isinstance(d, str):
                    det.append(u"%s @%d: %s" % (rel, w, d))
                    continue
                # FIXED, não sticky: o tema desenha o header fora do fluxo
                # (absolute sobre o hero); sticky o poria no fluxo e empurraria
                # a dobra em 98px. E o JS de scroll do tema o esconde
                # (opacity:0) — a barra tem que seguir visível E clicável.
                if d["pos"] != "fixed" or d["top"] != 0:
                    det.append(u"%s @%d: %s, top %dpx após scroll"
                               % (rel, w, d["pos"], d["top"]))
                if d["op"] < 0.99 or d["pe"] == "none":
                    det.append(u"%s @%d: opacity %s / pointer-events %s"
                               % (rel, w, d["op"], d["pe"]))
                if d["z"] < 50:
                    det.append(u"%s @%d: z-index %d (conteúdo pode cobrir)"
                               % (rel, w, d["z"]))
            return (not det, u"; ".join(det[:4]))
        s.check("V27", u"barra superior colada no topo após rolar, em 4 cenários (#191)",
                v27)

        # V28 — onda 43 (#198). "Texto em nossas áreas de expertise e setores
        # em que atuamos está pequeno demais - precisa ser do mesmo tamanho de
        # 'Focamos em estratégia...'" (Mario, 10/08). Sem valor gêmeo: mede o
        # subtítulo do hero E os textos das duas seções na MESMA página e
        # compara os computados — se o hero mudar, a régua acompanha.
        def v28():
            det = []
            for rel in ["pt/", "en/", "de/"]:
                nav.abrir("%s/%s" % (base, rel), 1400, 900)
                d = nav.js(
                    "(function(){function fs(sel){var e=document.querySelector(sel);"
                    "return e?parseFloat(getComputedStyle(e).fontSize):null;}"
                    "return {hero:fs('.hero-texto p'),"
                    "exp_p:fs('.praticas-3__card .home-experience__list-item-content p'),"
                    "exp_more:fs('.praticas-3__card .home-experience__list-item-more'),"
                    "set_nome:fs('.onda18-const__nome'),"
                    "set_item:fs('.onda18-const__item')};})()")
                if isinstance(d, str) or d.get("hero") is None:
                    det.append(u"%s: não mediu o subtítulo do hero" % rel)
                    continue
                for chave in ("exp_p", "exp_more", "set_nome", "set_item"):
                    if d[chave] is None:
                        det.append(u"%s: %s não encontrado" % (rel, chave))
                    elif abs(d[chave] - d["hero"]) > 0.5:
                        det.append(u"%s: %s em %spx, hero em %spx"
                                   % (rel, chave, d[chave], d["hero"]))
            return (not det, u"; ".join(det[:5]))
        s.check("V28", u"textos de expertise e setores no tamanho do subtítulo do hero, 3 homes (#198)",
                v28)

        # V30 — onda 53 (#211). Mede o EFEITO dos 3 pedidos do Mario, não o
        # HTML (isso é da S147): o selo tem de estar À DIREITA do slogan e na
        # mesma faixa vertical; a faixa de IA tem de ATRAVESSAR as 3 colunas e
        # ficar abaixo delas; e o subtítulo mais longo não pode voltar a
        # estourar a primeira dobra — foi o que ele quebrou ao entrar (4 linhas
        # em 580px, 56px de sobra) e o que o alargamento p/ 640px consertou.
        def v30():
            det = []
            js = """(function(){
              var s=document.querySelector('.onda53-selo-ia');
              var h2=document.querySelector('.hero-texto h2');
              var ia=document.querySelector('.onda53-ia');
              var cards=[].slice.call(document.querySelectorAll('.praticas-3__card'));
              var f=document.querySelector('.clientes-logos');
              if(!s||!h2||!ia||!cards.length||!f) return 'faltou elemento no DOM';
              var r=function(e){return e.getBoundingClientRect()};
              var rs=r(s), rh=r(h2), ri=r(ia);
              var esq=r(cards[0]).left, dir=r(cards[cards.length-1]).right;
              var baixo=Math.max.apply(null,cards.map(function(c){return r(c).bottom}));
              return {acima: rs.bottom<=rh.top+2 && rs.left<=rh.left+4,
                      seloVisivel: rs.width>0 && rs.height>0,
                      atravessa: Math.round(ri.width) >= Math.round(dir-esq)-2,
                      abaixo: ri.top >= baixo-2,
                      sobra: Math.round(r(f).bottom)-window.innerHeight,
                      overflowX: document.documentElement.scrollWidth-document.documentElement.clientWidth};
            })()"""
            for rel in ("pt/index.html", "en/index.html", "de/index.html"):
                for larg in (1920, 1400, 1200):
                    nav.abrir("%s/%s" % (base, rel.replace("index.html", "")), larg, 900)
                    d = nav.js(js)
                    if isinstance(d, str):
                        det.append(u"%s @%d: %s" % (rel, larg, d))
                        continue
                    if not d.get("seloVisivel"):
                        det.append(u"%s @%d: selo invisível" % (rel, larg))
                    if not d.get("acima"):
                        det.append(u"%s @%d: selo não está ACIMA do slogan, alinhado à esquerda"
                                   % (rel, larg))
                    if not d.get("atravessa"):
                        det.append(u"%s @%d: faixa de IA não atravessa as 3 práticas" % (rel, larg))
                    if not d.get("abaixo"):
                        det.append(u"%s @%d: faixa de IA não está abaixo dos cards" % (rel, larg))
                    if abs(d.get("sobra", 99)) > 4:
                        det.append(u"%s @%d: subtítulo estourou a dobra (sobra %dpx)"
                                   % (rel, larg, d["sobra"]))
                    if d.get("overflowX", 0) > 0:
                        det.append(u"%s @%d: overflow-x de %dpx" % (rel, larg, d["overflowX"]))
            return (not det, u"; ".join(det[:4]))
        s.check("V30", u"selo AI Powered acima do slogan e IA transversal, sem estourar a dobra (#211)",
                v30)

        # V31 — #221: "dessa pagina, retirar qualquer full stop nos textos".
        # Mede o TEXTO RENDERIZADO (nao a string do HTML): percorre os nos de
        # texto das 3 homes e exige que nenhum termine em ponto. A UNICA excecao
        # e a marca "Mirow & Co." — ali o ponto e nome, nao pontuacao (R4).
        # Cobre tambem o que esta escondido em modal, que so aparece no clique.
        def v31():
            js = """(function(){
              var out=[], w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT), n;
              while(n=w.nextNode()){
                var t=(n.textContent||'').trim();
                if(t.length<8 || t.charAt(t.length-1)!=='.') continue;
                var p=n.parentElement; if(!p) continue;
                if(['SCRIPT','STYLE','NOSCRIPT'].indexOf(p.tagName)>=0) continue;
                if(/Mirow\\s*&\\s*Co\\.$/.test(t)) continue;   // a marca fica
                out.push(t.slice(-52));
              }
              return out;})()"""
            det = []
            for rel in ("pt/index.html", "en/index.html", "de/index.html"):
                nav.abrir("%s/%s" % (base, rel.replace("index.html", "")), 1400, 900)
                r = nav.js(js)
                if isinstance(r, str):
                    det.append(u"%s: %s" % (rel, r))
                elif r:
                    det.append(u"%s: %d texto(s) com ponto final — \"…%s\""
                               % (rel, len(r), r[0]))
            return (not det, u"; ".join(det[:3]))
        s.check("V31", u"nenhum texto da home termina em ponto final, exceto a marca (#221)", v31)

        # V32 — #223: o Mario viu, no celular, "a barra branca mostrando só o &".
        # Não era regressão: a V14 media a barra com o CSS já carregado, e ali ela
        # sempre esteve navy. O que ninguém media era o intervalo ANTES de o CSS
        # externo chegar — no desktop dura milissegundos, num celular em rede móvel
        # dura o bastante para ser visto. O logo tem 8 paths brancos (as letras) e
        # 1 ciano (o "&"): sem fundo navy, sobra o "&".
        #
        # Mede as DUAS situações. A segunda é a que pega o bug: bloqueia o CSS
        # externo no navegador e exige que a barra continue navy pelo <style>
        # inline. Testar só com CSS é o erro de escopo do P2.1.
        def v32():
            det = []
            NAVY = "rgb(2, 14, 102)"
            leitura = ("(function(){var b=document.querySelector('.menu');"
                       "return b?getComputedStyle(b).backgroundColor:'sem barra';})()")
            for pag in ("pt/", "en/homepage/", "de/", "pt/contato/"):
                for larg in (390, 1400):
                    nav.abrir("%s/%s" % (base, pag), largura=larg, altura=844)
                    cor = nav.js(leitura)
                    if cor != NAVY:
                        det.append(u"%s @%d com CSS: barra %s" % (pag, larg, cor))
            # Agora sem o CSS do tema e das ondas.
            nav.ws.call(nav._id(), "Network.enable", {})
            nav.ws.call(nav._id(), "Network.setBlockedURLs",
                        {"urls": ["*onda6.css*", "*style.css*", "*themes*"]})
            try:
                for pag in ("pt/", "de/"):
                    nav.abrir("%s/%s" % (base, pag), largura=390, altura=844)
                    cor = nav.js(leitura)
                    if cor != NAVY:
                        det.append(u"%s @390 SEM css: barra %s — o logo branco some "
                                   u"no flash e sobra só o \"&\"" % (pag, cor))
            finally:
                nav.ws.call(nav._id(), "Network.setBlockedURLs", {"urls": []})
            return (not det, u"; ".join(det[:4]))
        s.check("V32", u"barra navy mesmo ANTES do CSS externo carregar, em 4 páginas (#223)",
                v32)

        # V33 — #225: a política PROMETE que o botão desliga o rastreamento. Uma
        # promessa dessas não pode ser verificada lendo o HTML: tem que clicar e
        # medir que o tracker some. Se um dia o opt-out quebrar, a página passa a
        # mentir para o titular — é o pior tipo de regressão possível aqui.
        def v33():
            det = []
            nav.abrir("%s/pt/politica-de-privacidade/" % base, largura=1400, altura=900)
            if not nav.js("!!document.getElementById('pol-optout')"):
                return (False, u"a política não tem o botão de oposição")
            nav.js("document.getElementById('pol-optout').click()")
            time.sleep(1)
            if nav.js("window.localStorage.getItem('mirow:leadfeeder:optout')") != "1":
                det.append(u"o clique não gravou a escolha")
            # Efeito onde importa: outra página, tracker fora do ar.
            nav.abrir("%s/pt/" % base, largura=1400, altura=900)
            time.sleep(2)
            if nav.js("window.mirowLeadfeederAtivo") is not False:
                det.append(u"o tracker continuou ativo depois do opt-out")
            n = nav.js("performance.getEntriesByType('resource')"
                       ".filter(function(e){return e.name.indexOf('lfeeder')>=0}).length")
            if n:
                det.append(u"%s requisição(ões) ao Leadfeeder mesmo com opt-out" % n)
            # Desfaz, para não contaminar as asserções seguintes.
            nav.js("try{localStorage.removeItem('mirow:leadfeeder:optout')}catch(e){}")
            return (not det, u"; ".join(det[:3]))
        s.check("V33", u"o opt-out da política realmente desliga o Leadfeeder (#225)", v33)

        # V34 — #227: autohospedar só vale se a fonte continuar sendo aplicada.
        # A S138 garante que a referência ao Google sumiu; sozinha, ela passaria
        # com o site inteiro em fonte de sistema. Aqui medimos o RENDER.
        def v34():
            det = []
            for pag in ("pt/", "en/homepage/", "de/", "pt/insights/"):
                nav.abrir("%s/%s" % (base, pag), largura=1400, altura=900)
                time.sleep(1)
                n = nav.js("""(function(){var c=0;var e=document.querySelectorAll('body *');
                  for(var i=0;i<e.length;i++){if(!e[i].offsetParent)continue;
                  var t=(e[i].textContent||'').trim();if(!t||e[i].children.length)continue;
                  if(getComputedStyle(e[i]).fontFamily.indexOf('Titillium')>=0)c++;}
                  return c;})()""")
                if not n or n < 10:
                    det.append(u"%s: só %s elemento(s) em Titillium Web — a fonte local "
                               u"não está sendo aplicada" % (pag, n))
                fora = nav.js("performance.getEntriesByType('resource')"
                              ".filter(function(e){return /fonts\\.(googleapis|gstatic)/"
                              ".test(e.name)}).length")
                if fora:
                    det.append(u"%s: %s requisição(ões) ao Google Fonts em runtime" % (pag, fora))
                locais = nav.js("performance.getEntriesByType('resource')"
                                ".filter(function(e){return /\\.woff2/.test(e.name)}).length")
                if not locais:
                    det.append(u"%s: nenhum woff2 carregado" % pag)
            return (not det, u"; ".join(det[:3]))
        s.check("V34", u"Titillium Web aplicada e servida localmente, 4 páginas (#227)", v34)

        # V35 — #229: nenhum elemento RENDERIZADO pode pedir peso que a fonte não
        # tem. A S127 já cobra isso, mas lendo o NOSSO css — e as 19 declarações
        # órfãs desta onda moravam no css do TEMA, que ela não olha. Por isso esta
        # aqui mede o computado no navegador: pega a classe inteira, não importa
        # em que arquivo a declaração esteja, nem se ela for inline.
        #
        # Por que importa, se o efeito é invisível: quando o CSS pede 500 e a
        # família não tem, o navegador serve o vizinho — e o texto sai num peso
        # que ninguém escolheu. Foi assim que os big numbers do hero saíram em
        # 900/Black na onda 35 sem ninguém ter escrito 900.
        def v35():
            FONTES = "wp-content/uploads/2026/07/fontes/fontes-mirow.css"
            disponiveis = set(int(x) for x in
                              re.findall(r"font-weight:\s*(\d+)", s.ler(FONTES)))
            if not disponiveis:
                return (False, u"não achei os pesos em %s" % FONTES)
            js = ("(function(){var o={},e=document.querySelectorAll('body *');"
                  "for(var i=0;i<e.length;i++){var x=e[i];if(!x.offsetParent)continue;"
                  "var t=(x.textContent||'').trim();if(!t||x.children.length)continue;"
                  "var c=getComputedStyle(x);"
                  "if(c.fontFamily.indexOf('Titillium')<0)continue;"
                  "var w=c.fontWeight;o[w]=(o[w]||0)+1;}return JSON.stringify(o);})()")
            det = []
            for pag in ("pt/", "pt/insights/", "pt/carreiras/", "de/", "en/homepage/"):
                nav.abrir("%s/%s" % (base, pag), largura=1400, altura=900)
                usados = json.loads(nav.js(js) or "{}")
                orfaos = {w: n for w, n in usados.items() if int(w) not in disponiveis}
                if orfaos:
                    det.append(u"%s: %s" % (pag, ", ".join(
                        u"peso %s em %d elemento(s)" % (w, n)
                        for w, n in sorted(orfaos.items()))))
            return (not det, u"%s — a fonte carrega %s"
                    % ("; ".join(det[:3]), sorted(disponiveis)))
        s.check("V35", u"nenhum elemento renderizado pede peso que a fonte não tem (#229)",
                v35)

        def v36():
            # Onda 63 (foto do iPhone do Mario, 19/08): "texto sobre texto, difícil
            # legibilidade". O `.onda53-slogan h2{margin-bottom:-20px}` valia em TODA
            # largura, mas foi calibrado na tinta do desktop (62px/160% ⇒ ~18,6px de
            # entrelinha morta). Abaixo de 992px a fonte cai para 38px/116% ⇒ ~3px de
            # entrelinha morta, e os -20px comiam 27px do parágrafo.
            #
            # Mede a TINTA, não a caixa: `Range.getClientRects()` dá o retângulo real
            # de cada linha de texto — a caixa de linha mente quando o line-height é
            # grande, que é exatamente a armadilha que criou o bug.
            #
            # Cobre 4 larguras e as 3 homes: o escopo do teste tem de cobrir o escopo
            # do título (lição da V07, que prometia "no máximo 2 linhas" medindo só
            # pt/ em 1920 enquanto o alemão quebrava em 3 no ar).
            js = ("(function(){"
                  "var card=document.querySelector('.hero-texto');"
                  "if(!card) return JSON.stringify({erro:'sem .hero-texto'});"
                  "function tinta(el){var mx=null;"
                  "var it=document.createNodeIterator(el,NodeFilter.SHOW_TEXT);var n;"
                  "while((n=it.nextNode())){if(!n.nodeValue.trim())continue;"
                  "var r=document.createRange();r.selectNodeContents(n);"
                  "var rc=r.getClientRects();"
                  "for(var i=0;i<rc.length;i++){if(rc[i].width<1||rc[i].height<1)continue;"
                  "var b={t:rc[i].top,b:rc[i].bottom};"
                  "if(!mx||b.t<mx.t)mx=mx?{t:b.t,b:Math.max(mx.b,b.b)}:b;"
                  "else if(b.b>mx.b)mx.b=b.b;}}"
                  "return mx;}"
                  "var alvos=[['eyebrow','.onda53-selo-ia'],['slogan','h2'],"
                  "['frase','p'],['pilulas','ul']];"
                  "var cx=[];"
                  "for(var i=0;i<alvos.length;i++){"
                  "var e=card.querySelector(alvos[i][1]);if(!e)continue;"
                  "var t=tinta(e);if(!t)continue;"
                  "cx.push({nome:alvos[i][0],t:Math.round(t.t),b:Math.round(t.b)});}"
                  "cx.sort(function(a,b){return a.t-b.t;});"
                  "var col=[];"
                  "for(var j=1;j<cx.length;j++){var folga=cx[j].t-cx[j-1].b;"
                  "if(folga<2) col.push(cx[j-1].nome+'/'+cx[j].nome+' folga '"
                  "+Math.round(folga)+'px');}"
                  "return JSON.stringify({col:col,n:cx.length});})()")
            det = []
            medidos = 0
            for rel in HOMES:
                for larg in (390, 768, 1024, 1400):
                    nav.abrir("%s/%s" % (base, rel), largura=larg, altura=900)
                    bruto = nav.js(js)
                    if not bruto:
                        det.append(u"%s@%d sem retorno" % (rel, larg))
                        continue
                    d = json.loads(bruto)
                    if d.get("erro"):
                        det.append(u"%s@%d %s" % (rel, larg, d["erro"]))
                        continue
                    medidos += 1
                    for c in d.get("col", []):
                        det.append(u"%s@%dpx: %s" % (rel, larg, c))
            return (not det, u"%d combinação(ões) medida(s); %s"
                    % (medidos, u"; ".join(det[:4])
                       or u"nenhum texto do card do hero encosta no vizinho"))
        s.check("V36", u"card do hero sem texto sobre texto, em 4 larguras (onda 63)", v36)

        def v37():
            # Onda 64 (Mario, 19/08): "no mobile, quando clico nas 3 linhas ... depois
            # fecho, a barra volta a ser branca e o mirow fica ilegível".
            #
            # Reproduzido e MEDIDO: a classe `menu--mobile-opened` sai certo ao fechar.
            # Quem pintava era `.header .menu:hover{background:#fff}` — em tela de toque
            # o :hover GRUDA depois do tap e só sai no próximo toque em outro lugar.
            # Logo branco sobre barra branca.
            #
            # Mede os DOIS ramos, porque o conserto não pode custar o hover do desktop:
            #   ponteiro fino  -> hover DEVE embranquecer (comportamento aprovado)
            #   toque          -> hover NÃO pode embranquecer
            #
            # Navegador PRÓPRIO de propósito: `Emulation.setTouchEmulationEnabled` vira
            # a media query e **não volta atrás** na mesma sessão — usar o `nav`
            # compartilhado envenenaria toda asserção V que rodasse depois.
            js = ("(function(){var m=document.querySelector('.header .menu');"
                  "if(!m) return '';var cs=getComputedStyle(m);"
                  "return JSON.stringify({fundo:cs.backgroundColor,"
                  "fino:matchMedia('(hover:hover) and (pointer:fine)').matches,"
                  "aberto:m.classList.contains('menu--mobile-opened')});})()")
            NAVY, BRANCO = "rgb(2, 14, 102)", "rgb(255, 255, 255)"
            det = []
            with Navegador() as n2:
                # 1) ponteiro fino: o hover branco do desktop tem de continuar
                n2.abrir("%s/pt/index.html" % base, largura=1400, altura=900)
                d = json.loads(n2.js(js) or "{}")
                if not d.get("fino"):
                    det.append(u"o navegador de teste não reporta ponteiro fino; "
                               u"ramo do desktop não medido")
                else:
                    n2.hover(700, 40)
                    d = json.loads(n2.js(js) or "{}")
                    if d.get("fundo") != BRANCO:
                        det.append(u"desktop: hover deixou de embranquecer (%s)"
                                   % d.get("fundo"))
                # 2) toque: nem no hover, nem depois de abrir e fechar o menu
                # SÓ setTouchEmulationEnabled: ele vira `(hover:hover)`/`(pointer:fine)`
                # para false, que é o que a regra consulta. NÃO ligar
                # `setEmitTouchEventsForMouse` — com ele o hover vira toque, nenhum
                # estado de hover é produzido, e a asserção passa a medir o vazio
                # (testado: com o bug de volta ela ficava VERDE).
                n2.ws.call(n2._id(), "Emulation.setTouchEmulationEnabled",
                           {"enabled": True, "maxTouchPoints": 5})
                for rel in HOMES:
                    n2.abrir("%s/%s" % (base, rel), largura=390, altura=800, forcar=True)
                    d = json.loads(n2.js(js) or "{}")
                    if d.get("fino"):
                        det.append(u"%s: emulação de toque não pegou" % rel)
                        continue
                    n2.js("var b=document.querySelector('.menu__hamburguer');"
                          "if(b){b.click();b.click();}")
                    n2.hover(60, 30)
                    d = json.loads(n2.js(js) or "{}")
                    if d.get("fundo") != NAVY:
                        det.append(u"%s: barra ficou %s após abrir/fechar o menu"
                                   % (rel, d.get("fundo")))
            return (not det, u"; ".join(det[:3])
                    or u"hover branco só com ponteiro fino; no toque a barra fica navy")
        def v38():
            # #104. A S167 confere o markup; esta mede o EFEITO, que e o criterio
            # de aceite da issue: "buscar 'pricing' retorna resultados reais".
            # Sem isto, a suite ficaria verde com o indice no lugar e a busca sem
            # renderizar nada -- exatamente o P2.1.
            det = []
            for rel, lang, termo in (("pt/insights/", "pt", "pricing"),
                                     ("en/insights/", "en", "pricing"),
                                     ("de/insights/", "de", "pricing")):
                nav.abrir("%s/%s?s=%s" % (base, rel, termo), 1400, 900)
                time.sleep(0.8)
                d = nav.js(
                    "(function(){var c=document.getElementById('onda67-busca-resultados');"
                    "if(!c)return 'sem contentor';"
                    "var its=c.querySelectorAll('.onda67-busca__item');"
                    "var langs=[];its.forEach(function(li){"
                    "langs.push((li.querySelector('a').getAttribute('href')||'/x/').split('/')[1]);});"
                    "var campo=document.querySelector('input[name=s]');"
                    "return JSON.stringify({n:its.length,marcas:c.querySelectorAll('mark').length,"
                    "campo:campo?campo.value:null,idiomas:Array.from(new Set(langs))});})()")
                if isinstance(d, str) and d.startswith("sem"):
                    det.append(u"%s: %s" % (rel, d))
                    continue
                try:
                    d = json.loads(d)
                except (ValueError, TypeError):
                    det.append(u"%s: nao consegui medir" % rel)
                    continue
                if d["n"] < 1:
                    det.append(u"%s: 0 resultado para %r" % (rel, termo))
                if d["marcas"] < 1:
                    det.append(u"%s: resultado sem o termo destacado" % rel)
                if d["campo"] != termo:
                    det.append(u"%s: o campo nao repete o termo buscado (%r)"
                               % (rel, d["campo"]))
                fora = [x for x in d["idiomas"] if x != lang]
                if fora:
                    det.append(u"%s: resultado de outro idioma: %s" % (rel, fora))
            # termo inexistente tem de dizer que nao achou, nao ficar em branco
            nav.abrir("%s/pt/insights/?s=zzzznaoexistexyz" % base, 1400, 900)
            time.sleep(0.8)
            vazio = nav.js(
                "(function(){var c=document.getElementById('onda67-busca-resultados');"
                "var v=c?c.querySelector('.onda67-busca__vazio'):null;"
                "return v?v.textContent.length:0;})()")
            if not vazio:
                det.append(u"termo inexistente nao mostra mensagem de nada encontrado")
            return (not det, u"; ".join(det[:4]) or u"busca responde nas 3 linguas")
        s.check("V38", u"buscar \"pricing\" devolve resultado real nas 3 línguas (#104)", v38)
        def v39():
            # Onda 68. A primeira versao do bloco de IA saiu com titulo navy
            # #020E66 e subtitulo cinza #7F7F7F, porque eu ASSUMI fundo branco --
            # a gramatica visual vinha da lista de imprensa, que e branca. O fundo
            # da pagina de pratica e uma IMAGEM azul, e o texto do proprio tema ali
            # e branco. Navy sobre aquele azul e ilegivel; cinza e pior.
            #
            # Nenhuma assercao de nome de cor pegaria isso: "color:#020E66" e uma
            # declaracao perfeitamente valida. E o getComputedStyle do fundo tambem
            # nao, porque background-image nao devolve cor. So o PIXEL PINTADO
            # revela. Entao esta assercao:
            #   1. fotografa a regiao do bloco,
            #   2. toma a cor de FUNDO como a mais frequente da regiao (o texto
            #      ocupa poucos pixels; o fundo ocupa a maioria),
            #   3. calcula o contraste WCAG entre cada cor de texto e esse fundo,
            #   4. exige >= 4.5:1 -- o piso de texto normal.
            # Mesma familia do pixel vermelho da onda 60b: medir o efeito, nao a
            # declaracao.
            import base64 as _b64

            def _lum(rgb):
                def canal(v):
                    v = v / 255.0
                    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
                return (0.2126 * canal(rgb[0]) + 0.7152 * canal(rgb[1])
                        + 0.0722 * canal(rgb[2]))

            def _contraste(a, b):
                la, lb = _lum(a), _lum(b)
                if la < lb:
                    la, lb = lb, la
                return (la + 0.05) / (lb + 0.05)

            det = []
            for rel in ("pt/pratica/estrategia/", "en/practice/strategy/",
                        "de/branchen/strategie/"):
                nav.abrir("%s/%s" % (base, rel), 1400, 900)
                info = nav.js(
                    "(function(){var b=document.querySelector('.onda68-ia');"
                    "if(!b)return 'sem bloco';"
                    "b.scrollIntoView({block:'start'});"
                    "var r=b.getBoundingClientRect();"
                    "function cor(sel){var e=b.querySelector(sel);"
                    "return e?getComputedStyle(e).color:null;}"
                    "return JSON.stringify({x:Math.round(r.left),y:Math.round(r.top),"
                    "w:Math.round(r.width),h:Math.round(r.height),"
                    "titulo:cor('.onda68-ia__titulo'),sub:cor('.onda68-ia__subtitulo'),"
                    "it:cor('.onda68-ia__item-titulo'),tx:cor('.onda68-ia__item-texto')});})()")
                if isinstance(info, str) and info.startswith("sem"):
                    det.append(u"%s: %s" % (rel, info))
                    continue
                try:
                    d = json.loads(info)
                except (ValueError, TypeError):
                    det.append(u"%s: nao consegui medir a caixa do bloco" % rel)
                    continue
                # o fecho tem fundo proprio (painel claro): fica fora da amostra
                png = nav.recorte(d["x"], max(0, d["y"]), d["w"],
                                  max(40, int(d["h"] * 0.62)))
                dec = _png_rgb(_b64.b64decode(png)) if png else None
                if not dec:
                    det.append(u"%s: nao consegui decodificar o recorte" % rel)
                    continue
                larg, alt, canais, linhas = dec
                freq = {}
                for y in range(0, alt, 2):
                    lin = linhas[y]
                    for x in range(0, larg, 3):
                        o = x * canais
                        k = (lin[o], lin[o + 1], lin[o + 2])
                        freq[k] = freq.get(k, 0) + 1
                fundo = max(freq.items(), key=lambda kv: kv[1])[0]
                for nome, css in (("titulo", d["titulo"]), ("subtitulo", d["sub"]),
                                  ("titulo do item", d["it"]), ("texto", d["tx"])):
                    if not css:
                        det.append(u"%s: sem cor para %s" % (rel, nome))
                        continue
                    m = re.findall(r"[\d.]+", css)
                    if len(m) < 3:
                        continue
                    rgb = tuple(int(float(v)) for v in m[:3])
                    alfa = float(m[3]) if len(m) > 3 else 1.0
                    # cor com alfa: compor sobre o fundo antes de medir (licao da
                    # onda 62c -- RGB debaixo de pixel translucido nao significa nada)
                    if alfa < 1.0:
                        rgb = tuple(int(round(rgb[i] * alfa + fundo[i] * (1 - alfa)))
                                    for i in range(3))
                    c = _contraste(rgb, fundo)
                    if c < 4.5:
                        det.append(u"%s: %s tem contraste %.2f:1 contra o fundo "
                                   u"%s (piso 4.5)" % (rel, nome, c, fundo))
            return (not det, u"; ".join(det[:4])
                    or u"contraste >= 4.5:1 em titulo, subtitulo e texto, 3 idiomas")
        s.check("V39", u"bloco \"Como usamos IA\" legível sobre o fundo real da página (#212)",
                v39)

        def v40():
            # Onda 72b (#253). O modal de líder vive DENTRO de <main>, que tem
            # position:relative + z-index:1 — o stacking context inteiro ficava
            # atrás do header fixo (z=90): o topo do modal sumia por baixo da
            # barra, sem nem scroll que o alcançasse, e o backdrop ia a z=-1
            # (nada escurecia). O Mario viu no staging ("conectado à barra").
            # Medição do EFEITO, com o modal ABERTO de verdade:
            #   1. elementFromPoint no alto da tela pertence ao modal (não ao menu);
            #   2. o diálogo cabe inteiro na viewport (top >= 0 e bottom <= vh);
            #   3. o backdrop está acima do header (z > 90).
            det = []
            nav.abrir("%s/pt/sobre-nos/lideres/" % base, 1600, 900)
            r = nav.js(
                "(function(){"
                "var b=document.querySelector('[data-bs-target=\"#modal_raoni-morais\"]');"
                "if(!b) return 'sem-botao'; b.click(); return 'ok';})()")
            if r != "ok":
                return (False, u"card do Raoni sem botão de modal")
            time.sleep(1.2)
            r = nav.js(
                "(function(){"
                "var d=document.querySelector('#modal_raoni-morais .modal-dialog');"
                "if(!d) return JSON.stringify({erro:'sem dialogo'});"
                "var rd=d.getBoundingClientRect();"
                "var topo=document.elementFromPoint(innerWidth/2, 40);"
                "var noModal=!!(topo && topo.closest('#modal_raoni-morais'));"
                "var bk=document.querySelector('.modal-backdrop');"
                "var c=d.querySelector('.modal-content'),"
                " body=d.querySelector('.modal-body'),"
                " btn=d.querySelector('.btn-close');"
                "var rc=c.getBoundingClientRect(), rb=btn?btn.getBoundingClientRect():null;"
                "return JSON.stringify({noModal:noModal, top:Math.round(rd.top),"
                " bottom:Math.round(rd.bottom), vh:innerHeight,"
                " ovH: body.scrollWidth - Math.round(body.getBoundingClientRect().width),"
                " btnFora: rb? (rb.right>rc.right+1||rb.top<rc.top-1) : true,"
                " bkz:bk?parseInt(getComputedStyle(bk).zIndex)||0:0});})()")
            d = json.loads(r)
            if d.get("erro"):
                det.append(d["erro"])
            else:
                if not d["noModal"]:
                    det.append(u"o alto da tela não é o modal — voltou para trás do header")
                if d["top"] < 0 or d["bottom"] > d["vh"]:
                    det.append(u"diálogo não cabe na viewport (top=%s bottom=%s vh=%s)"
                               % (d["top"], d["bottom"], d["vh"]))
                if d["bkz"] <= 90:
                    det.append(u"backdrop com z-index %s (atrás do header)" % d["bkz"])
                # Onda 72c: o corpo tinha 20px de overflow horizontal (scrollbar no
                # pé) e o X de 48px vazava 19px para fora da borda — as duas classes
                # que o Mario apontou ("janela fora de tamanho com X dentro").
                if d["ovH"] > 2:
                    det.append(u"corpo do modal com %dpx de overflow horizontal" % d["ovH"])
                if d["btnFora"]:
                    det.append(u"botão de fechar fora da borda do modal")
            return (not det, u"; ".join(det)
                    or u"modal acima do header, inteiro na viewport, backdrop ativo")
        s.check("V40", u"modal de líder abre acima do header, inteiro na viewport (#253)",
                v40)

        def v41():
            # Onda 76 — primeiro passo da reconstrução fluida. Mede o EFEITO da
            # tipografia em duas larguras, com getComputedStyle, e cobra as duas
            # metades do invariante:
            #   (a) CRESCE: em 1920 o texto é maior que em 390. Sem isto, o clamp
            #       existe no arquivo e não faz nada — que é exatamente o estado
            #       anterior (declaração de 15px vencida por outra de 13px, e o
            #       site achando que era responsivo);
            #   (b) NÃO ENCOLHE: em 390 o tamanho é pelo menos o piso declarado no
            #       próprio script da onda. É a metade que protege o celular — a
            #       forma errada de "fluidificar" é deixar o texto minguar lá.
            # Os pisos vêm da constante FLUIDAS do 150 (nunca número escrito aqui:
            # valor gêmeo diverge na primeira mudança de tamanho).
            fluidas = _mod150().FLUIDAS
            piso = dict((sel, float(mini.replace("px", ""))) for sel, mini, _p, _t in fluidas)
            # onde cada seletor existe de fato (medido na auditoria de 31/08)
            ONDE = {".rede__titulo": "pt/sobre-nos/nossa-rede/",
                    ".onda18-imprensa__titulo": "pt/imprensa/"}
            det = []
            medido = 0
            for sel, pagina in ONDE.items():
                vals = {}
                for larg in (390, 1920):
                    nav.abrir("%s/%s" % (base, pagina), larg, 900)
                    v = nav.js("(function(){var e=document.querySelector(%s);"
                               "return e?parseFloat(getComputedStyle(e).fontSize):null;})()"
                               % json.dumps(sel))
                    vals[larg] = None if v in (None, "null") else float(v)
                if vals[390] is None or vals[1920] is None:
                    det.append(u"%s não encontrado em %s" % (sel, pagina))
                    continue
                medido += 1
                if vals[1920] <= vals[390] + 0.5:
                    # sem seta unicode: o console do Windows e cp1252 e a suite
                    # ABORTA ao imprimir "→" -- o grep por FALHA nao acha nada e
                    # a sabotagem parece ter passado. Falso verde por encoding.
                    det.append(u"%s nao cresce: 390 vale %.1f e 1920 vale %.1f"
                               % (sel, vals[390], vals[1920]))
                if vals[390] < piso.get(sel, 0) - 0.5:
                    det.append(u"%s encolheu no celular: %.1f < piso %.1f"
                               % (sel, vals[390], piso[sel]))
            return (not det, u"; ".join(det)
                    or u"%d seletor(es) fluidos: crescem até 1920 e não encolhem em 390"
                       % medido)
        s.check("V41", u"tipografia fluida cresce em tela grande e não encolhe no celular (onda 76)",
                v41)

        def v42():
            # Onda 78: os chips existem no HTML (S181) — aqui se mede se eles
            # APARECEM. Três coisas que o markup não garante:
            #   (a) cada chip tem área > 0 (não está colapsado nem display:none);
            #   (b) o ícone SVG dentro do chip também tem área — ícone que não
            #       desenha é o defeito que o favicon vazio ensinou (erro 16);
            #   (c) o card cresceu para caber: no desktop nenhum chip fica fora
            #       da borda do card (o pedido foi "faça tudo isso caber").
            det = []
            nav.abrir("%s/pt/sobre-nos/lideres/" % base, 1440, 900)
            d = nav.js(
                "(function(){"
                "var out={chips:0,semArea:0,iconeSemArea:0,vazando:0};"
                "document.querySelectorAll('.page-leaders__list-item').forEach(function(c){"
                " var rc=c.getBoundingClientRect();"
                " c.querySelectorAll('.onda78-inst__item').forEach(function(ch){"
                "  out.chips++;"
                "  var r=ch.getBoundingClientRect();"
                "  if(r.width<8||r.height<8) out.semArea++;"
                # a marca do chip pode ser <svg> (icone de tipo) OU <img> (logo real):
                # cobrar <svg> em todos era o teste da onda 78, e ficou estreito quando
                # a 79 trocou 26 deles por imagem
                "  var mk=ch.querySelector('svg,img');"
                "  var rs=mk?mk.getBoundingClientRect():{width:0,height:0};"
                "  if(rs.width<6||rs.height<6) out.iconeSemArea++;"
                "  if(r.right>rc.right+1||r.bottom>rc.bottom+1) out.vazando++;"
                " });});"
                "return JSON.stringify(out);})()")
            d = json.loads(d) if isinstance(d, str) else d
            # Onda 79: os logos reais. Medido pela CAIXA RENDERIZADA, nunca por
            # naturalWidth -- SVG sem dimensao intrinseca reporta naturalWidth=0
            # no Chrome mesmo desenhando perfeitamente, e foi assim que eu quase
            # cacei um bug que nao existia (17 dos 26 "nao carregavam").
            logos = nav.js(
                "[...document.querySelectorAll('.onda78-inst__logo')].filter("
                "function(i){var r=i.getBoundingClientRect();"
                "return r.width>=4&&r.height>=4;}).length")
            total_logos = nav.js("document.querySelectorAll('.onda78-inst__logo').length")
            if int(total_logos or 0) and int(logos or 0) != int(total_logos):
                det.append(u"%d de %d logo(s) sem área renderizada"
                           % (int(total_logos) - int(logos or 0), int(total_logos)))
            if not d["chips"]:
                return (False, u"nenhum chip de instituição renderizado")
            if d["semArea"]:
                det.append(u"%d chip(s) sem área visível" % d["semArea"])
            if d["iconeSemArea"]:
                det.append(u"%d chip(s) com marca (logo ou ícone) sem área" % d["iconeSemArea"])
            if d["vazando"]:
                det.append(u"%d chip(s) fora da borda do card" % d["vazando"])
            return (not det, u"; ".join(det)
                    or u"%d chips visíveis (%s com logo real), dentro do card"
                       % (d["chips"], total_logos))
        s.check("V42", u"chips de instituição aparecem e cabem no card (onda 78)", v42)


        s.check("V37", u"barra do topo não embranquece no toque após fechar o menu (onda 64)",
                v37)


# ------------------------------------------------------------------- main

def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    raiz = os.path.abspath(args[0])
    pub = raiz if os.path.basename(raiz) == "public" else os.path.join(raiz, "public")
    if not os.path.isdir(pub):
        raise SystemExit(u"não achei public/ em %s" % raiz)
    rapido = "--rapido" in args
    verboso = "-v" in args
    filtro = None
    etapas = None
    mostrar_tempos = "--tempos" in args
    Navegador.espera_fixa = "--espera-fixa" in args
    for a in args:
        if a.startswith("--so="):
            filtro = a[5:]
        elif a.startswith("--para="):
            pedidas = set(x.strip() for x in a[7:].split(",") if x.strip())
            invalidas = pedidas - set(ETAPAS_VALIDAS)
            if invalidas:
                raise SystemExit(u"etapa desconhecida: %s. Válidas: %s"
                                 % (", ".join(sorted(invalidas)), ", ".join(ETAPAS_VALIDAS)))
            etapas = pedidas
        elif a.startswith("--desde="):
            ref = a[8:]
            mudou = arquivos_mudados(ref)
            etapas = etapas_do_diff(mudou)
            print(u"--desde=%s: %d arquivo(s) mudado(s) -> etapas %s"
                  % (ref, len(mudou), ", ".join(sorted(etapas))))
            for f in mudou[:6]:
                print(u"    %s" % f)
            if len(mudou) > 6:
                print(u"    … e %d outro(s)" % (len(mudou) - 6))

    print(u"suite de verificações — %s" % pub)
    print(u"-" * 72)
    s = Suite(pub, verboso=verboso, filtro=filtro, etapas=etapas)
    estaticas(s)
    if not rapido:
        print(u"-" * 72)
        ao_vivo(s)
    print(u"-" * 72)
    for cid, titulo, issue in PENDENTES:
        s.pendente(cid, titulo, issue)

    print(u"-" * 72)
    n_ok = sum(1 for r in s.res if r[2] == "OK")
    n_fa = sum(1 for r in s.res if r[2] == "FALHA")
    n_pe = sum(1 for r in s.res if r[2] == "PENDENTE")
    print(u"%d OK · %d FALHA · %d PENDENTE" % (n_ok, n_fa, n_pe))
    if s.puladas:
        print(u"%d asserção(ões) fora das etapas pedidas — o gate do deploy roda TODAS"
              % s.puladas)
    if Navegador.loads:
        print(u"%d page load(s) no Chrome, %.1f s somados (%.1f s cada)"
              % (Navegador.loads, Navegador.tempo_loads,
                 Navegador.tempo_loads / Navegador.loads))
    if mostrar_tempos and s.tempos:
        print(u"-" * 72)
        print(u"as 12 asserções mais lentas (é aqui que o gate gasta):")
        for gasto, cid, titulo in sorted(s.tempos, reverse=True)[:12]:
            print(u"  %6.1f s  %-6s %s" % (gasto, cid, titulo[:62]))
        total = sum(t[0] for t in s.tempos)
        print(u"  %6.1f s  TOTAL de %d asserção(ões)" % (total, len(s.tempos)))
    if n_fa:
        print(u"\nDEPLOY BLOQUEADO — %d asserção(ões) falhando:" % n_fa)
        for cid, titulo, estado, detalhe in s.res:
            if estado == "FALHA":
                print(u"  %s %s — %s" % (cid, titulo, detalhe))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
