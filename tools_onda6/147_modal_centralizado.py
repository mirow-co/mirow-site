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
  align-items: safe center;
  min-height: calc(100% - 3.5rem);
}
div.modal[id^="modal_"] .modal-content {
  max-height: calc(100vh - 3.5rem);
  overflow-y: auto;
}
/* O modal vive DENTRO de <main>, que tem position:relative; z-index:1 — o
   stacking context inteiro fica atras do header fixo (z=90): o topo do modal
   sumia por baixo da barra, e era isso o "conectado a barra" do Mario. Com o
   modal aberto (classe do proprio Bootstrap no body), o main sobe acima do
   header e o backdrop volta ao z padrao (o tema o manda para -1, apagando o
   escurecimento). */
body.modal-open main {
  z-index: 2000;
}
body.modal-open .modal-backdrop.show {
  z-index: 1050;
}
/* v3 (Mario, 24/08: "nao quero que seja essa janela fora de tamanho com X
   dentro - pode ser bem melhor"). Medido antes de mexer: o corpo tinha 20px de
   overflow horizontal (scrollbar no pe do modal), o X era um quadrado de 48px
   VAZANDO 19px para fora da borda direita, e canto reto. */
div.modal[id^="modal_"] .modal-dialog {
  max-width: min(1140px, calc(100vw - 3rem));
}
div.modal[id^="modal_"] .modal-content {
  border-radius: 14px;
  overflow-x: hidden;
  box-shadow: 0 24px 64px rgba(2, 14, 102, 0.45);
  border: 0;
}
div.modal[id^="modal_"] .modal-body {
  overflow-x: hidden;
}
div.modal[id^="modal_"] .btn-close {
  position: absolute;
  top: 14px;
  right: 14px;
  left: auto;
  width: 38px;
  height: 38px;
  padding: 0;
  margin: 0;
  border-radius: 50%;
  background-color: #020E66;
  background-size: 14px;
  filter: none;
  opacity: 1;
  z-index: 10;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='%23fff'%3e%3cpath d='M.293.293a1 1 0 0 1 1.414 0L8 6.586 14.293.293a1 1 0 1 1 1.414 1.414L9.414 8l6.293 6.293a1 1 0 0 1-1.414 1.414L8 9.414l-6.293 6.293a1 1 0 0 1-1.414-1.414L6.586 8 .293 1.707a1 1 0 0 1 0-1.414z'/%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: center;
}
div.modal[id^="modal_"] .btn-close:hover {
  background-color: #00ADEC;
}
/* O tema poe um quadrado branco 40x25 no canto do painel navy
   (.modal-leaders__intro::before) — dentro do modal ele le como defeito. */
div.modal[id^="modal_"] .modal-leaders__intro::before {
  display: none;
}
div.modal[id^="modal_"] .modal-leaders__intro {
  border-radius: 10px;
}
"""

# v2 (mesma sessao, 24/08): o Mario mandou o modal do Raoni ainda "quebrado" no
# staging. Causa: o modal dele e mais ALTO que a viewport, e flex align-items:center
# com conteudo maior que o conteiner corta o TOPO (nao da nem para rolar ate ele).
# Conserto: `safe center` (nunca corta) + o conteudo passa a caber na tela e rolar
# POR DENTRO (max-height no .modal-content), como o modal-dialog-scrollable do
# proprio Bootstrap. Modal baixo continua centralizado; modal alto vira painel de
# altura cheia com scroll interno.


def main(raiz):
    pub = resolve_public(raiz)
    mudou = escrever_bloco_css(pub, "modal-centralizado", CSS, onda="onda72")
    print("onda72:modal-centralizado %s" % ("gravado" if mudou else "ja estava"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
