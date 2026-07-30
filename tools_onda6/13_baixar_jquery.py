# -*- coding: utf-8 -*-
"""
13_baixar_jquery.py — repoe o jQuery que faltava no espelho (os modais dependem dele).

Uso:  python tools_onda6/13_baixar_jquery.py <raiz-da-arvore>

- O espelho referencia wp-includes/js/jquery/jquery.min.js?ver=3.7.1 (WP 6.9), mas o
  arquivo nao foi capturado — dava 404 e, sem jQuery, o bootstrap do tema nao abria os
  modais de bio dos lideres. O jquery-migrate 3.4.1 ja estava no espelho.
- Baixa a versao 3.7.1 oficial e confere o hash SRI publicado pelo projeto jQuery
  antes de gravar. Se o hash nao casar, nao grava nada.
- Idempotente: se o arquivo local ja tem o hash certo, nao baixa de novo.
"""
import base64
import hashlib
import io
import os
import sys
import urllib.request

DESTINO_REL = "wp-includes/js/jquery/jquery.min.js"
URL = "https://code.jquery.com/jquery-3.7.1.min.js"
SRI = "sha256-/JqT3SQfawRcv/BIHPThkBvs0OEvtFFmqPF/lYI/Cxo="


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def sri(dados):
    return "sha256-" + base64.b64encode(hashlib.sha256(dados).digest()).decode()


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    destino = os.path.join(pub, DESTINO_REL.replace("/", os.sep))

    if os.path.exists(destino):
        with open(destino, "rb") as f:
            atual = f.read()
        if sri(atual) == SRI:
            print("jquery ja no lugar e conferido: %s (%d bytes)"
                  % (DESTINO_REL, len(atual)))
            return
        print("jquery local com hash diferente do esperado — vai rebaixar")

    print("baixando %s" % URL)
    dados = urllib.request.urlopen(URL, timeout=60).read()
    achado = sri(dados)
    if achado != SRI:
        raise SystemExit("hash nao confere!\n  esperado: %s\n  obtido:   %s" % (SRI, achado))
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "wb") as f:
        f.write(dados)
    print("jquery escrito: %s (%d bytes, %s)" % (DESTINO_REL, len(dados), achado))


if __name__ == "__main__":
    main()
