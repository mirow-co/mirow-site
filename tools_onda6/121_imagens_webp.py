# -*- coding: utf-8 -*-
"""Onda 61: imagens em WebP e no tamanho que a pagina realmente usa.

PEDIDO: o PageSpeed de 18/08 pede "Improve image delivery — 330 KiB" na home.

MEDIDO NO NAVEGADOR (nao suposto) — natural x exibido em 1400px:
    edp.svg            3426x1263  ->  81x30    (42x maior que o necessario, 414 KB)
    mercedes-benz.svg  1400x354   -> 119x30    (301 KB de path com 5 casas decimais)
    taesa.png           400x147   ->  82x30
    Andreas/Felipe/prof/Elmar  232x246 -> 192x204   (PNG, 64-76 KB cada)
    os 6 selos         natural == exibido        (so ganho de formato)

ESTE SCRIPT trata os RASTERS (Pillow). Os dois SVG pesados vao no 122.
  - converte para WebP com qualidade calibrada
  - redimensiona para 3x o tamanho exibido quando o arquivo e maior que isso
    (3x cobre tela de DPR 3; acima disso o ganho de nitidez nao se ve)
  - reescreve a referencia em TODA pagina, preservando alt/width/height
  - `width`/`height` no HTML passam a ser a dimensao NOVA do arquivo

PROVA DE QUE NAO MUDA O VISUAL: `tools_onda6/qa/comparar_regiao.py` fotografa a
regiao antes e depois e compara pixel a pixel. A onda 61 so fecha com o diff medido.

Idempotente: se o .webp ja existe e o HTML ja aponta para ele, nao faz nada.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public

try:
    from PIL import Image
except ImportError:
    raise SystemExit("este script precisa do Pillow (pip install Pillow)")

# (caminho relativo a public/, maior lado exibido em px, qualidade webp)
ALVOS = [
    ("wp-content/uploads/2023/02/Andreas-Mirow.png", 204, 86),
    ("wp-content/uploads/2023/02/Felipe-Diniz-1.png", 204, 86),
    ("wp-content/uploads/2023/02/prof.png", 204, 86),
    ("wp-content/uploads/2023/02/Elmar-Gans-1.png", 204, 86),
    # taesa: 400x147 tem gcd 1, entao QUALQUER redimensionamento muda a razao e
    # empurra a fileira centrada. Fica no tamanho original, so troca de formato.
    ("wp-content/uploads/2026/07/clientes/taesa.png", 147, 90),
    ("wp-content/uploads/2023/02/certificate-cdp.png", 86, 90),
    ("wp-content/uploads/2023/02/certificate-basedtargets.png", 94, 90),
    ("wp-content/uploads/2023/02/certificate-seventowatch.png", 86, 90),
    ("wp-content/uploads/2023/02/certificate-growingfirms.png", 86, 90),
    ("wp-content/uploads/2023/02/certificate-globalimpact.png", 86, 90),
    ("wp-content/uploads/2023/04/image-52.png", 98, 90),
]
# variantes do mesmo arquivo que outras paginas usam (a home alema, por exemplo)
EXTRA = ["wp-content/uploads/2023/02/Andreas-Mirow-232x239-1.png",
         "wp-content/uploads/2023/02/Felipe-Diniz-1-232x239-1.png",
         "wp-content/uploads/2023/02/prof-232x239-1.png",
         "wp-content/uploads/2024/04/certificate-cdp.png",
         "wp-content/uploads/2024/04/certificate-basedtargets.png",
         "wp-content/uploads/2024/04/certificate-seventowatch.png",
         "wp-content/uploads/2024/04/certificate-growingfirms.png",
         "wp-content/uploads/2024/04/certificate-globalimpact.png",
         "wp-content/uploads/2024/04/image-52.png"]

FATOR_DPR = 3


def converte(pub, rel, lado_exibido, qual):
    orig = os.path.join(pub, rel.replace("/", os.sep))
    if not os.path.exists(orig):
        return None
    novo_rel = re.sub(r"\.png$", ".webp", rel)
    novo = os.path.join(pub, novo_rel.replace("/", os.sep))
    im = Image.open(orig)
    w, h = im.size
    teto = lado_exibido * FATOR_DPR
    if max(w, h) > teto:
        esc = float(teto) / max(w, h)
        im = im.resize((max(1, int(round(w * esc))), max(1, int(round(h * esc)))),
                       Image.LANCZOS)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if "A" in im.mode or im.mode == "P" else "RGB")
    im.save(novo, "WEBP", quality=qual, method=6)
    return novo_rel, im.size, os.path.getsize(orig), os.path.getsize(novo)


# NAO MEXER EM width/height DO HTML (licao medida na onda 61):
# eu havia reescrito os atributos com as dimensoes do arquivo novo. O aspecto muda na
# 3a casa (edp: 243/90 = 2,700 contra 3426/1263 = 2,712), e numa fileira CENTRADA isso
# redistribui todos os itens por fracoes de pixel — o diff acusou mudanca de
# antialiasing em 7 logos que eu nunca toquei. Os atributos sao dica de PROPORCAO, nao
# precisam casar com os pixels do arquivo: mantendo os originais, o layout fica
# bit-identico e so muda o pixel dos logos realmente trocados.

def main(raiz):
    pub = resolve_public(raiz)
    trocas = {}
    total_antes = total_depois = 0
    for rel, lado, qual in ALVOS:
        r = converte(pub, rel, lado, qual)
        if not r:
            print("  ausente: %s" % rel)
            continue
        novo_rel, dim, antes, depois = r
        trocas[rel] = (novo_rel, dim)
        total_antes += antes
        total_depois += depois
        print("%-52s %6.1f KB -> %5.1f KB  %s" % (rel.split("/")[-1], antes / 1024.0,
                                                  depois / 1024.0, "%dx%d" % dim))
    # variantes: mesma regra do arquivo-base de mesmo nome
    base = {os.path.basename(k): v for k, v in ((a[0], (a[1], a[2])) for a in ALVOS)}
    for rel in EXTRA:
        nome = os.path.basename(rel)
        chave = nome.replace("-232x239-1", "")
        if chave not in base:
            continue
        lado, qual = base[chave]
        r = converte(pub, rel, lado, qual)
        if r:
            novo_rel, dim, antes, depois = r
            trocas[rel] = (novo_rel, dim)
            total_antes += antes
            total_depois += depois
            print("%-52s %6.1f KB -> %5.1f KB  %s" % (nome, antes / 1024.0,
                                                      depois / 1024.0, "%dx%d" % dim))

    # reescreve as referencias no HTML (width/height ficam como estao)
    tocados = 0
    for dp, _d, fs in os.walk(pub):
        if os.sep + ".git" in dp:
            continue
        for nome in fs:
            if not nome.endswith(".html"):
                continue
            fp = os.path.join(dp, nome)
            with io.open(fp, encoding="utf-8") as f:
                h = f.read()
            o = h
            for antigo_rel, (novo_rel, dim) in trocas.items():
                esc_antigo = antigo_rel.replace("/", chr(92) + "/")
                # o guarda testa AS DUAS formas. Testando so a normal, as paginas cujo
                # unico resto era o JSON-LD escapado eram puladas antes da troca.
                if antigo_rel not in h and esc_antigo not in h:
                    continue
                # duas formas: o caminho normal e o ESCAPADO do JSON-LD do Yoast
                # ("\/wp-content\/uploads\/..."), que um replace simples nao pega.
                # Sem isto o schema seguia apontando para o PNG enquanto a pagina
                # mostrava o WebP — e o PNG ficava preso no espelho so por causa disso.
                h = h.replace(antigo_rel, novo_rel)
                h = h.replace(esc_antigo, novo_rel.replace("/", chr(92) + "/"))
            if h != o:
                with io.open(fp, "w", encoding="utf-8", newline="") as f:
                    f.write(h)
                tocados += 1
    print("-" * 66)
    print("%d arquivo(s) convertido(s): %.0f KB -> %.0f KB (economia de %.0f KB)"
          % (len(trocas), total_antes / 1024.0, total_depois / 1024.0,
             (total_antes - total_depois) / 1024.0))
    print("%d pagina(s) com referencia reescrita" % tocados)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
