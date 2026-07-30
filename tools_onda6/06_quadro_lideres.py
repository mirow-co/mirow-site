# -*- coding: utf-8 -*-
"""
06_quadro_lideres.py — deixa o quadro de lideres na composicao e ordem exatas.

Uso:  python tools_onda6/06_quadro_lideres.py <raiz-da-arvore>

Composicao decidida pelo Mario (30/07), em todas as linguas:

  PAGINAS DE LIDERES (quadro completo, 8 pessoas):
  1 Andreas Mirow  2 Felipe Diniz  3 Prof. Dr Stephan Friedrich
  4 Elmar Gans (Senior Expert)  5 Renato Alvarenga  6 Michael Munch
  7 Raoni Morais  8 Joao Daniel Ramos (Gerente de projetos / Engagement manager)

  HOME (capa) — revisao do Mario no mesmo dia: so os 4 primeiros
  (Andreas, Felipe, Stephan, Elmar). Os 8 completos ficam nas paginas de lideres.

- Saem: Giulia Turcato, Lucas Duarte, Mariana Nakagawa, Matheus Strapasson.
- Cargos dos demais ficam como o site ja usa; so o Elmar muda (-> Senior Expert).
- Os cards existentes sao REAPROVEITADOS na integra (foto, modal, bio) e apenas
  reordenados/filtrados; quem nao tem card na pagina ganha um card novo com o
  mesmo markup do tema (sem modal, porque nao existe modal para ele naquela pagina).
- Idempotente: reconstroi sempre a mesma sequencia.
- Modais orfaos de quem saiu ficam no HTML (invisiveis) — nada de imagem apagada.
"""
import io
import os
import re
import sys

FOTO_JOAO = "wp-content/uploads/2026/07/joao-daniel-ramos.png"

CARGO_JOAO = {
    "pt": u"Gerente de projetos",
    "en": u"Engagement manager",
    "de": u"Engagement Manager",
}

# ordem final. Campos:
#   chave | nome como aparece no site | cargo a FORCAR no card existente (None = manter
#   o que o site ja usa) | cargo a usar quando o card precisa ser criado | foto do card novo
ORDEM = [
    ("andreas", u"Andreas Mirow", None,
     u"Managing Partner - andreas.mirow@mirow.com.br",
     "wp-content/uploads/2023/02/Andreas-Mirow.png"),
    ("felipe", u"Felipe Diniz", None, u"Partner",
     "wp-content/uploads/2023/02/Felipe-Diniz-1.png"),
    ("stephan", u"Prof. Dr Stephan Friedrich", None, u"Partner",
     "wp-content/uploads/2023/02/prof.png"),
    ("elmar", u"Elmar Gans", u"Senior Expert", u"Senior Expert",
     "wp-content/uploads/2023/02/Elmar-Gans-1.png"),
    ("renato", u"Renato Alvarenga", None, u"Senior Advisor",
     "wp-content/uploads/2023/02/Renato-Alvarenga-1.png"),
    ("michael", u"Michael Munch", None, u"Associate Partner",
     "wp-content/uploads/2023/02/Michael-Munch.png"),
    ("raoni", u"Raoni Morais", None, u"Senior Expert",
     "wp-content/uploads/2023/02/Raoni-Moraes.png"),
    ("joao", u"João Daniel Ramos", None, None, FOTO_JOAO),
]

FORA = [u"Giulia Turcato", u"Lucas Duarte", u"Mariana Nakagawa", u"Matheus Strapasson"]

RE_HOME_CARD = re.compile(r'<button class="home-leaders__card".*?</button>', re.S)
RE_PAG_CARD = re.compile(r'<button class="page-leaders__list-item".*?</button>', re.S)
# cards novos (de quem nao tem modal na pagina) sao <div>, nao <button>
RE_HOME_DIV = re.compile(r'<div class="home-leaders__card".*?</div>', re.S)
RE_PAG_DIV = re.compile(r'<div class="page-leaders__list-item".*?</span></span></div>', re.S)


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def base_prefix(html):
    m = re.search(r'(?:src|href)="(/[^"]*?/)wp-content/', html)
    return m.group(1) if m else "/"


def idioma_do_caminho(rel):
    if rel.startswith("de/"):
        return "de"
    if rel.startswith("en/"):
        return "en"
    return "pt"


def nome_do_card(bloco):
    m = re.search(r'<h4>(.*?)</h4>', bloco, re.S)
    if not m:
        m = re.search(r'page-leaders__list-title">(.*?)<small', bloco, re.S)
    if not m:
        return None
    nome = re.sub(r'<[^>]+>', '', m.group(1))
    nome = nome.replace("Private:", "").strip()
    return nome


def card_home_novo(nome, cargo, foto, prefix):
    return ('<div class="home-leaders__card"><img src="%s%s"><span><h4>%s</h4>'
            '<p>%s</p></span></div>' % (prefix, foto, nome, cargo))


def card_pagina_novo(nome, cargo, foto, prefix):
    return ('<div class="page-leaders__list-item">'
            '<span class="page-leaders__list-wrap-image">'
            '<span class="page-leaders__list-image" style="background-image: url(%s%s)">'
            '</span></span><span class="page-leaders__list-wrap-content">'
            '<span class="page-leaders__list-wrap-content-header">'
            '<h3 class="page-leaders__list-title">%s'
            '<small class="page-leaders__list-role">%s</small></h3></span></span>'
            '</div>' % (prefix, foto, nome, cargo))


def ajusta_cargo(bloco, cargo_alvo):
    """Troca o cargo dentro de um card existente, preservando todo o resto."""
    if not cargo_alvo:
        return bloco
    novo = re.sub(r'(page-leaders__list-role">)[^<]*(</small>)',
                  lambda m: m.group(1) + cargo_alvo + m.group(2), bloco, count=1)
    if novo != bloco:
        return novo
    return re.sub(r'(</h4><p>)[^<]*', lambda m: m.group(1) + cargo_alvo,
                  bloco, count=1)


def processa(path, pub):
    rel = os.path.relpath(path, pub).replace(os.sep, "/")
    with io.open(path, encoding="utf-8") as f:
        html = f.read()
    if "home-leaders__card" in html:
        rexes, novo_card, tipo = (RE_HOME_CARD, RE_HOME_DIV), card_home_novo, "home"
    elif "page-leaders__list-item" in html:
        rexes, novo_card, tipo = (RE_PAG_CARD, RE_PAG_DIV), card_pagina_novo, "pagina"
    else:
        return None
    achados = sorted([m for rex in rexes for m in rex.finditer(html)],
                     key=lambda m: m.start())
    if not achados:
        return None

    prefix = base_prefix(html)
    idioma = idioma_do_caminho(rel)
    por_nome = {}
    for m in achados:
        nome = nome_do_card(m.group(0))
        if nome and nome not in por_nome:
            por_nome[nome] = m.group(0)

    partes = []
    novos = []
    # a home mostra so os 4 primeiros; o quadro completo fica nas paginas de lideres
    composicao = ORDEM[:4] if tipo == "home" else ORDEM
    for chave, nome, cargo, cargo_novo, foto in composicao:
        cargo_alvo = cargo
        if chave == "joao":
            cargo_alvo = CARGO_JOAO[idioma]
            cargo_novo = CARGO_JOAO[idioma]
        if nome in por_nome:
            bloco = ajusta_cargo(por_nome[nome], cargo_alvo)
            # o prefixo "Private:" e resquicio de post privado do WordPress
            bloco = bloco.replace("Private: ", "").replace("Private:", "")
            partes.append(bloco)
        else:
            partes.append(novo_card(nome, cargo_novo, foto, prefix))
            novos.append(nome)

    ini, fim = achados[0].start(), achados[-1].end()
    novo_html = html[:ini] + "".join(partes) + html[fim:]
    if novo_html == html:
        print("sem mudanca: %s (%s)" % (rel, tipo))
        return False
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(novo_html)
    removidos = [n for n in FORA if n in por_nome]
    print("quadro de lideres refeito: %s (%s, %d cards; novos: %s; fora: %s)"
          % (rel, tipo, len(partes), ", ".join(novos) or "-",
             ", ".join(removidos) or "-"))
    return True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = 0
    vistos = 0
    for root, _dirs, files in os.walk(pub):
        for f in files:
            if f != "index.html":
                continue
            path = os.path.join(root, f)
            with io.open(path, encoding="utf-8") as fh:
                cabeca = fh.read()
            if "home-leaders__card" not in cabeca and "page-leaders__list-item" not in cabeca:
                continue
            vistos += 1
            if processa(path, pub):
                alterados += 1
    print("\nresumo: %d de %d pagina(s) com quadro de lideres alterada(s)"
          % (alterados, vistos))


if __name__ == "__main__":
    main()
