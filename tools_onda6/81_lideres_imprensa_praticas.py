# -*- coding: utf-8 -*-
"""81 — onda 26, os tres pedidos de HTML (S-101, S-102, S-103).

Uso:
    python tools_onda6/81_lideres_imprensa_praticas.py <raiz-que-contem-public>

S-101 (#159) — "adicionar ao nossos lideres na pagina inicial os emails do
  andreas e do felipe, nao do stephan nem do elmar."
  O card de lider e um <button> (abre o modal da bio), entao o link de e-mail nao
  pode morar dentro dele — usa o mesmo truque da S-50 (LinkedIn): um <a> no
  wrapper `.onda18-lider`, sobreposto, ao lado do icone do "in". Assunto e corpo
  no idioma da pagina, como a S-72. Stephan e Elmar ficam sem e-mail, a pedido.

S-102 (#160) — "na pagina imprensa, qualquer lugar da row pode ser um link para
  o artigo, nao apenas seu titulo."
  Cada linha passa a ser UM link so: o conteudo do <li> (logo, veiculo, data e
  titulo) vira o conteudo de um <a> em grid. Um link por linha, nao dois
  sobrepostos — e navegavel por teclado. O titulo deixa de ser <a> e vira <span>
  com a mesma classe, para o estilo (e a assercao S57b, que cobra o logo grudado
  no veiculo) seguirem valendo.

S-103 (#161) — "nas paginas de praticas, trocar o Elmar pelo Andreas e Felipe,
  sempre."
  Em toda pagina de pratica: o bloco do Elmar (botao + modal) sai; se Andreas ou
  Felipe nao estiverem lá, entram — botao e modal copiados da pagina de
  Estrategia do MESMO idioma, que ja traz os dois com a bio traduzida. Paginas de
  pratica sem Elmar nao sao tocadas.

Idempotente: cada mudanca e detectada pelo proprio marcador/classe antes de
escrever; rodar 2x reporta 0 mudancas.
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

# ------------------------------------------------------------------ S-101

# mesmo texto da S-72 (assunto e corpo por idioma)
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
ROTULO_MAIL = {"pt": u"E-mail de %s", "en": u"Email %s", "de": u"E-Mail an %s"}

# quem ganha e-mail no card da home (Stephan e Elmar ficam de fora, a pedido)
EMAILS_LIDER = {
    u"Andreas Mirow": "andreas.mirow@mirow.com.br",
    u"Felipe Diniz": "felipe.diniz@mirow.com.br",
}

CSS_MAIL = u"""/* ---- S-101: e-mail no card de lider da home ---------------------------
   O card e um <button> (modal da bio), entao o link mora no wrapper e se
   sobrepoe — mesmo padrao do icone do LinkedIn da S-50. Fica a esquerda dele. */
.onda26-lider__mail{position:absolute;right:35px;bottom:0;width:35px;height:35px;
  z-index:3;display:flex;align-items:center;justify-content:center;
  color:#0E41A7;border-radius:3px;transition:background 200ms ease,color 200ms ease}
.onda26-lider__mail:hover,.onda26-lider__mail:focus-visible{
  background:rgba(0,173,236,.22);color:#00ADEC;outline:none}
.onda26-lider__mail svg{display:block}
/* no mobile o card estreita (45% da largura) e o cargo chegava a passar por
   baixo do envelope — "Managing Partne✉". Reserva a faixa dos dois icones. */
@media only screen and (max-width: 991px){
  .onda26-lider--mail .home-leaders__card span p{padding-right:74px;
    box-sizing:border-box}
}"""

SVG_MAIL = (u'<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true" '
            u'focusable="false"><path fill="currentColor" d="M3 5h18a1 1 0 0 1 1 1v12'
            u'a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm1.6 2L12 12.3 19.4 7H4.6'
            u'ZM20 8.9l-7.4 5.3a1 1 0 0 1-1.2 0L4 8.9V17h16V8.9Z"/></svg>')

RE_LIDER = re.compile(r'<div class="onda18-lider(?: [^"]*)?">.*?</div>', re.S)

# ------------------------------------------------------------------ S-103

DOADORES = {
    "pt": "pt/pratica/estrategia/index.html",
    "en": "en/practice/strategy/index.html",
    "de": "de/practice/strategie/index.html",
}
LISTA_DONOS = '<div class="experience-single__banner-owner-list">'
BOTAO_DONO = '<button class="experience-single__banner-owner"'


def fatiar_div(html, ini):
    """Devolve o fim (exclusivo) da <div> que comeca em `ini`, contando aninhamento."""
    i = ini
    nivel = 0
    while True:
        m = re.compile(r'<div\b|</div>').search(html, i)
        if not m:
            raise ValueError("div sem fechamento em %d" % ini)
        if m.group(0) == "</div>":
            nivel -= 1
            if nivel == 0:
                return m.end()
        else:
            nivel += 1
        i = m.end()


def blocos_de_dono(html):
    """[(nome, ini, fim)] de cada dono da pratica — botao + modal que o segue."""
    out = []
    for m in re.finditer(re.escape(BOTAO_DONO) + r'.*?<p><strong>([^<]*)</strong>',
                         html, re.S):
        nome = m.group(1).strip()
        fim_botao = html.find("</button>", m.end())
        if fim_botao < 0:
            continue
        fim_botao += len("</button>")
        ini_modal = html.find('<div class="modal fade"', fim_botao)
        # o modal tem de vir imediatamente depois do botao (e o padrao do tema)
        if ini_modal < 0 or (ini_modal - fim_botao) > 4:
            out.append((nome, m.start(), fim_botao))
            continue
        out.append((nome, m.start(), fatiar_div(html, ini_modal)))
    return out


# ------------------------------------------------------------------ S-102

RE_ITEM_IMPRENSA = re.compile(
    r'<li class="onda18-imprensa__item">'
    r'(?P<cabeca>.*?)'
    r'<a class="onda18-imprensa__titulo" href="(?P<href>[^"]+)"'
    r'(?P<attrs>[^>]*)>(?P<titulo>.*?)</a>'
    r'</li>', re.S)

CSS_IMPRENSA = u"""/* ---- S-102: a linha inteira e o link ----------------------------------
   O grid sai do <li> e vai para o <a> que agora envolve a linha toda: assim
   clicar no logo, no veiculo ou na data abre o artigo, e existe UM link por
   linha (nao dois sobrepostos) — o leitor de tela anuncia uma vez, o Tab para
   uma vez. */
.onda18-imprensa__item{display:block;padding:0}
.onda26-imprensa__link{display:grid;
  grid-template-columns:34px minmax(150px,190px) 108px 1fr;
  align-items:center;gap:0 18px;padding:16px 22px;
  text-decoration:none;color:inherit}
.onda26-imprensa__link:focus-visible{outline:2px solid #00ADEC;outline-offset:-2px}
.onda18-imprensa__item:hover .onda18-imprensa__titulo{color:#00ADEC;
  border-bottom-color:#00ADEC}
@media only screen and (max-width: 991px){
  .onda26-imprensa__link{grid-template-columns:28px 1fr;gap:6px 14px;
    padding:14px 16px}
}"""


def com_email(html, lang):
    """S-101 — insere o link de e-mail no card de Andreas e de Felipe."""
    assunto, corpo = EMAIL_TXT.get(lang, EMAIL_TXT["pt"])
    query = "?subject=%s&amp;body=%s" % (quote(assunto.encode("utf-8"), safe=""),
                                         quote(corpo.encode("utf-8"), safe=""))

    def sub(m):
        bloco = m.group(0)
        if "onda26-lider__mail" in bloco:
            # já tem o link: garante só a classe-gancho (idempotência)
            if "onda26-lider--mail" not in bloco:
                bloco = bloco.replace('<div class="onda18-lider"',
                                      '<div class="onda18-lider onda26-lider--mail"', 1)
            return bloco
        mn = re.search(r'<h4>([^<]*)</h4>', bloco)
        if not mn:
            return bloco
        nome = mn.group(1).strip()
        endereco = EMAILS_LIDER.get(nome)
        if not endereco:
            return bloco
        rotulo = ROTULO_MAIL.get(lang, ROTULO_MAIL["pt"]) % nome
        link = (u'<a class="onda26-lider__mail" href="mailto:%s%s" '
                u'aria-label="%s" title="%s">%s</a>'
                % (endereco, query, rotulo, rotulo, SVG_MAIL))
        # a classe no wrapper e o gancho do CSS que reserva a faixa dos icones
        bloco = bloco.replace('<div class="onda18-lider"',
                              '<div class="onda18-lider onda26-lider--mail"', 1)
        return bloco[:-len("</div>")] + link + "</div>"

    return RE_LIDER.sub(sub, html)


def imprensa_linha_toda(html):
    """S-102 — o conteudo do <li> passa a morar dentro de um <a> em grid."""
    if "onda26-imprensa__link" in html:
        return html

    def sub(m):
        titulo = (u'<span class="onda18-imprensa__titulo">%s</span>'
                  % m.group("titulo"))
        return (u'<li class="onda18-imprensa__item">'
                u'<a class="onda26-imprensa__link" href="%s"%s>%s%s</a></li>'
                % (m.group("href"), m.group("attrs").rstrip(),
                   m.group("cabeca"), titulo))

    return RE_ITEM_IMPRENSA.sub(sub, html)


def praticas_sem_elmar(html, doador_blocos):
    """S-103 — tira o Elmar; garante Andreas e Felipe (copiados do doador)."""
    donos = blocos_de_dono(html)
    if not any(u"Elmar" in n for n in (d[0] for d in donos)):
        return html, []
    acoes = []
    # 1) fora o Elmar (de tras para a frente, para nao mover os offsets)
    for nome, ini, fim in reversed(donos):
        if u"Elmar" in nome:
            html = html[:ini] + html[fim:]
            acoes.append(u"Elmar removido")
    # 2) quem falta entra no inicio da lista, na ordem Andreas, Felipe
    presentes = [n for n, _i, _f in blocos_de_dono(html)]
    faltando = [n for n in (u"Andreas Mirow", u"Felipe Diniz") if n not in presentes]
    if faltando:
        pos = html.find(LISTA_DONOS)
        if pos < 0:
            return html, acoes + [u"AVISO: sem .experience-single__banner-owner-list"]
        pos += len(LISTA_DONOS)
        inserir = u"".join(doador_blocos[n] for n in faltando)
        html = html[:pos] + inserir + html[pos:]
        acoes.append(u"entraram: %s" % ", ".join(faltando))
    return html, acoes


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mudou = escrever_bloco_css(pub, "imprensa-linha", CSS_IMPRENSA, onda="onda26")
    print("bloco onda26:imprensa-linha %s" % ("gravado" if mudou else "ja estava igual"))
    mudou = escrever_bloco_css(pub, "lider-mail", CSS_MAIL, onda="onda26")
    print("bloco onda26:lider-mail %s" % ("gravado" if mudou else "ja estava igual"))

    # doadores do S-103: botao + modal de Andreas e Felipe, por idioma
    doador = {}
    for lang, rel in DOADORES.items():
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        doador[lang] = {}
        for nome, ini, fim in blocos_de_dono(h):
            if nome in (u"Andreas Mirow", u"Felipe Diniz"):
                doador[lang][nome] = h[ini:fim]
        faltam = [n for n in (u"Andreas Mirow", u"Felipe Diniz")
                  if n not in doador[lang]]
        if faltam:
            raise SystemExit(u"doador %s sem %s" % (rel, faltam))

    n101 = n102 = n103 = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            p = os.path.join(dirpath, nome)
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            h = ler(p)
            novo = h
            lang = idioma_da_pagina(h)

            if 'class="onda18-lider' in novo:
                antes = novo
                novo = com_email(novo, lang)
                if novo != antes:
                    n101 += 1
                    print("  S-101 e-mails no card: %s" % rel)

            if "onda18-imprensa__item" in novo:
                antes = novo
                novo = imprensa_linha_toda(novo)
                if novo != antes:
                    n102 += 1
                    print("  S-102 linha inteira clicavel: %s" % rel)

            if LISTA_DONOS in novo:
                antes = novo
                novo, acoes = praticas_sem_elmar(novo, doador[lang])
                if novo != antes:
                    n103 += 1
                    print("  S-103 %s: %s" % (rel, "; ".join(acoes)))

            if novo != h:
                gravar(p, novo)

    print("S-101 paginas: %d | S-102 paginas: %d | S-103 paginas: %d"
          % (n101, n102, n103))



if __name__ == "__main__":
    main()
