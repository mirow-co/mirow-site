# -*- coding: utf-8 -*-
"""Prepara o dado geografico dos mapas da Nossa Rede (roda UMA vez, offline).

Uso:
    python tools_onda6/_prep_mapas_ne.py <caminho do ne_110m_admin_0_countries.geojson>

Le o GeoJSON de paises do **Natural Earth 1:110m** (dominio publico, sem exigencia
de atribuicao — naturalearthdata.com/about/terms-of-use) e grava um recorte enxuto
em `tools_onda6/dados/mapas-ne110m.json`, com so o que os dois mapas precisam:
paises que cruzam o recorte das Americas ou da Europa, coordenadas arredondadas a
2 casas (~1 km, mais que suficiente na escala de tela).

Por que um arquivo derivado no repo, e nao o GeoJSON inteiro: o original tem 838 KB
e 177 paises; o recorte fica na casa das dezenas de KB e deixa o gerador
(`88_rede_mapas_reais.py`) reproduzivel sem rede. O SVG que vai para `public/` e
gerado desse recorte.
"""
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(AQUI, "dados", "mapas-ne110m.json")

# recortes (lon_min, lat_min, lon_max, lat_max) — os mesmos do gerador
RECORTES = {
    "americas": (-168.0, -56.0, -33.0, 60.0),
    "europa": (-12.0, 34.0, 33.0, 62.0),
}
MARGEM = 12.0   # graus de folga: pais vizinho que entra de raspao no recorte


def bbox_de(coords, caixa=None):
    for c in coords:
        if isinstance(c[0], (int, float)):
            x, y = c[0], c[1]
            if caixa is None:
                caixa = [x, y, x, y]
            else:
                caixa[0] = min(caixa[0], x)
                caixa[1] = min(caixa[1], y)
                caixa[2] = max(caixa[2], x)
                caixa[3] = max(caixa[3], y)
        else:
            caixa = bbox_de(c, caixa)
    return caixa


def cruza(a, b):
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def aneis(geom):
    """Todos os aneis externos de um Polygon/MultiPolygon (buracos sao ignorados:
    na escala de tela um lago nao muda a leitura e cada anel extra pesa)."""
    t = geom["type"]
    if t == "Polygon":
        return [geom["coordinates"][0]]
    if t == "MultiPolygon":
        return [poli[0] for poli in geom["coordinates"]]
    return []


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    with io.open(sys.argv[1], encoding="utf-8") as f:
        dados = json.load(f)

    caixas = {k: (v[0] - MARGEM, v[1] - MARGEM, v[2] + MARGEM, v[3] + MARGEM)
              for k, v in RECORTES.items()}
    saida = {"fonte": "Natural Earth 1:110m Admin 0 Countries (dominio publico)",
             "paises": {}}
    for feat in dados["features"]:
        nome = feat["properties"].get("NAME") or feat["properties"].get("ADMIN")
        rings = aneis(feat["geometry"])
        if not rings:
            continue
        guardar = []
        for anel in rings:
            cx = bbox_de(anel)
            if not any(cruza(cx, c) for c in caixas.values()):
                continue
            if len(anel) < 4:
                continue
            guardar.append([[round(p[0], 2), round(p[1], 2)] for p in anel])
        if guardar:
            saida["paises"][nome] = guardar

    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with io.open(DESTINO, "w", encoding="utf-8", newline="\n") as f:
        json.dump(saida, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    n_pontos = sum(len(a) for aa in saida["paises"].values() for a in aa)
    print("%s: %d paises, %d aneis, %d pontos, %.0f KB"
          % (os.path.relpath(DESTINO, os.path.dirname(AQUI)),
             len(saida["paises"]),
             sum(len(a) for a in saida["paises"].values()),
             n_pontos, os.path.getsize(DESTINO) / 1024.0))


if __name__ == "__main__":
    main()
