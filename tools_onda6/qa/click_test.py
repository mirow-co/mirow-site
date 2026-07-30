# -*- coding: utf-8 -*-
"""Prova que um link e MESMO clicavel (nada do tema por cima dele).

Uso: python click_test.py <url> <seletor-css> [largura] [altura]

O que faz, nessa ordem:
  1. mede o retangulo do elemento;
  2. roda document.elementFromPoint no centro dele — se voltar outra coisa, ha
     um overlay engolindo o clique (foi o que aconteceu com o hero sem CSS: o
     .banner__background, absolute e z-index 1, ficava por cima);
  3. dispara um clique de mouse DE VERDADE (Input.dispatchMouseEvent, nao
     element.click()) e captura o href para onde o navegador iria.

Ex.: python click_test.py http://127.0.0.1:8611/mirow-site/pt/ ".hero-contatos__link--wa"
"""
import json
import subprocess
import sys
import tempfile
import time
import urllib.request

from shot import CHROME, WS

PREP = r"""
(function(){
  window.__cliques = [];
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('a');
    window.__cliques.push(a ? a.href : '(nao caiu em <a>: ' + e.target.tagName + ')');
    e.preventDefault();
  }, true);
  return true;
})()
"""


def main():
    url, seletor = sys.argv[1], sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 1400
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 900
    profile = tempfile.mkdtemp(prefix="cdpclick")
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                             "--remote-debugging-port=9335", "--user-data-dir=" + profile,
                             "--window-size=%d,%d" % (width, height), "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = None
        for _ in range(60):
            try:
                tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9335/json", timeout=5))
                for t in tabs:
                    if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                        ws_url = t["webSocketDebuggerUrl"]
                        break
                if ws_url:
                    break
            except Exception:
                pass
            time.sleep(0.5)
        if not ws_url:
            raise SystemExit("nao consegui falar com o Chrome")
        ws = WS(ws_url)
        ws.call(1, "Page.enable")
        ws.call(2, "Emulation.setDeviceMetricsOverride", {
            "width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})
        ws.call(3, "Page.navigate", {"url": url})
        time.sleep(7)

        expr = ("(function(){var e=document.querySelector(%s);if(!e)return null;"
                "var b=e.getBoundingClientRect();"
                "var x=Math.round(b.left+b.width/2),y=Math.round(b.top+b.height/2);"
                "var alvo=document.elementFromPoint(x,y);"
                "var a=alvo&&alvo.closest?alvo.closest('a'):null;"
                "return JSON.stringify({x:x,y:y,w:Math.round(b.width),h:Math.round(b.height),"
                "topo:alvo?alvo.tagName+'.'+(alvo.className||''):null,"
                "href:a?a.href:null,cor:getComputedStyle(e).color,"
                "fonte:getComputedStyle(e).fontSize});})()" % json.dumps(seletor))
        r = ws.call(4, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
        val = r["result"]["result"]["value"]
        if not val:
            raise SystemExit("elemento nao encontrado: %s" % seletor)
        info = json.loads(val)
        print("retangulo: %dx%d no ponto (%d,%d)" % (info["w"], info["h"], info["x"], info["y"]))
        print("cor do texto: %s | tamanho: %s" % (info["cor"], info["fonte"]))
        print("elementFromPoint: %s" % info["topo"])
        print("href sob o ponto: %s" % info["href"])

        ws.call(5, "Runtime.evaluate", {"expression": PREP, "returnByValue": True})
        for tipo in ("mousePressed", "mouseReleased"):
            ws.call(6, "Input.dispatchMouseEvent", {
                "type": tipo, "x": info["x"], "y": info["y"],
                "button": "left", "clickCount": 1})
        time.sleep(1)
        r = ws.call(7, "Runtime.evaluate", {
            "expression": "JSON.stringify(window.__cliques)", "returnByValue": True})
        cliques = json.loads(r["result"]["result"]["value"])
        print("clique real -> %s" % (cliques or "NADA (clique nao chegou no link)"))
        ok = bool(cliques) and cliques[0] == info["href"] and info["href"]
        print("RESULTADO: %s" % ("CLICAVEL OK" if ok else "FALHOU"))
        sys.exit(0 if ok else 1)
    finally:
        proc.terminate()


main()
