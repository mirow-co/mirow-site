# -*- coding: utf-8 -*-
"""Le o DOM salvo do PageSpeed Insights e extrai notas, metricas e auditorias que falham.

O arquivo salvo pelo navegador traz o relatorio MOBILE e o DESKTOP no mesmo DOM,
entao a separacao e por ordem de aparicao dos dois containers de relatorio.
"""
import io, re, html, sys

arq = sys.argv[1] if len(sys.argv) > 1 else \
    r"C:\Users\admin\Downloads\analysis\PageSpeed Insights_mobile.html"
t = io.open(arq, encoding="utf-8", errors="ignore").read()


def limpa(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()


# ---- notas por categoria ----
print("=== NOTAS (gauge) ===")
gauges = re.findall(
    r'lh-gauge__percentage[^>]*>([^<]{1,6})<.*?lh-gauge__label[^>]*>([^<]{1,40})<',
    t, re.S)
for v, lab in gauges:
    print("  %-22s %s" % (limpa(lab), limpa(v)))

# ---- metricas ----
print()
print("=== METRICAS ===")
mets = re.findall(
    r'lh-metric__title[^>]*>(.*?)</span>.*?lh-metric__value[^>]*>(.*?)</div>',
    t, re.S)
for tit, val in mets:
    print("  %-30s %s" % (limpa(tit)[:30], limpa(val)))

# ---- auditorias que falham ou ficam em amarelo ----
print()
print("=== AUDITORIAS COM PROBLEMA (fail/average) ===")
vistos = []
for m in re.finditer(r'class="[^"]*lh-audit lh-audit--(fail|average)[^"]*"(.{0,4000}?)'
                     r'lh-audit__title[^>]*>(.*?)</span>', t, re.S):
    estado, meio, titulo = m.group(1), m.group(2), limpa(m.group(3))
    # valor exibido, se houver
    dv = re.search(r'lh-audit__display-text[^>]*>(.*?)</div>',
                   t[m.end():m.end() + 3000], re.S)
    val = limpa(dv.group(1))[:40] if dv else ""
    chave = (estado, titulo)
    if chave in vistos:
        continue
    vistos.append(chave)
    print("  [%-7s] %-62s %s" % (estado, titulo[:62], val))
print("  (%d distintas)" % len(vistos))
