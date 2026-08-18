# -*- coding: utf-8 -*-
r"""Classifica as imagens pesadas do espelho por FORMA DE USO, e projeta o WebP.

    python tools_onda6/qa/medir_imagens.py [raiz-que-contem-public]

Serve para escolher o alvo de uma onda de imagem sem chutar. Distingue o que o
NAVEGADOR baixa do que so o robo le:

    IMG      <img src>/srcset          -> baixada quando a pagina abre
    BGSTYLE  style="background:url()"  -> baixada; e com `cover` trocar o arquivo
                                          NAO move layout (o aspecto do arquivo
                                          nao define a caixa) -> alvo mais seguro
    CSS      url() em .css             -> baixada se o seletor casar
    SCHEMA   JSON-LD / og:image        -> o navegador NAO baixa; peso de SEO

TRES ARMADILHAS QUE ESTE ARQUIVO JA PAGOU (18/08/2026) — nao reintroduzir:

1. Capturar so o PRIMEIRO atributo do <img> declara orfa toda variante de
   `srcset`. Na primeira versao isso deu **96 falsas orfas / 22,6 MB**. Aqui se le
   o TAG INTEIRO. E P2.1 aplicado ao proprio medidor.
2. Regex de classe negada non-greedy (`[^...]+?\.png`) NAO TERMINA sobre o
   `bundle-js.js` minificado de 1,5 MB (backtracking). Achar a extensao e caminhar
   para tras e linear — ver `tools_onda6/qa/../../tools/verificacoes.py` S162 para
   o mesmo cuidado.
3. `<source src="...mp4">` casa com a mesma regex de `<img>`. Somar sem filtrar
   extensao de imagem mostrou **43 MB de "imagem"** na pagina de carreiras, que
   eram um MP4 de 40 MB. Foi o acidente que revelou a onda 62a — mas como MEDIDA
   de imagem estava errado.

Taxa real do WebP medida em 18/08 convertendo e pesando (nao estimada):
PNG corta **93-97%**; JPEG ja comprimido corta **17%** (Imagem1-scaled) a 42%.
Por isso a onda de imagem decidida pelo Mario e "atacar os PNG": eles sao
**159 dos 169 arquivos e 47,4 dos 48,9 MB**.
"""
import io, os, re, collections

import sys
raiz = sys.argv[1] if len(sys.argv) > 1 else "."
pub = os.path.join(os.path.abspath(raiz), "public")
TETO = 120 * 1024
EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")

arquivos = {}
for dp, _d, fs in os.walk(pub):
    if os.sep + ".git" in dp:
        continue
    for nome in fs:
        if nome.endswith((".html", ".css", ".xml", ".js", ".txt", ".json")):
            fp = os.path.join(dp, nome)
            with io.open(fp, encoding="utf-8", errors="ignore") as f:
                arquivos[os.path.relpath(fp, pub).replace(os.sep, "/")] = f.read()

grandes = {}
for dp, _d, fs in os.walk(pub):
    if os.sep + ".git" in dp:
        continue
    for nome in fs:
        if not nome.lower().endswith(EXT):
            continue
        fp = os.path.join(dp, nome)
        t = os.path.getsize(fp)
        if t > TETO:
            grandes[os.path.relpath(fp, pub).replace(os.sep, "/")] = t


def normaliza(ref, dir_origem):
    ref = ref.split("?")[0].split("#")[0]
    if ref.startswith("/mirow-site/"):
        return ref[len("/mirow-site/"):]
    if ref.startswith("/"):
        return ref.lstrip("/")
    if ref.startswith("http"):
        m = re.match(r'https?://[^/]+/(.*)$', ref)
        if not m:
            return None
        r = m.group(1)
        return r[len("mirow-site/"):] if r.startswith("mirow-site/") else r
    return os.path.normpath(os.path.join(dir_origem, ref)).replace(os.sep, "/")


# pega o TAG INTEIRO: um <img> traz src E srcset com 4 variantes, e capturar so o
# primeiro atributo fazia as variantes do srcset parecerem orfas — P2.1 no proprio medidor
IMGTAG = re.compile(r'<(?:img|source)\b[^>]*>', re.I)
DENTRO = re.compile(r'[^\s"\'(),]+\.(?:png|jpg|jpeg|webp|gif|svg)', re.I)
BG = re.compile(r'background(?:-image)?\s*:\s*[^;"\']*url\((["\']?)([^)"\']+)\1\)', re.I)
CSSURL = re.compile(r'url\((["\']?)([^)"\']+)\1\)', re.I)
META = re.compile(r'<meta[^>]+content="([^"]+\.(?:png|jpg|jpeg|webp|gif|svg))"', re.I)
JSONIMG = re.compile(r'"(?:url|contentUrl|thumbnailUrl|image)"\s*:\s*"([^"]+?\.(?:png|jpg|jpeg|webp|gif|svg))"', re.I)

uso = collections.defaultdict(set)      # rel -> {formas}
onde = collections.defaultdict(set)     # rel -> {paginas}
for origem, txt in arquivos.items():
    d = os.path.dirname(origem)
    t = txt.replace(u"\\/", u"/")
    pares = []
    if origem.endswith(".css"):
        pares += [("CSS", m.group(2)) for m in CSSURL.finditer(t)]
    else:
        for tag in IMGTAG.finditer(t):
            pares += [("IMG", u.group(0)) for u in DENTRO.finditer(tag.group(0))]
        pares += [("BGSTYLE", m.group(2)) for m in BG.finditer(t)]
        pares += [("SCHEMA", m.group(1)) for m in META.finditer(t)]
        pares += [("SCHEMA", m.group(1)) for m in JSONIMG.finditer(t)]
    for forma, ref in pares:
        for parte in re.split(r'\s*,\s*', ref):
            cand = parte.strip().split(" ")[0]
            rel = normaliza(cand, d)
            if rel and rel in grandes:
                uso[rel].add(forma)
                onde[rel].add(origem)

# agrega por forma
tot = collections.Counter()
peso = collections.Counter()
for rel, t in grandes.items():
    formas = uso.get(rel)
    chave = "+".join(sorted(formas)) if formas else "SEM-REFERENCIA"
    tot[chave] += 1
    peso[chave] += t

print("=== %d imagens >120 KB, %.1f MB ===" % (len(grandes), sum(grandes.values()) / 1048576.0))
print("%-22s %6s %10s" % ("forma de uso", "arqs", "MB"))
for chave, n in tot.most_common():
    print("%-22s %6d %10.1f" % (chave, n, peso[chave] / 1048576.0))

print()
print("=== o que o NAVEGADOR baixa (IMG/BGSTYLE/CSS), top 25 ===")
baixadas = [(t, rel) for rel, t in grandes.items()
            if uso.get(rel) and uso[rel] - {"SCHEMA"}]
baixadas.sort(reverse=True)
print("total: %d arquivos, %.1f MB" % (len(baixadas), sum(t for t, _ in baixadas) / 1048576.0))
for t, rel in baixadas[:25]:
    print("  %7.0f KB  %-9s x%-3d %s"
          % (t / 1024.0, "+".join(sorted(uso[rel])), len(onde[rel]), rel))

print()
print("=== SO no schema (robo le, navegador nao baixa), top 10 ===")
so_schema = [(t, rel) for rel, t in grandes.items() if uso.get(rel) == {"SCHEMA"}]
so_schema.sort(reverse=True)
print("total: %d arquivos, %.1f MB" % (len(so_schema), sum(t for t, _ in so_schema) / 1048576.0))
for t, rel in so_schema[:10]:
    print("  %7.0f KB  x%-3d %s" % (t / 1024.0, len(onde[rel]), rel))

print()
print("=== SEM referencia nenhuma (candidatas a remocao) ===")
sem = [(t, rel) for rel, t in grandes.items() if not uso.get(rel)]
sem.sort(reverse=True)
print("total: %d arquivos, %.1f MB" % (len(sem), sum(t for t, _ in sem) / 1048576.0))
for t, rel in sem:
    print("  %7.0f KB  %s" % (t / 1024.0, rel))
