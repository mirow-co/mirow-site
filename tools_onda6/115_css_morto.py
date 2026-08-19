# -*- coding: utf-8 -*-
"""Onda 60 (PageSpeed 18/08): tira do HTML as folhas de estilo que a pagina nao usa.

O PageSpeed acusa "Reduce unused CSS — 280 KiB" e "Render-blocking requests".
Duas folhas herdadas de plugin do WordPress sao carregadas em TODAS as 109 paginas
e bloqueiam o desenho:

  dashicons.min.css      36 KiB, 1.720 ms de bloqueio  -> 100% sem uso, em pagina NENHUMA
                                                          (nenhuma classe dashicons-* existe)
  formidableforms.css    23 KiB, 1.250 ms de bloqueio  -> so as paginas com formulario usam

Isto e mudanca de CONTEUDO (remover uma tag <link>), nao de tema. O arquivo continua
no disco; so deixa de ser pedido por quem nao usa.

REGRA: a remocao e por MEDICAO, nao por lista fixa. Para cada folha, o script confere
se alguma classe dela aparece no HTML daquela pagina; se aparecer, mantem. Assim uma
pagina futura que passe a usar o plugin nao perde o estilo em silencio.

Idempotente: 2o run reporta 0 mudancas.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public

# id do <link> -> marcador que prova uso real da folha naquela pagina
FOLHAS = {
    "dashicons-css": ("dashicons-",),
    "formidable-css": ("frm_forms", "frm_form_field", "frm-show-form"),
    # Onda 62d: o PageSpeed de 18/08 nomeia addtoany.min.css como o PIOR bloqueador
    # isolado do render — 36 KB, 283 ms. Medido: 109 paginas carregam, so 55 usam o
    # botao de compartilhar, e as 3 homes estao entre as que NAO usam. Mesmo criterio
    # das outras duas: quem usa continua carregando.
    "addtoany-css": ("a2a_kit", "addtoany_shortcode", "a2a_button"),
}

RE_LINK = re.compile(r"<link[^>]*id='([a-z0-9-]+)'[^>]*/?>\s*")


def ler(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def gravar(p, s):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def main(raiz):
    pub = resolve_public(raiz)
    removidos = {k: 0 for k in FOLHAS}
    mantidos = {k: 0 for k in FOLHAS}
    tocados = 0
    for dp, _d, fs in os.walk(pub):
        if os.sep + ".git" in dp:
            continue
        for nome in fs:
            if not nome.endswith(".html"):
                continue
            fp = os.path.join(dp, nome)
            h = ler(fp)
            orig = h
            for css_id, provas in FOLHAS.items():
                m = re.search(r"<link[^>]*id='%s'[^>]*/?>\s*" % re.escape(css_id), h)
                if not m:
                    continue
                # o HTML sem a propria tag, para a prova de uso nao casar com o href
                sem_tag = h[:m.start()] + h[m.end():]
                if any(p in sem_tag for p in provas):
                    mantidos[css_id] += 1
                    continue
                h = sem_tag
                removidos[css_id] += 1
            if h != orig:
                gravar(fp, h)
                tocados += 1
    for css_id in FOLHAS:
        print("%-18s removido de %3d pagina(s), mantido em %3d"
              % (css_id, removidos[css_id], mantidos[css_id]))
    print("arquivos alterados: %d" % tocados)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
