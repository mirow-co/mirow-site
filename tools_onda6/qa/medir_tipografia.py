# -*- coding: utf-8 -*-
"""Mede o font-size COMPUTADO de um conjunto de seletores em varias larguras.

    python tools_onda6/qa/medir_tipografia.py [--json saida.json]

E o instrumento da reconstrucao fluida: antes de trocar `font-size:15px` +
media query por `clamp()`, precisa existir o retrato de como o navegador
desenha hoje. Depois da troca, roda de novo e compara -- o criterio nao e
"o CSS mudou", e "o tamanho nas pontas continua igual e o meio deixou de
pular".

Le o efeito (getComputedStyle), nunca a declaracao (P2.1).
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from verificacoes import Navegador, ServidorLocal  # noqa: E402

LARGURAS = [390, 768, 992, 1200, 1440, 1920]

# pagina -> seletores que interessam naquela pagina
ALVOS = {
    "pt/imprensa/": [
        ".onda18-imprensa__veiculo",
        ".onda18-imprensa__data",
        ".onda18-imprensa__titulo",
    ],
    "pt/sobre-nos/nossa-rede/": [
        ".rede__titulo",
        ".rede__eyebrow",
        ".rede-lista__nome",
        ".rede-lista__local",
        ".rede-mapa__legenda",
    ],
    "pt/": [
        ".rodape-menu a",
        ".menu__languages-list li a",
        ".rodape-legal .footer__contacts-link",
    ],
}

JS = """
(function(sels){
  var out = {};
  sels.forEach(function(s){
    var el = document.querySelector(s);
    out[s] = el ? parseFloat(getComputedStyle(el).fontSize) : null;
  });
  return JSON.stringify(out);
})(%s)
"""


def main():
    saida = None
    for i, a in enumerate(sys.argv):
        if a == "--json" and i + 1 < len(sys.argv):
            saida = sys.argv[i + 1]

    medidas = {}
    with ServidorLocal("public") as srv, Navegador() as nav:
        for pagina, sels in ALVOS.items():
            medidas[pagina] = {}
            for larg in LARGURAS:
                nav.abrir("%s/%s" % (srv.base(), pagina), largura=larg, altura=900)
                bruto = nav.js(JS % json.dumps(sels))
                vals = json.loads(bruto) if isinstance(bruto, str) else bruto
                medidas[pagina][larg] = vals

    for pagina, porlarg in medidas.items():
        print(u"\n== %s" % pagina)
        sels = ALVOS[pagina]
        print(u"%-42s %s" % ("seletor", " ".join("%7d" % l for l in LARGURAS)))
        for s in sels:
            linha = []
            for l in LARGURAS:
                v = porlarg[l].get(s)
                linha.append("%7s" % ("-" if v is None else ("%.1f" % v)))
            print(u"%-42s %s" % (s, " ".join(linha)))
    if saida:
        io.open(saida, "w", encoding="utf-8", newline="").write(
            json.dumps(medidas, indent=1, ensure_ascii=False))
        print(u"\ngravado: %s" % saida)


if __name__ == "__main__":
    main()
