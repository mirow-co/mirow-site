# -*- coding: utf-8 -*-
"""69 — onda 18, S-67/S-68/S-69 (issues #125 #126 #127): a pagina "Nosso Trabalho"
vira "Nossos Valores".

Uso:
    python tools_onda6/69_nossos_valores.py <raiz-que-contem-public>

S-67  "ao inves de .../pt/sobre-nos/nosso-trabalho/, fazer nossos-valores"
      - renomeia a pasta nos 3 idiomas (+ as 2 duplicatas de raiz do espelho):
          pt/sobre-nos/nosso-trabalho   -> pt/sobre-nos/nossos-valores
          sobre-nos/nosso-trabalho      -> sobre-nos/nossos-valores
          en/about-us/our-work          -> en/about-us/our-values
          de/ueber-uns/unsere-arbeit    -> de/ueber-uns/unsere-werte
          de/unsere-arbeit              -> de/unsere-werte
      - reescreve os links internos (menus, hreflang, canonical, sitemap): so
        padroes de CAMINHO COMPLETO, para nao acertar a classe "page-our-work"
        nem a imagem "bg-banner-our-work.png"
      - deixa no caminho antigo um index.html de redirect (o GitHub Pages nao tem
        redirect de servidor; e o mesmo padrao do public/index.html da raiz)

S-68  "retire o bloco 'Conheca mais sobre o nosso trabalho', va direto para nossa
      cultura ethos mirow e depois por que a mirow"
      - sai a <section class="internal-banner"> (o <h1> dela ja era vazio; o unico
        texto era exatamente esse subtitulo). A ordem cultura -> reasons ja e a
        pedida, entao nada a reordenar.

S-69  "o bloco solucoes para varios setores precisa ser removido daqui"
      - sai a <section class="segments"> (Industrias / Solucoes para diversos
        setores). O conteudo de setores passa a viver na home, na S-70.

NAO FEITO de proposito (fora do pedido, precisa de decisao do Mario): o RÓTULO do
menu segue "Nosso Trabalho" / "Our Work" / "Unsere Arbeit" apontando para a URL
nova. Trocar o rotulo para "Nossos Valores" e um pedido novo.

Idempotente: rename so acontece se o destino nao existe; remocoes deixam marcador.
"""
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

# (pasta antiga, pasta nova, url antiga, url nova)
RENOMEAR = [
    ("pt/sobre-nos/nosso-trabalho", "pt/sobre-nos/nossos-valores"),
    ("sobre-nos/nosso-trabalho", "sobre-nos/nossos-valores"),
    ("en/about-us/our-work", "en/about-us/our-values"),
    ("de/ueber-uns/unsere-arbeit", "de/ueber-uns/unsere-werte"),
    ("de/unsere-arbeit", "de/unsere-werte"),
]

# trocas de link, sempre com caminho completo (nunca o fragmento solto)
TROCAS = [
    ("/pt/sobre-nos/nosso-trabalho/", "/pt/sobre-nos/nossos-valores/"),
    ("/sobre-nos/nosso-trabalho/", "/sobre-nos/nossos-valores/"),
    ("/en/about-us/our-work/", "/en/about-us/our-values/"),
    ("/de/ueber-uns/unsere-arbeit/", "/de/ueber-uns/unsere-werte/"),
    ("/de/unsere-arbeit/", "/de/unsere-werte/"),
    # variantes escapadas do JSON-LD (\/ em vez de /)
    (r"\/pt\/sobre-nos\/nosso-trabalho\/", r"\/pt\/sobre-nos\/nossos-valores\/"),
    (r"\/en\/about-us\/our-work\/", r"\/en\/about-us\/our-values\/"),
    (r"\/de\/ueber-uns\/unsere-arbeit\/", r"\/de\/ueber-uns\/unsere-werte\/"),
    # oembed (aponta para o WP, que vai morrer — trocado so por consistencia)
    ("%2Fsobre-nos%2Fnosso-trabalho%2F", "%2Fsobre-nos%2Fnossos-valores%2F"),
    ("%2Fabout-us%2Four-work%2F", "%2Fabout-us%2Four-values%2F"),
    ("%2Fueber-uns%2Funsere-arbeit%2F", "%2Fueber-uns%2Funsere-werte%2F"),
]

MARK_REDIR = "onda18:redirect-s67"
MARK_S68 = "<!-- onda18:s68-banner-removido -->"
MARK_S69 = "<!-- onda18:s69-segments-removido -->"

TITULOS = {
    "pt/sobre-nos/nossos-valores": u"Nossos Valores — Mirow & Co.",
    "sobre-nos/nossos-valores": u"Nossos Valores — Mirow & Co.",
    "en/about-us/our-values": u"Our Values — Mirow & Co.",
    "de/ueber-uns/unsere-werte": u"Unsere Werte — Mirow & Co.",
    "de/unsere-werte": u"Unsere Werte — Mirow & Co.",
}


def remover_secao(html, classe, marcador):
    """Remove <section class="classe"> ... </section> (1a ocorrencia)."""
    if marcador in html:
        return html
    alvo = '<section class="%s"' % classe
    ini = html.find(alvo)
    if ini < 0:
        return html
    fim = html.find("</section>", ini)
    if fim < 0:
        return html
    fim += len("</section>")
    return html[:ini] + marcador + html[fim:]


def stub_redirect(pub, antiga, nova):
    """index.html de redirect no caminho antigo."""
    destino = "/mirow-site/%s/" % nova
    titulo = TITULOS.get(nova, u"Mirow & Co.")
    html = (u'<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">\n'
            u'<!-- %s: a pagina mudou de nosso-trabalho para nossos-valores -->\n'
            u'<meta http-equiv="refresh" content="0;url=%s">\n'
            u'<link rel="canonical" href="%s">\n'
            u'<meta name="robots" content="noindex,follow">\n'
            u'<title>%s</title></head>\n'
            u'<body><p>Esta página mudou de endereço. '
            u'<a href="%s">Ir para Nossos Valores</a>.</p></body></html>\n'
            % (MARK_REDIR, destino, destino, titulo, destino))
    d = os.path.join(pub, antiga.replace("/", os.sep))
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "index.html")
    atual = ler(p) if os.path.exists(p) else ""
    if atual == html:
        return False
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(html)
    return True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    # (1) S-67 — renomear as pastas
    movidas = 0
    for antiga, nova in RENOMEAR:
        pa = os.path.join(pub, antiga.replace("/", os.sep))
        pn = os.path.join(pub, nova.replace("/", os.sep))
        if os.path.isdir(pn):
            continue  # ja renomeado
        if not os.path.isdir(pa):
            print("  AVISO: nao achei %s" % antiga)
            continue
        os.makedirs(os.path.dirname(pn), exist_ok=True)
        shutil.move(pa, pn)
        movidas += 1
        print("  movida: %s -> %s" % (antiga, nova))
    print("S-67 pastas renomeadas: %d" % movidas)

    # (2) S-67 — reescrever links internos em todo o espelho
    alterados = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not (n.endswith(".html") or n.endswith(".xml")):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if MARK_REDIR in h:
                continue  # o proprio stub
            novo = h
            for de, para in TROCAS:
                if de in novo:
                    novo = novo.replace(de, para)
            if novo != h:
                gravar(p, novo)
                alterados += 1
    print("S-67 arquivos com links reescritos: %d" % alterados)

    # (3) S-67 — stub de redirect no caminho antigo
    stubs = 0
    for antiga, nova in RENOMEAR:
        if stub_redirect(pub, antiga, nova):
            stubs += 1
    print("S-67 stubs de redirect gravados: %d" % stubs)

    # (4) S-68 e S-69 — limpeza da propria pagina
    tocadas = 0
    for _antiga, nova in RENOMEAR:
        p = os.path.join(pub, nova.replace("/", os.sep), "index.html")
        if not os.path.exists(p):
            continue
        h = ler(p)
        novo = remover_secao(h, "internal-banner", MARK_S68)
        novo = remover_secao(novo, "segments", MARK_S69)
        if novo != h:
            gravar(p, novo)
            tocadas += 1
            print("  limpa: %s" % nova)
    print("S-68/S-69 paginas limpas: %d" % tocadas)


if __name__ == "__main__":
    main()
