# -*- coding: utf-8 -*-
"""Onda 73 (mirow-marketing#254): o LinkedIn de cada lider passa a vir de um
mestre unico, e o link do Stephan -- que caia em 404 -- e consertado.

O defeito: o site publicava `linkedin.com/in/prof-dr-stephan-friedrich-von-den-eichen-681883139`,
que o LinkedIn redireciona para `/404/` ("This page doesn't exist"), medido no
navegador em 25/08/2026. O perfil vivo e o MESMO slug sem o sufixo numerico, e foi
o Mario quem passou a URL certa. Estava em 12 arquivos, 4 por idioma.

Por que um mestre (P3): o `sameAs` do JSON-LD sai do card da listagem (o 111 le
`d["linkedin"]`), entao a URL vive em varios HTML e nao havia UM lugar que
declarasse qual e a correta. A tabela LINKEDIN abaixo e esse lugar, com a data em
que cada URL foi verificada de verdade -- num navegador, nao por curl (o LinkedIn
responde HTTP 999 a cliente que nao e navegador, e 999 nao distingue perfil vivo
de perfil morto; e por isso que o gate NAO prova que o link esta vivo, so que o
site concorda com esta tabela).
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_css = __import__("_onda7_css")
ler, gravar, resolve_public = _css.ler, _css.gravar, _css.resolve_public

# MESTRE. Verificadas no navegador (sessao do Mario) em 25/08/2026: cada URL
# abriu o perfil da pessoa. A do Stephan e a unica que mudou nesta onda.
LINKEDIN = {
    u"Andreas Mirow": "https://www.linkedin.com/in/andreas-mirow/",
    u"Felipe Diniz": "https://www.linkedin.com/in/felipe-diniz-713a129/",
    u"Prof. Dr Stephan Friedrich": "https://www.linkedin.com/in/prof-dr-stephan-friedrich-von-den-eichen/",
    u"Raoni Morais": "https://www.linkedin.com/in/raoni-r-morais/",
    u"Renato Alvarenga": "https://www.linkedin.com/in/renato-alvarenga-5b2332/",
}

# Pessoas que aparecem no site mas NAO estao no cadastro de lideres (PAGINAS do
# 110): o Elmar Gans (segue na listagem e nos cards, fora do schema por decisao
# do Felipe -- classe C2 do backlog) e o Joao Daniel Ramos (fora do schema por
# nao ter pagina propria -- classe C3). As duas URLs tambem foram abertas no
# navegador em 25/08/2026 e as duas estao vivas.
#
# Achado ao verificar, que NAO e desta onda e nao foi mexido: o perfil do Elmar
# diz "Founder & CEO at Stealth Startup (AI)", sem a Mirow. O backlog registra o
# caso dele como "mudanca de situacao em curso"; se ele saiu, vale a regra do
# "quem saiu sai do site" (ondas 33 e 68b). Decisao do Mario, nao minha.
OUTROS = {
    u"Elmar Gans": "https://www.linkedin.com/in/elmar-gans-2329a422/",
    u"João Daniel Ramos": "https://www.linkedin.com/in/joao-daniel-palma-ramos/",
}

# Slug morto -> slug vivo. Substituicao literal de string: sem regex, sem
# backslash (erro 13 do CLAUDE.md). A troca cobre a forma com e sem barra final.
MORTOS = {
    "prof-dr-stephan-friedrich-von-den-eichen-681883139":
        "prof-dr-stephan-friedrich-von-den-eichen",
}


def main(raiz):
    pub = os.path.join(os.path.abspath(raiz), "public")
    mudados = 0
    for base, _dirs, arquivos in os.walk(pub):
        for arq in arquivos:
            if not arq.endswith(".html"):
                continue
            p = os.path.join(base, arq)
            h = ler(p)
            novo = h
            for morto, vivo in MORTOS.items():
                if morto in novo:
                    novo = novo.replace(morto, vivo)
            if novo != h:
                gravar(p, novo)
                mudados += 1
                print(u"  %s" % os.path.relpath(p, pub).replace(os.sep, "/"))
    print(u"148: %d arquivo(s) com o LinkedIn do Stephan corrigido" % mudados)
    return mudados


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
