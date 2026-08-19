# -*- coding: utf-8 -*-
u"""133 — issue #215: o llms.txt passa a declarar IA, e para de mandar o robô
para uma página que virou stub.

Uso: python tools_onda6/133_llms_ia_e_contato.py <raiz-que-contem-public>

DOIS CONSERTOS, E O SEGUNDO NÃO ESTAVA NO PEDIDO
------------------------------------------------
**(1) IA (o pedido, #215).** A camada que os LLMs leem não dizia uma palavra
sobre IA. O `knowsAbout` do JSON-LD já cita *advanced analytics* (medido em
19/08), mas o `llms.txt` descrevia a firma sem mencionar IA — enquanto a home,
desde a onda 58, abre com o selo **AI Powered** e a frase *"consultoria
estratégica tradicional que utiliza IA nos seus projetos de estratégia e
inovação, compras e go-to-market/pricing"*.

**O limite que o próprio pedido impõe, e que este script respeita:** *"nunca
prometer no invisível o que o visível não diz"*. Então o `llms.txt` recebe
**exatamente** o que já está publicado e visível na home — nem uma aplicação de
IA a mais. O detalhe por prática (issues #212/#213/#214) entra aqui **na mesma
onda em que as seções visíveis entrarem**, e não antes; aquelas dependem do OK
do Andreas.

**(2) O link morto, achado ao medir.** O arquivo mandava o robô para
`/pt/contato/` e anunciava *"WhatsApp, e-mail e formulário"*. Medido: aquela
página é **stub de redirect** (`canonical` para `/pt/`) e **não tem formulário
nenhum** — a página de contato foi eliminada, e o contato passou a ser as
pílulas do hero. Ou seja: a camada feita para ensinar a máquina estava
ensinando (a) uma URL que redireciona e (b) um canal que não existe.

Também entra o **escritório de São Paulo**, que o arquivo não citava — a sede
jurídica (CNPJ) é no Rio e a filial é em São Paulo (ver o comentário da S149),
e o `llms.txt` só conhecia o Rio.

Idempotente: rodar 2x reporta 0 mudanças.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public  # noqa: E402

# ------------------------------------------------------------------ (1) IA
# Cada frase abaixo tem contrapartida VISIVEL hoje:
#   "AI Powered"                     -> selo do hero das 3 homes (onda 58, #211)
#   "consultoria estrategica         -> paragrafo do hero das 3 homes
#    tradicional que utiliza IA..."
# Nada aqui afirma aplicacao de IA que a pagina nao afirme.
BLOCO_IA = u"""
## Inteligência artificial

Posicionamento declarado no site (selo **AI Powered** na página inicial):
consultoria estratégica tradicional que **utiliza IA nos projetos** de
estratégia e inovação, sourcing/compras e go-to-market/pricing — com
resultados acordados, trabalhando lado a lado com a equipe do cliente.

A IA entra como ferramental dentro do método, não como produto separado: não
há oferta de "projeto de IA" avulsa. O detalhamento por prática está em
elaboração e será publicado nas páginas das próprias práticas.
"""

# --------------------------------------------------- (2) contato e escritorio
CONTATO_ANTES = u"""- [Contato](/pt/contato/): WhatsApp, e-mail e formulário"""
CONTATO_DEPOIS = u"""- [Carreiras](/pt/carreiras/): vagas abertas e envio de currículo"""

RODAPE_ANTES = u"""## Contato

- Rua Lauro Müller, 116 — sala 1504, Rio de Janeiro — RJ, Brasil, CEP 22290-160
- LinkedIn: https://www.linkedin.com/company/mirow-co-/
- Instagram: https://www.instagram.com/mirowandco"""

RODAPE_DEPOIS = u"""## Contato

Não há formulário de contato no site: os canais diretos ficam na página
inicial (WhatsApp, e-mail, LinkedIn e Instagram).

- Sede (assento jurídico): Rua Lauro Müller, 116 — sala 1504,
  Rio de Janeiro — RJ, Brasil, CEP 22290-160
- Escritório: Av. Ibirapuera, 2033 — conjunto 133, São Paulo — SP, Brasil,
  CEP 04029-100
- LinkedIn: https://www.linkedin.com/company/mirow-co-/
- Instagram: https://www.instagram.com/mirowandco"""

# a linha de abertura tambem passa a citar o escritorio, sem tirar a sede
ABERTURA_ANTES = u"> Consultoria estratégica brasileira (Rio de Janeiro) especializada em"
ABERTURA_DEPOIS = (u"> Consultoria estratégica brasileira — sede no Rio de Janeiro, "
                   u"escritório\n> em São Paulo — especializada em")


def main(argv):
    pub = resolve_public(argv[1] if len(argv) > 1 else ".")
    caminho = os.path.join(pub, "llms.txt")
    if not os.path.exists(caminho):
        raise SystemExit(u"nao achei %s" % caminho)
    txt = io.open(caminho, encoding="utf-8").read()
    original = txt

    # (1) o bloco de IA entra ANTES de "## Páginas principais"
    if u"## Inteligência artificial" not in txt:
        marca = u"\n## Páginas principais"
        if marca not in txt:
            raise SystemExit(u"nao achei a secao 'Páginas principais' no llms.txt")
        txt = txt.replace(marca, BLOCO_IA + marca, 1)
        print(u"  + bloco de IA")
    else:
        print(u"  = bloco de IA (ja tem)")

    # (2) o link de contato morto vira carreiras
    if CONTATO_ANTES in txt:
        txt = txt.replace(CONTATO_ANTES, CONTATO_DEPOIS, 1)
        print(u"  + link morto /pt/contato/ (stub, sem form) -> /pt/carreiras/")
    else:
        print(u"  = link de contato (ja tratado)")

    if RODAPE_ANTES in txt:
        txt = txt.replace(RODAPE_ANTES, RODAPE_DEPOIS, 1)
        print(u"  + rodape: escritorio de Sao Paulo e a nota de que nao ha formulario")
    else:
        print(u"  = rodape (ja tratado)")

    if ABERTURA_ANTES in txt:
        txt = txt.replace(ABERTURA_ANTES, ABERTURA_DEPOIS, 1)
        print(u"  + abertura cita sede e escritorio")
    else:
        print(u"  = abertura (ja tratada)")

    if txt == original:
        print(u"\n0 mudanca")
        return

    with io.open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)

    # rele e confere o EFEITO, nao a intencao (P2.1)
    de_volta = io.open(caminho, encoding="utf-8").read()
    problemas = []
    if not re.search(r"(?i)intelig[eê]ncia artificial|\bIA\b|AI Powered", de_volta):
        problemas.append(u"o arquivo gravado nao menciona IA")
    if u"/pt/contato/" in de_volta:
        problemas.append(u"ainda aponta para /pt/contato/, que e stub")
    if u"formulário" in de_volta and u"Não há formulário" not in de_volta:
        problemas.append(u"ainda promete formulario")
    if u"São Paulo" not in de_volta:
        problemas.append(u"nao cita o escritorio de Sao Paulo")
    # todo link interno tem de resolver e nao ser stub
    for m in re.finditer(r"\]\((/[^)]+)\)", de_volta):
        rel = m.group(1).strip("/").replace("/", os.sep)
        p = os.path.join(pub, rel, "index.html")
        if not os.path.exists(p):
            problemas.append(u"link %s nao existe" % m.group(1))
            continue
        h = io.open(p, encoding="utf-8", errors="ignore").read()
        if 'http-equiv="refresh"' in h or "window.location.replace" in h:
            problemas.append(u"link %s e stub de redirect" % m.group(1))
    if problemas:
        for pr in problemas:
            print(u"  ERRO: %s" % pr)
        raise SystemExit(1)
    print(u"\nllms.txt: %d bytes, IA declarada, todo link interno resolve e "
          u"nenhum e stub" % len(de_volta.encode("utf-8")))


if __name__ == "__main__":
    main(sys.argv)
