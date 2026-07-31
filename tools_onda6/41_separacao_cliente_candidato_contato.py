# -*- coding: utf-8 -*-
"""
41_separacao_cliente_candidato_contato.py — onda 11, issue S-12 (parte contato).

Uso:  python tools_onda6/41_separacao_cliente_candidato_contato.py <raiz-que-contem-public>

Pedido (issue mirow-co/mirow-marketing#61): separar claramente o "Fale Conosco"
de CLIENTE do de CANDIDATO — feedback dos estagiarios: hoje os dois se
confundem.

Na pagina de contato (que ja esta enxuta desde a onda 9: banner -> formulario
-> barra "transform your career", ver 29_contato_enxuto.py), o formulario e a
barra de carreiras ja SAO os dois caminhos certos, so faltam rotulados de forma
explicita:

  1. <h2 class="contact__title"> ganha uma linha "Voce e cliente?" (equivalente
     em EN/DE) antes do titulo original.
  2. O <h3> da barra de carreiras ganha "Voce e candidato?" antes do texto
     original.

Zero CSS novo: o rotulo entra como <small> DENTRO dos elementos que ja tem cor
branca garantida por regra do tema (`.contact__title{color:var(--whiteColor)}`
e `.links__list-link{color:var(--whiteColor)}`, herdada pelo h3 filho) — nao
precisa de nenhuma classe ou estilo novo.

Paginas atingidas: as 5 variantes de contato do espelho (mesma lista do
29_contato_enxuto.py e do 40) — contato/ e novo/contato/ sao copias identicas
de pt/contato/, mantidas em sincronia por consistencia.

Idempotente: remove o marcador antigo antes de inserir o novo.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, idioma_da_pagina, ler, resolve_public  # noqa: E402

PAGINAS = [
    "contato/index.html",
    "pt/contato/index.html",
    "en/contact-us/index.html",
    "de/kontakt/index.html",
    "novo/contato/index.html",
]

ROTULO_CLIENTE = {
    "pt": u"Você é cliente?",
    "en": u"Are you a client?",
    "de": u"Sind Sie Kunde?",
}
ROTULO_CANDIDATO = {
    "pt": u"Você é candidato?",
    "en": u"Are you a candidate?",
    "de": u"Sind Sie Bewerber?",
}

INI_CLI = u"<!-- onda11:s12-persona-cliente -->"
FIM_CLI = u"<!-- /onda11:s12-persona-cliente -->"
INI_CAN = u"<!-- onda11:s12-persona-candidato -->"
FIM_CAN = u"<!-- /onda11:s12-persona-candidato -->"

RE_H2 = re.compile(r'(<h2 class="contact__title">)(.*?)(</h2>)', re.S)
RE_H3 = re.compile(r'(<a class="links__list-link[^"]*"[^>]*>\s*<h3>)(.*?)(</h3>)', re.S)


def tira_marcador(texto, ini, fim):
    return re.sub(re.escape(ini) + r".*?" + re.escape(fim), "", texto, flags=re.S)


def aplicar(html, idioma):
    mudou = False

    def sub_h2(m):
        miolo = tira_marcador(m.group(2), INI_CLI, FIM_CLI)
        novo_miolo = u"%s<small>%s</small><br>%s%s" % (
            INI_CLI, ROTULO_CLIENTE[idioma], FIM_CLI, miolo)
        return m.group(1) + novo_miolo + m.group(3)

    novo, n = RE_H2.subn(sub_h2, html, count=1)
    if n:
        mudou = mudou or (novo != html)
        html = novo

    def sub_h3(m):
        miolo = tira_marcador(m.group(2), INI_CAN, FIM_CAN)
        novo_miolo = u"%s<small>%s</small><br>%s%s" % (
            INI_CAN, ROTULO_CANDIDATO[idioma], FIM_CAN, miolo)
        return m.group(1) + novo_miolo + m.group(3)

    novo, n = RE_H3.subn(sub_h3, html, count=1)
    if n:
        mudou = mudou or (novo != html)
        html = novo

    return html, mudou


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    alterados = 0
    for rel in PAGINAS:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: nao existe %s" % rel)
            continue
        html = ler(path)
        idioma = idioma_da_pagina(html)
        antes = html
        novo, _ = aplicar(html, idioma)
        if novo != antes:
            gravar(path, novo)
            alterados += 1
            print("rotulos cliente/candidato (%s): %s" % (idioma, rel))
        else:
            print("sem mudanca: %s" % rel)

    print("\nresumo: %d arquivo(s) HTML alterado(s)" % alterados)


if __name__ == "__main__":
    main()
