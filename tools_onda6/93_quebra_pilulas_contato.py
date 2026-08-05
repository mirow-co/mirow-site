# -*- coding: utf-8 -*-
"""93 — onda 40, S-131 (#184): quebra de linha depois da 2a pilula de contato.

Uso:
    python tools_onda6/93_quebra_pilulas_contato.py <raiz-que-contem-public> [--dry-run]

A onda 39 poz as 4 pilulas em 2+2 com um grid de 2 colunas. Funcionou, mas o grid
faz as duas colunas COMPARTILHAREM largura: a coluna 1 fica do tamanho da maior
pilula dela ("Falar no WhatsApp"), entao o Instagram comecava na borda dessa
coluna, alinhado com o "E-mail" e longe do "LinkedIn".

Pedido do Mario (05/08): "instagram deve ficar mais proximo de linkedin, nao
necessariamente paralelo com o item `email`".

O jeito de ter 2+2 SEM colunas compartilhadas e voltar ao flex-wrap (que empacota
natural, com o gap normal entre vizinhos) e forcar a quebra depois da 2a pilula.
A quebra e um item de flex de largura total e altura zero — tecnica padrao, e a
unica que nao exige coluna compartilhada nem media query por idioma.

Este script insere esse item (`<li class="hero-contatos__quebra">`) depois do 2o
`<li>` da lista, nas paginas que tem o bloco onda8:hero-contatos. O CSS dele vive
no bloco onda40:quebra-pilulas do onda6.css.

Por que um <li> vazio e nao um pseudo-elemento: `::before`/`::after` de um `li`
sao filhos DELE, nao da `ul`, entao nao entram no fluxo do flex da lista. E a `ul`
so tem dois pseudo-elementos, ja usados pelo tema em outros contextos.
`aria-hidden` + sem conteudo mantem a lista limpa para leitor de tela.

Idempotente: nao insere de novo se a quebra ja estiver no lugar certo.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

MARK = "onda40:quebra-pilulas"
QUEBRA = ('<li class="hero-contatos__quebra" aria-hidden="true"></li>'
          '<!-- %s -->' % MARK)

# a <ul> das pilulas do hero
REX_UL = re.compile(r'(<ul class="hero-contatos"[^>]*>)(.*?)(</ul>)', re.S)


def divide_lis(interior):
    """Devolve a lista de <li>...</li> de primeiro nivel do interior da <ul>.

    Nao serve regex simples: cada <li> tem <a>, <svg> e <span> dentro. Aqui se
    varre contando abre/fecha de <li>, que nao aninha nesta lista.
    """
    itens, i = [], 0
    while True:
        ini = interior.find("<li", i)
        if ini < 0:
            break
        prof, j = 0, ini
        while True:
            m = re.compile(r'<li\b|</li>').search(interior, j)
            if not m:
                return itens
            if m.group(0) == "</li>":
                prof -= 1
                if prof == 0:
                    itens.append((ini, m.end()))
                    i = m.end()
                    break
            else:
                prof += 1
            j = m.end()
    return itens


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    dry = "--dry-run" in sys.argv

    n, ja, avisos = 0, 0, []
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if not nome.endswith(".html"):
                continue
            p = os.path.join(dirpath, nome)
            h = ler(p)
            if 'class="hero-contatos"' not in h:
                continue
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            m = REX_UL.search(h)
            if not m:
                avisos.append("%s: nao achei a <ul> das pilulas" % rel)
                continue
            interior = m.group(2)
            lis = divide_lis(interior)
            # a quebra nao conta como pilula
            reais = [(a, b) for a, b in lis
                     if "hero-contatos__quebra" not in interior[a:b]]
            if len(reais) != 4:
                avisos.append("%s: %d pilulas (esperado 4) — nao mexi"
                              % (rel, len(reais)))
                continue
            if MARK in interior:
                # confere que esta DEPOIS da 2a pilula, e nao em outro lugar
                pos = interior.find("hero-contatos__quebra")
                if reais[1][1] <= pos <= reais[2][0]:
                    ja += 1
                    continue
                # fora de lugar: remove para reinserir certo
                interior = re.sub(
                    r'<li class="hero-contatos__quebra"[^>]*></li>'
                    r'(<!-- %s -->)?' % re.escape(MARK), "", interior)
                lis = divide_lis(interior)
                reais = [(a, b) for a, b in lis
                         if "hero-contatos__quebra" not in interior[a:b]]
            corte = reais[1][1]
            novo_interior = interior[:corte] + QUEBRA + interior[corte:]
            novo = h[:m.start()] + m.group(1) + novo_interior + m.group(3) + h[m.end():]
            n += 1
            if not dry:
                gravar(p, novo)

    print("quebra inserida em %d pagina(s) | ja tinham: %d%s"
          % (n, ja, " (dry-run)" if dry else ""))
    for a in avisos:
        print("  AVISO %s" % a)


if __name__ == "__main__":
    main()
