# -*- coding: utf-8 -*-
"""Onda 59 (GEO, mirow-marketing#233): paginas individuais de lider recebem
cargo + bio + LinkedIn, copiados dos cards da listagem do mesmo idioma.

Fonte unica: <button class="page-leaders__list-item"> de cada listagem
(cargo em .page-leaders__list-role, bio em .page-leaders__list-wrap-content-summary,
LinkedIn no primeiro <a> do card). Nada e redigido a mao.

Idempotente: o bloco vive entre marcadores onda59:geo-bio e e reescrito por igual.
"""
import io
import os
import re
import sys

LISTAGENS = {
    "pt": "pt/sobre-nos/lideres/index.html",
    "en": "en/about-us/leaders/index.html",
    "de": "de/ueber-uns/fuehrungskraefte/index.html",
}

# slug da pagina individual por idioma (so os 6 lideres com pagina propria)
# Michael Munch saiu de PAGINAS em 20/08/2026: deixou a firma em 19/08 e o Mario
# pediu para retirar "totalmente da pagina, de tudo". Tirar daqui e o que apaga o no
# `Person` dele do JSON-LD das 3 listagens E das 3 homes, na proxima execucao do 111.
PAGINAS = {
    u"Andreas Mirow": {"pt": "pt/lider/andreas-mirow", "en": "en/leader/andreas-mirow", "de": "de/lider/andreas-mirow"},
    u"Felipe Diniz": {"pt": "pt/lider/felipe-diniz", "en": "en/leader/felipe-diniz", "de": "de/lider/felipe-diniz"},
    u"Prof. Dr Stephan Friedrich": {"pt": "pt/lider/prof-dr-stephan-friedrich", "en": "en/leader/prof-dr-stephan-friedrich", "de": "de/lider/prof-dr-stephan-friedrich"},
    u"Renato Alvarenga": {"pt": "pt/lider/renato-alvarenga", "en": "en/leader/renato-alvarenga", "de": "de/lider/renato-alvarenga"},
    u"Raoni Morais": {"pt": "pt/lider/raoni-morais", "en": "en/leader/raoni-morais", "de": "de/lider/raoni-morais"},
}

RE_CARD = re.compile(r'<button class="page-leaders__list-item".*?</button>', re.S)
RE_TITULO = re.compile(r'page-leaders__list-title">(.*?)<small', re.S)
RE_CARGO = re.compile(r'page-leaders__list-role">(.*?)</small>', re.S)
RE_LINKEDIN = re.compile(r'href="(https://www\.linkedin\.com/in/[^"]+)"')
RE_BIO = re.compile(r'page-leaders__list-wrap-content-summary">(.*?)</ul>', re.S)
RE_LI = re.compile(r'<li>(.*?)</li>', re.S)
RE_TEXTO = re.compile(r'(<div class="blog-single__text">).*?(</div>)', re.S)

INI = "<!-- onda59:geo-bio:ini -->"
FIM = "<!-- onda59:geo-bio:fim -->"


def ler(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def gravar(p, s):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def limpa(s):
    return re.sub(r"<[^>]+>", "", s).strip()


def extrai_cards(html):
    dados = {}
    for card in RE_CARD.findall(html):
        m = RE_TITULO.search(card)
        if not m:
            continue
        nome = limpa(m.group(1)).replace("Private:", "").strip()
        cargo = ""
        mc = RE_CARGO.search(card)
        if mc:
            cargo = limpa(mc.group(1))
            # o card do Andreas traz " - email" grudado no cargo
            cargo = cargo.split(" - ")[0].strip()
        linkedin = ""
        ml = RE_LINKEDIN.search(card)
        if ml:
            linkedin = ml.group(1)
        bullets = []
        mb = RE_BIO.search(card)
        if mb:
            bullets = [limpa(li) for li in RE_LI.findall(mb.group(1)) if limpa(li)]
        dados[nome] = {"cargo": cargo, "linkedin": linkedin, "bio": bullets}
    return dados


# Onda 72 (#250, e-mail do Felipe de 24/08/2026): a pagina individual dele ganha a
# "bio media" em paragrafos, verbatim do anexo (traducoes en/de minhas). Os demais
# seguem com os bullets do card. O JSON-LD (111) continua usando a descricao curta
# do card — a bio media e texto para humano, da pagina individual.
BIO_MEDIA = {
    u"Felipe Diniz": {
        "pt": [
            u"Felipe Diniz é sócio da Mirow & Co. desde 2018, onde lidera a prática de Energia e Inovação. São 18 anos de consultoria estratégica ininterruptos, iniciados na McKinsey & Company e seguidos por Schlumberger Business Consulting, e Monitor Deloitte.",
            u"Atende clientes de setores intensivos em capital — energia elétrica, gás natural, óleo e gás, automotivo — além de extensa experiência em segmentos como seguros, tecnologia, educação e setor público. Tem grande atuação em projetos de planejamento estratégico, inovação e novos modelos de negócio, estratégia comercial e pricing, eficiência e redução de custos, finanças corporativas e desenho organizacional e de governança.",
            u"É PhD em Economia pela University of Chicago. Foi docente do Departamento de Economia e orientador acadêmico do Executive MBA da Booth School of Business, na mesma universidade.",
        ],
        "en": [
            u"Felipe Diniz has been a partner at Mirow & Co. since 2018, where he leads the Energy and Innovation practice. He brings 18 uninterrupted years of strategy consulting, starting at McKinsey & Company and followed by Schlumberger Business Consulting and Monitor Deloitte.",
            u"He serves clients in capital-intensive sectors — electricity, natural gas, oil and gas, automotive — with extensive experience in segments such as insurance, technology, education and the public sector. He works broadly on strategic planning, innovation and new business models, commercial strategy and pricing, efficiency and cost reduction, corporate finance, and organizational and governance design.",
            u"He holds a PhD in Economics from the University of Chicago, where he also taught in the Department of Economics and served as academic advisor to the Executive MBA at the Booth School of Business.",
        ],
        "de": [
            u"Felipe Diniz ist seit 2018 Partner bei Mirow & Co., wo er die Practice Energie und Innovation leitet. Er bringt 18 ununterbrochene Jahre Strategieberatung mit, begonnen bei McKinsey & Company, gefolgt von Schlumberger Business Consulting und Monitor Deloitte.",
            u"Er betreut Kunden in kapitalintensiven Branchen — Elektrizität, Erdgas, Öl und Gas, Automobil — mit umfangreicher Erfahrung in Segmenten wie Versicherungen, Technologie, Bildung und öffentlichem Sektor. Er arbeitet in Projekten zu strategischer Planung, Innovation und neuen Geschäftsmodellen, Vertriebsstrategie und Pricing, Effizienz und Kostensenkung, Corporate Finance sowie Organisations- und Governance-Design.",
            u"Er ist PhD in Wirtschaftswissenschaften der University of Chicago, wo er auch am Department of Economics lehrte und akademischer Berater des Executive MBA der Booth School of Business war.",
        ],
    },
}


def bloco_bio(d, nome=None, lang=None):
    partes = [INI]
    if d["cargo"]:
        partes.append('<p class="onda59-cargo"><strong>%s</strong></p>' % d["cargo"])
    paragrafos = BIO_MEDIA.get(nome, {}).get(lang)
    if paragrafos:
        partes.extend("<p>%s</p>" % p for p in paragrafos)
    elif d["bio"]:
        partes.append("<ul>%s</ul>" % "".join("<li>%s</li>" % b for b in d["bio"]))
    if d["linkedin"]:
        partes.append('<p><a href="%s" target="_blank" rel="noopener noreferrer">LinkedIn</a></p>' % d["linkedin"])
    partes.append(FIM)
    return "\n".join(partes)


def main(raiz):
    pub = os.path.join(os.path.abspath(raiz), "public")
    mudancas = 0
    for lang, rel in LISTAGENS.items():
        listagem = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(listagem):
            raise SystemExit("listagem ausente: %s" % rel)
        cards = extrai_cards(ler(listagem))
        for nome, paginas in PAGINAS.items():
            if nome not in cards:
                raise SystemExit(u"card de %s ausente na listagem %s" % (nome, lang))
            d = cards[nome]
            if not d["bio"]:
                raise SystemExit(u"bio vazia para %s em %s — nao publicar bloco vazio" % (nome, lang))
            alvo = os.path.join(pub, paginas[lang].replace("/", os.sep), "index.html")
            if not os.path.exists(alvo):
                raise SystemExit("pagina individual ausente: %s" % paginas[lang])
            h = ler(alvo)
            novo_bloco = bloco_bio(d, nome, lang)
            m = RE_TEXTO.search(h)
            if not m:
                raise SystemExit("blog-single__text ausente em %s" % paginas[lang])
            atual = m.group(0)
            desejado = "%s\n%s\n%s" % (m.group(1), novo_bloco, m.group(2))
            if atual != desejado:
                h = h.replace(atual, desejado, 1)
                gravar(alvo, h)
                mudancas += 1
                print("bio injetada: %s (%s)" % (paginas[lang], lang))
    print("total de mudancas: %d" % mudancas)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
