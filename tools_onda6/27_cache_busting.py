# -*- coding: utf-8 -*-
"""
27_cache_busting.py — onda 8.1: ?v=<N> em todos os assets proprios das ondas.

Uso:  python tools_onda6/27_cache_busting.py <raiz-que-contem-public>

RODAR SEMPRE POR ULTIMO na sequencia da onda: qualquer script que insira um
<link>/<script> novo o faz sem query, e e este aqui que carimba a versao.

Por que existe
--------------
O Mario abriu o site no ar e viu os contatos do hero quebrados: texto azul
empilhado, icones minusculos, clique sem efeito. O CSS novo ESTAVA no servidor —
o navegador dele e que serviu a versao velha do onda6.css, do cache, porque a URL
do <link> nunca muda. Sem o CSS: os <li> viram lista vertical, o <a> pega o azul
padrao do navegador e o `.banner__background` (absolute, z-index 1) fica por cima
dos links e come o clique. Ou seja: um bug de cache com cara de bug de layout.

A partir daqui todo asset proprio das ondas carrega ?v=<VERSAO>. Nas proximas
ondas basta INCREMENTAR a constante abaixo e rodar este script — todas as
paginas passam a pedir o arquivo novo.

    VERSAO = 9   ->  onda6.css?v=9

Cobre os quatro assets proprios: onda6/onda6.css, onda6/onda8-dobra.js,
onda6/onda9-rede.js (mapa da pagina "Nossa rede") e clientes/clientes-logos.css.
O CSS do TEMA entrou na lista na onda 58 (#229). A regra antiga dizia "o tema nao e
tocado (os assets dele tem a versao que o WordPress ja carimbou)" -- e valia enquanto
nunca mexiamos nele. Mexemos duas vezes: tirar os @import de fontes (#227) e trocar os
pesos orfaos (#229). Arquivo que a gente edita TEM de ser versionado por nos, senao o
navegador serve `?ver=1` do cache e a correcao nao existe no ar (erro no 9 do CLAUDE.md).

Idempotente: se a versao ja e a atual, nao mexe.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

# >>> proximas ondas: incrementar aqui e rodar o script <<<
VERSAO = 96

ASSETS = [
    "wp-content/uploads/2026/07/onda6/onda6.css",
    "wp-content/uploads/2026/07/onda6/onda8-dobra.js",
    "wp-content/uploads/2026/07/onda6/onda9-rede.js",
    "wp-content/uploads/2026/07/onda6/onda13-hero-plexus.js",
    "wp-content/uploads/2026/07/onda6/onda17-horizonte.js",
    "wp-content/uploads/2026/07/onda6/onda31-medicao.js",
    "wp-content/uploads/2026/07/onda6/onda54-leadfeeder.js",
    "wp-content/uploads/2026/08/onda67/busca.js",
    "wp-content/uploads/2026/07/fontes/fontes-mirow.css",
    "wp-content/uploads/2026/07/clientes/clientes-logos.css",
    # CSS do tema: entrou porque passamos a edita-lo (ver acima).
    "wp-content/themes/mirow/public/bundle-css.css",
    # Onda 68: os favicons. Trocamos o CONTEUDO dos arquivos mantendo o nome (as
    # 109 paginas ja os referenciam), entao SEM carimbo o navegador serviria o
    # icone velho do cache e a troca "nao funcionaria" no ar. Favicon e o caso
    # mais agressivo de cache que existe -- erro 6 e 9 do CLAUDE.md.
    # `favicon.ico` da RAIZ nao entra: nenhuma tag o referencia (o navegador bate
    # em /favicon.ico por convencao), logo nao ha href para carimbar.
    "wp-content/uploads/2023/04/cropped-favicon-mirow-32x32.png",
    "wp-content/uploads/2023/04/cropped-favicon-mirow-180x180.png",
    "wp-content/uploads/2023/04/cropped-favicon-mirow-192x192.png",
    "wp-content/uploads/2023/04/cropped-favicon-mirow-270x270.png",
    "wp-content/themes/mirow/favicon.ico",
    # Onda 68, segunda metade: o mask-icon do Safari e o manifest. Os dois entram
    # por `href=`. O `icone-mirow-512.png` NAO entra: ele e citado dentro do JSON do
    # manifest e dentro do JSON-LD, e carimbar URL de dado estruturado atrapalha o
    # crawler em vez de ajudar -- ali a URL e identidade, nao cache de navegador.
    # As derivadas de `og:image` tambem ficam fora, pelo mesmo motivo: o scraper
    # indexa pela URL, e trocar a URL a cada onda invalidaria preview que ja funciona.
    "wp-content/uploads/2026/08/onda68/marca-m-mask.svg",
    "site.webmanifest",
]

# Onda 80c. PASTAS inteiras de asset nosso, para o carimbo nao depender de alguem
# lembrar de listar arquivo por arquivo.
#
# O caso que obrigou: os 26 logos de instituicao da onda 79 entraram sem `?v=`.
# Duas horas depois eu troquei o CONTEUDO desses arquivos (a onda 80 tirou de
# dentro deles um <style> que vazava e pintava a pagina inteira de vermelho) --
# e o Mario continuou vendo tudo vermelho, com o HTML novo na tela. O navegador
# dele estava injetando o SVG VELHO, do cache, porque a URL nunca mudou.
#
# E o pior tipo desse bug: eu media a pagina num navegador limpo e via correto,
# ele abria no dele e via errado, e nos dois casos o servidor estava certo.
# Erro 6 e 9 do CLAUDE.md, na variante "o asset que EU criei nesta onda".
#
# Por pasta, e nao por arquivo, porque a lista de logos muda a cada lider novo --
# lista manual e valor gemeo esperando divergir (erro 18).
PASTAS = [
    "wp-content/uploads/2026/08/onda79/logos/",
    # Entraram na mesma onda, pelo mesmo motivo: a onda 80 editou o CONTEUDO de
    # energisa.svg, bnews.svg e imp-consulting-logo.svg (tirou de dentro deles o
    # <style> com nome de classe generico, que colide entre dois logos injetados
    # na mesma pagina). Os tres saiam com o `?ver=1` que o WordPress carimbou uma
    # vez, em 2023, e que nunca mais muda -- ou seja, cache eterno sobre arquivo
    # que a gente edita. Quem descobriu foi a S183, na primeira execucao dela.
    "wp-content/uploads/2026/07/clientes/",
    "wp-content/uploads/2026/08/imprensa-logos/",
    "wp-content/uploads/2026/08/rede/",
]


def carimbar(html):
    """Poe/atualiza ?v=VERSAO em toda referencia aos nossos assets.

    Aceita aspa SIMPLES ou DUPLA. O padrao antigo exigia aspa dupla, e o <link>
    do tema que o WordPress gera usa simples:
        <link rel='stylesheet' href='/wp-content/themes/.../bundle-css.css?ver=1'>
    Resultado: ao registrar o CSS do tema na lista (onda 58), o carimbo nao pegava
    e a correcao teria ficado presa no cache dos visitantes. Mesma classe do furo
    do dns-prefetch do AddToAny (onda 55b), que tambem assumia aspa dupla.
    """
    # `content=` entrou na onda 68: o <meta name="msapplication-TileImage"> declara
    # o icone do bloco do Windows em content=, nao em href=, e por isso o 270x270
    # era o UNICO dos 5 favicons que saia sem carimbo -- conferido no navegador, os
    # outros 4 vinham com ?v=82 e ele nao. Erro 6 do CLAUDE.md, na variante que o
    # atributo esconde. Nenhum og:image entra por aqui porque a ASSETS lista so
    # arquivo nosso, e nenhum deles e imagem de preview.
    ASPA = '["\']'
    for asset in ASSETS:
        rex = re.compile(r'((?:href|src|content)=)(' + ASPA + r')([^"\']*?'
                         + re.escape(asset) + r')(\?[^"\']*)?\2')
        html = rex.sub(lambda m: u'%s%s%s?v=%d%s'
                       % (m.group(1), m.group(2), m.group(3), VERSAO, m.group(2)), html)
    # Onda 67: o busca.js usa window.ONDA67_V no ?v= do busca-indice.json. Aquele
    # numero e escrito pelo 134_busca_estatica.py no momento em que ele roda, e
    # sem esta linha ele nao acompanharia a VERSAO -- o navegador serviria o
    # INDICE VELHO depois de uma onda que muda conteudo, e a busca devolveria
    # pagina que nao existe mais. Valor gemeo, resolvido no carimbo.
    # o mesmo carimbo, agora para qualquer arquivo dentro das PASTAS
    for pasta in PASTAS:
        rex = re.compile(r'((?:href|src|content)=)(' + ASPA + r')([^"\']*?'
                         + re.escape(pasta) + r'[A-Za-z0-9._-]+)(\?[^"\']*)?\2')
        html = rex.sub(lambda m: u'%s%s%s?v=%d%s'
                       % (m.group(1), m.group(2), m.group(3), VERSAO, m.group(2)), html)
    html = re.sub(r'window\.ONDA67_V\s*=\s*"\d+"',
                  'window.ONDA67_V="%d"' % VERSAO, html)
    return html


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    alterados = 0
    tocados = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if not nome.endswith(".html"):
                continue
            path = os.path.join(dirpath, nome)
            html = ler(path)
            if not any(a in html for a in ASSETS) and not any(x in html for x in PASTAS):
                continue
            tocados += 1
            novo = carimbar(html)
            if novo != html:
                gravar(path, novo)
                alterados += 1

    print("paginas com asset proprio: %d" % tocados)
    print("versao carimbada: v=%d" % VERSAO)
    print("\nresumo: %d arquivo(s) HTML alterado(s)" % alterados)


if __name__ == "__main__":
    main()
