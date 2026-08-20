# -*- coding: utf-8 -*-
"""Onda 68 (#247) -- derivada 1200x630 para todo `og:image` fora do padrao.

O PROBLEMA MEDIDO nas 109 paginas de conteudo. O `og:image` de artigo era a
imagem de banner do post, servida como estava:

    Imagem1-scaled.jpg                 2560x1475   927 KB   razao 1,74
    Automotive-industry-scaled.jpg     2560x1920   686 KB   razao 1,33
    energia-1.jpg                      2560x1707   679 KB   razao 1,50
    iStock-1652035117-...jpg           2560x 729   221 KB   razao 3,51
    imagem_gerada-...webp              1792x 493   117 KB   razao 3,63

O cartao de preview e 1,91:1. Entregar 1,33 (4:3) ou 3,63 (faixa) faz o scraper
recortar o centro por conta propria, e o resultado e imprevisivel -- num 4:3 ele
corta ~30% de cima e de baixo; numa faixa de 3,63 ele letterboxa ou estica. E
927 KB para uma miniatura de conversa e desperdicio puro.

A REGRA, explicita, para cada arquivo (nenhuma decisao caso a caso):
  1. mais de 200 KB, ou
  2. mais largo que 1600 px, ou
  3. razao fora de 1,905 por mais de 15%, ou
  4. formato que nao seja JPEG nem PNG
...entao gera derivada 1200x630 e a pagina passa a apontar para ela.

Sobre o item 4: WebP e o formato certo para imagem de PAGINA (ondas 61/62c) e
continua sendo -- a derivada NAO substitui o arquivo original, que segue servindo
a pagina. O que muda e so o que vai no `og:image`, porque suporte a WebP em
preview varia por cliente de mensageria, e JPEG e aceito em todos. E seguro por
construcao, nao por confiar num cliente especifico.

O que NAO e tocado: arquivo que ja esta 1200x630 em JPEG/PNG -- os 6 cartoes de
lider da onda 68 e o `og-mirow.png`. Eles passam pela regra sem gerar nada.

RECORTE: cover + centro. A imagem cobre 1200x630 pelo lado que falta e o excedente
sai igualmente dos dois lados -- mesma coisa que o scraper faria, exceto que aqui
o resultado e VISIVEL e versionado, e da para conferir.

Idempotente por assinatura das entradas (mesmo contrato do 139: comparar pixel de
JPEG nao distingue ruido de conteudo -- medido, o maximo do ida-e-volta e 51
niveis). Confere o que gravou: dimensao, peso e que abre.

Uso:  python tools_onda6/140_og_image_derivada.py .
"""

from __future__ import print_function

import hashlib
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa: E402

from _onda7_css import ler, resolve_public  # noqa: E402

LARG, ALT = 1200, 630
IDEAL = LARG / float(ALT)
DESTINO = "wp-content/uploads/2026/08/onda68"
TETO_KB = 120          # o teto da S163; derivada tem de caber nele
TETO_KB_ORIG = 200
TETO_LARG = 1600
DESVIO_RAZAO = 0.15
QUALIDADES = (86, 80, 74, 68, 62, 56, 50)   # cai a qualidade ate caber no teto
PARAMS_V = 1

MANIFESTO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "dados", "og-image-derivada.json")


def _slug(nome):
    s = re.sub(r'\.[A-Za-z0-9]+$', '', nome).lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:60]


def precisa(caminho):
    """(bool, motivo) pela regra declarada no docstring. Sem caso a caso."""
    im = Image.open(caminho)
    kb = os.path.getsize(caminho) / 1024.0
    w, h = im.size
    r = w / float(h)
    if kb > TETO_KB_ORIG:
        return True, "%.0f KB" % kb
    if w > TETO_LARG:
        return True, "%d px de largura" % w
    if abs(r - IDEAL) / IDEAL > DESVIO_RAZAO:
        return True, "razao %.2f" % r
    if im.format not in ("JPEG", "PNG"):
        return True, "formato %s" % im.format
    return False, ""


def derivar(caminho):
    """Cover + recorte central para exatamente 1200x630."""
    im = Image.open(caminho)
    im = im.convert("RGB")
    w, h = im.size
    escala = max(LARG / float(w), ALT / float(h))
    nw, nh = int(round(w * escala)), int(round(h * escala))
    im = im.resize((max(nw, LARG), max(nh, ALT)), Image.LANCZOS)
    w, h = im.size
    esq = (w - LARG) // 2
    topo = (h - ALT) // 2
    return im.crop((esq, topo, esq + LARG, topo + ALT))


def assinatura(caminho):
    h = hashlib.sha1()
    h.update(("PARAMS_V=%d|%dx%d|" % (PARAMS_V, LARG, ALT)).encode("utf-8"))
    with open(caminho, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    sm = ler(os.path.join(pub, "sitemap.xml"))
    locs = re.findall(r'<loc>([^<]+)</loc>', sm)

    # --- descobre os og:image em uso e quem os usa ---
    usos = {}
    for u in locs:
        p = u.replace("https://mirow.com.br/", "").strip("/")
        fp = os.path.join(pub, *(p.split("/") + ["index.html"]))
        if not os.path.exists(fp):
            continue
        h = ler(fp)
        m = re.search(r'<meta property="og:image" content="([^"]+)"', h)
        if not m:
            continue
        ref = m.group(1).replace("https://mirow.com.br/", "").lstrip("/")
        usos.setdefault(ref, []).append(fp)

    dest = os.path.join(pub, DESTINO.replace("/", os.sep))
    if not os.path.isdir(dest):
        os.makedirs(dest)

    manifesto = {}
    try:
        with io.open(MANIFESTO, encoding="utf-8") as f:
            manifesto = json.load(f)
    except Exception:
        pass
    novo_manifesto = {}

    escritos, trocadas, mantidos = 0, 0, 0
    troca = {}

    for ref in sorted(usos):
        origem = os.path.join(pub, ref.replace("/", os.sep))
        if not os.path.exists(origem):
            print("  AUSENTE %s" % ref)
            continue
        # derivada nossa nunca se re-deriva
        if ref.startswith(DESTINO):
            mantidos += 1
            continue
        prec, motivo = precisa(origem)
        if not prec:
            mantidos += 1
            continue

        nome = "og-%s-1200x630.jpg" % _slug(os.path.basename(ref))
        alvo = os.path.join(dest, nome)
        rel_alvo = "%s/%s" % (DESTINO, nome)
        troca[ref] = rel_alvo
        ass = assinatura(origem)
        novo_manifesto[rel_alvo] = ass

        if manifesto.get(rel_alvo) != ass or not os.path.exists(alvo):
            im = derivar(origem)
            dados = None
            for q in QUALIDADES:
                buf = io.BytesIO()
                im.save(buf, format="JPEG", quality=q, optimize=True,
                        progressive=True)
                dados = buf.getvalue()
                if len(dados) / 1024.0 <= TETO_KB:
                    break
            with open(alvo, "wb") as fh:
                fh.write(dados)
            escritos += 1
        print("  %-46s -> %-44s %5.0f KB  (%s)"
              % (os.path.basename(ref)[:46], nome[:44],
                 os.path.getsize(alvo) / 1024.0, motivo))

    # --- confere o que gravou ---
    falhas = []
    for rel_alvo in novo_manifesto:
        fp = os.path.join(pub, rel_alvo.replace("/", os.sep))
        if not os.path.exists(fp):
            falhas.append("%s nao foi gravado" % rel_alvo)
            continue
        im = Image.open(fp)
        im.load()
        kb = os.path.getsize(fp) / 1024.0
        if im.size != (LARG, ALT):
            falhas.append("%s saiu %dx%d" % (rel_alvo, im.size[0], im.size[1]))
        if kb > TETO_KB:
            falhas.append("%s tem %.0f KB, acima do teto de %d" % (rel_alvo, kb, TETO_KB))
    if falhas:
        print("")
        for f in falhas:
            print("  FALHA: %s" % f)
        raise SystemExit(1)

    # --- repontar as paginas ---
    for ref, rel_alvo in troca.items():
        for fp in usos[ref]:
            h = ler(fp)
            novo = h.replace(
                '<meta property="og:image" content="https://mirow.com.br/%s"' % ref,
                '<meta property="og:image" content="https://mirow.com.br/%s"' % rel_alvo)
            if novo != h:
                with io.open(fp, "w", encoding="utf-8", newline="") as fh:
                    fh.write(novo)
                trocadas += 1

    if novo_manifesto != manifesto:
        with io.open(MANIFESTO, "w", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(novo_manifesto, indent=2, sort_keys=True,
                                ensure_ascii=False) + u"\n")

    print("\nderivadas gravadas: %d   og:image ja no padrao: %d   paginas repontadas: %d"
          % (escritos, mantidos, trocadas))
    print("resumo: %d arquivo(s) alterado(s)" % (escritos + trocadas))


if __name__ == "__main__":
    main()
