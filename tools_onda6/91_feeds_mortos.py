# -*- coding: utf-8 -*-
"""91 — onda 33, S-122 (#106): remove as referencias mortas a /feed/.

Uso:
    python tools_onda6/91_feeds_mortos.py <raiz-que-contem-public> [--dry-run]

O espelho herdou do WordPress um `<link rel="alternate" type="application/rss+xml">`
por artigo, apontando para o feed de comentarios daquele artigo (`.../feed/`). Num
site estatico nao existe feed nenhum: o leitor de RSS que seguir o link recebe 404,
e o crawler gasta orcamento de rastreio em 37 URLs que nao existem.

Medido em 04/08, antes de mexer: 37 `<link>`, todos com `application/rss+xml`, e
**0 dos 37 alvos existe no disco** — nao ha feed legitimo a preservar. Fora de
`<link>` nao ha nenhuma ocorrencia de `/feed/` no site.

A issue #106 tinha 4 itens; o estado de cada um em 04/08:
  1. markup de UI do ChatGPT nas 4 paginas `de/.../digital/` — JA NAO EXISTE
     (medido: 0 paginas). Item obsoleto, resolvido por alguma onda anterior.
  2. as referencias a /feed/ — E ESTE SCRIPT.
  3. reconciliar a dual-tag GA4 (G-VK4QHHHS5X herdada x G-5VTS0MZK79 nossa) —
     FORA DESTA ONDA, de proposito. E da frente de medicao (`resp-marcell`) e esta
     bloqueado pela #100: o dominio `mirow.com.br` ainda e servido pelo WordPress,
     entao a tag herdada e a UNICA que ve trafego real. Tirar a herdada agora
     interromperia a serie historica sem ganho nenhum. Cai junto com o cutover.
  4. assercao — S122 na suite.

Idempotente: remove so o que existe; no segundo run reporta 0.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

# O <link> inteiro, com a quebra/indentacao que o WordPress deixou em volta, para
# nao sobrar linha em branco no <head>.
REX = re.compile(r'[ \t]*<link rel="alternate" type="application/rss\+xml"'
                 r'[^>]*?/feed/[^>]*?>[ \t]*\r?\n?')


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    dry = "--dry-run" in sys.argv

    n_pag, n_link, sobrou = 0, 0, []
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if not nome.endswith(".html"):
                continue
            p = os.path.join(dirpath, nome)
            h = ler(p)
            if "/feed/" not in h:
                continue
            novo, quantos = REX.subn("", h)
            if "/feed/" in novo:
                # sobra que o padrao nao pegou: melhor avisar do que apagar torto
                rel = os.path.relpath(p, pub).replace(os.sep, "/")
                sobrou.append(rel)
            if quantos:
                n_pag += 1
                n_link += quantos
                if not dry:
                    gravar(p, novo)

    print("paginas limpas: %d | <link> de feed removidos: %d%s"
          % (n_pag, n_link, " (dry-run)" if dry else ""))
    for rel in sobrou:
        print("  AVISO: ainda sobra /feed/ em %s" % rel)


if __name__ == "__main__":
    main()
