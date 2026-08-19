# -*- coding: utf-8 -*-
u"""134 — issue #104 / S-47: o campo de busca passa a buscar.

Uso: python tools_onda6/134_busca_estatica.py <raiz-que-contem-public>

O PROBLEMA, MEDIDO
------------------
O formulário do tema é `<form class="search-form" action="/" method="get">` com
`name="s"` e um campo oculto `post_type=post`. Isso é markup de WordPress: o
servidor recebe `?s=termo` e responde. **No espelho estático servido pelo GitHub
Pages não existe quem responda** — medido em 19/08, `/?s=pricing` devolve o
**stub de redirect da raiz**, que joga o visitante em `/pt/`. Ele digitou, apertou
Enter e não recebeu nem uma página de "nada encontrado".

Era o único dos três caminhos de conversão mortos (aulão S-43/#99) que o visitante
**aciona de propósito**, e estava assim desde o cutover.

O QUE ESTE SCRIPT FAZ, NAS 3 PÁGINAS QUE TÊM O CAMPO
----------------------------------------------------
(`/pt/insights/`, `/en/insights/`, `/de/insights/` — medido: são só essas três)

1. **`action` deixa de ser `/`** e passa a ser a própria página. Submeter recarrega
   `…/insights/?s=termo`, e o JS lê o termo da URL. Consequência de escolher isso
   em vez de uma página de busca nova: nenhuma URL nova para entrar em sitemap,
   canonical e hreflang, e um link direto com `?s=` funciona.
2. **O campo oculto `post_type=post` sai.** É parâmetro do WordPress, não tem
   leitor no espelho, e ia na query string sem função.
3. **O `<label>` passa a estar no idioma da página.** Hoje as três dizem
   *"Search in /pt/"*, *"Search in /en/"*, *"Search in /de/"* — texto de
   depuração que vazou para produção, em inglês inclusive na página alemã.
4. Entra o contêiner de resultados e o `busca.js` (com `?v=` — erro 6 do CLAUDE.md).

O ÍNDICE
--------
`public/busca-indice.json`, gerado por `tools/gen_busca.py` a partir do
`sitemap.xml` (P3: o sitemap já é gerado do `rel=canonical`, então o índice não
pode divergir do que o site considera canônico). 109 páginas, 126 KB, e **só é
baixado quando há termo na URL** — quem abre a página de Insights sem buscar nada
não paga o download.

Idempotente: rodar 2x reporta 0 mudanças.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

# medido: sao exatamente estas 3 que tem <form class="search-form">
PAGINAS = {
    "pt": ("pt/insights/index.html", u"Buscar no site",
           u"Buscar", u"O que você procura?"),
    "en": ("en/insights/index.html", u"Search the site",
           u"Search", u"What are you looking for?"),
    "de": ("de/insights/index.html", u"Website durchsuchen",
           u"Suchen", u"Wonach suchen Sie?"),
}

JS_REL = "wp-content/uploads/2026/08/onda67/busca.js"

CSS = """
/* ---- onda67 (#104): resultados da busca estatica -------------------------
   Herda a tipografia do corpo; a lista usa a mesma gramatica visual da lista de
   imprensa (linha inteira clicavel, fundo branco, separador fino), para nao
   inventar um componente novo. */
.onda67-busca{margin:0 0 44px}
.onda67-busca__contagem{font-size:15px;color:#7F7F7F;margin:0 0 14px}
.onda67-busca__vazio{font-size:17px;color:#071C25;margin:0;padding:18px 20px;
  background:#fff;border-left:3px solid #00ADEC}
.onda67-busca__lista{list-style:none;margin:0;padding:0;background:#fff}
.onda67-busca__item+.onda67-busca__item{border-top:1px solid #E5E5E5}
.onda67-busca__link{display:grid;gap:4px;padding:18px 22px;text-decoration:none}
.onda67-busca__link:hover .onda67-busca__titulo{color:#00ADEC}
.onda67-busca__titulo{font-size:clamp(16px,14.6px + 0.19vw,18px);font-weight:700;
  color:#020E66;line-height:1.3}
.onda67-busca__trecho{font-size:15px;color:#071C25;line-height:1.5}
.onda67-busca__trecho mark{background:#AAD5E8;color:#071C25;padding:0 2px}
@media only screen and (max-width: 991px){
  .onda67-busca__link{padding:16px 16px}
  .onda67-busca__trecho{font-size:14px}
}
"""

REX_FORM = re.compile(r'<form class="search-form".*?</form>', re.S)
REX_LABEL = re.compile(r'(<label class="search-form__label" for="search">)(.*?)(</label>)', re.S)
REX_OCULTO = re.compile(r'<input class="search-form__input-hidden"[^>]*>')
REX_INPUT = re.compile(r'(<input class="search-form__input" type="text" name="s"[^>]*)(/?>)')


def versao_atual(pub):
    u"""A VERSAO do cache busting, para o ?v= do js e do indice."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "27_cache_busting.py")
    m = re.search(r"^VERSAO\s*=\s*(\d+)", io.open(p, encoding="utf-8").read(), re.M)
    return m.group(1) if m else "1"


def main(argv):
    pub = resolve_public(argv[1] if len(argv) > 1 else ".")
    v = versao_atual(pub)
    mudou = []

    for lang, (rel, rotulo, botao, placeholder) in sorted(PAGINAS.items()):
        p = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(p):
            raise SystemExit(u"falta %s" % rel)
        html = ler(p)
        original = html

        m = REX_FORM.search(html)
        if not m:
            raise SystemExit(u"%s: nao achei <form class=\"search-form\">" % rel)
        form = m.group(0)
        novo_form = form

        # 1. action -> a propria pagina
        alvo = "/" + rel[:-len("index.html")]
        novo_form = novo_form.replace('action="/"', 'action="%s"' % alvo, 1)

        # 2. o campo oculto do WordPress sai
        novo_form = REX_OCULTO.sub("", novo_form)

        # 3. rotulo no idioma da pagina (era "Search in /pt/")
        novo_form = REX_LABEL.sub(
            lambda mm: mm.group(1) + rotulo + mm.group(3), novo_form)

        # placeholder e aria no campo
        if "placeholder=" not in novo_form:
            novo_form = REX_INPUT.sub(
                lambda mm: (mm.group(1) + ' placeholder="%s" aria-label="%s"'
                            % (placeholder, rotulo) + mm.group(2)), novo_form)

        html = html.replace(form, novo_form, 1)

        # 4. contentor de resultados logo depois do form
        if 'id="onda67-busca-resultados"' not in html:
            html = html.replace(
                novo_form,
                novo_form + '<div class="onda67-busca" id="onda67-busca-resultados"></div>',
                1)

        # 5. o js, com ?v= (erro 6 do CLAUDE.md)
        if "onda67/busca.js" not in html:
            prefixo_m = re.search(r'(?:src|href)="(/[^"]*?/)wp-content/', html)
            prefixo = prefixo_m.group(1) if prefixo_m else "/"
            tag = ('<script>window.ONDA67_V="%s";</script>'
                   '<script src="%s%s?v=%s" defer></script>' % (v, prefixo, JS_REL, v))
            html = html.replace("</body>", tag + "</body>", 1)

        if html != original:
            gravar(p, html)
            mudou.append(rel)
            print(u"  + %s" % rel)
        else:
            print(u"  = %s (ja estava)" % rel)

    mudou_css = escrever_bloco_css(pub, "busca", CSS, onda="onda67")

    # rele e confere o EFEITO
    problemas = []
    for lang, (rel, rotulo, _b, _ph) in sorted(PAGINAS.items()):
        h = ler(os.path.join(pub, rel.replace("/", os.sep)))
        if 'action="/"' in h and "search-form" in h.split('action="/"')[0][-200:]:
            problemas.append(u"%s: o form ainda posta para a raiz" % rel)
        if "post_type" in h:
            problemas.append(u"%s: o campo oculto do WordPress continua la" % rel)
        if rotulo not in h:
            problemas.append(u"%s: rotulo nao ficou no idioma" % rel)
        if 'id="onda67-busca-resultados"' not in h:
            problemas.append(u"%s: sem contentor de resultados" % rel)
        if "onda67/busca.js?v=" not in h:
            problemas.append(u"%s: js ausente ou sem ?v=" % rel)
    if not os.path.exists(os.path.join(pub, "busca-indice.json")):
        problemas.append(u"falta public/busca-indice.json — rode tools/gen_busca.py")
    if not os.path.exists(os.path.join(pub, JS_REL.replace("/", os.sep))):
        problemas.append(u"falta o proprio busca.js no disco")

    if problemas:
        for pr in problemas:
            print(u"  ERRO: %s" % pr)
        raise SystemExit(1)

    print(u"\n%d pagina(s) alterada(s); bloco onda67:busca %s"
          % (len(mudou), u"gravado" if mudou_css else u"ja estava igual"))


if __name__ == "__main__":
    main(sys.argv)
