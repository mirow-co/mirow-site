# -*- coding: utf-8 -*-
"""72 — onda 18, S-72 e S-73 (issues #130 e #131).

Uso:
    python tools_onda6/72_email_e_hero_numeros.py <raiz-que-contem-public>

S-72 — "ao clicar no email, ele deve vir pre-preenchido com algum texto-padrao +
  assunto, que o cliente pode deletar se quiser."
  Todo link de e-mail DOS CANAIS DE CONTATO (icone do header, do hero e do rodape)
  passa a levar ?subject= e &body= no idioma da pagina. O texto e o mesmo da
  mensagem-padrao do formulario (S-61), para o cliente ver a mesma voz nos dois
  caminhos. Continua editavel: e so texto pre-preenchido no cliente de e-mail.
  NAO mexe no e-mail pessoal dos lideres nos modais — aquele e contato direto.

S-73 — "o tamanho do texto abaixo dos big numbers na pagina inicial deve ser tao
  grande quanto o texto 'Focamos em estrategia...' e os big numbers do mesmo
  tamanho do Estrategia, Confianca, Resultados."
  Os tokens do tema no desktop: .banner h2 = 62px (slogan) e .banner p = 18px
  (paragrafo). A pilha ia de 40px/14px para 62px/18px, e a coluna alarga para o
  texto nao virar 3 linhas (a assercao V07 cobra no maximo 2).

Idempotente: mailto reescrito so quando ainda nao tem query; CSS em bloco marcado.
"""
import os
import re
import sys

try:
    from urllib.parse import quote
except ImportError:  # py2
    from urllib import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (escrever_bloco_css, gravar, idioma_da_pagina, ler,  # noqa: E402
                        resolve_public)

# S-72 — assunto e corpo por idioma (mesmo texto do formulario, S-61)
EMAIL_TXT = {
    "pt": (u"Contato pelo site da Mirow & Co.",
           u"Olá! Vim pelo site da Mirow & Co. e gostaria de conversar sobre "
           u"um desafio da minha empresa."),
    "en": (u"Contact from the Mirow & Co. website",
           u"Hello! I came from the Mirow & Co. website and would like to talk "
           u"about a challenge at my company."),
    "de": (u"Kontakt über die Website von Mirow & Co.",
           u"Hallo! Ich komme über die Website von Mirow & Co. und würde "
           u"gerne über eine Herausforderung in meinem Unternehmen sprechen."),
}

# só os links dos CANAIS de contato entram (nunca o e-mail pessoal de líder)
CLASSES_CANAL = ("menu__contatos-link--mail", "hero-contatos__link--mail")

CSS = """/* ---- S-73: pilha de numeros na tipografia do hero ----------------------
   O tema define o slogan em 62px (.banner h2) e o paragrafo em 18px (.banner p);
   a pilha estava em 40px/14px. Agora usa os MESMOS tamanhos. A coluna alarga
   junto, senao o texto de 18px passa de 2 linhas (assercao V07). */
@media only screen and (min-width: 1200px){
  .hero-numeros{gap:14px;width:400px}
  .hero-numeros__valor{font-size:62px !important;line-height:1}
  .hero-numeros__texto{font-size:18px !important;line-height:1.35;margin-top:6px}
}
@media only screen and (min-width: 1440px){
  .hero-numeros{width:440px}
}
/* viewport baixo: a onda 10 encolhia a pilha (33px/13px). O pedido do Mario e
   igualar ao hero, entao aqui o tamanho fica, e o que cede e o espacamento. */
@media only screen and (min-width: 1200px) and (max-height: 820px){
  .hero-numeros{gap:8px}
  .hero-numeros__valor{font-size:62px !important}
  .hero-numeros__texto{font-size:18px !important}
}"""


def mailto_com_texto(html, lang):
    """S-72 — acrescenta subject/body aos mailto dos canais de contato."""
    assunto, corpo = EMAIL_TXT.get(lang, EMAIL_TXT["pt"])
    query = "?subject=%s&amp;body=%s" % (quote(assunto.encode("utf-8"), safe=""),
                                         quote(corpo.encode("utf-8"), safe=""))

    def sub(m):
        tag = m.group(0)
        if not any(c in tag for c in CLASSES_CANAL):
            return tag
        # já tem query? (idempotência)
        if re.search(r'href="mailto:[^"]*\?', tag):
            return re.sub(r'href="mailto:([^"?]+)\?[^"]*"',
                          lambda mm: 'href="mailto:%s%s"' % (mm.group(1), query), tag)
        return re.sub(r'href="mailto:([^"]+)"',
                      lambda mm: 'href="mailto:%s%s"' % (mm.group(1), query), tag)

    return re.sub(r'<a\b[^>]*href="mailto:[^"]*"[^>]*>', sub, html)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mudou = escrever_bloco_css(pub, "hero-numeros-s73", CSS, onda="onda18")
    print("bloco onda18:hero-numeros-s73 %s" % ("gravado" if mudou else "ja estava igual"))

    alterados = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if "mailto:" not in h:
                continue
            novo = mailto_com_texto(h, idioma_da_pagina(h))
            if novo != h:
                gravar(p, novo)
                alterados += 1
    print("resumo: %d pagina(s) com mailto pre-preenchido nos canais de contato"
          % alterados)


if __name__ == "__main__":
    main()
