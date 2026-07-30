# -*- coding: utf-8 -*-
"""
05_remover_frases_home.py — remove as 3 frases de encheção da home que o Andreas listou.

Uso:  python tools_onda5/05_remover_frases_home.py <raiz-da-arvore>

Frases (chunk MMK-CONV006-C10), nas 3 linguas:
  1) "We develop unique, robust, and pragmatic solutions in a short space of time"
  2) "We bring new perspectives to key top management challenges ..."
  3) "Through the teamwork and hands-on attitude of our team, we deliver the best ..."

No espelho elas vivem em <div class="our-jobs__text"><p>...</p></div> dentro de
<div class="our-jobs__text-wrap">. O script remove os blocos das frases e, se o
container ficar vazio, remove o container tambem. O link "conheca mais sobre o nosso
trabalho" (our-jobs__more) e a secao permanecem intactos. Idempotente.
"""
import io
import os
import re
import sys

TEXT_RE = re.compile(r'[ \t]*<div class="our-jobs__text"[^>]*>\s*<p>.*?</p>\s*</div>\s*', re.S)
WRAP_RE = re.compile(r'[ \t]*<div class="our-jobs__text-wrap">\s*</div>\s*', re.S)

# marcadores para conferir que estamos removendo as frases certas (uma por lingua)
MARCADORES = [
    "short space of time", "curto espa", "kurzer Zeit", "kurzen Zeit",
    "new perspectives", "novas perspectivas", "neue Perspektiven",
    "full potential", "todo o seu potencial", "volle Potenzial",
]


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = 0
    for root, _dirs, files in os.walk(pub):
        for f in files:
            if not f.endswith(".html"):
                continue
            path = os.path.join(root, f)
            with io.open(path, encoding="utf-8") as fh:
                html = fh.read()
            if 'class="our-jobs__text-wrap"' not in html:
                continue
            trecho = html[html.index('class="our-jobs__text-wrap"'):][:4000]
            if not any(m in trecho for m in MARCADORES):
                print("pulado (frases nao encontradas): %s"
                      % os.path.relpath(path, pub).replace(os.sep, "/"))
                continue
            novo, n = TEXT_RE.subn("", html)
            novo, nw = WRAP_RE.subn("", novo)
            if novo != html:
                with io.open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(novo)
                alterados += 1
                print("%s: %d frase(s) removida(s), %d container(es) vazio(s) removido(s)"
                      % (os.path.relpath(path, pub).replace(os.sep, "/"), n, nw))
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
