# -*- coding: utf-8 -*-
"""
105_email_andreas_e_felipe.py -- S-136 (#201): os botoes GENERICOS de e-mail
passam a ter dois destinatarios (Andreas + Felipe). Os mailtos de card/modal
de lider ficam intactos -- sao o e-mail pessoal de cada lider.

Uso:  python tools_onda6/105_email_andreas_e_felipe.py <raiz-que-contem-public>

Escopo: so os <a> das 3 classes genericas (pilula do hero, icone da barra
superior, trilho lateral). Idempotente: com o Felipe ja no href, o padrao
antigo nao casa e o 2o run reporta 0 mudancas.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

CLASSES = ("hero-contatos__link--mail",
           "menu__contatos-link--mail",
           "onda19-lateral__link--mail")

ANTIGO = "mailto:andreas.mirow@mirow.com.br?"
NOVO = "mailto:andreas.mirow@mirow.com.br,felipe.diniz@mirow.com.br?"

# <a ...classe generica... href="mailto:andreas...?..."
RE_A = re.compile(r'<a class="[^"]*(?:%s)[^"]*"[^>]*>' % "|".join(CLASSES))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = 0
    trocas = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            path = os.path.join(dirpath, nome)
            html = ler(path)
            n = 0

            def troca(m):
                nonlocal n
                tag = m.group(0)
                if ANTIGO in tag:
                    n += 1
                    return tag.replace(ANTIGO, NOVO)
                return tag

            novo_html = RE_A.sub(troca, html)
            if n:
                gravar(path, novo_html)
                alterados += 1
                trocas += n
    print("Felipe adicionado em %d botao(oes), %d pagina(s)" % (trocas, alterados))


if __name__ == "__main__":
    main()
