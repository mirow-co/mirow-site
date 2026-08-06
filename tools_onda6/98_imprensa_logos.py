# -*- coding: utf-8 -*-
"""Onda 41 / S-136 (issue mirow-marketing#190): logos grandes dos veículos à
esquerda na Imprensa.

Pedido do Mario (06/08, verbatim): "melhorar os logos dos veículos de mídia
dentro de 'Imprensa', de forma a deixar logos grandes no lado esquerdo, dando
destaque a esses veículos. busque esses logos online."

Os logos de favicon (16–64px, uploads/2026/08/imprensa/) saem; entram wordmarks
oficiais buscados online (uploads/2026/08/imprensa-logos/), com o mapa e as
fontes no mestre P3 do repo privado:

    08_Site/2026-08-06_imprensa-veiculos-curadoria.json

Veículo com `arquivo: null` no mestre vira wordmark tipográfico (fallback de
texto) — hoje epbr (site fora do ar), CZ Insights e Money Times (sem asset
utilizável).

O layout muda só por CSS (grid-areas sobre os mesmos 4 filhos do link):

    [ LOGO grande ]  VEÍCULO · data
    [  à esquerda ]  Título da matéria

Uso: python tools_onda6/98_imprensa_logos.py <raiz> [--mestre=<caminho.json>]
"""
import io
import json
import os
import re
import sys

from _onda7_css import resolve_public, ler, gravar, escrever_bloco_css

MESTRE_DEFAULT = os.path.join(
    os.environ.get("USERPROFILE", ""), "OneDrive - Mirow", "Mirow & Co",
    "05_Marketing", "05_NovoMarketing", "08_Site",
    "2026-08-06_imprensa-veiculos-curadoria.json")

PAGINAS = ["pt/imprensa/index.html", "en/press/index.html",
           "de/presse/index.html"]

DIR_LOGOS = "wp-content/uploads/2026/08/imprensa-logos"

# mesmo mecanismo dos logos de clientes: a query impede o plugin svgs-inline
# do tema de inlinar o SVG (ids/classes genericas colidem entre logos).
QUERY_ANTI_INLINE = "?ver=1"

CSS = """
/* ---- S-136 (#190): logo grande do veiculo a esquerda ------------------
   O grid do link (S-102) deixa de ser [icone|veiculo|data|titulo] numa linha
   e vira duas colunas: o logo ocupa a coluna esquerda inteira (destaque ao
   veiculo, pedido do Mario 06/08) e o conteudo empilha a direita. Os filhos
   do <a> sao os mesmos 4 — so as areas mudam. */
.onda26-imprensa__link{grid-template-columns:200px max-content 1fr;
  grid-template-areas:"logo veiculo data" "logo titulo titulo";
  align-items:center;gap:4px 26px;padding:20px 22px}
.onda41-imprensa__logo{grid-area:logo;justify-self:start;align-self:center;
  display:block;width:auto;height:auto;max-width:176px;max-height:52px;
  object-fit:contain;background:none;border-radius:0;padding:0}
.onda41-imprensa__logo--texto{font-weight:900;font-size:24px;line-height:1.1;
  color:#020E66;letter-spacing:.01em}
.onda18-imprensa__veiculo{grid-area:veiculo;font-size:13px;font-weight:700;
  letter-spacing:.08em;text-transform:uppercase;color:#7F7F7F}
.onda18-imprensa__data{grid-area:data;font-size:13px}
.onda18-imprensa__titulo{grid-area:titulo;font-size:17px}
@media only screen and (max-width: 991px){
  .onda26-imprensa__link{grid-template-columns:132px 1fr;
    grid-template-areas:"logo veiculo" "logo data" "titulo titulo";
    gap:2px 16px;padding:16px 16px}
  .onda41-imprensa__logo{max-width:116px;max-height:40px}
  .onda41-imprensa__logo--texto{font-size:19px}
  .onda18-imprensa__data{grid-column:auto}
  .onda18-imprensa__titulo{grid-column:1 / -1;margin-top:8px}
}
"""


def carregar_mestre(caminho):
    with io.open(caminho, encoding="utf-8") as f:
        return {v["nome"]: v["arquivo"]
                for v in json.load(f)["veiculos"]}


def trocar_logos(html, prefixo, mapa):
    """Troca cada <img onda18-imprensa__logo> pelo logo grande (ou texto)."""
    rex = re.compile(
        r'<img class="onda18-imprensa__logo[^"]*"[^>]*>\s*'
        r'<span class="onda18-imprensa__veiculo">([^<]*)</span>')
    faltando = set()

    def sub(m):
        nome = m.group(1).replace("&amp;", "&")
        if nome not in mapa:
            faltando.add(nome)
            return m.group(0)
        arq = mapa[nome]
        if arq:
            # sem loading="lazy": os logos SAO o conteudo da pagina, pesam
            # poucos KB cada, e a caixa 0x0 pre-carga aparecia como elemento
            # zerado no contact sheet (e como layout shift para o leitor).
            novo = ('<img class="onda41-imprensa__logo" src="%s%s/%s%s" '
                    'alt="%s">'
                    % (prefixo, DIR_LOGOS, arq,
                       QUERY_ANTI_INLINE if arq.endswith(".svg") else "",
                       m.group(1)))
        else:
            novo = ('<span class="onda41-imprensa__logo '
                    'onda41-imprensa__logo--texto" aria-hidden="true">%s</span>'
                    % m.group(1))
        return novo + ('<span class="onda18-imprensa__veiculo">%s</span>'
                       % m.group(1))

    novo = rex.sub(sub, html)
    return novo, faltando


def main(argv):
    root = argv[1] if len(argv) > 1 else "."
    mestre = MESTRE_DEFAULT
    for a in argv[2:]:
        if a.startswith("--mestre="):
            mestre = a.split("=", 1)[1]
    pub = resolve_public(root)
    mapa = carregar_mestre(mestre)

    # os arquivos declarados existem? (mesma trava do gen_clients)
    sem_arquivo = [a for a in mapa.values()
                   if a and not os.path.exists(
                       os.path.join(pub, DIR_LOGOS.replace("/", os.sep), a))]
    if sem_arquivo:
        raise SystemExit("logo(s) declarado(s) no mestre e ausente(s) em %s: %s"
                         % (DIR_LOGOS, ", ".join(sem_arquivo)))

    mudadas = 0
    for rel in PAGINAS:
        p = os.path.join(pub, rel.replace("/", os.sep))
        html = ler(p)
        if 'onda41-imprensa__logo' in html:
            print("ok (ja feito): %s" % rel)
            continue
        m = re.search(r'(?:src|href)="(/[^"]*?/)wp-content/', html)
        prefixo = m.group(1) if m else "/"
        novo, faltando = trocar_logos(html, prefixo, mapa)
        if faltando:
            raise SystemExit("%s: veiculo(s) fora do mestre: %s"
                             % (rel, ", ".join(sorted(faltando))))
        if novo == html:
            raise SystemExit("%s: nenhum logo trocado — markup mudou?" % rel)
        gravar(p, novo)
        mudadas += 1
        print("logos trocados: %s" % rel)

    mudou_css = escrever_bloco_css(pub, "imprensa-logos", CSS, onda="onda41")
    print("%d pagina(s) mudada(s); css %s"
          % (mudadas, "atualizado" if mudou_css else "inalterado"))


if __name__ == "__main__":
    main(sys.argv)
