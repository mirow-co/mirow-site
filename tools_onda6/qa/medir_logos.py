# -*- coding: utf-8 -*-
"""Mede se cada logo de instituicao aparece INTEIRO dentro do chip.

    python tools_onda6/qa/medir_logos.py

Nao mede "o logo esta la" (a V42 ja faz isso e passou verde com todos cortados).
Mede, no navegador, para cada logo:

  - a razao de aspecto RENDERIZADA contra a razao NATURAL (viewBox do svg ou
    naturalWidth/Height do img). Se as duas divergem, o desenho esta distorcido
    ou recortado;
  - o quanto da caixa disponivel ele usa. Logo que renderiza a 11px de altura
    numa faixa de 20px foi espremido pelo teto de largura.

O caso que originou: svg inline SEM viewBox nao escala, e `height:16px` recorta.
"""
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from verificacoes import Navegador, ServidorLocal  # noqa: E402

JS = """
(function(){
  var out = [];
  document.querySelectorAll('.onda78-inst__logo').forEach(function(e){
    var r = e.getBoundingClientRect();
    // o nome vem do <span> do chip -- textContent do <li> inteiro traz junto o
    // <style>/<metadata> que veio dentro do svg injetado, e vira lixo na tabela
    var sp = e.closest('li') ? e.closest('li').querySelector('span') : null;
    var nome = sp ? sp.textContent.trim() : '?';
    var cs = getComputedStyle(e);
    var nat = 0;
    if (e.tagName === 'IMG') {
      if (e.naturalWidth && e.naturalHeight) nat = e.naturalWidth / e.naturalHeight;
    } else {
      var vb = e.getAttribute('viewBox');
      if (vb) { var p = vb.split(/[ ,]+/); if (+p[3]) nat = (+p[2]) / (+p[3]); }
    }
    out.push([nome, e.tagName, Math.round(r.width*10)/10, Math.round(r.height*10)/10,
              Math.round(nat*1000)/1000,
              parseFloat(cs.paddingLeft) || 0, parseFloat(cs.paddingTop) || 0]);
  });
  return JSON.stringify(out);
})()
"""


def main():
    import json
    with ServidorLocal("public") as srv, Navegador() as nav:
        nav.abrir(srv.base() + "/pt/sobre-nos/lideres/", largura=1440, altura=900)
        dados = json.loads(nav.js(JS))
    # A caixa NAO e a medida do desenho. Com object-fit:contain (img) e com
    # preserveAspectRatio "meet" (svg), o desenho e inscrito na caixa e sobra
    # letterbox -- comparar aspecto da caixa com aspecto natural acusa "cortado"
    # onde ha so margem. O numero que decide legibilidade e a ALTURA DE TINTA:
    #     tinta = min(altura util, largura util / razao natural)
    # Uma wordmark 11:1 numa faixa util de 122px rende 11px de tinta, ainda que a
    # caixa diga 20px de altura -- e 11px de altura para um logotipo com letra e
    # o que o Mario chamou de "nao da para ler".
    print(u"%-26s %-4s %7s %8s %7s  %s" %
          ("chip", "tag", "caixa", "natural", "tinta", "veredito"))
    ruins = 0
    for nome, tag, w, h, nat, pl, pt in dados:
        util_w, util_h = max(w - 2 * pl, 0), max(h - 2 * pt, 0)
        tinta = min(util_h, util_w / nat) if nat else 0
        if not nat:
            v = "sem medida natural"
            ruins += 1
        elif tinta < 12:
            v = "PEQUENO DEMAIS (%.1fpx de tinta)" % tinta
            ruins += 1
        else:
            v = "ok"
        print(u"%-26s %-4s %3.0fx%-3.0f %8.2f %7.1f  %s"
              % (nome[:26], tag, w, h, nat, tinta, v))
    print(u"\n%d logo(s) medido(s), %d com problema" % (len(dados), ruins))
    return ruins


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
