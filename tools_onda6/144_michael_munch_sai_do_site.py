# -*- coding: utf-8 -*-
"""Onda 68 -- Michael Munch sai do site, de tudo.

PEDIDO DO MARIO (20/08/2026, verbatim): "inclusive pode retirar o michael munch
totalmente da pagina, de tudo. ele nao trabalha mais aqui desde ontem".

Mesma regra da onda 33 ("quem saiu sai do site", `88_quem_saiu_sai_do_site.py`), com
uma diferenca que muda o trabalho: os 4 daquela onda ja estavam FORA da listagem de
lideres e do JSON-LD -- sobravam so as paginas de perfil, stubs e autoria. O Michael
esta DENTRO: card na listagem dos 3 idiomas, no `Person` do JSON-LD, e -- desde
hoje -- tambem nas 3 homes, porque a onda 68 levou o bloco da onda 59 para elas.

PEGADA MEDIDA antes de mexer (14 arquivos HTML + 2 de dados):

    3 paginas de perfil    pt/lider/michael-munch, en/leader/..., de/lider/...
    3 listagens de lider   card + no Person
    3 homes                no Person (entrou hoje, na propria onda 68)
    5 stubs                pt/lider/591, pt/leader/591, lider/591, leader/591,
                           de/leader/michael-munch
    2 dados                sitemap.xml, busca-indice.json
    2 assets               og-lider-michael-munch.jpg, Michael-Munch.png

O QUE ESTE SCRIPT FAZ:
  1. remove o `<button class="page-leaders__list-item">` dele das 3 listagens, por
     varredura BALANCEADA de tag (nao por regex guloso);
  2. grava stub de redirect nas 3 paginas de perfil, destino = listagem de lideres
     do idioma;
  3. reaponta os 5 stubs DIRETO para a listagem -- senao o visitante daria dois
     saltos (stub -> perfil, que agora tambem e stub), o que a S107 proibe;
  4. apaga os 2 assets que ficam orfaos.

O QUE FICA FORA DESTE SCRIPT, de proposito, porque e edicao de CODIGO e nao de
conteudo: a entrada dele em `PAGINAS`/`KNOWS` do `110_geo_bios_lideres.py`. Sai de
la na mao, e o `111` regenera o JSON-LD das 3 listagens E das 3 homes sem ele. Se
ficasse aqui, o script mexeria em si mesmo a cada onda.

REGISTRO DE UM ACHADO QUE ESTE PEDIDO TORNOU OBSOLETO: a `S151` acusou, no gate
desta onda, que `pt/lider/michael-munch/` ainda referenciava o slug antigo `591` em
8 lugares do JSON-LD do Yoast. A referencia existia desde a onda 59 e estava
ESCAPADA (`https:\\/\\/...\\/591\\/`); a S151 procurava a forma limpa e passou verde
por um mes. Quem a revelou foi o `143`, que reserializou o JSON com json.dumps do
Python (que nao escapa barra). Com o Michael saindo, as 8 referencias saem junto --
mas a cegueira da S151 e real e vale como licao (erro 17 do CLAUDE.md).

Idempotente: no 2o run os cards ja nao existem, os perfis ja sao stub, os stubs ja
apontam para a listagem e os assets ja foram apagados -- reporta 0 mudanca.

Uso:  python tools_onda6/144_michael_munch_sai_do_site.py .
"""

from __future__ import print_function

import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _onda7_css import gravar, ler, resolve_public  # noqa: E402

# O marcador NAO carrega o nome nem o slug da pessoa: ele vai para dentro de um
# comentario HTML que o publico recebe, e a primeira versao dizia
# `onda68:michael-munch-saiu` -- ou seja, o pedido era tirar "de tudo" e eu deixava
# o slug no ar. Quem apontou foi a propria varredura de pegada deste script.
MARK = "onda68:perfil-encerrado"

# O modal de bio e um elemento SEPARADO do card e sobrevive a remocao dele -- foi
# exatamente o achado da onda 33 (4 modais orfaos na en/homepage). Medido: depois que
# o card sai, ZERO referencia ao id do modal fora dele mesmo. HTML morto que so o
# robo le. Ele e localizado pelo CONTEUDO (ver `remover_modal`), porque o id difere
# entre as linguas.

NOME = u"Michael Munch"
SLUG = "michael-munch"

PERFIS = {
    "pt": "pt/lider/michael-munch/index.html",
    "en": "en/leader/michael-munch/index.html",
    "de": "de/lider/michael-munch/index.html",
}

LISTAGENS = {
    "pt": "pt/sobre-nos/lideres/index.html",
    "en": "en/about-us/leaders/index.html",
    "de": "de/ueber-uns/fuehrungskraefte/index.html",
}

# Sem o prefixo `/mirow-site/`: o cutover de 11/08 poe o espelho na raiz do dominio.
# O `88` da onda 33 ainda tem o prefixo antigo nas constantes -- funciona porque
# aquele trabalho ja esta aplicado, mas nao serve de molde para caminho novo.
DESTINO = {
    "pt": "/pt/sobre-nos/lideres/",
    "en": "/en/about-us/leaders/",
    "de": "/de/ueber-uns/fuehrungskraefte/",
}

TEXTO = {
    "pt": (u"Esta pessoa não faz mais parte da equipe.",
           u"Ver os líderes da Mirow &amp; Co."),
    "en": (u"This person is no longer part of the team.",
           u"See the leaders of Mirow &amp; Co."),
    "de": (u"Diese Person gehört nicht mehr zum Team.",
           u"Die Führungskräfte von Mirow &amp; Co."),
}

ASSETS = [
    "wp-content/uploads/2026/08/onda68/og-lider-michael-munch.jpg",
    "wp-content/uploads/2023/02/Michael-Munch.png",
]


def stub(lang):
    d = DESTINO[lang]
    frase, rotulo = TEXTO[lang]
    return (
        u'<!DOCTYPE html><html lang="%s"><head><meta charset="utf-8">\n'
        # O comentario NAO cita o nome: a primeira versao dizia "Michael Munch deixou
        # a firma em 19/08/2026" e isso vai para o HTML que o publico recebe. O pedido
        # foi tirar a pessoa "de tudo"; deixar o nome num comentario servido e deixar
        # no site. O rastro fica no commit e na issue, que e onde ele pertence.
        u'<!-- %s: perfil encerrado; redireciona para a listagem de lideres -->\n'
        u'<meta http-equiv="refresh" content="0;url=%s">\n'
        u'<link rel="canonical" href="https://mirow.com.br%s">\n'
        u'<meta name="robots" content="noindex,follow">\n'
        u'<title>Mirow &amp; Co.</title></head>\n'
        u'<body><p>%s <a href="%s">%s</a>.</p></body></html>'
        % (lang, MARK, d, d, frase, d, rotulo))


def remover_card(html, nome):
    """Remove o <button class="page-leaders__list-item"> que contem `nome`.

    Varredura BALANCEADA: acha a abertura, conta <button>/</button> e corta no
    fechamento correspondente. Regex `<button.*?</button>` com DOTALL cortaria no
    primeiro </button> que aparecesse, e um card com botao aninhado sairia partido
    -- o tipo de estrago que so aparece no render.
    """
    ini = 0
    while True:
        m = re.search(r'<button class="page-leaders__list-item"', html[ini:])
        if not m:
            return html, False
        abre = ini + m.start()
        prof, i = 0, abre
        while i < len(html):
            if html.startswith("<button", i):
                prof += 1
                i += 7
            elif html.startswith("</button>", i):
                prof -= 1
                i += 9
                if prof == 0:
                    break
            else:
                i += 1
        bloco = html[abre:i]
        if nome in bloco:
            # come tambem o espaco em branco imediatamente antes do card
            j = abre
            while j > 0 and html[j - 1] in " \t\r\n":
                j -= 1
            return html[:j] + html[i:], True
        ini = abre + 1


def remover_modal(html, nome):
    """Remove o `<div class="modal fade">` cujo CONTEUDO tem `nome`.

    Por conteudo, nao por id, e essa foi a correcao: o id do modal nao e o mesmo
    nas tres linguas. Em `pt/index.html` ele e `modal_591` (slug NUMERICO antigo) e
    em `en/index.html` e `modal_michael-munch` (slug nominal), porque a troca de slug
    da onda 59 tocou so o PT. Uma primeira versao deste script fixava
    `MODAL_ID = "modal_591"`, removeu o modal em 1 pagina e passou batido nas outras
    5 -- e a varredura de pegada e que apontou. Localizar pelo conteudo funciona em
    qualquer idioma e sobrevive a proxima troca de slug.

    Varredura BALANCEADA: o modal tem 6 niveis de div, e `<div.*?</div>` com DOTALL
    cortaria no primeiro fechamento, deixando 5 aberturas orfas -- estrago que so
    aparece no render, e que cada navegador conserta a sua maneira.
    """
    for m in re.finditer(r'<div class="modal fade"[^>]*>', html):
        ini = m.start()
        prof, i = 0, ini
        while i < len(html):
            if html.startswith("<div", i):
                prof += 1
                i += 4
            elif html.startswith("</div>", i):
                prof -= 1
                i += 6
                if prof == 0:
                    break
            else:
                i += 1
        if prof != 0:
            continue                     # markup desbalanceado: nao arrisca
        if nome not in html[ini:i]:
            continue
        j = ini
        while j > 0 and html[j - 1] in " \t\r\n":
            j -= 1
        return html[:j] + html[i:], True
    return html, False


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mud = 0

    # --- 1. card fora das 3 listagens ---
    for lang, rel in LISTAGENS.items():
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        novo, achou = remover_card(h, NOME)
        if achou:
            gravar(p, novo)
            mud += 1
            print("  card removido: %s" % rel)

    # --- 1b. o modal de bio, em toda pagina que o carrega ---
    for dp, _d, fs in os.walk(pub):
        for f in fs:
            if f != "index.html":
                continue
            p = os.path.join(dp, f)
            h = ler(p)
            if NOME not in h:
                continue
            novo, achou = remover_modal(h, NOME)
            if not achou:
                continue
            gravar(p, novo)
            mud += 1
            print("  modal removido: %s"
                  % os.path.relpath(p, pub).replace(os.sep, "/"))

    # --- 2. as 3 paginas de perfil viram stub ---
    for lang, rel in PERFIS.items():
        p = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(p):
            continue
        novo = stub(lang)
        if ler(p) != novo:
            gravar(p, novo)
            mud += 1
            print("  perfil -> stub: %s" % rel)

    # --- 3. todo stub que apontava para o perfil (ou para 591) vai direto ---
    for dp, _d, fs in os.walk(pub):
        for f in fs:
            if f != "index.html":
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            if rel in PERFIS.values():
                continue
            h = ler(p)
            if SLUG not in h and "lider/591" not in h and "leader/591" not in h:
                continue
            # so stub: pagina de conteudo com o nome dele nao existe mais nesta altura
            if 'http-equiv="refresh"' not in h:
                continue
            lang = rel.split("/")[0]
            lang = lang if lang in DESTINO else "pt"
            novo = stub(lang)
            if h != novo:
                gravar(p, novo)
                mud += 1
                print("  stub reapontado: %s -> %s" % (rel, DESTINO[lang]))

    # --- 4. assets orfaos ---
    for ref in ASSETS:
        fp = os.path.join(pub, ref.replace("/", os.sep))
        if not os.path.exists(fp):
            continue
        base = os.path.basename(ref)
        citado = []
        for dp, _d, fs in os.walk(pub):
            for f in fs:
                if not f.endswith((".html", ".json", ".xml", ".css", ".js", ".txt")):
                    continue
                if base in ler(os.path.join(dp, f)):
                    citado.append(os.path.relpath(os.path.join(dp, f), pub))
        if citado:
            print("  MANTIDO (ainda citado em %d arquivo): %s -> %s"
                  % (len(citado), base, citado[0]))
            continue
        os.remove(fp)
        mud += 1
        print("  asset orfao removido: %s" % ref)

    # --- confere o EFEITO ---
    faltou = []
    for dp, _d, fs in os.walk(pub):
        for f in fs:
            if not f.endswith((".html", ".json", ".xml")):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            h = ler(p)
            if NOME in h:
                faltou.append(rel)
    if faltou:
        print("")
        print("  AINDA CITAM %s (%d): %s" % (NOME, len(faltou), ", ".join(faltou[:6])))
        print("  -> sitemap/busca sao regerados depois; JSON-LD sai com o 111")

    print("\nresumo: %d arquivo(s) alterado(s)" % mud)


if __name__ == "__main__":
    main()
