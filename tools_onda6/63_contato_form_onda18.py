# -*- coding: utf-8 -*-
"""63 — onda 18, S-58..S-62 (issues #116 #117 #118 #119 #120): formulario de contato.

Uso:
    python tools_onda6/63_contato_form_onda18.py <raiz-que-contem-public>

Cinco pedidos do Mario, todos no formulario Formidable (form_id=1) que aparece na
pagina de contato de cada idioma e nas paginas de lider/artigo:

  S-58  titulo: "Voce e cliente? Fale conosco" -> "Voce quer ser nosso cliente? Fale conosco"
  S-59  label do campo 4 (field_e6lis6): "Area de Atuacao" -> "Empresa"
  S-60  telefone (campo 6, field_q1ajd) deixa de ser obrigatorio
  S-61  textarea Mensagem (campo 5, field_9jv0r1) chega com mensagem-padrao editavel
  S-62  botao de envio deixa de ser azul-contra-azul (bloco CSS onda18:contato-botao)

Idempotente: cada troca e detectada pelo estado final (rodar 2x = 0 mudancas).
O texto-padrao da mensagem (S-61) e uma proposta do Claude — precisa de OK do Mario.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (escrever_bloco_css, gravar, idioma_da_pagina, ler,  # noqa: E402
                        resolve_public)

MARK_PERSONA = re.compile(
    r'(<!-- onda11:s12-persona-cliente -->)(.*?)(<!-- /onda11:s12-persona-cliente -->)', re.S)

# S-58 — titulo por idioma
TITULO = {
    "pt": u"<small>Você quer ser nosso cliente?</small><br>",
    "en": u"<small>Do you want to become our client?</small><br>",
    "de": u"<small>Möchten Sie unser Kunde werden?</small><br>",
}

# S-59 — label do campo "Area de Atuacao"
EMPRESA = {"pt": u"Empresa", "en": u"Company", "de": u"Unternehmen"}

# S-61 — mensagem-padrao pre-preenchida (PROPOSTA — depende de OK do Mario)
PADRAO = {
    "pt": (u"Olá! Vim pelo site da Mirow & Co. e gostaria de conversar sobre "
           u"um desafio da minha empresa."),
    "en": (u"Hello! I came from the Mirow & Co. website and would like to talk "
           u"about a challenge at my company."),
    "de": (u"Hallo! Ich komme über die Website von Mirow & Co. und würde "
           u"gerne über eine Herausforderung in meinem Unternehmen sprechen."),
}

# S-62 — botao de envio visivel contra o fundo azul
CSS = """/* S-62: o botao herdava #0e41a7 do tema sobre a secao azul (invisivel).
   Passa a ciano Mirow com texto navy — o contraste maximo da paleta.
   A regra do tema e `.contact__form .frm_pro_form .frm_button_submit` (3 classes,
   com !important): o seletor daqui precisa da MESMA especificidade ou mais, senao
   perde mesmo tendo !important. */
.contact .contact__form .frm_pro_form .frm_button_submit,
.contact .contact__form .frm_pro_form .frm_final_submit{
  background:#00ADEC !important;border:2px solid #00ADEC !important;
  color:#020E66 !important;font-weight:700 !important;letter-spacing:.02em;
  transition:background 200ms ease,color 200ms ease}
.contact .contact__form .frm_pro_form .frm_button_submit:hover,
.contact .contact__form .frm_pro_form .frm_final_submit:hover{
  background:#fff !important;border-color:#fff !important;color:#020E66 !important}
/* S-60: o asterisco sai do proprio label (o container muda de numero por idioma) */"""


def titulo(html, lang):
    """S-58 — troca o texto da persona no titulo da pagina de contato."""
    novo = TITULO.get(lang, TITULO["pt"])
    def sub(m):
        return m.group(1) + novo + m.group(3)
    return MARK_PERSONA.sub(sub, html, count=1)


def label_empresa(html, lang):
    """S-59 — renomeia o label do campo de area de atuacao.

    O id do campo tem sufixo por idioma (field_e6lis6 / ...62 / ...63), porque o
    Formidable duplicou o formulario por lingua — daí o \\d* nos padroes.
    """
    alvo = EMPRESA.get(lang, EMPRESA["pt"])
    rex = re.compile(
        r'(<label for="field_e6lis6\d*"[^>]*>)([^<]*)(\s*<span class="frm_required")', re.S)
    return rex.sub(lambda m: m.group(1) + alvo + "\n        " + m.group(3).lstrip(), html)


def telefone_opcional(html):
    """S-60 — o campo de telefone deixa de ser obrigatorio.

    O container tem numero diferente em cada idioma (frm_field_6/60/67...), entao
    ele e achado pelo INPUT que carrega dentro (type=tel), nao pelo id.
    """
    # (a) container do telefone perde a classe frm_required_field
    partes = re.split(r'(?=<div id="frm_field_\d+_container")', html)
    for i, parte in enumerate(partes):
        if not parte.startswith('<div id="frm_field_'):
            continue
        if not re.search(r'type="tel" id="field_q1ajd\d*"', parte):
            continue
        m = re.match(r'<div id="frm_field_\d+_container"[^>]*>', parte)
        if m:
            partes[i] = (m.group(0).replace(" frm_required_field", "")
                         + parte[m.end():])
    html = "".join(partes)

    # (b) o asterisco do label sai
    def sem_asterisco(m):
        return re.sub(r'\s*<span class="frm_required"[^>]*>\*</span>', "", m.group(0))
    html = re.sub(r'<label for="field_q1ajd\d*".*?</label>', sem_asterisco, html, flags=re.S)

    # (c) o input perde aria-required e a mensagem de obrigatorio
    def input_opcional(m):
        tag = m.group(0)
        tag = tag.replace(' aria-required="true"', "")
        tag = re.sub(r'\s*data-reqmsg="[^"]*"', "", tag)
        return tag
    html = re.sub(r'<input type="tel" id="field_q1ajd\d*"[^>]*/>', input_opcional, html)
    return html


def mensagem_padrao(html, lang):
    """S-61 — textarea da mensagem chega preenchida com o texto-padrao."""
    texto = PADRAO.get(lang, PADRAO["pt"])
    rex = re.compile(r'(<textarea name="item_meta\[\d+\]" id="field_9jv0r1\d*"[^>]*>)'
                     r'(.*?)(</textarea>)', re.S)

    def sub(m):
        if m.group(2).strip():
            return m.group(0)  # ja preenchido (idempotencia)
        return m.group(1) + texto + m.group(3)
    return rex.sub(sub, html, count=1)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mudou_css = escrever_bloco_css(pub, "contato-botao", CSS, onda="onda18")
    print("bloco onda18:contato-botao %s" % ("gravado" if mudou_css else "ja estava igual"))

    tot = {"titulo": 0, "empresa": 0, "telefone": 0, "mensagem": 0, "paginas": 0}
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if n != "index.html":
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if not re.search(r'id="form_contact-form\d*"', h):
                continue
            lang = idioma_da_pagina(h)
            orig = h

            antes = h
            h = titulo(h, lang)
            if h != antes:
                tot["titulo"] += 1
            antes = h
            h = label_empresa(h, lang)
            if h != antes:
                tot["empresa"] += 1
            antes = h
            h = telefone_opcional(h)
            if h != antes:
                tot["telefone"] += 1
            antes = h
            h = mensagem_padrao(h, lang)
            if h != antes:
                tot["mensagem"] += 1

            if h != orig:
                gravar(p, h)
                tot["paginas"] += 1

    print("resumo: %d pagina(s) alterada(s) — titulo %d, empresa %d, telefone %d, mensagem %d"
          % (tot["paginas"], tot["titulo"], tot["empresa"], tot["telefone"], tot["mensagem"]))


if __name__ == "__main__":
    main()
