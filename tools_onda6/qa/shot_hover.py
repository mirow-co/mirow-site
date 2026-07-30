# -*- coding: utf-8 -*-
"""Screenshot com o mouse REALMENTE parado em cima de um elemento.

Uso: python shot_hover.py <url> <seletor-css> <saida.png> [largura] [altura] [aos-off]

Por que existe: a onda 9 poe um cartao que so aparece no :hover do pin do mapa.
Nem `element.click()` nem CSS forcado provam que o hover funciona — so um
movimento de mouse de verdade (Input.dispatchMouseEvent com type=mouseMoved),
que e o que o Chrome usa para decidir o :hover.

Rola a pagina ate o elemento, move o mouse ao centro dele, espera a transicao e
captura a viewport (a dobra), que e onde o cartao esta.

Ex.: python shot_hover.py http://127.0.0.1:8621/mirow-site/pt/sobre-nos/nossa-rede/ \\
         ".rede-pin[data-parceiro='4'] .rede-pin__botao" onda9-rede-pt-hover.png
"""
import base64
import json
import subprocess
import sys
import tempfile
import time
import urllib.request

from shot import CHROME, WS

AOS_ON = ("var s=document.createElement('style');"
          "s.textContent='[data-aos]{opacity:1!important;transform:none!important;"
          "visibility:visible!important}';document.head.appendChild(s);"
          "document.querySelectorAll('[data-aos]').forEach(function(e){"
          "e.classList.add('aos-animate')});true")


def main():
    url, seletor, saida = sys.argv[1], sys.argv[2], sys.argv[3]
    width = int(sys.argv[4]) if len(sys.argv) > 4 else 1400
    height = int(sys.argv[5]) if len(sys.argv) > 5 else 900
    aos_off = "aos-off" in sys.argv[6:]

    profile = tempfile.mkdtemp(prefix="cdphover")
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                             "--remote-debugging-port=9337", "--user-data-dir=" + profile,
                             "--window-size=%d,%d" % (width, height), "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = None
        for _ in range(60):
            try:
                tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9337/json", timeout=5))
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
        if aos_off:
            ws.call(4, "Runtime.evaluate", {"expression": AOS_ON})
            time.sleep(1)

        # rola ate o elemento e devolve o centro dele JA em coordenadas de viewport
        expr = ("(function(){var e=document.querySelector(%s);if(!e)return null;"
                "e.scrollIntoView({block:'center',behavior:'instant'});"
                "var b=e.getBoundingClientRect();"
                "return JSON.stringify({x:Math.round(b.left+b.width/2),"
                "y:Math.round(b.top+b.height/2)});})()" % json.dumps(seletor))
        r = ws.call(5, "Runtime.evaluate", {"expression": expr, "returnByValue": True})
        val = r["result"]["result"]["value"]
        if not val:
            raise SystemExit("elemento nao encontrado: %s" % seletor)
        pos = json.loads(val)
        time.sleep(1)

        # dois mouseMoved: o primeiro "entra" na pagina, o segundo assenta no alvo
        for x, y in ((pos["x"] - 40, pos["y"] - 40), (pos["x"], pos["y"])):
            ws.call(6, "Input.dispatchMouseEvent", {
                "type": "mouseMoved", "x": x, "y": y, "buttons": 0})
            time.sleep(0.4)
        time.sleep(1)

        # confere que o cartao esta mesmo visivel antes de salvar
        chk = ws.call(7, "Runtime.evaluate", {"expression": (
            "(function(){var e=document.querySelector(%s);"
            "var pin=e&&e.closest('.rede-pin');if(!pin)return 'sem pin';"
            "var c=pin.querySelector('.rede-pin__card');if(!c)return 'sem cartao';"
            "var s=getComputedStyle(c);return s.visibility+' / opacity '+s.opacity;})()"
            % json.dumps(seletor)), "returnByValue": True})
        print("estado do cartao: %s" % chk["result"]["result"].get("value"))

        # SEM `clip`: com clip o Chrome interpreta as coordenadas em relacao ao
        # DOCUMENTO, e a captura volta o topo da pagina em vez da dobra rolada.
        r = ws.call(8, "Page.captureScreenshot", {"format": "png"})
        if "result" not in r:
            raise SystemExit("CDP erro: %s" % r)
        with open(saida, "wb") as f:
            f.write(base64.b64decode(r["result"]["data"]))
        print("%s  (%dx%d)" % (saida, width, height))
    finally:
        proc.terminate()


main()
