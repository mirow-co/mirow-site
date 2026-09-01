# -*- coding: utf-8 -*-
"""Fotografa a cor computada de todo SVG injetado, para comparar antes x depois.

    python tools_onda6/qa/cores_dos_logos.py antes.json
    ... mexe nos arquivos ...
    python tools_onda6/qa/cores_dos_logos.py depois.json antes.json

Existe porque converter `<style>` em atributo de apresentacao e uma operacao que
PODE apagar a cor de um logo sem que nada mais reclame -- e um logo preto no
lugar de um azul nao quebra teste nenhum, so fica errado no ar. Entao a prova nao
e "o script rodou": e a lista de cores da pagina ser a MESMA antes e depois.

Varre as paginas onde ha SVG nosso injetado: home (barra de clientes), imprensa
(logos de veiculo), nossa rede (logos de parceiro) e lideres (logos de
instituicao).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from verificacoes import Navegador, ServidorLocal  # noqa: E402

PAGINAS = ["/pt/", "/pt/imprensa/", "/pt/nossa-rede/", "/pt/sobre-nos/lideres/"]

JS = """
(function(){
  var m = {};
  document.querySelectorAll('svg path, svg circle, svg rect, svg polygon, svg ellipse')
    .forEach(function(e){
      var f = getComputedStyle(e).fill;
      m[f] = (m[f]||0) + 1;
    });
  return JSON.stringify(m);
})()
"""


def coletar():
    dados = {}
    with ServidorLocal("public") as srv, Navegador() as nav:
        for pag in PAGINAS:
            nav.abrir(srv.base() + pag, largura=1440, altura=900)
            dados[pag] = json.loads(nav.js(JS))
    return dados


def comparar(depois, antes):
    ruim = 0
    for pag in PAGINAS:
        a, d = antes.get(pag, {}), depois.get(pag, {})
        for cor in sorted(set(a) | set(d)):
            na, nd = a.get(cor, 0), d.get(cor, 0)
            if na != nd:
                print(u"  %-22s %-28s antes %3d  depois %3d" % (pag, cor, na, nd))
                ruim += 1
        if not (set(a) | set(d)):
            print(u"  %-22s (nenhum svg medido)" % pag)
    print(u"\n%s" % (u"IDENTICO: nenhuma cor mudou em nenhuma pagina"
                     if not ruim else u"%d diferenca(s) de cor" % ruim))
    return ruim


def main():
    saida = sys.argv[1] if len(sys.argv) > 1 else "cores.json"
    dados = coletar()
    with open(saida, "w") as f:
        json.dump(dados, f, indent=1, sort_keys=True)
    print(u"gravado %s" % saida)
    if len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            return comparar(dados, json.load(f))
    for pag in PAGINAS:
        print(u"  %-22s %d cor(es), %d elemento(s)"
              % (pag, len(dados[pag]), sum(dados[pag].values())))
    return 0


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
