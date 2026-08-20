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


def bloco_bio(d):
    partes = [INI]
    if d["cargo"]:
        partes.append('<p class="onda59-cargo"><strong>%s</strong></p>' % d["cargo"])
    if d["bio"]:
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
            novo_bloco = bloco_bio(d)
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
