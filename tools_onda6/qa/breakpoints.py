# -*- coding: utf-8 -*-
"""Contact sheet multi-breakpoint: UMA pagina em N larguras, num UNICO html.

Uso: python breakpoints.py <url> [saida.html] [aos-off] [bp=320,390,768,1024,1366,1920]

Para cada breakpoint: screenshot full-page + metricas que pegam bug responsivo
de verdade (overflow-x com os elementos culpados, telas de dobra, elementos
zerados). Sai um HTML unico com as imagens em base64 — da para arrastar para o
chat/e-mail sem pasta junto. Revisao "no olho", sem dev tools (workflow do
Bruno, 03/08/2026). 320px e o piso WCAG 1.4.10 (reflow sem scroll horizontal).

Regra P4 do repo: nenhuma onda vira "PRONTO, aguardando OK" sem o contact
sheet da(s) pagina(s)-alvo. Saida default em _qa_breakpoints/ (gitignored).
"""
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shot import WS, CHROME  # noqa: E402

BREAKPOINTS = [320, 390, 768, 1024, 1366, 1920]
ALTURA = 900
PORTA = 9337

AOS_OFF_JS = (
    "var s=document.createElement('style');"
    "s.textContent='[data-aos]{opacity:1!important;transform:none!important;"
    "visibility:visible!important}';document.head.appendChild(s);"
    "document.querySelectorAll('[data-aos]').forEach(function(e){"
    "e.classList.add('aos-animate')});true")

# medicoes que pegam bug responsivo real (overflow-x e o nº 1 no mobile)
MEDICOES_JS = """
(function(){
  var de=document.documentElement;
  var overflow=de.scrollWidth-window.innerWidth;
  var culpados=[];
  if(overflow>1){
    var todos=document.querySelectorAll('body *');
    for(var i=0;i<todos.length&&culpados.length<5;i++){
      var r=todos[i].getBoundingClientRect();
      if(r.width>0&&r.right>window.innerWidth+1){
        var el=todos[i];
        var nome=el.tagName.toLowerCase();
        if(el.className&&typeof el.className==='string')
          nome+='.'+el.className.trim().split(/\\s+/).slice(0,2).join('.');
        if(culpados.indexOf(nome)<0)culpados.push(nome);
      }
    }
  }
  var zerados=[];
  var chaves=document.querySelectorAll('img,h1,h2,.hero-contatos__link');
  for(var j=0;j<chaves.length&&zerados.length<5;j++){
    var rr=chaves[j].getBoundingClientRect();
    var cs=getComputedStyle(chaves[j]);
    if(cs.display!=='none'&&(rr.width===0||rr.height===0)){
      var nn=chaves[j].tagName.toLowerCase();
      if(chaves[j].className&&typeof chaves[j].className==='string')
        nn+='.'+chaves[j].className.trim().split(/\\s+/)[0];
      if(zerados.indexOf(nn)<0)zerados.push(nn);
    }
  }
  return JSON.stringify({
    overflow: overflow,
    culpados: culpados,
    zerados: zerados,
    telas: Math.round(de.scrollHeight/window.innerHeight*10)/10,
    altura: Math.max(document.body.scrollHeight,de.scrollHeight)
  });
})()
"""


def capturar(ws, mid, url, width, aos_off, primeira):
    ws.call(mid + 1, "Emulation.setDeviceMetricsOverride", {
        "width": width, "height": ALTURA, "deviceScaleFactor": 1,
        "mobile": width < 768})
    if primeira:
        ws.call(mid + 2, "Page.navigate", {"url": url})
        time.sleep(7)
    else:
        # re-navegar (nao so re-override): media queries de load-time e o
        # onda8-dobra.js medem no carregamento — override a quente falseia
        ws.call(mid + 2, "Page.reload")
        time.sleep(4)
    if aos_off:
        ws.call(mid + 3, "Runtime.evaluate", {"expression": AOS_OFF_JS})
        time.sleep(1)
    ev = ws.call(mid + 4, "Runtime.evaluate", {
        "expression": MEDICOES_JS, "returnByValue": True})
    met = json.loads(ev["result"]["result"]["value"])
    h = max(ALTURA, min(int(met["altura"]), 20000))
    r = ws.call(mid + 5, "Page.captureScreenshot", {
        "format": "png", "captureBeyondViewport": True,
        "clip": {"x": 0, "y": 0, "width": width, "height": h, "scale": 1}})
    if "result" not in r:
        raise SystemExit("CDP erro em %dpx: %s" % (width, r))
    met["png_b64"] = r["result"]["data"]
    met["width"] = width
    return met


def montar_contact_sheet(url, resultados, out):
    colunas = []
    for m in resultados:
        ok = m["overflow"] <= 1 and not m["zerados"]
        cor = "#2E7D32" if ok else "#C62828"
        selo = "OK" if ok else "PROBLEMA"
        detalhes = ["overflow-x: %dpx" % max(0, m["overflow"]),
                    "dobra: %s telas" % m["telas"]]
        if m["culpados"]:
            detalhes.append("vazando: " + ", ".join(m["culpados"]))
        if m["zerados"]:
            detalhes.append("zerados: " + ", ".join(m["zerados"]))
        colunas.append(
            '<div class="col"><div class="head" style="border-color:%s">'
            '<b>%dpx</b> <span style="color:%s">%s</span><br><small>%s</small></div>'
            '<a href="data:image/png;base64,%s" target="_blank">'
            '<img src="data:image/png;base64,%s" alt="%dpx"></a></div>'
            % (cor, m["width"], cor, selo, " · ".join(detalhes),
               m["png_b64"], m["png_b64"], m["width"]))
    html = (
        '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<title>Breakpoints — %s</title><style>'
        'body{font-family:Arial,sans-serif;background:#0d1230;color:#fff;margin:16px}'
        'h1{font-size:16px;font-weight:normal}'
        '.sheet{display:flex;gap:14px;overflow-x:auto;align-items:flex-start}'
        '.col{flex:none}'
        '.head{border-top:4px solid;padding:6px 2px;font-size:13px;margin-bottom:6px}'
        '.col img{width:300px;display:block;border:1px solid #334;border-radius:4px}'
        'small{color:#AAD5E8}'
        '</style></head><body><h1>Contact sheet — %s — %s '
        '(clique na imagem para o tamanho real)</h1>'
        '<div class="sheet">%s</div></body></html>'
        % (url, url, time.strftime("%Y-%m-%d %H:%M"), "".join(colunas)))
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    url = sys.argv[1]
    extras = sys.argv[2:]
    aos_off = "aos-off" in extras
    bps = list(BREAKPOINTS)
    out = None
    for a in extras:
        if a.startswith("bp="):
            bps = [int(x) for x in a[3:].split(",")]
        elif a not in ("aos-off",) and not a.startswith("bp="):
            out = a
    if not out:
        slug = re.sub(r"[^a-z0-9]+", "-", url.split("//")[-1].lower()).strip("-")[:60]
        pasta = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))), "_qa_breakpoints")
        os.makedirs(pasta, exist_ok=True)
        out = os.path.join(pasta, "%s-%s.html" % (slug, time.strftime("%Y%m%d-%H%M")))

    profile = tempfile.mkdtemp(prefix="cdpbp")
    proc = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--remote-debugging-port=%d" % PORTA, "--user-data-dir=" + profile,
         "--window-size=1400,900", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        ws_url = None
        for _ in range(60):
            try:
                tabs = json.load(urllib.request.urlopen(
                    "http://127.0.0.1:%d/json" % PORTA, timeout=5))
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
        resultados = []
        mid = 100
        for k, bp in enumerate(bps):
            resultados.append(capturar(ws, mid, url, bp, aos_off, k == 0))
            m = resultados[-1]
            print("%dpx: overflow=%dpx telas=%s %s" % (
                bp, max(0, m["overflow"]), m["telas"],
                "OK" if m["overflow"] <= 1 and not m["zerados"] else
                "PROBLEMA " + ",".join(m["culpados"] + m["zerados"])))
            mid += 10
        montar_contact_sheet(url, resultados, out)
        print("contact sheet: %s" % out)
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
