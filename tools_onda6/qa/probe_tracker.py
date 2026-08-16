# -*- coding: utf-8 -*-
"""probe_tracker.py — o que um tracker de terceiro REALMENTE envia daqui.

    python tools_onda6/qa/probe_tracker.py <host-do-fornecedor> [pagina]

    python tools_onda6/qa/probe_tracker.py sc.lfeeder.com pt/contato/

Por que existe (14/08/2026, mirow-marketing#222)
------------------------------------------------
Ia-se publicar o Data Reveal (Data Stone) em 112 paginas. A leitura do codigo dele
nao bastou — vinha ofuscado — e a captura so da REDE deu **falso negativo**, porque
os corpos vao cifrados (envelope RSA+AES) e como Blob nos beacons. Campo ilegivel
nao e "nao vazou" (R13, regra 2).

So instrumentando o momento ANTES da cifragem a resposta apareceu: o tracker enviava
o conteudo inteiro do formulario de contato — nome, e-mail, telefone e a mensagem —
SEM o visitante ter clicado em enviar. O produto foi reprovado por causa desta
medicao.

Regra que ficou: **nenhum tracker de terceiro vai ao ar sem passar por aqui.**
Declaracao de fornecedor nao e evidencia — e a mesma logica do P2.1 aplicada a
codigo que nao e nosso.

Como funciona
-------------
Instala, ANTES de qualquer script da pagina (Page.addScriptToEvaluateOnNewDocument):
  1. fetch / XMLHttpRequest / sendBeacon  -> o que sai, e para onde
  2. TextEncoder.encode                   -> todo texto que vira bytes
  3. crypto.subtle.encrypt                -> o texto claro no ato de cifrar
  4. Blob                                 -> corpo dos beacons

Depois digita valores-isca no formulario, dispara o abandono (sem submeter) e
procura as iscas em TUDO que foi capturado. Isca que aparece = vazou.

Saida: relatorio no terminal e captura bruta em _qa_probe/ (gitignored).
"""
from __future__ import unicode_literals

import io
import json
import base64
import os
import sys
import time
import urllib.parse

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
sys.path.insert(0, os.path.join(RAIZ, "tools_onda6", "qa"))

from verificacoes import Navegador, ServidorLocal  # noqa: E402

HOOK = r"""
window.__cap = [];
window.__claro = [];
(function () {
  function reg(via, url, body) {
    try { window.__cap.push({via: via, url: String(url),
                             body: body ? String(body).slice(0, 4000) : null}); } catch (e) {}
  }
  var of = window.fetch;
  window.fetch = function (u, o) {
    reg('fetch', (u && u.url) || u, o && o.body); return of.apply(this, arguments);
  };
  var oo = XMLHttpRequest.prototype.open, os_ = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (m, u) { this.__u = u; return oo.apply(this, arguments); };
  XMLHttpRequest.prototype.send = function (b) { reg('xhr', this.__u, b); return os_.apply(this, arguments); };
  if (navigator.sendBeacon) {
    var ob = navigator.sendBeacon.bind(navigator);
    navigator.sendBeacon = function (u, d) { reg('beacon', u, d); return ob(u, d); };
  }
  /* O que importa: o texto CLARO, antes de virar ciphertext. */
  var oe = TextEncoder.prototype.encode;
  TextEncoder.prototype.encode = function (t) {
    try { if (t && String(t).length > 2) window.__claro.push(String(t).slice(0, 6000)); } catch (e) {}
    return oe.apply(this, arguments);
  };
  if (window.crypto && crypto.subtle && crypto.subtle.encrypt) {
    var oc = crypto.subtle.encrypt.bind(crypto.subtle);
    crypto.subtle.encrypt = function (a, k, d) {
      try { window.__claro.push('[ENCRYPT] ' + new TextDecoder().decode(d).slice(0, 6000)); } catch (e) {}
      return oc(a, k, d);
    };
  }
  var OB = window.Blob;
  window.Blob = function (parts, opts) {
    try { (parts || []).forEach(function (x) {
      if (typeof x === 'string' && x.length > 2) window.__claro.push('[BLOB] ' + x.slice(0, 6000));
    }); } catch (e) {}
    return new OB(parts, opts);
  };
  window.Blob.prototype = OB.prototype;
})();
"""

# Iscas: strings improvaveis de aparecer por acaso. Se sairem da maquina, vazaram.
ISCAS = {
    "item_meta[1]": u"Isca Nome Probe",
    "item_meta[3]": u"isca-probe-nao-enviada@exemplo-mirow.com.br",
    "item_meta[6]": u"11987654321",
    "item_meta[5]": u"Texto que o probe digitou e NAO enviou.",
}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    host = args[0]
    pagina = args[1] if len(args) > 1 else "pt/contato/"

    with ServidorLocal(os.path.join(RAIZ, "public")) as srv, Navegador() as nav:
        nav.ws.call(nav._id(), "Page.addScriptToEvaluateOnNewDocument", {"source": HOOK})
        # Aquece: a home primeiro, para o cookie do GA existir quando a pagina-alvo
        # carregar. Sem isso nao da para ver se o tracker LE identificador do GA.
        nav.abrir("%s/pt/" % srv.base())
        nav.abrir("%s/%s" % (srv.base(), pagina.strip("/") + "/"))

        for campo, valor in ISCAS.items():
            nav.js("""
            (function(){
              var el = document.querySelector('[name="%s"]');
              if (!el) return 'sem campo';
              el.focus(); el.value = %s;
              el.dispatchEvent(new Event('input', {bubbles:true}));
              el.dispatchEvent(new Event('change', {bubbles:true}));
              el.blur(); return 'ok';
            })()
            """ % (campo, json.dumps(valor)))
            time.sleep(0.4)

        # Abandono: sai da aba sem submeter. O timer costuma ser de ~8s.
        nav.js("document.dispatchEvent(new Event('visibilitychange'));"
               "window.dispatchEvent(new Event('blur'));"
               "window.dispatchEvent(new Event('beforeunload'));")
        time.sleep(12)

        reqs = json.loads(nav.js("JSON.stringify(window.__cap)") or "[]")
        claro = json.loads(nav.js("JSON.stringify(window.__claro)") or "[]")

        # Rede de seguranca contra o proprio probe (defeito real, 14/08): os hooks
        # acima so pegam fetch/XHR/sendBeacon. O Leadfeeder envia por GET em
        # <script>/pixel, para um host DIFERENTE do que serve o script
        # (sc.lfeeder.com serve, tr.lfeeder.com recebe) — e o probe disse
        # "nao medido" quando na verdade estava olhando para o lugar errado.
        # A Performance API ve TODO recurso, qualquer que seja o transporte.
        recursos = json.loads(nav.js(
            "JSON.stringify(performance.getEntriesByType('resource')"
            ".map(function(e){return e.name}))") or "[]")

    saida = os.path.join(RAIZ, "_qa_probe")
    if not os.path.isdir(saida):
        os.makedirs(saida)
    with io.open(os.path.join(saida, "captura.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"requisicoes": reqs, "texto_claro": claro},
                           indent=1, ensure_ascii=False))

    def decodifica(url):
        """Devolve os parametros de query, decodificando base64 quando for o caso.

        Payload em base64 na query e o padrao do Leadfeeder — legivel, ao contrario
        do envelope RSA+AES do Data Reveal. Se um dia nao decodificar, e sinal de
        que o conteudo e opaco, e isso precisa aparecer no relatorio."""
        out = []
        for k, vs in urllib.parse.parse_qs(urllib.parse.urlparse(url).query).items():
            v = vs[0]
            try:
                dec = base64.b64decode(v + "=" * (-len(v) % 4)).decode("utf-8")
                if dec.strip().startswith(("{", "[")):
                    out.append((k + " (base64)", dec))
                    continue
            except Exception:
                pass
            out.append((k, v))
        return out

    do_host = [r for r in reqs if host in (r.get("url") or "")]
    rec_host = [u for u in recursos if host in u]
    print(u"\npagina:      %s" % pagina)
    print(u"fornecedor:  %s" % host)
    print(u"requisicoes: %d via fetch/xhr/beacon, %d para o fornecedor" % (len(reqs), len(do_host)))
    print(u"recursos:    %d no total, %d para o fornecedor (qualquer transporte)"
          % (len(recursos), len(rec_host)))
    for u in rec_host:
        print(u"\n  -> %s" % u.split("?")[0])
        for k, v in decodifica(u):
            print(u"     %s = %s" % (k, v[:700]))
    print(u"blocos de texto claro capturados: %d" % len(claro))

    tudo = (json.dumps(reqs, ensure_ascii=False) + json.dumps(claro, ensure_ascii=False)
            + json.dumps([decodifica(u) for u in rec_host], ensure_ascii=False))
    print(u"\n=== as iscas sairam da maquina? ===")
    vazou = []
    for campo, valor in ISCAS.items():
        # Compara por trecho: o campo pode reformatar o valor (mascara de telefone).
        marca = valor.split()[0] if u" " in valor else valor[:12]
        if marca in tudo:
            vazou.append(campo)
        print(u"  %-14s %s" % (campo, u"VAZOU" if marca in tudo else u"nao apareceu"))

    if not do_host and not rec_host:
        print(u"\nATENCAO: nenhuma requisicao para %s. O tracker esta DESLIGADO ou o host"
              u" mudou — isto NAO e aprovacao, e ausencia de medicao (R13)." % host)
        return 2
    if vazou:
        print(u"\nREPROVADO: %d campo(s) de formulario sairam sem submit: %s"
              % (len(vazou), ", ".join(vazou)))
        return 1
    print(u"\nAPROVADO neste teste: nenhuma isca de formulario saiu da maquina.")
    print(u"Escopo do que foi medido: %s, formulario preenchido e abandonado."
          u" Nao cobre outras paginas nem submit de verdade." % pagina)
    return 0


if __name__ == "__main__":
    sys.exit(main())
