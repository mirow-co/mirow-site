# -*- coding: utf-8 -*-
"""46 — S-28 (issue #80): Elmar como Senior Expert nas paginas de pratica.

Uso:
    python tools_onda6/46_elmar_senior_expert_praticas.py <raiz-que-contem-public>

O PROBLEMA
----------
O chip do banner das paginas de pratica (37 paginas: practice/, pratica/,
branchen/ x pt/en/de) mostra "Private: Elmar Gans / Managing Partner":

  - "Private:" e artefato do WordPress — a pagina de perfil do Elmar foi
    marcada como privada no CMS original e o tema imprimia o titulo do post
    com o prefixo;
  - "Managing Partner" e o cargo antigo. A decisao do Mario (onda 6) e que o
    Elmar aparece como **Senior Expert** — e assim que a home e a pagina de
    lideres ja o mostram, nas 3 linguas ("Senior Expert" e igual em pt/en/de).

O QUE ESTE SCRIPT FAZ
---------------------
Duas substituicoes literais, nas paginas que as contiverem:

  1. chip do banner:
     <strong>Private: Elmar Gans</strong>Managing Partner
     -> <strong>Elmar Gans</strong>Senior Expert
  2. role no modal do Elmar:
     Elmar Gans</h4><h5 class="modal-leaders__role">Managing Partner
     -> Elmar Gans</h4><h5 class="modal-leaders__role">Senior Expert
  3. prefixo "Private: " no titulo de QUALQUER modal de lider
     (<h4 class="modal-leaders__title">Private: ...) — o artefato aparece
     tambem em 4 modais de ex-lideres na en/homepage (Marcelo Soares,
     Marcelo Massarente, Lucas Santiago, Fernando Fabbris). Aqui so cai o
     prefixo do CMS; a permanencia desses modais e pedido a parte (quem saiu).

Nenhum CSS muda. Idempotente: no segundo run nada contem os textos antigos.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

TROCAS = [
    ("<strong>Private: Elmar Gans</strong>Managing Partner",
     "<strong>Elmar Gans</strong>Senior Expert"),
    ('Elmar Gans</h4><h5 class="modal-leaders__role">Managing Partner',
     'Elmar Gans</h4><h5 class="modal-leaders__role">Senior Expert'),
    ('class="modal-leaders__title">Private: ',
     'class="modal-leaders__title">'),
]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = 0
    trocas_total = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            novo = h
            trocas = 0
            for velho, certo in TROCAS:
                trocas += novo.count(velho)
                novo = novo.replace(velho, certo)
            if novo != h:
                gravar(p, novo)
                alterados += 1
                trocas_total += trocas
                rel = os.path.relpath(p, pub).replace(os.sep, "/")
                print("  %s (%d troca(s))" % (rel, trocas))
    print("\nresumo: %d arquivo(s) alterado(s), %d substituicao(oes)"
          % (alterados, trocas_total))


if __name__ == "__main__":
    main()
