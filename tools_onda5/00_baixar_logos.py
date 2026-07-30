# -*- coding: utf-8 -*-
"""
00_baixar_logos.py — baixa os logos oficiais dos 15 clientes para o espelho estatico.

Uso:  python tools_onda5/00_baixar_logos.py <raiz-da-arvore>
      (raiz = pasta que contem `public/`, ou a propria `public/`)

Idempotente: nao rebaixa arquivo que ja existe com tamanho > 0.
Destino: public/wp-content/uploads/2026/07/clientes/<slug>.<ext>
Fontes registradas em tools_onda5/logos-fontes.md
"""
import os
import sys
import urllib.request

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 MirowMarketingBot/1.0",
    "Accept": "image/svg+xml,image/png,image/jpeg,*/*;q=0.8",
    "Accept-Encoding": "identity",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

# (slug, url, extensao)
LOGOS = [
    ("mercedes-benz", "https://upload.wikimedia.org/wikipedia/commons/9/9e/Mercedes-Benz_Logo_2010.svg", "svg"),
    ("ipiranga", "https://upload.wikimedia.org/wikipedia/commons/3/38/Ipiranga_logo_%282023%29.svg", "svg"),
    ("wilson-sons", "https://wilsonsons.com.br/wp-content/themes/wilsonsons_2021/assets/images/logo.svg", "svg"),
    ("taesa", "https://ri.taesa.com.br/wp-content/themes/ri-taesa/imgs/logo-taesa.png", "png"),
    ("dexco", "https://upload.wikimedia.org/wikipedia/commons/c/c4/Logotipo_da_Dexco.svg", "svg"),
    ("eneva", "https://upload.wikimedia.org/wikipedia/commons/7/73/Logotipo_da_Eneva.svg", "svg"),
    ("klabin", "https://upload.wikimedia.org/wikipedia/commons/1/10/Klabin.svg", "svg"),
    ("edp", "https://upload.wikimedia.org/wikipedia/commons/d/d2/EDP_2022.svg", "svg"),
    ("energisa", "https://upload.wikimedia.org/wikipedia/commons/8/89/Energisa.svg", "svg"),
    ("suzano", "https://upload.wikimedia.org/wikipedia/commons/4/42/Logotipo_da_Suzano_%282019%29.svg", "svg"),
    ("xp", "https://upload.wikimedia.org/wikipedia/commons/b/b2/XP_Inc._Logo.svg", "svg"),
    ("yara", "https://upload.wikimedia.org/wikipedia/commons/4/42/Yara_logo.svg", "svg"),
    ("santos-brasil", "https://upload.wikimedia.org/wikipedia/commons/c/c3/Logo_da_Santos_Brasil.jpg", "jpg"),
    ("sulamerica", "https://upload.wikimedia.org/wikipedia/commons/0/01/Logotipo_da_SulAm%C3%A9rica.svg", "svg"),
    ("volkswagen", "https://upload.wikimedia.org/wikipedia/commons/6/6d/Volkswagen_logo_2019.svg", "svg"),
]


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def normalizar_svg(path):
    """Garante width/height numericos no <svg> raiz (senao o img renderiza 0x0).

    Alguns logos oficiais vem so com viewBox (ou width/height="100%"), o que faz o
    <img> colapsar dentro de um container flex. Idempotente.
    """
    import re
    with open(path, encoding="utf-8", errors="replace") as f:
        s = f.read()
    m = re.search(r"<svg\b[^>]*>", s)
    if not m:
        return False
    tag = m.group(0)
    tem_w = re.search(r'\swidth="(\d+(?:\.\d+)?)(?:px)?"', tag)
    tem_h = re.search(r'\sheight="(\d+(?:\.\d+)?)(?:px)?"', tag)
    if tem_w and tem_h:
        return False
    vb = re.search(r'viewBox="\s*[-\d.]+[,\s]+[-\d.]+[,\s]+([\d.]+)[,\s]+([\d.]+)', tag)
    if not vb:
        return False
    w, h = vb.group(1), vb.group(2)
    novo = re.sub(r'\s(?:width|height)="[^"]*"', "", tag)
    novo = novo[:4] + ' width="%s" height="%s"' % (w, h) + novo[4:]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s[:m.start()] + novo + s[m.end():])
    return True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    dest = os.path.join(pub, "wp-content", "uploads", "2026", "07", "clientes")
    os.makedirs(dest, exist_ok=True)
    baixados, mantidos, erros = 0, 0, []
    for slug, url, ext in LOGOS:
        path = os.path.join(dest, "%s.%s" % (slug, ext))
        if os.path.exists(path) and os.path.getsize(path) > 0:
            mantidos += 1
            continue
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
            if not data:
                raise IOError("resposta vazia")
            with open(path, "wb") as f:
                f.write(data)
            baixados += 1
            print("baixado: %s.%s (%d bytes)" % (slug, ext, len(data)))
        except Exception as exc:  # noqa: BLE001
            erros.append((slug, str(exc)))
            print("ERRO %s: %s" % (slug, exc))
    norm = 0
    for slug, _url, ext in LOGOS:
        path = os.path.join(dest, "%s.%s" % (slug, ext))
        if ext == "svg" and os.path.exists(path) and normalizar_svg(path):
            norm += 1
            print("svg normalizado (width/height): %s.svg" % slug)

    print("\nresumo: %d baixados, %d ja existiam, %d svg normalizados, %d erros"
          % (baixados, mantidos, norm, len(erros)))
    if erros:
        sys.exit(1)


if __name__ == "__main__":
    main()
