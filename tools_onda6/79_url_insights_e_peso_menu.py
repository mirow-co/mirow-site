# -*- coding: utf-8 -*-
"""79 — onda 25, S-94 e S-95.

Uso:
    python tools_onda6/79_url_insights_e_peso_menu.py <raiz-que-contem-public>

S-94 — "texto na barra superior/inferior de praticas e negritado enquanto aquele de
  sobre nos nao e - padronizar de uma forma so."
  Os dois submenus passam ao MESMO peso (600). O tamanho segue diferente de
  proposito: Praticas sao 3 palavras em vitrine (26px), Sobre nos e uma lista de 5
  itens (19px) — o pedido era sobre negrito, nao sobre tamanho.

S-96 — "remova 'Para solicitacoes de imprensa, favor entrar em contato com
  mirow@agenciaecomunica.com.br' - nao temos mais essa agencia."
  Sai a linha (e o espacador de 100px que a antecedia). O marcador
  onda12:imprensa-formatacao, que fechava DENTRO desse <h5>, e preservado logo
  antes — senao o script 45 da onda 12 perde a propria ancora.

S-95 — "mudar https://mirow-co.github.io/mirow-site/analises/ -> .../insights/"
  A pagina de insights em PT respondia em /analises/. Passa a /insights/, igual ao
  que EN e DE ja usavam (/en/insights/, /de/insights/). Mesmo procedimento da S-67:
  renomeia a pasta (e a duplicata de raiz do espelho), reescreve os links internos
  por CAMINHO COMPLETO e deixa um stub de redirect no caminho antigo.

Idempotente: rename so se o destino nao existe; CSS em bloco marcado.
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

RENOMEAR = [
    ("pt/analises", "pt/insights"),
    ("analises", "insights"),
]

# so caminho completo — "analises" solto aparece em texto e em nome de arquivo
TROCAS = [
    ("/pt/analises/", "/pt/insights/"),
    ("/analises/", "/insights/"),
    (r"\/pt\/analises\/", r"\/pt\/insights\/"),
    (r"\/analises\/", r"\/insights\/"),
    ("%2Fanalises%2F", "%2Finsights%2F"),
]

MARK_REDIR = "onda25:redirect-s95"
MARK_IMPRENSA = "<!-- /onda12:imprensa-formatacao -->"
AGENCIA = "agenciaecomunica"

CSS = """/* ---- S-94: mesmo peso nos dois submenus -------------------------------
   Praticas estava em 700 e Sobre nos em 400. Agora os dois em 600. O TAMANHO
   segue diferente de proposito (26px x 19px): Praticas sao 3 palavras em
   vitrine, Sobre nos e lista de 5 itens — o pedido era sobre negrito. */
.menu__nav-sublink{font-weight:600 !important}
.menu__nav-sublinks.onda18-praticas .menu__nav-sublink{font-weight:600 !important}"""


def stub(pub, antiga, nova):
    destino = "/mirow-site/%s/" % nova
    html = (u'<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">\n'
            u'<!-- %s: a pagina de insights mudou de /analises/ para /insights/ -->\n'
            u'<meta http-equiv="refresh" content="0;url=%s">\n'
            u'<link rel="canonical" href="%s">\n'
            u'<meta name="robots" content="noindex,follow">\n'
            u'<title>Insights — Mirow &amp; Co.</title></head>\n'
            u'<body><p>Esta página mudou de endereço. '
            u'<a href="%s">Ir para Insights</a>.</p></body></html>\n'
            % (MARK_REDIR, destino, destino, destino))
    d = os.path.join(pub, antiga.replace("/", os.sep))
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "index.html")
    if os.path.exists(p) and ler(p) == html:
        return False
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(html)
    return True


def sem_agencia(html):
    """S-96: remove a linha da agencia de imprensa (e o espacador antes dela)."""
    if AGENCIA not in html:
        return html
    i = html.find(AGENCIA)
    ini = html.rfind('<!-- wp:heading', 0, i)
    if ini < 0:
        return html
    # o espacador imediatamente anterior existe so para separar essa linha
    j = html.rfind("<!-- wp:spacer -->", 0, ini)
    if j >= 0 and (ini - j) < 260:
        ini = j
    fim = html.find("<!-- /wp:heading -->", i)
    if fim < 0:
        return html
    fim += len("<!-- /wp:heading -->")
    # o marcador da onda 12 fechava dentro do <h5>: preserva-lo
    resto = MARK_IMPRENSA if MARK_IMPRENSA in html[ini:fim] else ""
    return html[:ini] + resto + html[fim:]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mudou = escrever_bloco_css(pub, "peso-submenu", CSS, onda="onda25")
    print("bloco onda25:peso-submenu %s" % ("gravado" if mudou else "ja estava igual"))

    movidas = 0
    for antiga, nova in RENOMEAR:
        pa = os.path.join(pub, antiga.replace("/", os.sep))
        pn = os.path.join(pub, nova.replace("/", os.sep))
        if os.path.isdir(pn):
            continue
        if not os.path.isdir(pa):
            print("  AVISO: nao achei %s" % antiga)
            continue
        os.makedirs(os.path.dirname(pn) or pub, exist_ok=True)
        shutil.move(pa, pn)
        movidas += 1
        print("  movida: %s -> %s" % (antiga, nova))
    print("S-95 pastas renomeadas: %d" % movidas)

    alterados = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not (n.endswith(".html") or n.endswith(".xml")):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if MARK_REDIR in h:
                continue
            novo = h
            for de, para in TROCAS:
                if de in novo:
                    novo = novo.replace(de, para)
            if novo != h:
                gravar(p, novo)
                alterados += 1
    print("S-95 arquivos com links reescritos: %d" % alterados)

    stubs = sum(1 for a, nv in RENOMEAR if stub(pub, a, nv))
    print("S-95 stubs de redirect gravados: %d" % stubs)

    # S-96 — a linha da agencia de imprensa sai
    limpas = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if n != "index.html":
                continue
            p2 = os.path.join(dp, n)
            h2 = ler(p2)
            if AGENCIA not in h2:
                continue
            novo2 = sem_agencia(h2)
            if novo2 != h2:
                gravar(p2, novo2)
                limpas += 1
                print("  linha da agencia removida: %s"
                      % os.path.relpath(p2, pub).replace(os.sep, "/"))
    print("S-96 paginas limpas: %d" % limpas)


if __name__ == "__main__":
    main()
