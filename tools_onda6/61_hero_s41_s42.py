# -*- coding: utf-8 -*-
"""Onda 16 — S-41 (#97) + S-42 (#98).

S-41: big numbers bem mais a direita (encostando no viewport, nao no
container), nenhum bloquinho com mais de 2 linhas (caixa mais larga),
e o painel do slogan + subtitulo + pills puxado para a esquerda.

S-42: hover dos links de contato com a cor da marca de cada app —
WhatsApp verde (ja existia), LinkedIn #0A66C2, Instagram #E1306C,
e-mail ciano Mirow #00ADEC. Vale para as pills do hero e para os
icones da barra superior e do rodape (todas as paginas).

Idempotente: 2a execucao reporta 0 mudancas.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public, escrever_bloco_css, ler, gravar

CSS_S41 = """
/* S-41 (#97): a pilha de numeros vai ate perto da borda direita do viewport
   ((100% - 100vw)/2 = margem do container ate a borda; +40px de respiro) e
   alarga para os textos nao passarem de 2 linhas. O painel do slogan faz o
   movimento espelhado para a esquerda — min() garante que em viewport
   estreito ele nunca fique PIOR que os -30px que ja tinha (onda15). */
@media only screen and (min-width: 1200px){
  .hero-numeros{
    right:calc((100% - 100vw)/2 + 40px);
    width:330px;
  }
  .hero-texto{
    margin-left:min(-30px, calc((100% - 100vw)/2 + 40px));
  }
}
@media only screen and (min-width: 1440px){
  .hero-numeros{width:380px}
}
"""

CSS_S42 = """
/* S-42 (#98): hover com a cor da marca de cada app. WhatsApp verde ja vinha
   da onda8; aqui entram LinkedIn, Instagram e e-mail (ciano Mirow — escolha
   para manter coerencia com o site). Pills do hero: fundo na cor da marca;
   icones das barras: so a cor do icone. */
.hero-contatos__link--in:hover,.hero-contatos__link--in:focus-visible{
  color:#fff !important;background:#0A66C2;border-color:#0A66C2}
.hero-contatos__link--ig:hover,.hero-contatos__link--ig:focus-visible{
  color:#fff !important;background:#E1306C;border-color:#E1306C}
.hero-contatos__link--mail:hover,.hero-contatos__link--mail:focus-visible{
  color:#020e66 !important;background:#00ADEC;border-color:#00ADEC}
.menu__contatos-link--in:hover,.menu__contatos-link--in:focus-visible{
  color:#378FE9}
.menu__contatos-link--ig:hover,.menu__contatos-link--ig:focus-visible{
  color:#E1306C}
.menu__contatos-link--mail:hover,.menu__contatos-link--mail:focus-visible{
  color:#00ADEC}
"""

# href -> sufixo do modificador
DESTINOS = (
    ("mailto:", "mail"),
    ("linkedin.com", "in"),
    ("instagram.com", "ig"),
)

BASES = ("hero-contatos__link", "menu__contatos-link")

RE_A = re.compile(r"<a\b[^>]*>")


def classificar(tag):
    """Devolve o sufixo do modificador para a tag <a>, ou None."""
    m = re.search(r'href="([^"]*)"', tag)
    if not m:
        return None
    href = m.group(1)
    for trecho, sufixo in DESTINOS:
        if trecho in href:
            return sufixo
    return None


def marcar_links(html):
    """Adiciona a classe modificadora nos links de contato. Idempotente."""
    def sub(m):
        tag = m.group(0)
        for base in BASES:
            if base not in tag:
                continue
            if re.search(re.escape(base) + r"--\w", tag):
                return tag  # ja tem modificador (--wa ou desta onda)
            sufixo = classificar(tag)
            if not sufixo:
                return tag
            novo = tag.replace('class="%s' % base,
                               'class="%s %s--%s' % (base, base, sufixo), 1)
            if novo == tag:  # base nao e a primeira classe do atributo
                novo = re.sub(r'class="([^"]*\b%s)\b' % re.escape(base),
                              r'class="\1 %s--%s' % (base, sufixo), tag, count=1)
            return novo
        return tag
    return RE_A.sub(sub, html)


def main(root):
    pub = resolve_public(root)
    mudancas = 0

    if escrever_bloco_css(pub, "hero-layout-s41", CSS_S41, onda="onda16"):
        mudancas += 1
        print("css: onda16:hero-layout-s41 gravado")
    if escrever_bloco_css(pub, "hover-marcas-s42", CSS_S42, onda="onda16"):
        mudancas += 1
        print("css: onda16:hover-marcas-s42 gravado")

    paginas_mudadas = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            p = os.path.join(dirpath, nome)
            try:
                html = ler(p)
            except Exception:
                continue
            if not any(b in html for b in BASES):
                continue
            novo = marcar_links(html)
            if novo != html:
                gravar(p, novo)
                paginas_mudadas += 1
    if paginas_mudadas:
        print("html: classes --mail/--in/--ig em %d paginas" % paginas_mudadas)
    mudancas += paginas_mudadas
    print("total: %d mudancas" % mudancas)
    return mudancas


if __name__ == "__main__":
    raiz = sys.argv[1] if len(sys.argv) > 1 else "."
    main(raiz)
