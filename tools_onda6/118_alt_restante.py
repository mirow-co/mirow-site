# -*- coding: utf-8 -*-
"""Onda 60: fecha o `alt` em TODAS as imagens do site, nao so nas 4 da home.

A assercao S153 (escrita nesta mesma onda) cobra a CLASSE do defeito e por isso
achou 120 imagens sem alt que o PageSpeed nao listou — ele auditou a home, e o
problema estava tambem nas 36 paginas de pratica e nas de carreiras.

Cada grupo recebeu uma decisao explicita, e nenhuma foi por adivinhacao:

| grupo                              | qtd | alt                                    |
|------------------------------------|-----|----------------------------------------|
| experience-single__banner-owner    |  33 | nome do lider, lido do modal que o     |
|                                    |     | proprio botao abre (data-bs-target)    |
| experience-single__cases-list-item |  60 | "" (decorativa) — a descricao do caso  |
|                                    |     | esta no <p> ao lado                    |
| home-experience__list-item-header  |   9 | "" (decorativa) — o titulo da pratica  |
|                                    |     | esta escrito ao lado do icone          |
| value-offer__item-header (carreiras)|  9 | "" (decorativa) — idem, texto ao lado  |
| selos de reconhecimento            |  18 | nome real da instituicao (ver abaixo)  |

SOBRE OS SELOS: o atributo `title` traz um slug ("certificate-cdp"), que seria um
alt ruim, e o nome do arquivo nao diz qual instituicao e ("image-52.png"). Em vez
de deduzir, ABRI as seis imagens e li o que esta escrito nelas:

    certificate-cdp.png          -> "CDP - Disclosure Insight Action"
    certificate-globalimpact.png -> "UN Global Compact"
    certificate-seventowatch.png -> "Seven to Watch"
    certificate-basedtargets.png -> "Science Based Targets"
    certificate-growingfirms.png -> "Consulting Fastest Growing Firms"
    image-52.png                 -> "Great Place to Work"

Nomear os selos, e nao deixa-los vazios, tem valor de GEO: sao reconhecimentos da
firma, e o robo passa a ler quais sao. `alt=""` fica so onde a imagem realmente
nao carrega informacao que o texto vizinho ja de.

Idempotente: 2o run reporta 0 mudancas.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public

# nome do arquivo do selo -> instituicao (lida da propria imagem)
SELOS = {
    "certificate-cdp": u"CDP - Disclosure Insight Action",
    "certificate-globalimpact": u"UN Global Compact",
    "certificate-seventowatch": u"Seven to Watch",
    "certificate-basedtargets": u"Science Based Targets",
    "certificate-growingfirms": u"Consulting Fastest Growing Firms",
    "image-52": u"Great Place to Work",
}

# containers cujo <img> e decorativo: o texto ao lado ja diz o que a imagem mostra
DECORATIVAS = (
    "experience-single__cases-list-item",
    "home-experience__list-item-header",
    "value-offer__item-header",
)

RE_IMG = re.compile(r"<img\b[^>]*>")
RE_SRC = re.compile(r'src="([^"]+)"')
# botao de dono da pratica: <button class="experience-single__banner-owner"
# data-bs-target="#modal_andreas-mirow"> ... <img ...>
RE_OWNER = re.compile(
    r'(<button class="experience-single__banner-owner"[^>]*'
    r'data-bs-target="#(modal_[^"]+)"[^>]*>.*?)(<img\b[^>]*>)', re.S)


def ler(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def gravar(p, s):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def com_alt(tag, texto):
    """Devolve a tag <img> com alt=texto, preservando o resto e o fechamento."""
    if re.search(r"\balt\s*=", tag):
        return tag
    if tag.rstrip().endswith("/>"):
        corpo = tag.rstrip()[:-2].rstrip()
        return '%s alt="%s" />' % (corpo, texto)
    corpo = tag.rstrip()[:-1].rstrip()
    return '%s alt="%s">' % (corpo, texto)


def nome_do_modal(html, modal_id):
    """Nome do lider, lido do <h4>/<h3> do modal que o botao abre."""
    m = re.search(r'id="%s"(.{0,2000}?)</h[34]>' % re.escape(modal_id), html, re.S)
    if not m:
        return None
    m2 = re.findall(r"<h[34][^>]*>(.*?)$", m.group(1), re.S)
    if not m2:
        return None
    nome = re.sub(r"<[^>]+>", "", m2[-1])
    nome = nome.replace("Private:", "").strip()
    return nome or None


def main(raiz):
    pub = resolve_public(raiz)
    tocados = 0
    contagem = {"lider": 0, "selo": 0, "decorativa": 0}
    sem_decisao = []
    for dp, _d, fs in os.walk(pub):
        if os.sep + ".git" in dp:
            continue
        for nome in fs:
            if not nome.endswith(".html"):
                continue
            fp = os.path.join(dp, nome)
            rel = os.path.relpath(fp, pub).replace(os.sep, "/")
            h = ler(fp)
            if "<img" not in h:
                continue
            orig = h

            # 1. foto do dono da pratica -> nome lido do modal que ela abre
            def trata_owner(m):
                antes, modal_id, tag = m.groups()
                if re.search(r"\balt\s*=", tag):
                    return m.group(0)
                pessoa = nome_do_modal(h, modal_id)
                if not pessoa:
                    return m.group(0)
                contagem["lider"] += 1
                return antes + com_alt(tag, pessoa)
            h = RE_OWNER.sub(trata_owner, h)

            # 2. selos de reconhecimento -> nome da instituicao
            def trata_img(m):
                tag = m.group(0)
                if re.search(r"\balt\s*=", tag):
                    return tag
                src = RE_SRC.search(tag)
                if not src:
                    return tag
                base = os.path.basename(src.group(1).split("?")[0])
                base = os.path.splitext(base)[0]
                if base in SELOS:
                    contagem["selo"] += 1
                    return com_alt(tag, SELOS[base])
                return tag
            h = RE_IMG.sub(trata_img, h)

            # 3. decorativas -> alt="" (declarado, nao ausente)
            for m in list(RE_IMG.finditer(h))[::-1]:
                tag = m.group(0)
                if re.search(r"\balt\s*=", tag):
                    continue
                pre = h[max(0, m.start() - 300):m.start()]
                classes = re.findall(r'class="([^"]+)"', pre)
                ultima = classes[-1] if classes else ""
                if any(c in ultima for c in DECORATIVAS):
                    contagem["decorativa"] += 1
                    h = h[:m.start()] + com_alt(tag, "") + h[m.end():]

            if h != orig:
                gravar(fp, h)
                tocados += 1

            for m in RE_IMG.finditer(h):
                if not re.search(r"\balt\s*=", m.group(0)):
                    sem_decisao.append(u"%s: %s" % (rel, m.group(0)[:70]))

    print("paginas alteradas: %d" % tocados)
    print("  alt de lider (lido do modal): %d" % contagem["lider"])
    print("  alt de selo (nome da instituicao): %d" % contagem["selo"])
    print("  alt=\"\" decorativa: %d" % contagem["decorativa"])
    if sem_decisao:
        print("SEM DECISAO (%d) — nao inventei alt para estas:" % len(sem_decisao))
        for x in sem_decisao[:10]:
            print("  %s" % x)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
