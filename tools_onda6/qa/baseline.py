# -*- coding: utf-8 -*-
u"""Fotografa o estado ATUAL das paginas-alvo, para o "antes" existir.

Uso:
    python tools_onda6/qa/baseline.py <rotulo>        # ex.: antes / depois
    python tools_onda6/qa/baseline.py comparar <a> <b>

POR QUE ESTE ARQUIVO EXISTE
---------------------------
Decisao do Mario (19/08): a reconstrucao fluida vai direto, SEM escrever antes a
familia de assercoes de comportamento. Consequencia aceita: as 25 assercoes `V`
prendem o pixel do modelo antigo e varias vao falhar de proposito, entao nao
existe numero que separe "mudei porque quis" de "quebrei sem ver".

Isto nao substitui assercao — e o P4 que o repo ja exige (contact sheet antes de
dizer PRONTO), com duas coisas a mais:

1. TEXTO RENDERIZADO. O `innerText` de cada pagina, por largura. Se o texto e
   identico antes e depois, tudo que mudou foi apresentacao. Conteudo perdido numa
   migracao de CSS e irreversivel sem ninguem notar — e o que eu nao abro mao.
2. CONTINUIDADE. As propriedades que a reconstrucao existe para consertar (corpo
   do titulo, do slogan, dos titulos de secao; largura dos cards; gap das grades)
   medidas de 320 a 2560 em passos de 64px. O modelo de hoje tem PENHASCO: salta
   de 62px para 38px na fronteira de 992. O objetivo e a curva ficar continua, e
   este arquivo e o que mostra o penhasco sumindo — em numero, nao em impressao.

Saida em `_baseline/<rotulo>/`: PNG por pagina x largura, `texto.json`,
`continuidade.json` e `resumo.txt`. A pasta e gitignored.
"""
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
sys.path.insert(0, AQUI)

from verificacoes import Navegador, ServidorLocal  # noqa: E402

PAGINAS = [("home-pt", "pt/"), ("home-en", "en/"), ("home-de", "de/"),
           ("imprensa", "pt/imprensa/")]

# larguras do contact sheet + as fronteiras onde o modelo atual tem degrau
LARGURAS_FOTO = [320, 390, 480, 768, 991, 992, 1200, 1366, 1920, 2560]

# passo fino para a curva de continuidade
PASSO = 64
FAIXA = (320, 2560)

# o que medir: rotulo -> (seletor, propriedade)
SONDAS = [
    (u"eyebrow", ".onda53-selo-ia", "fontSize"),
    (u"slogan", ".onda53-slogan h2", "fontSize"),
    (u"subtitulo-hero", ".hero-texto > p", "fontSize"),
    (u"titulo-secao", ".onda30-titulo-secao", "fontSize"),
    (u"big-number", ".hero-numeros__valor", "fontSize"),
    (u"legenda-number", ".hero-numeros__texto", "fontSize"),
    (u"card-texto-largura", ".hero-texto", "width"),
    (u"card-numeros-largura", ".hero-numeros", "width"),
    (u"abertura-titulo", ".onda29-abertura__titulo", "fontSize"),
    (u"abertura-apoio", ".onda29-abertura__apoio", "fontSize"),
    (u"imprensa-titulo", ".onda18-imprensa__titulo", "fontSize"),
    (u"imprensa-wordmark", ".onda41-imprensa__logo--texto", "fontSize"),
]

JS_SONDAR = """(function(sondas){
  var out = {};
  sondas.forEach(function(s){
    var el = document.querySelector(s[1]);
    if (!el) { out[s[0]] = null; return; }
    // ONDA 66: elemento nao renderizado NAO pode entrar na curva. O primeiro
    // baseline acusou salto de 287% no big-number entre 1152 e 1216px, e era
    // artefato: o card esta display:none abaixo de 1200px e eu media o font-size
    // do elemento OCULTO, que e o default do tema. Numero de coisa que ninguem
    // ve nao significa nada -- mesma familia do "campo vazio nao e False".
    var r0 = el.getBoundingClientRect();
    if (!el.offsetParent && getComputedStyle(el).position !== 'fixed') {
      out[s[0]] = null; return; }
    if (r0.width < 1 || r0.height < 1) { out[s[0]] = null; return; }
    var cs = getComputedStyle(el);
    var v = cs[s[2]];
    if (s[2] === 'width') v = el.getBoundingClientRect().width;
    out[s[0]] = typeof v === 'string' ? parseFloat(v) : Math.round(v * 10) / 10;
  });
  out['_vw'] = document.documentElement.clientWidth;
  out['_overflow'] = document.documentElement.scrollWidth
                   - document.documentElement.clientWidth;
  return JSON.stringify(out);
})(SONDAS_JSON)"""

JS_TEXTO = """(function(){
  var m = document.querySelector('main') || document.body;
  return (m.innerText || '').replace(/\\s+/g, ' ').trim();
})()"""


def capturar(rotulo):
    import subprocess
    destino = os.path.join(RAIZ, "_baseline", rotulo)
    if not os.path.isdir(destino):
        os.makedirs(destino)
    textos, curvas = {}, {}
    sondas_json = json.dumps([[a, b, c] for a, b, c in SONDAS])

    with ServidorLocal("public") as srv:
        for nome, rel in PAGINAS:
            url = "%s/%s" % (srv.base(), rel)

            # --- fotos: pelo shot.py, que ja resolve AOS, altura e CDP ---
            for w in LARGURAS_FOTO:
                alvo = os.path.join(destino, "%s-%dpx.png" % (nome, w))
                subprocess.run([sys.executable, os.path.join(AQUI, "shot.py"),
                                url, alvo, str(w), "aos-off", "h=1400"],
                               capture_output=True)

            # --- texto renderizado e curva de continuidade ---
            # o resize e um abrir() com largura: o Navegador nao tem redimensionar,
            # e o setDeviceMetricsOverride dele roda dentro do abrir
            with Navegador(1400, 900) as nav:
                nav.abrir(url)
                textos[nome] = nav.js(JS_TEXTO)
                serie = []
                w = FAIXA[0]
                while w <= FAIXA[1]:
                    nav.abrir(url, largura=w, altura=900)
                    d = nav.js(JS_SONDAR.replace("SONDAS_JSON", sondas_json))
                    try:
                        serie.append(json.loads(d) if isinstance(d, str) else d)
                    except Exception:
                        serie.append({"_vw": w, "_erro": True})
                    w += PASSO
                curvas[nome] = serie

    io.open(os.path.join(destino, "texto.json"), "w", encoding="utf-8").write(
        json.dumps(textos, ensure_ascii=False, indent=1))
    io.open(os.path.join(destino, "continuidade.json"), "w", encoding="utf-8").write(
        json.dumps(curvas, ensure_ascii=False, indent=1))
    resumo(rotulo, curvas, destino)
    print(u"baseline '%s' em %s" % (rotulo, destino))


def degraus(serie, chave):
    u"""Maior salto relativo entre duas larguras VIZINHAS. E a medida do penhasco."""
    pior, onde = 0.0, None
    ant = None
    for p in serie:
        v = p.get(chave)
        if v is None:
            ant = None
            continue
        if ant is not None and ant[1]:
            rel = abs(v - ant[1]) / float(ant[1])
            if rel > pior:
                pior, onde = rel, (ant[0], p.get("_vw"), ant[1], v)
        ant = (p.get("_vw"), v)
    return pior, onde


def resumo(rotulo, curvas, destino):
    L = [u"BASELINE '%s' — descontinuidade por sonda" % rotulo,
         u"(maior salto entre duas larguras vizinhas, passo de %dpx)" % PASSO, u""]
    for nome, serie in curvas.items():
        ovf = max((p.get("_overflow") or 0) for p in serie)
        L.append(u"%s   overflow-x maximo: %dpx" % (nome, ovf))
        for chave, _sel, _prop in SONDAS:
            pior, onde = degraus(serie, chave)
            if onde is None:
                L.append(u"    %-22s (nao encontrado)" % chave)
                continue
            marca = u"  <<< PENHASCO" if pior >= 0.15 else u""
            L.append(u"    %-22s salto max %5.1f%%  entre %dpx e %dpx (%.1f -> %.1f)%s"
                     % (chave, pior * 100, onde[0], onde[1], onde[2], onde[3], marca))
        L.append(u"")
    txt = u"\n".join(L)
    io.open(os.path.join(destino, "resumo.txt"), "w", encoding="utf-8").write(txt)
    print(txt)


def comparar(a, b):
    base = os.path.join(RAIZ, "_baseline")
    ta = json.load(io.open(os.path.join(base, a, "texto.json"), encoding="utf-8"))
    tb = json.load(io.open(os.path.join(base, b, "texto.json"), encoding="utf-8"))
    L = [u"TEXTO RENDERIZADO: '%s' x '%s'" % (a, b), u""]
    for nome in sorted(set(ta) | set(tb)):
        xa, xb = ta.get(nome, u""), tb.get(nome, u"")
        if xa == xb:
            L.append(u"  %-12s IDENTICO (%d chars)" % (nome, len(xa)))
        else:
            L.append(u"  %-12s DIFERENTE: %d -> %d chars ***" % (nome, len(xa), len(xb)))
            pa, pb = xa.split(u" "), xb.split(u" ")
            so_a = [w for w in pa if w not in set(pb)][:12]
            so_b = [w for w in pb if w not in set(pa)][:12]
            if so_a:
                L.append(u"      sumiu: %s" % u" ".join(so_a))
            if so_b:
                L.append(u"      surgiu: %s" % u" ".join(so_b))
    ca = json.load(io.open(os.path.join(base, a, "continuidade.json"), encoding="utf-8"))
    cb = json.load(io.open(os.path.join(base, b, "continuidade.json"), encoding="utf-8"))
    L += [u"", u"DESCONTINUIDADE: '%s' x '%s' (menor e melhor)" % (a, b), u""]
    for nome in sorted(set(ca) & set(cb)):
        L.append(u"  %s" % nome)
        for chave, _s, _p in SONDAS:
            pa, oa = degraus(ca[nome], chave)
            pb, ob = degraus(cb[nome], chave)
            if oa is None and ob is None:
                continue
            seta = u"melhorou" if pb < pa - 0.01 else (
                u"piorou ***" if pb > pa + 0.01 else u"igual")
            L.append(u"    %-22s %5.1f%% -> %5.1f%%   %s"
                     % (chave, pa * 100, pb * 100, seta))
        L.append(u"")
    txt = u"\n".join(L)
    io.open(os.path.join(base, "comparacao-%s-%s.txt" % (a, b)), "w",
            encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "comparar":
        comparar(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 2:
        capturar(sys.argv[1])
    else:
        raise SystemExit(__doc__)
