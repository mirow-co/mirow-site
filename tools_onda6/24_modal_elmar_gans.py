# -*- coding: utf-8 -*-
"""
24_modal_elmar_gans.py — onda 8, pedido 3 do Mario: o Elmar Gans nao abria bio.

Uso:  python tools_onda6/24_modal_elmar_gans.py <raiz-que-contem-public>

Diagnostico (antes de mexer em nada)
------------------------------------
Nas 4 paginas de lideres do espelho o card do Elmar ja tem os icones de LinkedIn
(linkedin.com/in/elmar-gans-2329a422/) e de e-mail — o que faltava era o MODAL:
o botao dele aponta para

    data-bs-target="#modal_?post_type=leader&p=129"   (PT; EN p=2779, DE p=3452)

ou seja, o permalink quebrado que o WordPress gerou para o post "leader" dele. O
modal com esse id nao existe na pagina de lideres — ele ficou orfao nas paginas
de praticas (branchen/practice/pratica), que o WP renderizava com a lista inteira
de lideres. Resultado: clicar no card nao abria nada, e o seletor invalido ainda
derrubava o handler do Bootstrap.

O que este script faz
---------------------
1. Colhe o modal ORIGINAL do Elmar (por idioma) nas paginas onde ele sobrevive —
   nada de bio inventada: e o texto que o site antigo ja publicava.
2. Corrige tres coisas nesse markup: o id vira `modal_elmar-gans`, o titulo perde
   o prefixo "Private: " que o WP vazou, e o cargo passa a ser o mesmo do card
   (Senior Expert — decisao do Andreas), no lugar do antigo "Managing Partner".
3. Insere o modal na pagina de lideres e reaponta o card para `#modal_elmar-gans`.

Nas HOMES o problema era outro (e e o que o Mario viu): o quadro tem os 4
primeiros lideres, mas o card do Elmar tinha sido criado na onda 6 como um <div>
mudo — sem o icone de LinkedIn e sem abrir modal, porque naquele momento nao
existia modal dele em pagina nenhuma. Agora que existe, o card vira <button>
igual aos outros tres (icone colhido dos proprios cards da pagina) e o modal
entra na home tambem.

Idempotente: reescreve o modal se ja existir.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, idioma_da_pagina, ler, resolve_public  # noqa: E402

NOME = u"Elmar Gans"
SLUG = u"elmar-gans"
# ids do post "leader" dele no WordPress, por idioma (lidos do proprio espelho)
PID = {"pt": "129", "en": "2779", "de": "3452"}

RE_DIV = re.compile(r"<div\b|</div>")
RE_CARD = re.compile(r'<button class="page-leaders__list-item".*?</button>', re.S)
RE_HOME_DIV = re.compile(r'<div class="home-leaders__card">.*?</div>', re.S)
RE_HOME_BTN = re.compile(r'<button class="home-leaders__card".*?</button>', re.S)


def fim_balanceado(html, ini):
    nivel = 0
    for m in RE_DIV.finditer(html, ini):
        nivel += 1 if m.group(0) == "<div" else -1
        if nivel == 0:
            return m.end()
    return -1


def recorta(html, marca):
    pos = html.find(marca)
    if pos < 0:
        return None
    ini = html.rfind("<div", 0, pos)
    fim = fim_balanceado(html, ini)
    return html[ini:fim] if fim > 0 else None


def colher_originais(pub):
    """Modal original do Elmar por idioma, colhido das paginas que ainda o tem."""
    achados = {}
    for dirpath, _dirs, files in os.walk(pub):
        if len(achados) == len(PID):
            break
        for nome in files:
            if nome != "index.html":
                continue
            path = os.path.join(dirpath, nome)
            try:
                html = ler(path)
            except Exception:
                continue
            if "post_type=leader" not in html or NOME not in html:
                continue
            for idioma, pid in PID.items():
                if idioma in achados:
                    continue
                bloco = recorta(html, 'id="modal_?post_type=leader&p=%s"' % pid)
                if bloco and NOME in bloco:
                    achados[idioma] = (bloco, os.path.relpath(path, pub).replace(os.sep, "/"))
    return achados


def ajustar(bloco, cargo):
    bloco = bloco.replace('id="modal_?post_type=leader&p=%s"' % PID["pt"],
                          'id="modal_%s"' % SLUG)
    bloco = bloco.replace('id="modal_?post_type=leader&p=%s"' % PID["en"],
                          'id="modal_%s"' % SLUG)
    bloco = bloco.replace('id="modal_?post_type=leader&p=%s"' % PID["de"],
                          'id="modal_%s"' % SLUG)
    # o WP vazou o prefixo "Private: " do post nao publicado
    bloco = bloco.replace(u">Private: %s<" % NOME, u">%s<" % NOME)
    # cargo do modal = cargo do card (Senior Expert), no lugar de "Managing Partner"
    bloco = re.sub(r'(<h5 class="modal-leaders__role">)[^<]*(</h5>)',
                   lambda m: m.group(1) + cargo + m.group(2), bloco, count=1)
    return bloco


def acha_card(html):
    """Card do Elmar na pagina: o do quadro completo OU o da home. (m, cargo)."""
    for m in RE_CARD.finditer(html):
        if u'list-title">%s<' % NOME in m.group(0):
            cargo = re.search(r'<small class="page-leaders__list-role">([^<]*)</small>',
                              m.group(0))
            return m, (cargo.group(1) if cargo else u"Senior Expert"), "lideres"
    for rex in (RE_HOME_BTN, RE_HOME_DIV):
        for m in rex.finditer(html):
            if u"<h4>%s</h4>" % NOME in m.group(0):
                cargo = re.search(r"<p>([^<]*)", m.group(0))
                return m, (cargo.group(1).strip() if cargo else u"Senior Expert"), "home"
    return None, None, None


def card_home(bloco, html):
    """Transforma o card <div> da home em <button> que abre o modal.

    A arte do icone e COLHIDA de outro card da propria pagina — nenhum SVG novo.
    """
    if bloco.startswith("<button"):
        return re.sub(r'data-bs-target="#[^"]*"',
                      'data-bs-target="#modal_%s"' % SLUG, bloco, count=1)
    img = re.search(r"<img [^>]*>", bloco)
    cargo = re.search(r"<p>([^<]*)", bloco)
    outro = RE_HOME_BTN.search(html)
    svg = re.search(r"<svg.*?</svg>", outro.group(0), re.S) if outro else None
    return (u'<button class="home-leaders__card" data-bs-toggle="modal"  '
            u'data-bs-target="#modal_%s">%s<span><h4>%s</h4><p>%s%s</p></span></button>'
            % (SLUG, img.group(0) if img else "", NOME,
               cargo.group(1).strip() if cargo else u"Senior Expert",
               svg.group(0) if svg else ""))


def processa(path, pub, originais):
    rel = os.path.relpath(path, pub).replace(os.sep, "/")
    html = ler(path)
    if NOME not in html:
        return None
    card, cargo, tipo = acha_card(html)
    if card is None:
        return None

    idioma = idioma_da_pagina(html)
    if idioma not in originais:
        print("AVISO: sem modal original em %s para %s" % (idioma, rel))
        return False
    modal = ajustar(originais[idioma][0], cargo)

    orig = html
    # 1) card aponta para o modal novo (na home, o <div> vira <button>)
    if tipo == "home":
        novo_card = card_home(card.group(0), html)
    else:
        novo_card = re.sub(r'data-bs-target="#[^"]*"',
                           'data-bs-target="#modal_%s"' % SLUG, card.group(0), count=1)
    html = html[:card.start()] + novo_card + html[card.end():]

    # 2) modal: substitui se ja existe, senao insere depois do ultimo modal
    marca = 'id="modal_%s"' % SLUG
    pos = html.find(marca)
    if pos >= 0:
        ini = html.rfind("<div", 0, pos)
        fim = fim_balanceado(html, ini)
        html = html[:ini] + modal + html[fim:]
    else:
        ult = html.rfind('class="modal fade"')
        if ult < 0:
            print("AVISO: nenhum modal existente em %s — nada feito" % rel)
            return False
        ini = html.rfind("<div", 0, ult)
        fim = fim_balanceado(html, ini)
        html = html[:fim] + modal + html[fim:]

    if html == orig:
        print("sem mudanca: %s" % rel)
        return False
    gravar(path, html)
    print("modal do Elmar aplicado (%s): %s" % (idioma, rel))
    return True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    originais = colher_originais(pub)
    for idioma in sorted(originais):
        print("modal original %s colhido de %s" % (idioma, originais[idioma][1]))
    faltando = [i for i in PID if i not in originais]
    if faltando:
        print("AVISO: sem original para: %s" % ", ".join(sorted(faltando)))

    alterados = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            if processa(os.path.join(dirpath, nome), pub, originais):
                alterados += 1
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
