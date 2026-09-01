# -*- coding: utf-8 -*-
"""Mede a cor COMPUTADA dos icones da pagina de lideres.

    python tools_onda6/qa/medir_cor_icones.py

Existe por causa do vermelho da onda 79: um <style> dentro de um SVG de logo,
promovido a folha global pela injecao inline do tema, pintou de #ab1727 todo
<path> da pagina -- marca, LinkedIn, e-mail, WhatsApp.

Mede duas coisas, e a segunda e a que quase ninguem escreve:
  1. nenhum <path> FORA dos chips de instituicao esta com o vermelho da Carnegie
     Mellon (nem com qualquer cor que so exista dentro de um logo nosso);
  2. os logos que TINHAM <style> continuam coloridos -- porque a conversao para
     atributo poderia ter apagado a cor em vez de contela, e um logo preto no
     lugar de um azul passaria despercebido numa verificacao que so olha o 1.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from verificacoes import Navegador, ServidorLocal  # noqa: E402

# cores que so podem existir DENTRO de um logo de instituicao
INTRUSAS = {"rgb(171, 23, 39)": "vermelho Carnegie Mellon",
            "rgb(217, 60, 100)": "rosa IMP",
            "rgb(0, 20, 220)": "azul Schlumberger"}

JS_FORA = """
(function(){
  var m = {};
  document.querySelectorAll('path, circle, rect, polygon').forEach(function(e){
    if (e.closest('.onda78-inst')) return;
    var f = getComputedStyle(e).fill;
    m[f] = (m[f]||0) + 1;
  });
  return JSON.stringify(m);
})()
"""

JS_DENTRO = """
(function(){
  var out = [];
  ['carnegie-mellon-tepper','imp','puc-rio','schlumberger'].forEach(function(slug){
    var el = document.querySelector('[src*="'+slug+'"], .onda78-inst__logo');
    var alvo = null;
    document.querySelectorAll('.onda78-inst__logo').forEach(function(e){
      var s = e.getAttribute('src') || e.getAttribute('data-src') || '';
      if (s.indexOf(slug) >= 0) alvo = e;
      if (!alvo && e.tagName !== 'IMG') {
        var t = e.closest('li'); var sp = t ? t.querySelector('span') : null;
      }
    });
    // svg injetado perde o src: usa o <span> do chip para achar
    if (!alvo) {
      var nomes = {'carnegie-mellon-tepper':'Carnegie','imp':'IMP','puc-rio':'PUC',
                   'schlumberger':'Schlumberger'};
      document.querySelectorAll('.onda78-inst__item').forEach(function(li){
        var sp = li.querySelector('span');
        if (sp && sp.textContent.indexOf(nomes[slug]) >= 0)
          alvo = li.querySelector('.onda78-inst__logo');
      });
    }
    if (!alvo) { out.push([slug, 'NAO ENCONTRADO', 0]); return; }
    var cores = {};
    alvo.querySelectorAll('path, circle, rect, polygon').forEach(function(e){
      var f = getComputedStyle(e).fill;
      cores[f] = (cores[f]||0) + 1;
    });
    if (alvo.tagName === 'IMG') { out.push([slug, 'img (isolado)', 1]); return; }
    out.push([slug, JSON.stringify(cores), Object.keys(cores).length]);
  });
  return JSON.stringify(out);
})()
"""


def main():
    with ServidorLocal("public") as srv, Navegador() as nav:
        nav.abrir(srv.base() + "/pt/sobre-nos/lideres/", largura=1440, altura=900)
        fora = json.loads(nav.js(JS_FORA))
        dentro = json.loads(nav.js(JS_DENTRO))

    ruim = 0
    print(u"--- cores fora dos chips (marca, menu, rodape, redes) ---")
    for cor, n in sorted(fora.items(), key=lambda kv: -kv[1]):
        marca = ""
        if cor in INTRUSAS:
            marca = "  <<< INTRUSA: %s" % INTRUSAS[cor]
            ruim += 1
        print(u"  %-28s %4d elemento(s)%s" % (cor, n, marca))

    print(u"\n--- os 4 logos que tinham <style> continuam coloridos? ---")
    for slug, cores, n in dentro:
        vazio = (n == 0)
        print(u"  %-24s %s%s" % (slug, cores, "   <<< SEM COR" if vazio else ""))
        if vazio:
            ruim += 1
    print(u"\n%s" % (u"OK" if not ruim else u"%d PROBLEMA(S)" % ruim))
    return ruim


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
