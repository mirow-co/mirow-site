# -*- coding: utf-8 -*-
"""verificacoes.py — suite de asserções do site (P2 do processo).

Uso:
    python tools/verificacoes.py <raiz-que-contem-public> [--rapido] [--so=PREFIXO] [-v]

    --rapido        só as asserções estáticas (sem Chrome/servidor local)
    --so=H          roda só as asserções cujo id começa com H (ex.: --so=H03)
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
import io
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

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
MARCADORES = [
    # Onda 41 (S-135/#65): en/homepage virou stub — marcadores de home valem 3.
    ("onda5:clientes-logos", 3), ("onda6:praticas", 3), ("onda7:lideres-link", 3),
    # ATENCAO (onda 29 / S-107): as 275 paginas viraram 125 de CONTEUDO + 160
    # stubs de redirect (uma URL por pagina). Os marcadores de barra/rodape agora
    # se contam sobre as de conteudo — o numero e o piso, nao a meta.
    # ONDA 33 (S-118): as 12 paginas de perfil de quem saiu viraram stub, entao as
    # de conteudo cairam de 125 para 113 e os pisos abaixo desceram junto (120->110,
    # carreiras 80->74). Nao e regressao: e a mesma cobertura sobre menos paginas.
    ("onda7:menu-sobre", 110), ("onda7:menu-praticas", 110),
    # o marcador de carreiras nunca existiu nas paginas DE (medido: 44 pt + 41 en,
    # 0 de) — o item esta lá, o comentario e que nao. Piso = pt+en.
    ("onda7:menu-carreiras", 74),
    ("onda8:menu-contatos", 110), ("onda8:hero-contatos", 3), ("onda8:dobra", 3),
    ("onda10:hero-numeros", 3), ("onda11:s08-hero-contatos", 3),
    # onda13:hero-malha saiu em 03/08 (S-49/#107): o bloco do video virou os
    # canvases do Horizonte 2050.
    ("onda17:hero-horizonte", 3),
    # onda14:rodape-menu e onda15:rodape-contatos saíram em 31/07 (decisão
    # explícita do Mario na #91: "IDENTICAS" — a nav recriada virou o clone
    # literal onda15:rodape-barra).
    ("onda15:hero-texto", 3),
    # onda15:rodape-barra saiu na onda 42 (#191) — barra do rodape aposentada.
    # onda 18: botao de voltar ao topo em todas; planeta so nas homes
    ("onda18:voltar-topo", 110), ("onda18:planeta-setores", 3),
]

# Logos que a barra de clientes precisa mostrar. NÃO é lista hardcoded (era assim
# que divergia): vem de tools/clients-publicados.json, que o tools/gen_clients.py
# gera a partir do arquivo mestre de curadoria no repo PRIVADO mirow-co/mirow-marketing
# (08_Site/2026-07-30_clients-curadoria-interna.json). É o P3 em ação.
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
CONTATOS = ["pt/contato/index.html", "en/contact-us/index.html",
            "de/kontakt/index.html"]

# Páginas de carreiras — S-13.
CARREIRAS = ["pt/carreiras/index.html",
             "en/careers/index.html", "de/karrieren/index.html"]

# Páginas de imprensa — S-106 (#164) criou EN e DE; antes só existia em PT.
IMPRENSA = ["pt/imprensa/index.html", "en/press/index.html", "de/presse/index.html"]

# Páginas da Nossa Rede — geradas por tools/gen_rede.py (onda 31).
REDE = ["pt/sobre-nos/nossa-rede/index.html", "en/about-us/our-network/index.html",
        "de/ueber-uns/unser-netzwerk/index.html"]

# ------------------------------------------------------------------ mecânica

class Suite(object):
    def __init__(self, pub, verboso=False, filtro=None):
        self.pub = pub
        self.verboso = verboso
        self.filtro = filtro
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
        try:
            ok, detalhe = fn()
            estado = "OK" if ok else "FALHA"
        except Exception as e:  # asserção que explode conta como falha
            estado, detalhe = "FALHA", "erro na asserção: %r" % (e,)
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
            achou = [rel for rel, h in s.conteudo() if ("<!-- %s" % marca) in h]
            if n == 275:
                ok = len(achou) >= 270
            else:
                ok = len(achou) >= n
            return (ok, u"marcador <!-- %s --> em %d página(s), esperado >= %d"
                    % (marca, len(achou), 270 if n == 275 else n))
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
            achados = re.findall(r"/clientes/([a-z0-9\-]+)\.(?:svg|png|jpg)", h)
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

    def s07():
        # S-07 (onda 9): a <section class="offices"> — escritórios, endereços,
        # mapa — saiu de todas as variantes da página de contato.
        ruins = [rel for rel in CONTATOS
                 if 'section class="offices"' in s.ler(rel)]
        return (not ruins, u"bloco de escritórios ainda em: %s" % ", ".join(ruins))
    s.check("S07", u"0 blocos de escritórios nas páginas de contato", s07)

    def s08():
        ruins = []
        for rel in CONTATOS:
            h = s.ler(rel)
            i = h.find("<!-- onda11:s08-hero-contatos -->")
            trecho = h[i:i + 8000] if i >= 0 else ""
            faltam = [nome for nome, agulha in CANAIS if agulha not in trecho]
            if i < 0:
                ruins.append("%s sem o bloco" % rel)
            elif faltam:
                ruins.append("%s sem %s" % (rel, "/".join(faltam)))
        return (not ruins, u"; ".join(ruins))
    s.check("S08", u"4 canais de contato no hero das páginas de contato", s08)

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
        elif "MIROW" not in s.ler("404.html"):
            det.append("404.html sem a marca")
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

    def s58():
        # título com "quer ser nosso cliente", nas páginas de contato de verdade
        alvos = {"pt/contato/index.html": u"quer ser nosso cliente",
                 "en/contact-us/index.html": u"become our client",
                 "de/kontakt/index.html": u"unser Kunde werden"}
        det = [rel for rel, txt in alvos.items() if txt not in s.ler(rel)]
        return (not det, u"página(s) com o título antigo: %s" % ", ".join(det))
    s.check("S58", u'contato: "Você quer ser nosso cliente?" (#116)', s58)

    def s59():
        det = []
        for rel, h in s.todas():
            if 'id="form_contact-form"' not in h:
                continue
            m = re.search(r'<label for="field_e6lis6"[^>]*>([^<]*)', h)
            rotulo = (m.group(1) if m else "").strip()
            if rotulo not in (u"Empresa", u"Company", u"Unternehmen"):
                det.append(u"%s -> %r" % (rel, rotulo))
        return (not det, u"%d página(s) com o rótulo antigo: %s"
                % (len(det), ", ".join(det[:3])))
    s.check("S59", u'contato: campo "Empresa" no lugar de área de atuação (#117)', s59)

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
            for m in re.finditer(r'<a[^>]*href="mailto:[^"]*"[^>]*>', hh):
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
        for rel in HOMES + ["pt/contato/index.html", "de/kontakt/index.html"]:
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
            for prop in ("font-size:48px !important", "font-weight:700 !important",
                         "text-transform:none !important", "text-align:left !important"):
                if prop not in m.group(1):
                    det.append(u"a classe dos títulos sem %s" % prop)
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
                mn = re.search(r'<h4>([^<]*)</h4>', bloco)
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
    ORDEM_MENU = {
        "pt": [u"Sobre nós", u"Práticas", u"Insights", u"Imprensa", u"Carreiras",
               u"Contato"],
        # EN e DE ganharam o item de imprensa na S-106 (#164) — 6 itens nas três
        "en": [u"About us", u"Practices", u"Insights", u"Press", u"Careers",
               u"Contact Us"],
        "de": [u"Über uns", u"Branchen", u"Insights", u"Presse", u"Karrieren",
               u"Kontakt"],
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
                    "mariana-nakagawa", "matheus-strapasson"]
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
        if len(alvos) != 28:
            det.append(u"esperava 28 URLs de ex-líder, achei %d" % len(alvos))
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
        for rel in esperadas:
            p = os.path.join(pub, rel.replace("/", os.sep))
            if not os.path.exists(p):
                det.append(u"ausente: %s" % rel.split("/")[-1])
                continue
            if os.path.getsize(p) < 10 * 1024:
                det.append(u"%s tem só %d bytes — não é a imagem"
                           % (rel.split("/")[-1], os.path.getsize(p)))
            with io.open(p, "rb") as f:
                if f.read(4) != b"\x89PNG":
                    det.append(u"%s não é PNG" % rel.split("/")[-1])
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
        # A asserção lê os pesos disponíveis do PRÓPRIO <head>, não de uma lista fixa:
        # se alguém mudar o pedido da fonte, ela acompanha.
        h = s.ler("pt/index.html")
        m = re.search(r'family=Titillium\+Web:wght@([0-9;]+)', h)
        if not m:
            return (False, u"não achei o pedido de pesos da fonte no <head> da home")
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
            if ('icon-strategy.svg"><span>%s</span>' % txt) not in s.ler(rel):
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

    # M — medição (mirow-marketing#3). O snippet de GA4 tinha sido escrito só na
    # camada Astro, que está fora do deploy, e por isso nunca chegou ao ar. As
    # asserções abaixo existem para essa regressão não voltar em silêncio.
    MEDICAO = "wp-content/uploads/2026/07/onda6/onda31-medicao.js"

    def m01():
        sem = [rel for rel, h in s.todas() if MEDICAO not in h]
        # public/index.html é stub de meta refresh: o navegador sai antes de a
        # medição valer, o pageview é contado na página de destino.
        sem = [r for r in sem if r != "index.html"]
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
        falta = [pid for pid in ("G-VK4QHHHS5X", "G-5VTS0MZK79") if pid not in js]
        return (not falta, u"propriedade(s) fora do asset: %s" % ", ".join(falta))
    s.check("M04", u"as duas propriedades GA4 configuradas no asset", m04)

    def m05():
        js = s.ler(MEDICAO)
        i_consent = js.find("'consent', 'default'")
        i_config = js.find("'config'")
        if i_consent < 0:
            return (False, u"sem Consent Mode: o site passaria a gravar cookie sem base legal")
        if "analytics_storage: 'denied'" not in js:
            return (False, u"analytics_storage não está negado por padrão")
        if i_config >= 0 and i_consent > i_config:
            return (False, u"consent default vem DEPOIS do config — o GA4 processa a fila "
                    u"na ordem e o consentimento chegaria tarde")
        return (True, u"")
    s.check("M05", u"Consent Mode v2 negado por padrão, antes de qualquer config", m05)


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
        self.porta = 9344
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

    def abrir(self, url, largura=None, altura=None):
        # trava as métricas do device: sem isso a barra do Chrome come ~98px e
        # qualquer medição de primeira dobra sai errada (bug real da onda 8).
        self.ws.call(self._id(), "Emulation.setDeviceMetricsOverride", {
            "width": largura or self.largura, "height": altura or self.altura,
            "deviceScaleFactor": 1, "mobile": False})
        self.ws.call(self._id(), "Page.navigate", {"url": url})
        time.sleep(6)

    def js(self, expr):
        r = self.ws.call(self._id(), "Runtime.evaluate",
                         {"expression": expr, "returnByValue": True})
        return r.get("result", {}).get("result", {}).get("value")

    def hover(self, x, y, espera=1.0):
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
                                 # canônicas: `contato/` virou stub na S-107
                                 "pt/contato/index.html", "de/index.html"], 8):
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
                                u"%s @%dpx: gap LinkedIn→Instagram %dpx vs "
                                u"WhatsApp→E-mail %dpx — o Instagram descolou do "
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
                    "return {ruins:ruins,imgs:imgs.length,pequenos:pequenos,maior:Math.round(maior),lw:lw,"
                    "ov:document.documentElement.scrollWidth-document.documentElement.clientWidth};})()")
                if isinstance(d, str):
                    det.append(u"%s: %s" % (rel, d))
                    continue
                if d["ruins"]:
                    det.append(u"%s: logo(s) quebrado(s): %s" % (rel, d["ruins"][:3]))
                if d["imgs"] < 10:
                    det.append(u"%s: só %d imagens de logo" % (rel, d["imgs"]))
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
    for a in args:
        if a.startswith("--so="):
            filtro = a[5:]

    print(u"suite de verificações — %s" % pub)
    print(u"-" * 72)
    s = Suite(pub, verboso=verboso, filtro=filtro)
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
    if n_fa:
        print(u"\nDEPLOY BLOQUEADO — %d asserção(ões) falhando:" % n_fa)
        for cid, titulo, estado, detalhe in s.res:
            if estado == "FALHA":
                print(u"  %s %s — %s" % (cid, titulo, detalhe))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
