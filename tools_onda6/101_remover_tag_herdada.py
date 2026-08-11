# -*- coding: utf-8 -*-
"""101 — onda 50, S-145 (#207): remover a tag GA4 herdada (G-VK4QHHHS5X).

Uso:
    python tools_onda6/101_remover_tag_herdada.py <raiz-que-contem-public> [--dry-run]

Decisao do Mario (11/08): desde a virada de DNS a propriedade institucional
G-5VTS0MZK79 recebe o trafego real (#100); a herdada G-VK4QHHHS5X — dono nunca
confirmado, acesso nunca obtido (#3) — sai do site.

O QUE MUDA
    1. O loader `gtag/js?id=G-VK4QHHHS5X` das paginas passa a carregar
       `id=G-5VTS0MZK79` (um loader basta; a config vem do onda31-medicao.js).
    2. `onda31-medicao.js` configura SO a institucional (IDS com 1 elemento) e o
       comentario de cabecalho deixa de descrever a dual-tag.

    Os geradores que embutem o loader (62/88/97) sao atualizados no mesmo commit
    para nao reintroduzir a herdada em rerun (regra "rerun de script de onda
    desfaz posteriores"); a assercao S145 cobre o efeito de qualquer jeito:
    0 ocorrencia de G-VK4QHHHS5X em public/.

Idempotente: segundo run reporta 0 mudanca.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import ler, resolve_public  # noqa: E402

HERDADA = "G-VK4QHHHS5X"
NOSSA = "G-5VTS0MZK79"

MEDICAO_REL = "wp-content/uploads/2026/07/onda6/onda31-medicao.js"

CABECALHO_ANTIGO = (
    " * Duas propriedades durante a transicao:\n"
    " *   G-VK4QHHHS5X — herdada do WordPress (veio no espelho do mirow.com.br). Dono\n"
    " *                  ainda nao confirmado. Mantida para nao interromper a serie.\n"
    " *   G-5VTS0MZK79 — propriedade institucional Mirow, criada em 2026-08-03.\n")
CABECALHO_NOVO = (
    " * Uma propriedade so (onda 50, #207): a institucional G-5VTS0MZK79, criada em\n"
    " * 2026-08-03. A tag herdada do WordPress (dono nunca confirmado) saiu por\n"
    " * decisao do Mario em 11/08 — desde a virada de DNS a institucional mede o\n"
    " * trafego real. A assercao M06 garante 0 referencia a herdada em public/.\n")


def gravar(path, conteudo):
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(conteudo)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    dry = "--dry-run" in sys.argv

    # ---- 1. loader nos HTMLs
    trocados = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if not nome.endswith(".html"):
                continue
            p = os.path.join(dirpath, nome)
            h = ler(p)
            if HERDADA not in h:
                continue
            novo = h.replace("gtag/js?id=%s" % HERDADA, "gtag/js?id=%s" % NOSSA)
            if HERDADA in novo:
                rel = os.path.relpath(p, pub).replace(os.sep, "/")
                print("  AVISO: %s referencia a herdada fora do loader" % rel)
            if novo != h:
                if not dry:
                    gravar(p, novo)
                trocados += 1
    print("loader: %d pagina(s) trocada(s) para %s%s"
          % (trocados, NOSSA, " (dry-run)" if dry else ""))

    # ---- 2. onda31-medicao.js
    p_js = os.path.join(pub, MEDICAO_REL.replace("/", os.sep))
    js = ler(p_js)
    novo = js.replace("var IDS = ['%s', '%s'];" % (HERDADA, NOSSA),
                      "var IDS = ['%s'];" % NOSSA)
    novo = novo.replace(CABECALHO_ANTIGO, CABECALHO_NOVO)
    if HERDADA in novo:
        print("  AVISO: a herdada ainda aparece no onda31-medicao.js")
    if novo != js:
        if not dry:
            gravar(p_js, novo)
        print("onda31-medicao.js: atualizado%s" % (" (dry-run)" if dry else ""))
    else:
        print("onda31-medicao.js: sem mudanca")


if __name__ == "__main__":
    main()
