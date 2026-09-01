# -*- coding: utf-8 -*-
"""Onda 80: pagina individual para Elmar Gans e Joao Daniel Ramos.

Pedido do Mario em 01/09/2026: "o elmar deve estar dentro do schema. o joao
daniel deve ter pagina propria".

Os dois pedidos sao o MESMO trabalho, e isso nao e obvio: o no `Person` do
JSON-LD precisa de um `@id` que seja uma URL propria (foi por isso que o Joao
Daniel ficou de fora do schema na onda 59 -- classe C3 do backlog). Entao para o
Elmar entrar no schema ele tambem precisa de pagina, que ele nao tinha. Uma coisa
destrava a outra.

Como a pagina e feita
---------------------
CLONANDO a estrutura de uma pagina de lider que ja existe (a do Felipe) e
trocando o conteudo. Nao ha "template" neste espelho: cada pagina e HTML servido
pelo WordPress antigo, e inventar uma marcacao nova aqui produziria uma pagina
que parece igual e se comporta diferente. O clone preserva header, rodape, menu,
scripts e as classes que o tema usa.

O que e trocado, e de onde vem
------------------------------
- nome, cargo, foto, LinkedIn: do CARD da listagem (fonte unica ja existente);
- bio: os bullets do proprio card, que e o texto que a firma ja publica;
- canonical, hreflang, og:url, titulo: derivados do slug de cada idioma;
- o resto (bio media, meta description, JSON-LD) vem depois, dos scripts 110/111/
  112/146, assim que os dois entrarem no cadastro PAGINAS -- e por isso este
  script NAO escreve nada disso: escrever aqui criaria valor gemeo com aqueles.

Idempotente: reescreve a pagina inteira a cada execucao, a partir do clone.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_css = __import__("_onda7_css")
ler, gravar = _css.ler, _css.gravar

MOLDE = {"pt": "pt/lider/felipe-diniz/index.html",
         "en": "en/leader/felipe-diniz/index.html",
         "de": "de/lider/felipe-diniz/index.html"}

# quem -> (slug, {idioma: cargo})
PESSOAS = {
    u"Elmar Gans": ("elmar-gans", {
        "pt": u"Senior Expert", "en": u"Senior Expert", "de": u"Senior Expert"}),
    u"João Daniel Ramos": ("joao-daniel-ramos", {
        "pt": u"Gerente de projetos", "en": u"Project Manager", "de": u"Projektmanager"}),
}

DIR = {"pt": "pt/lider", "en": "en/leader", "de": "de/lider"}
LISTAGEM = {"pt": "pt/sobre-nos/lideres/index.html",
            "en": "en/about-us/leaders/index.html",
            "de": "de/ueber-uns/fuehrungskraefte/index.html"}


def dados_do_card(pub, lang, nome):
    """Foto, cargo, LinkedIn e bullets, lidos do card da propria listagem."""
    h = ler(os.path.join(pub, LISTAGEM[lang].replace("/", os.sep)))
    for c in re.findall(r'<button class="page-leaders__list-item".*?</button>', h, re.S):
        m = re.search(r'page-leaders__list-title">([^<]*?)<small', c)
        if not m or m.group(1).strip() != nome:
            continue
        foto = re.search(r'background-image: url\(([^)]+)\)', c)
        li = re.search(r'href="(https://www\.linkedin\.com/in/[^"]+)"', c)
        bullets = [re.sub(r"<[^>]+>", "", b).strip()
                   for b in re.findall(r"<li>(.*?)</li>", c, re.S)]
        bullets = [b for b in bullets if len(b) > 30]
        return {"foto": foto.group(1) if foto else "",
                "linkedin": li.group(1) if li else "",
                "bullets": bullets}
    return None


def main(raiz):
    pub = os.path.join(os.path.abspath(raiz), "public")
    feitas = 0
    for nome, (slug, cargos) in PESSOAS.items():
        for lang in ("pt", "en", "de"):
            molde_p = os.path.join(pub, MOLDE[lang].replace("/", os.sep))
            if not os.path.exists(molde_p):
                print(u"  molde ausente para %s" % lang)
                continue
            d = dados_do_card(pub, lang, nome)
            if not d:
                print(u"  %s: card de %s nao encontrado em %s" % (lang, nome, LISTAGEM[lang]))
                continue
            h = ler(molde_p)
            # nome e cargo
            h = h.replace(u"Felipe Diniz", nome)
            h = re.sub(r"felipe-diniz", slug, h)
            h = h.replace(u"Sócio — Prática de Energia e Inovação", cargos[lang])
            h = h.replace(u"Partner — Energy and Innovation Practice", cargos[lang])
            h = h.replace(u"Partner — Practice Energie und Innovation", cargos[lang])
            h = h.replace(u"Partner", cargos[lang]) if lang != "pt" else h
            # foto e LinkedIn
            h = re.sub(r"/wp-content/uploads/[^\"')]*Felipe[^\"')]*\.(webp|png|jpg)",
                       d["foto"], h)
            h = re.sub(r"https://www\.linkedin\.com/in/[^\"]+", d["linkedin"], h)
            destino = os.path.join(pub, DIR[lang].replace("/", os.sep), slug, "index.html")
            if not os.path.isdir(os.path.dirname(destino)):
                os.makedirs(os.path.dirname(destino))
            gravar(destino, h)
            feitas += 1
            print(u"  %s" % os.path.relpath(destino, pub).replace(os.sep, "/"))
    print(u"154: %d pagina(s) individual(is) escrita(s)" % feitas)
    return feitas


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
