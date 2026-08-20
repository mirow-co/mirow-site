# -*- coding: utf-8 -*-
"""Onda 68 (#247) -- de QUATRO Organization no grafo para UMA.

O ACHADO. O levantamento de icones (docs/ICONES-EXPOSTOS.md) encontrou o site
declarando quatro entidades de organizacao diferentes ao Google:

    /pt/#organization                      (Yoast) tem logo, nao tem endereco
    /en/#organization                      (Yoast) idem
    /de/#organization                      (Yoast) idem
    https://mirow.com.br/#organization     (onda 59) tem endereco, descricao,
                                           fundacao, socios -- e NENHUM logo

Quatro `@id` distintos sao quatro entidades para o schema.org, nao uma vista de
quatro angulos. Nenhuma das quatro dizia ao mesmo tempo quem somos E qual e a
nossa marca -- exatamente o que o painel de conhecimento precisa. Liga direto no
handoff de GEO do Felipe (onda 59), em que os assistentes de IA inventavam
"consultoria alema com escritorio em Barcelona" na ausencia de fato legivel.

O QUE ESTE SCRIPT FAZ, e por que nesta ordem:

1. `"/<lang>/#organization"` -> `"https://mirow.com.br/#organization"`, em TODAS as
   ocorrencias, nao so na definicao. Sao tres por pagina: o proprio no, o
   `WebPage.about` e o `WebSite.publisher`. Trocar so a definicao deixaria os dois
   ponteiros apontando para uma entidade que passou a nao existir -- pior que o
   estado inicial.

2. `"/<lang>/#/schema/logo/image/"` -> `"https://mirow.com.br/#logo"`, o mesmo
   `@id` que o bloco da onda 59 usa. Assim o logo do Yoast e o nosso sao o MESMO
   no, com os mesmos valores, em vez de dois logos concorrendo na mesma entidade.

3. O `url`/`contentUrl` desse no passa a ser o raster quadrado do "m", 512x512. O
   que estava la era `logo_mirow_azul_e_branco1svg.svg`, e aquele arquivo tem
   `viewBox="0 0 210 297"` com `width="210mm" height="297mm"` -- e uma prancha
   **A4**, nao um logo. Era por isso que a dimensao declarada (210x297) parecia
   torta: ela descrevia a folha, nao a marca.

MEXER EM MARKUP DO TEMA. O bloco do Yoast e gerado, e a REGRA Nº ZERO diz para nao
tocar no tema. Aqui a mudanca e de CONTEUDO do JSON-LD, nao de tema: nao ha
WordPress vivo para regerar isso, o espelho e estatico, e o proprio repo ja edita o
`bundle-css.css` do tema desde a onda 58 pelo mesmo raciocinio. O arquivo do logo
antigo NAO e apagado -- so deixa de ser citado no schema.

O JSON e PARSEADO, alterado e reserializado -- nao ha regex costurando dentro de
JSON. Reserializar da o mesmo texto toda vez, entao o 2o run reporta 0 mudancas.

Uso:  python tools_onda6/143_schema_organizacao_unica.py .
"""

from __future__ import print_function

import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _onda7_css import ler, resolve_public  # noqa: E402

ORG_ID = "https://mirow.com.br/#organization"
LOGO_ID = "https://mirow.com.br/#logo"
LOGO_URL = ("https://mirow.com.br/wp-content/uploads/2026/08/onda68/"
            "icone-mirow-512.png")

# Duas formas convivem no espelho, e a primeira versao deste script so pegou uma
# delas: as 3 homes tinham o @id RELATIVO (`/pt/#organization`, efeito da
# canonicalizacao da onda 29) e as outras 106 tinham o ABSOLUTO POR IDIOMA
# (`https://mirow.com.br/pt/#organization`). Pior: a verificacao que eu havia
# escrito procurava a string relativa, entao ela passou VERDE tendo corrigido 3 de
# 109. No HTML os ids vem com barra escapada (`https:\/\/...`), o que ajudou a
# esconder -- por isso a checagem final agora RE-PARSEIA o grafo em vez de procurar
# string. P2.1: medir o efeito, nao a declaracao.
RE_ORG = re.compile(r'^(?:/|https://mirow\.com\.br/)(?:pt|en|de)/#organization$')
RE_LOGO = re.compile(
    r'^(?:/|https://mirow\.com\.br/)(?:pt|en|de)/#/schema/logo/image/$')

TAG = re.compile(
    r'(<script type="application/ld\+json" class="yoast-schema-graph">)(.*?)(</script>)',
    re.S)


def trocar_ids(no):
    """Reescreve @id e referencias, recursivamente, em qualquer profundidade."""
    mudou = False
    if isinstance(no, dict):
        for k, v in list(no.items()):
            if isinstance(v, str):
                if RE_ORG.match(v):
                    no[k] = ORG_ID
                    mudou = True
                elif RE_LOGO.match(v):
                    no[k] = LOGO_ID
                    mudou = True
            else:
                mudou = trocar_ids(v) or mudou
    elif isinstance(no, list):
        for v in no:
            mudou = trocar_ids(v) or mudou
    return mudou


def corrigir_logo(no):
    """O ImageObject do logo passa a apontar para a marca, com a dimensao real.

    RECURSIVA, e essa foi a correcao: a primeira versao percorria apenas os nos de
    TOPO de `@graph`, e nas 3 homes o Yoast escreve o ImageObject do logo ANINHADO
    dentro da propriedade `logo` da Organization, nao como no irmao. Resultado: as
    homes ficavam com o SVG A4 antigo enquanto as outras 106 ja tinham a marca, e as
    6 paginas que carregam os dois blocos passavam a declarar dois logos diferentes
    na mesma entidade -- pior que o estado inicial. Quem pegou foi a S174; o script
    tinha se declarado satisfeito.
    """
    mudou = False
    if isinstance(no, dict):
        if no.get("@id") == LOGO_ID:
            for campo in ("url", "contentUrl"):
                if no.get(campo) != LOGO_URL:
                    no[campo] = LOGO_URL
                    mudou = True
            for campo, valor in (("width", 512), ("height", 512),
                                 ("caption", "Mirow & Co.")):
                if no.get(campo) != valor:
                    no[campo] = valor
                    mudou = True
        for v in no.values():
            mudou = corrigir_logo(v) or mudou
    elif isinstance(no, list):
        for v in no:
            mudou = corrigir_logo(v) or mudou
    return mudou


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    alterados = 0
    tocados = 0
    for dp, _d, fs in os.walk(pub):
        for f in fs:
            if not f.endswith(".html"):
                continue
            fp = os.path.join(dp, f)
            h = ler(fp)
            m = TAG.search(h)
            if not m:
                continue
            tocados += 1
            try:
                d = json.loads(m.group(2))
            except Exception:
                print("  AVISO: json-ld do Yoast ilegivel em %s"
                      % os.path.relpath(fp, pub))
                continue
            mudou = trocar_ids(d)
            mudou = corrigir_logo(d) or mudou
            if not mudou:
                continue
            novo_json = json.dumps(d, ensure_ascii=False,
                                   separators=(",", ":"))
            novo = h[:m.start(2)] + novo_json + h[m.end(2):]
            with io.open(fp, "w", encoding="utf-8", newline="") as fh:
                fh.write(novo)
            alterados += 1

    # --- confere o EFEITO, re-parseando o grafo (nao procurando string) ---
    sobrou = []
    for dp, _d, fs in os.walk(pub):
        for f in fs:
            if not f.endswith(".html"):
                continue
            fp = os.path.join(dp, f)
            mm = TAG.search(ler(fp))
            if not mm:
                continue
            try:
                dd = json.loads(mm.group(2))
            except Exception:
                continue
            achados = []

            def varre(no):
                if isinstance(no, dict):
                    for k, v in no.items():
                        if isinstance(v, str) and v.endswith("#organization"):
                            achados.append(v)
                        elif isinstance(v, str) and "schema/logo/image" in v:
                            achados.append(v)
                        else:
                            varre(v)
                elif isinstance(no, list):
                    for v in no:
                        varre(v)

            varre(dd)
            for a in achados:
                if a != ORG_ID and a != LOGO_ID:
                    sobrou.append((os.path.relpath(fp, pub), a))
                    break
    if sobrou:
        print("  FALHA: %d pagina(s) com @id nao canonico (ex.: %s -> %s)"
              % (len(sobrou), sobrou[0][0], sobrou[0][1]))
        raise SystemExit(1)

    print("paginas com grafo do Yoast: %d" % tocados)
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
