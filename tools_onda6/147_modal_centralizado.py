# -*- coding: utf-8 -*-
"""Onda 72b (mirow-marketing#253): modal de lider centralizado na viewport.

Pedido do Mario (24/08/2026, olhando o staging v=84): "o card do lider nao aparece
centralizado na tela, mas sim como se conectado a barra superior, o que nao esta
certo." O tema usa Bootstrap 5 com .modal-dialog.modal-xl SEM modal-dialog-centered
— o dialogo ancora no topo. Pre-existente; nao e regressao da onda 72.

Conserto: CSS minimo, o mesmo que a classe modal-dialog-centered do proprio
Bootstrap aplicaria, restrito aos modais de lider (id^="modal_"). Bloco marcado
no onda6.css (regra n. zero).
"""
import sys

from _onda7_css import escrever_bloco_css, resolve_public

CSS = """
div.modal[id^="modal_"] .modal-dialog {
  display: flex;
  align-items: center;
  min-height: calc(100% - 3.5rem);
}
"""


def main(raiz):
    pub = resolve_public(raiz)
    mudou = escrever_bloco_css(pub, "modal-centralizado", CSS, onda="onda72")
    print("onda72:modal-centralizado %s" % ("gravado" if mudou else "ja estava"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
