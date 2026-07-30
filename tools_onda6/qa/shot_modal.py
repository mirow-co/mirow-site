# -*- coding: utf-8 -*-
"""Abre um modal do tema (clicando no card) e tira o screenshot da tela.

Serve para provar no QA que o modal de bio realmente abre — ou seja, que o jQuery
reposto em wp-includes/ esta funcionando.

Uso: python shot_modal.py <url> <#seletor-do-card> <saida.png> [largura] [altura]
Ex.: python shot_modal.py http://127.0.0.1:8611/mirow-site/sobre-nos/lideres/ \\
         modal_joao-daniel-ramos modal-joao-pt.png 1400 1000
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
    url, modal_id, out = sys.argv[1], sys.argv[2], sys.argv[3]
    width = int(sys.argv[4]) if len(sys.argv) > 4 else 1400
    height = int(sys.argv[5]) if len(sys.argv) > 5 else 1000
    profile = tempfile.mkdtemp(prefix="cdpmodal")
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                             "--remote-debugging-port=9334", "--user-data-dir=" + profile,
                             "--window-size=%d,%d" % (width, height), "about:blank"],
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
        time.sleep(8)
        # confere se o jQuery carregou (os modais do tema dependem dele)
        jq = ws.call(3, "Runtime.evaluate", {
            "expression": "typeof window.jQuery === 'function' ? window.jQuery.fn.jquery : 'AUSENTE'",
            "returnByValue": True})["result"]["result"]["value"]
        print("jQuery na pagina: %s" % jq)
        r = ws.call(4, "Runtime.evaluate", {"expression": (
            "(function(){var b=document.querySelector('[data-bs-target=\"#%s\"]');"
            "if(!b) return 'card nao encontrado'; b.click(); return 'clicado';})()" % modal_id),
            "returnByValue": True})
        print("clique: %s" % r["result"]["result"]["value"])
        time.sleep(2)
        estado = ws.call(5, "Runtime.evaluate", {"expression": (
            "(function(){var m=document.getElementById('%s');"
            "if(!m) return 'modal ausente';"
            "return m.classList.contains('show') ? 'ABERTO' : 'fechado';})()" % modal_id),
            "returnByValue": True})["result"]["result"]["value"]
        print("modal: %s" % estado)
        cap = ws.call(6, "Page.captureScreenshot", {"format": "png"})
        if "result" not in cap:
            raise SystemExit("CDP erro: %s" % cap)
        with open(out, "wb") as f:
            f.write(base64.b64decode(cap["result"]["data"]))
        print("%s (%dx%d)" % (out, width, height))
        if estado != "ABERTO":
            sys.exit(1)
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
