# -*- coding: utf-8 -*-
u"""108 — onda 53 (#221): a home sem ponto final nos textos.

Uso:
    python tools_onda6/108_home_sem_ponto_final.py <raiz-que-contem-public>

Pedido do Mario (13/08), verbatim:
    "dessa pagina, retirar qualquer full stop `.` nos textos"

E a mesma regra que a firma ja aplica em slide (R15 / slides.md: "bullet e
telegrama, nunca leva ponto final"), agora no site.

O QUE SAI: o ponto que FECHA o texto de um elemento — cards de pratica, faixa
de IA, bullets de bio dos lideres nos modais.

O QUE FICA (medido antes de escrever, com o navegador lendo os nos de texto):
  - o ponto da MARCA "Mirow & Co." — e nome, nao pontuacao (R4)
  - ponto de abreviacao NO MEIO do texto: "Prof. Dr", "Arthur D. Little",
    "St. Gall", "Mrd. R$". Nenhum texto da home tem duas frases, entao nao ha
    ponto separador de frase a preservar — so os finais saem.
  - ponto em URL, nome de arquivo e numero

Idempotente: rodar 2x nao muda nada (o 2o run nao acha ponto final).
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

PAGINAS = [os.path.join("pt", "index.html"),
           os.path.join("en", "index.html"),
           os.path.join("de", "index.html")]

# tags cujo texto e conteudo editorial
TAGS = "p|li|h1|h2|h3|h4|h5|h6|span|strong|em|b|i|td|figcaption|blockquote"

# caudas que NAO sao ponto final de frase
GUARDA = re.compile(
    r'(?:'
    r'Co|Cia|S\.?A|Inc|Ltd|Ltda|GmbH|etc|Jr|Sr|Dr|Prof|'   # marca e titulo
    r'\b[A-Z]'                                             # inicial isolada: "D."
    r')$'
)
# NAO guardar numero: "Rio2016." e ponto final de frase, nao separador decimal
# (o separador vive no MEIO do texto — "1.000", "Mrd. R$" — e este script so
# mexe no ponto que FECHA o elemento).


def tirar_ponto(html):
    """Remove o ponto que fecha o texto de um elemento editorial."""
    n = [0]

    def sub(m):
        texto, espaco, fecha = m.group(1), m.group(2), m.group(3)
        if GUARDA.search(texto):
            return m.group(0)
        n[0] += 1
        return texto + espaco + fecha

    # texto (sem tags dentro) antes do fechamento da tag; o espaco entre o ponto
    # e a tag e opcional — 3 bios escaparam na 1a versao por causa dele
    rex = re.compile(r'([^<>]*?[^\s<>.])\.(\s*)(</(?:%s)>)' % TAGS)
    return rex.sub(sub, html), n[0]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    pub = resolve_public(sys.argv[1])
    print(u"108 — home sem ponto final (#221)")
    total = 0
    for rel in PAGINAS:
        p = os.path.join(pub, rel)
        if not os.path.exists(p):
            print(u"  ! ausente: %s" % rel)
            continue
        h = ler(p)
        novo, n = tirar_ponto(h)
        if n:
            gravar(p, novo)
            total += n
        print(u"  %s %s: %d ponto(s)" % ("+" if n else "=", rel, n))
    print(u"%d ponto(s) removido(s)" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
