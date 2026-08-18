# -*- coding: utf-8 -*-
"""124_videos_orfaos_e_duplicatas.py — tira do espelho os MP4 que ninguem pede
e as copias byte-identicas dos que sao usados.

    python tools_onda6/124_videos_orfaos_e_duplicatas.py <raiz-que-contem-public> [--check]

Idempotente: rodar 2x reporta 0 mudancas.

O achado
--------
Medido em 18/08/2026: o espelho carrega **185 MB de MP4**, e `public/` tem 262 MB
— ou seja ~70% do site e video. A varredura de orfas da onda 61 (e a S160) so
olham extensoes de IMAGEM, entao nada disso foi visto:

    2023/04/video-bg-home.mp4        41,7 MB   0 referencias  -> ORFAO
    2024/04/video-bg-home-1.mp4      22,9 MB   0 referencias  -> ORFAO
    2024/04/video-bg-home-1-1.mp4    22,9 MB   0 referencias  -> ORFAO (copia do -1)
    video-bg-carreiras.mp4           41,6 MB   usado, existe 2x IDENTICO
    video-porque-mirow.mp4            7,1 MB   usado, existe 2x IDENTICO

Nos dois casos de duplicata e a pagina ALEMA que aponta para a copia de 2024/04,
enquanto pt/en apontam para a mais antiga. Consolidar = reescrever a referencia da
pagina alema e apagar a copia. Total: **136 MB**, sem mudar um pixel do que o
visitante ve — nenhum arquivo em uso muda de conteudo.

Por que isso importa mais que peso de disco
-------------------------------------------
Medido AO VIVO em producao: `pt/carreiras/` transfere **44 MB** para abrir, dos
quais **40.530 KB** sao o MP4 (`performance.getEntriesByType('resource')`). O
`<video>` e `autoplay muted loop`, 1280x720, 25,4 s — ~13 Mbps para um loop de
fundo mudo. Recomprimir e a onda seguinte (precisa de ffmpeg, que nao esta na
maquina); ESTE script nao mexe em bitrate, so remove peso morto.

Seguranca
---------
O script NAO confia em levantamento anterior. Antes de apagar qualquer arquivo,
ele varre `public/` inteiro e exige **zero** referencia ao caminho E ao basename;
antes de consolidar uma duplicata, exige que os dois arquivos sejam **byte a byte
identicos** (md5). Se qualquer condicao falhar, ele nao apaga e reporta.

A licao da onda 61b esta aplicada: referencia tambem e procurada na forma com
barras ESCAPADAS (`2024\\/04\\/...`), que e como o JSON-LD do Yoast escreve URL.
Testar so a forma normal foi o que fez o script da 61 dizer "0 paginas reescritas"
com a referencia ainda no lugar.
"""
import hashlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public, ler, gravar

# caminhos relativos a public/, com barra normal
ORFAOS = [
    "wp-content/uploads/2023/04/video-bg-home.mp4",
    "wp-content/uploads/2024/04/video-bg-home-1.mp4",
    "wp-content/uploads/2024/04/video-bg-home-1-1.mp4",
]

# duplicata -> canonica (a canonica e a que MAIS paginas ja pedem)
DUPLICATAS = {
    "wp-content/uploads/2024/04/video-bg-carreiras.mp4":
        "wp-content/uploads/2023/04/video-bg-carreiras.mp4",
    "wp-content/uploads/2024/04/video-porque-mirow.mp4":
        "wp-content/uploads/2023/03/video-porque-mirow.mp4",
}

TEXTO = (".html", ".css", ".js", ".xml", ".txt", ".json")


def md5(caminho):
    h = hashlib.md5()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def arquivos_de_texto(pub):
    for dp, _d, fs in os.walk(pub):
        if os.sep + ".git" in dp:
            continue
        for nome in fs:
            if nome.endswith(TEXTO):
                yield os.path.join(dp, nome)


def formas(rel):
    """Todas as formas em que uma referencia a `rel` pode estar escrita."""
    return [rel, "/" + rel, "/mirow-site/" + rel,
            rel.replace("/", "\\/"), ("/" + rel).replace("/", "\\/")]


def quem_referencia(pub, rel, textos):
    """Arquivos que mencionam o caminho OU o basename. Basename entra de proposito:
    para APAGAR, a duvida pesa contra apagar."""
    base = rel.split("/")[-1]
    alvos = formas(rel) + [base]
    achados = []
    for caminho, conteudo in textos.items():
        if any(a in conteudo for a in alvos):
            achados.append(os.path.relpath(caminho, pub).replace(os.sep, "/"))
    return achados


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    check = "--check" in sys.argv
    pub = resolve_public(sys.argv[1])

    textos = {}
    for caminho in arquivos_de_texto(pub):
        with io.open(caminho, encoding="utf-8", errors="ignore") as f:
            textos[caminho] = f.read()

    mudancas = 0
    liberado = 0

    # ---------- 1) consolidar duplicatas: reescrever referencia, depois apagar ----------
    for dup, canonica in sorted(DUPLICATAS.items()):
        fp_dup = os.path.join(pub, dup.replace("/", os.sep))
        fp_can = os.path.join(pub, canonica.replace("/", os.sep))
        if not os.path.exists(fp_dup):
            continue                                   # ja consolidado
        if not os.path.exists(fp_can):
            print("  ! canonica ausente, nao consolido: %s" % canonica)
            continue
        if md5(fp_dup) != md5(fp_can):
            print("  ! NAO sao identicos, nao consolido: %s" % dup)
            continue

        # reescreve toda forma da referencia, inclusive a de barras escapadas
        pares = list(zip(formas(dup), formas(canonica)))
        for caminho in sorted(textos):
            if not caminho.endswith((".html", ".css", ".js", ".xml", ".json")):
                continue
            antes = textos[caminho]
            depois = antes
            for de, para in pares:
                if de in depois:
                    depois = depois.replace(de, para)
            if depois != antes:
                if not check:
                    gravar(caminho, depois)
                textos[caminho] = depois
                mudancas += 1
                print("  ref reescrita: %s" % os.path.relpath(caminho, pub))

        sobrou = quem_referencia(pub, dup, textos)
        # o basename e o mesmo da canonica, entao o teste de basename sempre acusa;
        # aqui o que importa e o CAMINHO nao aparecer mais em lugar nenhum
        so_caminho = [q for q in sobrou
                      if any(a in textos[os.path.join(pub, q.replace("/", os.sep))]
                             for a in formas(dup))]
        if so_caminho:
            print("  ! ainda referenciado, nao apago: %s (%s)"
                  % (dup, ", ".join(so_caminho[:3])))
            continue
        tam = os.path.getsize(fp_dup)
        if not check:
            os.remove(fp_dup)
        liberado += tam
        mudancas += 1
        print("  duplicata removida: %-58s %6.1f MB" % (dup, tam / 1048576.0))

    # ---------- 2) orfaos: apagar somente com zero referencia ----------
    for rel in ORFAOS:
        fp = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(fp):
            continue                                   # ja removido
        refs = quem_referencia(pub, rel, textos)
        if refs:
            print("  ! tem referencia, NAO apago: %s (%s)" % (rel, ", ".join(refs[:3])))
            continue
        tam = os.path.getsize(fp)
        if not check:
            os.remove(fp)
        liberado += tam
        mudancas += 1
        print("  orfao removido:     %-58s %6.1f MB" % (rel, tam / 1048576.0))

    print("%s%d mudanca(s), %.1f MB liberado(s)"
          % ("[--check] " if check else "", mudancas, liberado / 1048576.0))


if __name__ == "__main__":
    main()
