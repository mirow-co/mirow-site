# -*- coding: utf-8 -*-
"""Onda 80b: tira o <style> de dentro dos SVG de logo -- ele VAZA para a pagina.

    python tools_onda6/156_svg_sem_style.py .

O DEFEITO
---------
O Mario, olhando o staging: "alguma coisa que voce fez fez com que o logo mirow,
linkedin email, whatsapp ficassem vermelhos, e nao azuis".

Causa medida: `carnegie-mellon-tepper.svg` vem da origem com

    <style>path {fill:#ab1727;}</style>

que e o vermelho da Carnegie Mellon. Dentro de um `<img>` isso e inofensivo --
SVG-como-imagem e um documento isolado, por especificacao. Mas o tema deste site
tem um script que promove `<img src="*.svg">` a `<svg>` INLINE, e ai o `<style>`
passa a ser uma folha de estilo **do documento inteiro**: o seletor `path`, que
nao tem escopo nenhum, pinta de vermelho todo `<path>` da pagina -- a marca no
topo, os icones de LinkedIn, e-mail e WhatsApp.

Eu tinha o texto `path {fill:#ab1727;}` impresso na minha propria medicao de
logos e nao liguei os pontos: eu media o tamanho do desenho, e o defeito era a
folha de estilo que ele carregava junto. Quem viu foi o Mario, olhando a pagina.

O CONSERTO
----------
Nao "escopar" o seletor: ELIMINAR o <style>, transformando cada declaracao em
ATRIBUTO DE APRESENTACAO no proprio elemento. Atributo nao tem alcance fora do
elemento -- nao existe versao dele que vaze.

Escopar seria a solucao obvia e e uma armadilha: o prefixo teria de valer nos
DOIS modos (injetado inline e servido como <img>), e nao ha seletor que faca as
duas coisas -- `:root path` casa o <svg> quando ele e imagem e o <html> quando
ele e inline, ou seja, volta a vazar exatamente no modo que quebrou.

Escopo: so `<style>` com regras simples (seletor de elemento ou de UMA classe,
declaracoes property:value). Qualquer coisa alem disso o script NAO toca e
REPORTA -- meia conversao silenciosa deixaria o logo sem cor.

Idempotente: arquivo sem <style> sai intacto.
"""
import io
import os
import re
import sys
import xml.dom.minidom

# Onda 80b, segunda metade: a varredura e de TODO svg nosso em uploads, nao so
# dos logos da onda 79. Os outros tres arquivos com <style> (energisa, bnews,
# imp-consulting) usam so seletor de CLASSE, entao nao vazam para a pagina do
# jeito que a Carnegie Mellon vazou -- mas os nomes sao genericos (`.cls-1`,
# `.st0`, `.fil1`) e dois logos injetados na MESMA pagina com a mesma classe se
# pintam um ao outro, com o ultimo injetado ganhando. Mesmo defeito, versao
# silenciosa. Alcance da varredura = alcance do problema (erro 17).
PASTA = os.path.join("wp-content", "uploads")

RE_STYLE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)
# "seletor { prop:valor; prop:valor }" com seletor de elemento ou .classe, um so
RE_REGRA = re.compile(r"([^{}]+)\{([^{}]*)\}")
RE_SEL_OK = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9]*|\.[A-Za-z_-][\w-]*)$")
ELEMENTOS = ("path", "g", "rect", "circle", "ellipse", "polygon", "polyline",
             "line", "text", "tspan", "use", "svg")


def regras(css):
    """[(seletor, [(prop, valor)])] ou None se houver algo que eu nao saiba converter."""
    # o CSS pode vir embrulhado em CDATA (o Corel grava assim, e foi o motivo de
    # o bnews.svg sair como "nao convertido" na primeira execucao)
    css = re.sub(r"<!\[CDATA\[|\]\]>", " ", css)
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
    if not css.strip():
        return []
    fora = []
    for sel, corpo in RE_REGRA.findall(css):
        decls = []
        for pedaco in corpo.split(";"):
            if not pedaco.strip():
                continue
            if ":" not in pedaco:
                return None
            prop, val = pedaco.split(":", 1)
            prop, val = prop.strip(), val.strip()
            if not prop or not val or "(" in prop:
                return None
            decls.append((prop, val))
        for s in sel.split(","):
            s = s.strip()
            if not RE_SEL_OK.match(s):
                return None
            fora.append((s, decls))
    # sobrou texto fora de qualquer bloco? entao nao entendi o arquivo
    if RE_REGRA.sub("", css).strip():
        return None
    return fora


def aplicar(svg, sel, decls):
    """Escreve as declaracoes como atributo nos elementos que o seletor casa."""
    if sel.startswith("."):
        alvo = re.compile(r'<([a-zA-Z][\w:-]*)\b([^>]*\bclass\s*=\s*"[^"]*(?<![\w-])'
                          + re.escape(sel[1:]) + r'(?![\w-])[^"]*"[^>]*)(/?)>')
    elif sel in ELEMENTOS:
        alvo = re.compile(r"<(" + sel + r")\b([^>]*?)(/?)>")
    else:
        return svg, 0

    def troca(m):
        tag, attrs, fim = m.group(1), m.group(2), m.group(3)
        # `<path d="..."/>`: o [^>]* do seletor de classe e GULOSO e engole a
        # barra do auto-fechamento, deixando fim="" -- e a reconstrucao gravava
        # `<path d="..."/ fill="#x">`, que nao e XML. Tres logos (PUC-Rio, IMP,
        # Schlumberger) sairam assim na primeira execucao: o tema desistia de
        # injetar, o <img> nao renderizava e o chip colapsava para 10px. Quem
        # pegou foi a medicao de tinta, nao a de cor -- a de cor comparava contra
        # um retrato tirado DEPOIS do estrago.
        if attrs.endswith("/"):
            attrs, fim = attrs[:-1], "/"
        novo = attrs
        for prop, val in decls:
            # atributo que ja existe no elemento VENCE o <style>? Nao: em SVG o
            # <style> tem prioridade sobre atributo de apresentacao. Entao aqui a
            # declaracao do style substitui o atributo homonimo.
            novo = re.sub(r'\s+' + re.escape(prop) + r'\s*=\s*"[^"]*"', "", novo)
            novo += ' %s="%s"' % (prop, val)
        return "<%s%s%s>" % (tag, novo, fim)

    novo, n = alvo.subn(troca, svg)
    return novo, n


def main(raiz):
    pasta = os.path.join(os.path.abspath(raiz), "public", PASTA)
    if not os.path.isdir(pasta):
        print(u"156: pasta de logos ausente")
        return 0
    limpos, ja, nao_sei = 0, 0, []
    todos = []
    for dirpath, _dirs, arquivos in os.walk(pasta):
        for a in arquivos:
            if a.lower().endswith(".svg"):
                todos.append(os.path.join(dirpath, a))
    for p in sorted(todos):
        nome = os.path.relpath(p, pasta).replace(os.sep, "/")
        with io.open(p, encoding="utf-8", errors="replace") as f:
            svg = f.read()
        if not RE_STYLE.search(svg):
            ja += 1
            continue
        conjunto = []
        ok = True
        for corpo in RE_STYLE.findall(svg):
            r = regras(corpo)
            if r is None:
                ok = False
                break
            conjunto.extend(r)
        if not ok:
            nao_sei.append(nome)
            continue
        novo = RE_STYLE.sub("", svg)
        total = 0
        for sel, decls in conjunto:
            novo, n = aplicar(novo, sel, decls)
            total += n
        # VERIFICAR POR OUTRO CAMINHO: quem confere se o arquivo continua sendo
        # SVG e um parser XML de verdade, nao a minha regex -- ela e justamente a
        # parte suspeita. Se o resultado nao e bem-formado, o arquivo ORIGINAL
        # fica e o script reporta. Meia conversao gravada em disco e pior que
        # conversao nenhuma: o logo some e a pagina nao acusa.
        try:
            xml.dom.minidom.parseString(novo.encode("utf-8"))
        except Exception as e:
            nao_sei.append(u"%s (a conversao quebrou o XML: %s)" % (nome, e))
            continue
        with io.open(p, "w", encoding="utf-8", newline="") as f:
            f.write(novo)
        limpos += 1
        print(u"  %-46s <style> convertido em atributo em %d elemento(s)" % (nome, total))
    print(u"156: %d svg limpo(s), %d ja estava(m) sem <style>" % (limpos, ja))
    for n in nao_sei:
        print(u"   NAO CONVERTIDO (css que eu nao sei traduzir, olhar a mao): %s" % n)
    return len(nao_sei)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
