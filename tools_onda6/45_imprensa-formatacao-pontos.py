# -*- coding: utf-8 -*-
"""
45_imprensa-formatacao-pontos.py — Imprensa: formatacao consistente dos pontos.

Issue: mirow-co/mirow-marketing#60 (S-11)

Uso:  python tools_onda6/45_imprensa-formatacao-pontos.py <raiz-da-arvore>

Diagnostico (leitura estatica do HTML, sem CSS proprio para <mark>/<hr>)
-------------------------------------------------------------------------
A pagina de Imprensa e uma lista de ~30 itens (data | veiculo + titulo-link),
cada um fechado por um <hr>. O tema (bundle-css.css) NAO tem nenhuma regra para
`mark` nem para `.wp-block-separator`/`hr` dentro de `.page-default` — cada
item so tem a formatacao que o proprio HTML do WordPress gravou inline. Isso
gera 2 defeitos objetivos, reproduzidos nos 2 arquivos-espelho da pagina
(public/imprensa/ e public/pt/imprensa/, conteudo identico):

1. O <hr> fica com a borda padrao do navegador (rgba(0,0,0,.1) tipicamente),
   que e essencialmente INVISIVEL no fundo navy escuro do tema — os itens
   ficam sem separacao visual real, apesar do <hr> existir no HTML.
2. O <mark> da data/veiculo tem background:#ffffff SEM padding nem
   border-radius — o texto encosta na borda da caixa branca, o que le como
   destaque quebrado (herda o comportamento cru do <mark>), nao como uma
   etiqueta. Alem disso a ordem das tags e inconsistente entre itens: uns tem
   <mark><strong>...</strong></mark>, outros <strong><mark>...</mark></strong>
   (mesmo resultado visual, HTML deselegante).

Correcao (só conteúdo/inline style — onda6.css continua intocado; ver
CLAUDE.md REGRA Nº ZERO. CSS novo de verdade, se algum dia for adotado no
arquivo de tema, fica proposto em tools_onda6/_css_pending_imprensa.css):

- <hr> ganha estilo inline visivel, reaproveitando a cor ja usada no tema para
  bordas sutis sobre o fundo navy (rgba(170,213,232,.35) — a mesma de
  .rede-mapa__box no onda6.css) e uma margem vertical maior, para separar os
  itens de fato.
- <mark> da data/veiculo ganha padding+border-radius+display:inline-block (vira
  uma etiqueta de verdade) e a ordem das tags e normalizada para
  <mark><strong>...</strong></mark> em todos os itens.
- Cada item ganha uma margem superior (no <h6> da data), para dar respiro
  alem do que o <hr> ja separa.

Preserva 100% o tema visual: mesma paleta (branco/azul #091ae4 da propria
pagina + o rgba(170,213,232,.35) que ja existe no onda6.css), mesma fonte,
nenhuma cor nova.

Idempotente: a 2a execucao encontra os mesmos <mark>/<hr> já no formato novo e
não muda nada (a marca ONDA12_MARK cuida disso).
"""
import io
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from _onda7_css import resolve_public, ler, gravar  # noqa: E402

ALVOS = ["imprensa/index.html", "pt/imprensa/index.html"]

MARCADOR_INI = u"<!-- onda12:imprensa-formatacao -->"
MARCADOR_FIM = u"<!-- /onda12:imprensa-formatacao -->"

# cor ja usada no onda6.css (.rede-mapa__box) para borda sutil sobre o navy
COR_SEPARADOR = "rgba(170,213,232,.35)"

RE_H6 = re.compile(
    r'<h6 class="wp-block-heading">(.*?)</h6>',
    re.S,
)
RE_HR = re.compile(
    r'<hr class="wp-block-separator has-alpha-channel-opacity"\s*/>',
)

# extrai o texto "DD/MM/AAAA | VEÍCULO" de qualquer combinação de <mark>/<strong>
RE_TEXTO = re.compile(r'>([^<>]*\d{2}/\d{2}/\d{4}[^<>]*)<', re.S)


def normaliza_h6(m):
    bloco = m.group(1)
    tm = RE_TEXTO.search(bloco)
    if not tm:
        return m.group(0)  # não é um item de data — não mexe (ex.: nenhum aqui, defensivo)
    texto = tm.group(1).strip()
    novo = (
        u'<h6 class="wp-block-heading" style="margin-top:32px">'
        u'<mark style="background-color:#ffffff;color:#091ae4;padding:3px 12px;'
        u'border-radius:4px;display:inline-block" class="has-inline-color">'
        u'<strong>%s</strong></mark></h6>' % texto
    )
    return novo


def aplicar(html):
    orig = html
    html = RE_H6.sub(normaliza_h6, html)
    html = RE_HR.sub(
        u'<hr class="wp-block-separator has-alpha-channel-opacity" '
        u'style="border:none;border-top:1px solid %s;opacity:1;margin:28px 0" />'
        % COR_SEPARADOR,
        html,
    )
    if html != orig and MARCADOR_INI not in html:
        # marca o início/fim da lista para tools/verificacoes.py rastrear a entrega
        marcador_alvo = u'<h1 class="wp-block-heading">Mirow na imprensa</h1>'
        if marcador_alvo in html:
            html = html.replace(marcador_alvo, MARCADOR_INI + marcador_alvo, 1)
        fim_alvo = (
            u'<h5 class="wp-block-heading has-text-align-center">Para solicitações '
            u'de imprensa, favor entrar em contato com mirow@agenciaecomunica.com.br</h5>'
        )
        if fim_alvo in html:
            html = html.replace(fim_alvo, fim_alvo + MARCADOR_FIM, 1)
    return html


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = 0
    vistos = 0
    for rel in ALVOS:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print(u"AUSENTE (esperado): %s" % rel)
            continue
        vistos += 1
        html = ler(path)
        novo = aplicar(html)
        if novo != html:
            gravar(path, novo)
            alterados += 1
            n_marks = novo.count('border-radius:4px;display:inline-block" class="has-inline-color">')
            n_hr = novo.count('border-top:1px solid %s' % COR_SEPARADOR)
            print(u"%s: %d etiqueta(s) de data normalizada(s), %d separador(es) visível(eis)"
                  % (rel, n_marks, n_hr))
        else:
            print(u"%s: sem mudança (já aplicado)" % rel)
    print(u"\nresumo: %d de %d página(s)-alvo alterada(s)" % (alterados, vistos))


if __name__ == "__main__":
    main()
