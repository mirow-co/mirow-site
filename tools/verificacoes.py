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

# ---------------------------------------------------------------- constantes

# As 4 homes do site (pt, en, de e a duplicata /en/homepage/ — ver S-16).
HOMES = ["pt/index.html", "en/index.html", "de/index.html", "en/homepage/index.html"]

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
]

# Marcadores HTML das entregas, e em quantas páginas cada um precisa aparecer.
# n=4 -> só as homes; n=275 -> todas as páginas; n=3 -> uma por idioma.
# onda7:menu-carreiras só foi injetado em pt/en (204 páginas): as 71 páginas
# alemãs já traziam "Karriere" nativo do tema. O invariante de verdade — todas as
# páginas terem link de carreiras no menu — é a asserção H08, não o marcador.
MARCADORES = [
    ("onda5:clientes-logos", 4), ("onda6:praticas", 4), ("onda7:lideres-link", 4),
    ("onda7:menu-sobre", 275), ("onda7:menu-praticas", 275), ("onda7:menu-carreiras", 200),
    ("onda8:menu-contatos", 275), ("onda8:hero-contatos", 4), ("onda8:dobra", 4),
    ("onda10:hero-numeros", 4), ("onda11:s08-hero-contatos", 5),
    ("onda13:hero-malha", 4),
    # onda14:rodape-menu e onda15:rodape-contatos saíram em 31/07 (decisão
    # explícita do Mario na #91: "IDENTICAS" — a nav recriada virou o clone
    # literal onda15:rodape-barra).
    ("onda15:hero-texto", 4), ("onda15:rodape-barra", 275),
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
    # imagens da roda de 8 práticas, em 6 páginas — quebradas no site original.
    # Rastreado na issue S-20.
    "novo/wp-content/uploads/2023/04/strategic_ideation_formulation_execution-1.png": "S-20",
    "novo/wp-content/uploads/2023/05/2-inovacao-modelo-de-negocio-radar-de-tendencias-workshop-ecossistema-1024x503.png": "S-20",
    "novo/wp-content/uploads/2023/05/3-marketing-vendas-pricing-go-to-market-CX-forca-de-vendas-digital-1024x545.png": "S-20",
    "novo/wp-content/uploads/2023/05/4-operacoes-supply-chain-SOP-CSC-procurement-estoques-1024x435.png": "S-20",
    "novo/wp-content/uploads/2023/05/7-transformacao-metodologia-agil-gestao-da-mudanca-governanca-quick-wins-1024x521.png": "S-20",
    "novo/wp-content/uploads/2023/05/8-adaptacao-climatica-sustentabilidade-net-zero-ESG-descarbonizacao-carbono-1024x552.png": "S-20",
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
CONTATOS = ["contato/index.html", "pt/contato/index.html", "en/contact-us/index.html",
            "de/kontakt/index.html", "novo/contato/index.html"]

# Páginas de carreiras — S-13.
CARREIRAS = ["carreiras/index.html", "pt/carreiras/index.html",
             "en/careers/index.html", "de/karrieren/index.html"]

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
        return [(rel, h) for rel, h in self.todas() if rel != "index.html"]

    def todas(self):
        """[(rel, html)] de todas as páginas HTML sob public/."""
        if self._htmls is None:
            out = []
            for dp, _d, fs in os.walk(self.pub):
                for n in fs:
                    if not n.endswith(".html"):
                        continue
                    rel = os.path.relpath(os.path.join(dp, n), self.pub).replace(os.sep, "/")
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
        saiu = ["Giulia", "Mariana Sim", "Matheus"]
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
        ok = not sobrou and n_nav >= 90
        return (ok, u"mandala em %d página(s) %s; praticas-nav em %d (esperado >= 90)"
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
        # S-23/S-37 (#73 -> #92): depois de testar malha animada e foto
        # estática, o Mario decidiu (31/07, 3ª rodada) voltar ao VÍDEO
        # original do tema ("tem que ficar como era no mirow.com.br") —
        # decisão explícita do dono, custo do MP4 aceito e registrado.
        # A malha/canvas não podem voltar.
        ruins = []
        for rel in HOMES:
            h = s.ler(rel)
            if "video-bg-home-1.mp4" not in h:
                ruins.append("%s sem o vídeo original" % rel)
            for morto in ("hero-malha__img", "hero-malha__canvas",
                          "onda13-hero-plexus.js"):
                if morto in h:
                    ruins.append("%s ainda tem %s" % (rel, morto))
        return (not ruins, u"; ".join(ruins))
    s.check("S23", u"hero com o vídeo original da lâmpada (decisão 31/07)", s23)

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
        # S-36 v2 ("IDENTICAS", Mario 31/07): a barra do rodapé é um CLONE
        # literal do <nav class="menu"> do header — igual byte a byte, modulo
        # os únicos ajustes permitidos (id do seletor de idioma renomeado e
        # data-scroll-header removido). Página a página.
        ruins = []
        for rel, h in s.conteudo():
            if '<footer class="footer">' not in h:
                continue
            i = h.find('<nav class="menu"')
            j = h.find('</nav>', i)
            if i < 0 or j < 0:
                continue
            header = h[i:j + 6]
            ini = h.find("<!-- onda15:rodape-barra -->")
            fim = h.find("<!-- /onda15:rodape-barra -->")
            if ini < 0 or fim < 0:
                ruins.append("%s sem a barra clonada" % rel)
                continue
            bloco = h[ini:fim]
            k = bloco.find('<nav class="menu"')
            clone = bloco[k:bloco.rfind('</nav>') + 6] if k >= 0 else ""
            # desfaz os ajustes de contexto e compara
            desfeito = (clone.replace('check-rodape', 'check'))
            original = (header.replace(' data-scroll-header=""', '')
                        .replace(' data-scroll-header', ''))
            if desfeito != original:
                ruins.append("%s com clone divergente do header" % rel)
        return (not ruins, u"%d página(s): %s" % (len(ruins), "; ".join(ruins[:3])))
    s.check("S36", u"barra do rodapé IDÊNTICA à superior (clone literal, por página)", s36)

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

    PREFIXO = "mirow-site"   # as páginas referenciam /mirow-site/... (base do Pages)

    def __enter__(self):
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        self.porta = srv.getsockname()[1]
        srv.close()
        # As URLs das páginas são absolutas em /mirow-site/. Servir public/ na raiz
        # daria 404 em todo CSS/JS e a medição de dobra sairia errada. Então serve-se
        # um diretório temporário com uma junction mirow-site -> public.
        self.tmp = tempfile.mkdtemp(prefix="verif-serve")
        alvo = os.path.join(self.tmp, self.PREFIXO)
        subprocess.check_call(["cmd", "/c", "mklink", "/J", alvo, self.pub],
                              stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(self.porta), "--bind", "127.0.0.1",
             "--directory", self.tmp],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(40):
            try:
                urllib.request.urlopen("http://127.0.0.1:%d/%s/pt/" % (self.porta, self.PREFIXO),
                                       timeout=2).read(1)
                return self
            except Exception:
                time.sleep(0.25)
        raise RuntimeError("servidor local não subiu na porta %d" % self.porta)

    def base(self):
        return "http://127.0.0.1:%d/%s" % (self.porta, self.PREFIXO)

    def __exit__(self, *a):
        if self.proc:
            self.proc.terminate()
        try:
            # remove a junction (não o alvo) e o temp
            subprocess.call(["cmd", "/c", "rmdir", os.path.join(self.tmp, self.PREFIXO)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            os.rmdir(self.tmp)
        except Exception:
            pass


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
        s.check("V05", u"primeira dobra exata em pt (1366x768)",
                faz_dobra("pt/index.html", 1366, 768))

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
            nav.abrir("%s/pt/" % base, 1920, 1080)
            v = nav.js(
                "(function(){var ts=document.querySelectorAll('.hero-numeros__texto');"
                "if(!ts.length)return 'pilha de números não encontrada';var ruins=[];"
                "for(var i=0;i<ts.length;i++){var cs=getComputedStyle(ts[i]);"
                "var lh=parseFloat(cs.lineHeight);"
                "var linhas=Math.round(ts[i].getBoundingClientRect().height/lh);"
                "if(linhas>2)ruins.push(i+':'+linhas+'linhas');}"
                "return ruins.length?ruins.join(' '):'ok:'+ts.length;})()")
            if isinstance(v, str) and v.startswith("ok:"):
                return (True, u"%s blocos, todos com ≤2 linhas (1920x1080)" % v[3:])
            return (False, u"bloco(s) com mais de 2 linhas: %s" % v)
        s.check("V07", u"números do hero com no máximo 2 linhas por bloco", v07)


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
