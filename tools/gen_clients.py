# -*- coding: utf-8 -*-
"""gen_clients.py — gera a barra de logos de clientes a partir do arquivo mestre (P3).

Uso:
    python tools/gen_clients.py <raiz-que-contem-public> [--mestre=<caminho.json>] [--dry]

POR QUE ESTE ARQUIVO EXISTE
---------------------------
A Sotreq ficou fora da barra de clientes por semanas, apesar de decidida pelo
sócio, porque havia DUAS fontes de verdade: a decisão (memória + doc de logos) e
a lista de `<li>` escrita à mão dentro do HTML. Os agentes seguiram o HTML.

A partir daqui existe UMA fonte: o arquivo mestre de curadoria, no repo PRIVADO
`mirow-co/mirow-marketing`:

    08_Site/2026-07-30_clients-curadoria-interna.json

Entra na barra quem tem `clearance == "partner-listed"`. O HTML das 4 homes é
GERADO deste arquivo — editar a barra à mão é violação de processo.

O que este script NÃO faz de propósito
--------------------------------------
Não silencia cliente liberado que esteja sem arquivo de logo. Ele reporta e sai
com código 1: cliente liberado e ausente da barra é exatamente o bug que a regra
existe para impedir. Hoje é o caso da Sotreq (issue S-03 — falta o arquivo).

Também grava `tools/clients-publicados.json` (só wordmark + slug, nada interno),
que é o que a suíte `verificacoes.py` lê para conferir a barra. Assim a asserção
não tem lista hardcoded que possa divergir.
"""
import io
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "tools_onda6"))

from _onda7_css import gravar, ler, resolve_public  # noqa: E402

MESTRE_PADRAO = os.path.join(
    os.path.expanduser("~"), "OneDrive - Mirow", "Mirow & Co", "05_Marketing",
    "05_NovoMarketing", "08_Site", "2026-07-30_clients-curadoria-interna.json")

HOMES = ["pt/index.html", "en/index.html", "de/index.html", "en/homepage/index.html"]

DIR_LOGOS = "wp-content/uploads/2026/07/clientes"

# Ordem de exibição, por wordmark do mestre. Curadoria visual (alterna alturas e
# setores para a barra não ficar com dois logos parecidos lado a lado), não
# ordem alfabética nem por número de projetos.
ORDEM = ["MERCEDES-BENZ", "VOLKSWAGEN", "IPIRANGA", "SUZANO", "KLABIN", "DEXCO",
         "EDP", "ENERGISA", "ENEVA", "TAESA", "YARA", "WILSON SONS",
         "SANTOS BRASIL", "XP", "SULAMÉRICA", "SOTREQ"]

# Logos cujo desenho é alto (mais verticais) e precisam da classe --alto para
# não estourar a linha da barra.
ALTOS = {"volkswagen", "klabin", "yara", "santos-brasil"}

# `?ver=1` no src dos SVGs NÃO é cache-busting — é proteção, e é load-bearing.
# O plugin svgs-inline do tema só inlina quando o src termina em "svg"
# (`h.endsWith("svg")`); com a query ele ignora o <img> e o navegador renderiza o
# SVG como imagem. Sem isso os logos entram inline no mesmo documento, as ids/
# classes genéricas deles (`a`, `st0`, `clip0`) colidem, e os logos saem picados.
# Ver tools_onda6/14_logos_clientes_sem_inline_svg.py. Não remover.
QUERY_ANTI_INLINE = "?ver=1"

# Nome do arquivo de logo por wordmark, quando não é o slug óbvio.
SLUG = {
    "MERCEDES-BENZ": "mercedes-benz", "WILSON SONS": "wilson-sons",
    "SANTOS BRASIL": "santos-brasil", "SULAMÉRICA": "sulamerica",
}

# Texto do alt por wordmark (o alt é conteúdo, não vem do wordmark em caps).
ALT = {
    "MERCEDES-BENZ": "Mercedes-Benz", "VOLKSWAGEN": "Volkswagen", "IPIRANGA": "Ipiranga",
    "SUZANO": "Suzano", "KLABIN": "Klabin", "DEXCO": "Dexco", "EDP": "EDP",
    "ENERGISA": "Energisa", "ENEVA": "Eneva", "TAESA": "Taesa", "YARA": "Yara",
    "WILSON SONS": "Wilson Sons", "SANTOS BRASIL": "Santos Brasil", "XP": "XP Inc.",
    "SULAMÉRICA": "SulAmerica", "SOTREQ": "Sotreq",
}


def slug_de(wordmark):
    return SLUG.get(wordmark, wordmark.lower().replace(" ", "-"))


def achar_logo(pub, slug):
    """Devolve o nome do arquivo de logo (com extensão) ou None."""
    for ext in ("svg", "png", "jpg"):
        nome = "%s.%s" % (slug, ext)
        if os.path.exists(os.path.join(pub, DIR_LOGOS.replace("/", os.sep), nome)):
            return nome
    return None


def montar_lista(pub, liberados):
    """Monta os <li> na ordem curada. Devolve (html, publicados, sem_logo)."""
    por_wordmark = dict((c["wordmark"], c) for c in liberados)
    desconhecidos = [w for w in por_wordmark if w not in ORDEM]
    if desconhecidos:
        raise SystemExit(
            u"cliente liberado que não está na ORDEM de exibição: %s\n"
            u"adicione em ORDEM/ALT (e em ALTOS/SLUG se preciso) antes de gerar."
            % ", ".join(sorted(desconhecidos)))

    lis, publicados, sem_logo = [], [], []
    for wordmark in ORDEM:
        if wordmark not in por_wordmark:
            continue
        slug = slug_de(wordmark)
        arq = achar_logo(pub, slug)
        if not arq:
            sem_logo.append((wordmark, slug))
            continue
        classe = "clientes-logos__item"
        if slug in ALTOS:
            classe += " clientes-logos__item--alto"
        query = QUERY_ANTI_INLINE if arq.endswith(".svg") else ""
        lis.append(
            u'        <li class="%s"><img src="{PREFIXO}%s/%s%s" alt="%s" '
            u'loading="lazy" decoding="async"></li>'
            % (classe, DIR_LOGOS, arq, query, ALT[wordmark]))
        publicados.append({"wordmark": wordmark, "slug": slug, "arquivo": arq})
    return u"\n".join(lis), publicados, sem_logo


def aplicar(pub, corpo_li, dry=False):
    """Substitui o conteúdo do <ul class="clientes-logos__list"> nas 4 homes."""
    mudou = []
    rex = re.compile(r'(<ul class="clientes-logos__list">)(.*?)(\s*</ul>)', re.S)
    for rel in HOMES:
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        m = rex.search(h)
        if not m:
            raise SystemExit(u"não achei a barra de clientes em %s" % rel)
        prefixo = re.search(r'(?:src|href)="(/[^"]*?/)wp-content/', h)
        prefixo = prefixo.group(1) if prefixo else "/"
        novo_corpo = u"\n" + corpo_li.replace("{PREFIXO}", prefixo)
        if m.group(2) == novo_corpo:
            continue
        # troca só o miolo do <ul>: o </ul> e a indentação dele ficam como estão
        novo = h[:m.start(2)] + novo_corpo + h[m.end(2):]
        if not dry:
            gravar(p, novo)
        mudou.append(rel)
    return mudou


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    dry = "--dry" in sys.argv
    mestre = MESTRE_PADRAO
    for a in sys.argv[2:]:
        if a.startswith("--mestre="):
            mestre = a[len("--mestre="):]
    if not os.path.exists(mestre):
        raise SystemExit(
            u"arquivo mestre não encontrado: %s\n"
            u"ele mora no repo PRIVADO mirow-co/mirow-marketing, em\n"
            u"08_Site/2026-07-30_clients-curadoria-interna.json\n"
            u"passe o caminho com --mestre=<...>" % mestre)

    with io.open(mestre, encoding="utf-8") as f:
        todos = json.load(f)
    liberados = [c for c in todos if c.get("clearance") == "partner-listed"]
    barrados = [c for c in todos if c.get("clearance") != "partner-listed"]

    print(u"mestre: %s" % mestre)
    print(u"%d cliente(s) no mestre · %d liberado(s) · %d fora"
          % (len(todos), len(liberados), len(barrados)))
    for c in barrados:
        print(u"  fora: %s (clearance=%s)" % (c["wordmark"], c.get("clearance")))

    corpo, publicados, sem_logo = montar_lista(pub, liberados)
    mudou = aplicar(pub, corpo, dry=dry)

    # lista pública que a suíte de verificações lê (sem nada interno)
    saida = os.path.join(AQUI, "clients-publicados.json")
    if not dry:
        with io.open(saida, "w", encoding="utf-8", newline="\n") as f:
            json.dump(publicados, f, ensure_ascii=False, indent=2)
            f.write(u"\n")

    print(u"%d logo(s) na barra%s" % (len(publicados), u" (dry-run)" if dry else u""))
    print(u"páginas alteradas: %s" % (u", ".join(mudou) if mudou else u"nenhuma (já estava igual)"))
    if not dry:
        print(u"lista publicada em tools/clients-publicados.json")

    if sem_logo:
        print(u"\nBLOQUEIO — cliente(s) liberado(s) SEM arquivo de logo em %s:" % DIR_LOGOS)
        for wordmark, slug in sem_logo:
            print(u"  %s — falta %s.svg (ou .png/.jpg)" % (wordmark, slug))
        print(u"Liberado e ausente da barra é exatamente o bug que este script existe\n"
              u"para impedir. Providencie o arquivo (issue S-03) e rode de novo.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
