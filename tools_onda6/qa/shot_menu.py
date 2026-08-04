# -*- coding: utf-8 -*-
"""Screenshot da primeira dobra com um menu da barra superior aberto (hover real).

Uso: python shot_menu.py <url> <saida.png> <seletor-css> [largura]

O seletor aponta o elemento sobre o qual o mouse e posicionado (ex.: o link
"Sobre nos" ou o botao de idiomas). O hover e disparado via CDP
(Input.dispatchMouseEvent), entao tanto o :hover do CSS quanto o mouseenter do
jQuery do tema rodam de verdade.

CUIDADO (achado na onda 27): a captura usa `captureBeyondViewport`, e nesse modo
o Chrome REPINTA a pagina e parte do estado de hover se perde — os links e os
icones da barra saem invisiveis (brancos sobre o painel branco) mesmo estando
corretos no navegador. Isso ja rendeu uma caca a bug inexistente. Para conferir
COR em estado de hover, capture sem `captureBeyondViewport` (viewport puro) ou
meca `getComputedStyle` via Runtime.evaluate.
"""
import base64
import json
import subprocess
import sys
import tempfile
import time
import urllib.request

from shot import WS, CHROME


def main():
    url, out, seletor = sys.argv[1], sys.argv[2], sys.argv[3]
    width = int(sys.argv[4]) if len(sys.argv) > 4 else 1400
    profile = tempfile.mkdtemp(prefix="cdpmenu")
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                             "--remote-debugging-port=9334", "--user-data-dir=" + profile,
                             "--window-size=%d,900" % width, "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = None
        for _ in range(60):
            try:
                tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9334/json", timeout=5))
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
        ws.call(2, "Page.navigate", {"url": url})
        time.sleep(7)
        r = ws.call(3, "Runtime.evaluate", {"expression": (
            "(function(){var e=document.querySelector(%s);if(!e)return null;"
            "var r=e.getBoundingClientRect();"
            "return [r.left+r.width/2, r.top+r.height/2];})()" % json.dumps(seletor)),
            "returnByValue": True})
        pos = r["result"]["result"].get("value")
        if not pos:
            raise SystemExit("seletor nao encontrado: %s" % seletor)
        x, y = pos
        for ev in ("mouseMoved", "mouseMoved"):
            ws.call(4, "Input.dispatchMouseEvent",
                    {"type": ev, "x": x, "y": y, "button": "none", "clickCount": 0})
            time.sleep(0.6)
        time.sleep(1.2)
        r = ws.call(5, "Page.captureScreenshot", {
            "format": "png", "captureBeyondViewport": True,
            "clip": {"x": 0, "y": 0, "width": width, "height": 900, "scale": 1}})
        if "result" not in r:
            raise SystemExit("CDP erro: %s" % r)
        with open(out, "wb") as f:
            f.write(base64.b64decode(r["result"]["data"]))
        print("%s  (menu %s aberto)" % (out, seletor))
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
