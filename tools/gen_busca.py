# -*- coding: utf-8 -*-
u"""gen_busca.py — gera o índice de busca estática a partir das páginas de conteúdo.

Uso:
    python tools/gen_busca.py <raiz-que-contem-public> [--dry]

POR QUE ESTE ARQUIVO EXISTE (issue #104 / S-47)
-----------------------------------------------
O campo de busca do tema posta `?s=<termo>` com `method="get"` para `action="/"`.
Num WordPress, o servidor responde. Num espelho estático servido pelo GitHub
Pages, **não existe quem responda**: o visitante digita, aperta Enter e cai na
raiz — que hoje é um stub de redirect. Era o terceiro caminho de conversão morto
do site (aulão S-43/#99), e o único que o visitante ACIONA de propósito.

A saída é um índice JSON gerado das páginas de conteúdo e uma busca no cliente.
Sem npm, sem serviço externo, sem chave de API: um `fetch` de um arquivo e uma
função de pontuação.

O QUE ENTRA NO ÍNDICE
---------------------
Só as páginas de CONTEÚDO, lidas do `sitemap.xml` — que já é gerado do
`rel=canonical` (onda 33). Assim o índice não pode divergir do que o site
considera canônico, e os 177 stubs de redirect ficam fora por construção: eles
são `noindex`, e indexar um redirect devolveria resultado que salta de página.

De cada página: idioma, URL, título e o texto do `#mainContent` — sem
`<script>`, `<style>`, cabeçalho, menu e rodapé, senão toda busca casaria com o
menu e todo resultado teria o mesmo trecho.

O texto vai truncado em 6.000 caracteres por página. Medido, o índice inteiro:
1.200 -> 126 KB · 2.500 -> 209 KB · 4.000 -> 281 KB · 6.000 -> 344 KB.

Escolhi 6.000 depois de um teste falhar: com 1.200, buscar "carga tributaria" no
PT devolvia **zero**, e a página de imprensa tem esse texto — no item da Revista
Amazônia, que fica na 13ª linha de uma lista de 43 e caía fora do corte. Ou seja,
o corte curto cegava justamente as páginas de LISTA, que são as que têm mais
conteúdo procurável. Como o índice só é baixado quando há termo na URL, 344 KB
sob demanda (≈100 KB comprimido) compra a lista inteira de imprensa e de
insights.

A BUSCA É POR IDIOMA
--------------------
Cada resultado carrega o idioma, e a página de busca só mostra os do idioma em
que o visitante está. Buscar "pricing" em `/pt/` não devolve a página alemã.
"""
import io
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "tools_onda6"))

from _onda7_css import resolve_public  # noqa: E402

TETO_TEXTO = 6000

REX_TIRAR = [
    re.compile(r"<script\b.*?</script>", re.S | re.I),
    re.compile(r"<style\b.*?</style>", re.S | re.I),
    re.compile(r"<noscript\b.*?</noscript>", re.S | re.I),
    re.compile(r"<header\b.*?</header>", re.S | re.I),
    re.compile(r"<footer\b.*?</footer>", re.S | re.I),
    re.compile(r"<nav\b.*?</nav>", re.S | re.I),
    re.compile(r"<!--.*?-->", re.S),
]


def texto_de(html):
    u"""Texto do conteúdo principal, sem mobília."""
    corpo = html
    m = re.search(r'<div id="mainContent">(.*)', corpo, re.S)
    if m:
        corpo = m.group(1)
    for rex in REX_TIRAR:
        corpo = rex.sub(u" ", corpo)
    corpo = re.sub(r"<[^>]+>", u" ", corpo)
    corpo = (corpo.replace("&nbsp;", u" ").replace("&amp;", u"&")
                  .replace("&lt;", u"<").replace("&gt;", u">")
                  .replace("&quot;", u'"').replace("&#039;", u"'")
                  .replace("&#8217;", u"'").replace("&#8211;", u"-"))
    return re.sub(r"\s+", u" ", corpo).strip()


def titulo_de(html):
    u"""Titulo da pagina, na ordem: h1 com texto, <title>, og:title.

    O h1 pode CASAR e vir VAZIO: em 6 paginas ele contem so a imagem da marca, e
    o texto esta no alt. Um fallback que so dispara quando o regex nao casa
    deixava essas 6 sem titulo -- e resultado de busca sem titulo e resultado
    inutil. Aqui cada candidato so vale se sobrar texto depois de tirar as tags.
    """
    def limpa(bruto):
        t = re.sub(r"<[^>]+>", u" ", bruto)
        t = (t.replace("&amp;", u"&").replace("&#039;", u"'")
              .replace("&#8217;", u"'").replace("&#8211;", u"-")
              .replace("&nbsp;", u" "))
        return re.sub(r"\s+", u" ", t).strip()

    for rex in (r"<h1[^>]*>(.*?)</h1>",
                r"<title[^>]*>(.*?)</title>",
                r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"'):
        for m in re.finditer(rex, html, re.S):
            t = limpa(m.group(1))
            # o sufixo do veiculo/tema no <title> nao ajuda a identificar a pagina
            t = re.sub(r"\s*[|–—-]\s*Mirow(\s*&(amp;)?\s*Co\.?)?\s*$",
                       u"", t).strip()
            if t:
                return t
    return u""


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(argv[1])
    dry = "--dry" in argv

    sm = os.path.join(pub, "sitemap.xml")
    if not os.path.exists(sm):
        raise SystemExit(u"nao achei o sitemap.xml — ele e a fonte das paginas "
                         u"de conteudo (gerado do canonical na onda 33)")
    urls = re.findall(r"<loc>([^<]+)</loc>",
                      io.open(sm, encoding="utf-8").read())

    itens, sem_arquivo, stubs = [], [], []
    for u in urls:
        rel = u.replace("https://mirow.com.br", "").strip("/")
        p = os.path.join(pub, rel.replace("/", os.sep), "index.html") if rel \
            else os.path.join(pub, "index.html")
        if not os.path.exists(p):
            sem_arquivo.append(u)
            continue
        html = io.open(p, encoding="utf-8", errors="ignore").read()
        # stub nunca entra: e noindex, e o resultado saltaria de pagina
        if 'http-equiv="refresh"' in html or "window.location.replace" in html:
            stubs.append(u)
            continue
        m = re.search(r'<html[^>]*lang="([a-zA-Z-]+)"', html)
        lang = (m.group(1) if m else "pt")[:2].lower()
        itens.append({"l": lang,
                      "u": u.replace("https://mirow.com.br", ""),
                      "t": titulo_de(html),
                      "x": texto_de(html)[:TETO_TEXTO]})

    if sem_arquivo:
        for u in sem_arquivo:
            print(u"  ERRO: sitemap lista %s e o arquivo nao existe" % u)
        raise SystemExit(1)

    itens.sort(key=lambda d: (d["l"], d["u"]))
    por_lang = {}
    for d in itens:
        por_lang[d["l"]] = por_lang.get(d["l"], 0) + 1

    saida = os.path.join(pub, "busca-indice.json")
    corpo = json.dumps({"gerado_de": "sitemap.xml", "itens": itens},
                       ensure_ascii=False, separators=(",", ":"))
    if not dry:
        with io.open(saida, "w", encoding="utf-8", newline="\n") as f:
            f.write(corpo)

    sem_titulo = [d["u"] for d in itens if not d["t"]]
    curtos = [d["u"] for d in itens if len(d["x"]) < 80]

    print(u"%d pagina(s) no indice (%s)%s"
          % (len(itens),
             u", ".join(u"%s=%d" % kv for kv in sorted(por_lang.items())),
             u" (dry-run)" if dry else u""))
    print(u"%d stub(s) fora, por construcao" % len(stubs))
    print(u"indice: %.1f KB" % (len(corpo.encode("utf-8")) / 1024.0))
    if sem_titulo:
        print(u"ATENCAO: %d pagina(s) sem <h1> nem <title>: %s"
              % (len(sem_titulo), sem_titulo[:3]))
    if curtos:
        print(u"ATENCAO: %d pagina(s) com menos de 80 chars de texto: %s"
              % (len(curtos), curtos[:5]))
    if not dry:
        print(u"gravado em public/busca-indice.json")


if __name__ == "__main__":
    main(sys.argv)
