# -*- coding: utf-8 -*-
"""Audita o que o navegador REALMENTE aplica de font-size no CSS nosso.

    python tools_onda6/qa/auditar_tipografia.py [--paginas pt/,pt/imprensa/,...]

Por que existe
--------------
O `onda6.css` tem 91 declaracoes de `font-size` em px. Algumas nao valem NADA: uma
onda posterior redeclarou o mesmo seletor e ganhou por ordem de cascata. A primeira
medicao da reconstrucao fluida achou o caso exemplar -- `.onda18-imprensa__veiculo`
declara 15px e 14px numa media query, e o navegador desenha 13px em TODA largura,
porque um bloco de 600 linhas abaixo redeclara 13px sem variante responsiva.

Migrar para `clamp()` uma regra que ja esta morta seria trabalho perdido; pior,
daria a impressao de que o site ficou fluido onde ele nao ficou. Entao a ordem e:
medir o que vale, e so depois mexer.

Saida: para cada seletor do nosso CSS, o que esta DECLARADO e o que o navegador
COMPUTA em 390px e em 1920px, com veredito:
  MORTA      -> nenhum valor declarado por nos bate com o computado
  FIXA       -> vale, e nao muda com a largura (candidata a clamp)
  RESPONSIVA -> vale, e ja muda com a largura (via media query)
  AUSENTE    -> o seletor nao existe em nenhuma pagina medida
"""
import io
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", ".."))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "tools"))
from verificacoes import Navegador, ServidorLocal  # noqa: E402

CSS = "public/wp-content/uploads/2026/07/onda6/onda6.css"
PADRAO = ["pt/", "pt/imprensa/", "pt/sobre-nos/nossa-rede/", "pt/sobre-nos/lideres/",
          "pt/lider/felipe-diniz/", "pt/pratica/estrategia/"]


def declaracoes(css_texto):
    """(seletor -> {valor_px: em_media_query}) para o nosso CSS."""
    fora = {}
    # blocos @media: guarda o corpo para saber se a regra esta dentro de um
    profundidade, i, dentro = 0, 0, []
    for m in re.finditer(r'@media[^{]*\{', css_texto):
        ini = m.end() - 1
        nivel, j = 0, ini
        while j < len(css_texto):
            if css_texto[j] == '{':
                nivel += 1
            elif css_texto[j] == '}':
                nivel -= 1
                if nivel == 0:
                    break
            j += 1
        dentro.append((m.start(), j))
    def em_media(pos):
        return any(a <= pos <= b for a, b in dentro)

    for m in re.finditer(r'([^{}@/][^{}]*)\{([^{}]*)\}', css_texto):
        corpo = m.group(2)
        fs = re.search(r'font-size:\s*([\d.]+)px', corpo)
        if not fs:
            continue
        for sel in m.group(1).split(","):
            sel = " ".join(sel.split())
            if not sel or sel.startswith("@"):
                continue
            fora.setdefault(sel, {})[float(fs.group(1))] = em_media(m.start())
    return fora


JS = """
(function(sels){
  var out={};
  sels.forEach(function(s){
    var el=null;
    try { el=document.querySelector(s); } catch(e) { el=null; }
    out[s]= el ? parseFloat(getComputedStyle(el).fontSize) : null;
  });
  return JSON.stringify(out);
})(%s)
"""


def main():
    paginas = PADRAO
    for i, a in enumerate(sys.argv):
        if a.startswith("--paginas="):
            paginas = [p for p in a.split("=", 1)[1].split(",") if p]

    css = io.open(CSS, encoding="utf-8").read()
    decl = declaracoes(css)
    sels = sorted(decl)
    print(u"seletores com font-size no nosso CSS: %d" % len(sels))

    computado = {}   # seletor -> {largura: valor}
    with ServidorLocal("public") as srv, Navegador() as nav:
        for larg in (390, 1920):
            for pagina in paginas:
                nav.abrir("%s/%s" % (srv.base(), pagina), largura=larg, altura=900)
                bruto = nav.js(JS % json.dumps(sels))
                vals = json.loads(bruto) if isinstance(bruto, str) else bruto
                for s, v in vals.items():
                    if v is not None:
                        computado.setdefault(s, {}).setdefault(larg, v)

    linhas = {"MORTA": [], "FIXA": [], "RESPONSIVA": [], "AUSENTE": []}
    for s in sels:
        d = decl[s]
        c = computado.get(s, {})
        if not c:
            linhas["AUSENTE"].append((s, sorted(d), None, None))
            continue
        p, g = c.get(390), c.get(1920)
        declarados = set(d)
        if p is not None and g is not None and abs(p - g) > 0.5:
            veredito = "RESPONSIVA"
        elif (p or g) in declarados or (g or p) in declarados:
            veredito = "FIXA"
        else:
            veredito = "MORTA"
        linhas[veredito].append((s, sorted(d), p, g))

    for chave in ("MORTA", "FIXA", "RESPONSIVA", "AUSENTE"):
        print(u"\n== %s (%d)" % (chave, len(linhas[chave])))
        for s, d, p, g in linhas[chave][:40]:
            print(u"   %-52s declarado %-18s 390:%-6s 1920:%-6s"
                  % (s[:52], ",".join("%g" % x for x in d),
                     "-" if p is None else "%g" % p,
                     "-" if g is None else "%g" % g))
    return 0


if __name__ == "__main__":
    sys.exit(main())
