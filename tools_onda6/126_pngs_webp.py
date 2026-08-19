# -*- coding: utf-8 -*-
r"""126_pngs_webp.py — os PNG pesados do espelho viram WebP, na MESMA dimensao.

    python tools_onda6/126_pngs_webp.py <raiz-que-contem-public> [--check] [--limite=N]

Idempotente: rodar 2x reporta 0 mudancas.

PEDIDO (Mario, 18/08/2026): "vamos atacar os pngs."

ESCOPO MEDIDO (tools_onda6/qa/medir_imagens.py), nao estimado:
    169 imagens acima de 120 KB somam 51,1 MB
    159 delas sao PNG e somam 47,4 MB   <- este script
     10 sao JPEG e somam  3,7 MB        <- FORA: JPEG ja comprimido corta so 17-42%

A DECISAO QUE DEFINE ESTE SCRIPT: **so troca de formato, nunca de dimensao.**
------------------------------------------------------------------------
A onda 61 gerou os rasters a "3x o exibido" e a largura renderizada do logo da EDP
caiu de 81,38 para 81,00 px -- porque **depois do load quem define a caixa e o
aspecto real do arquivo**, nao os atributos width/height do HTML. Como a fileira
era centrada, os 0,38 px se redistribuiram e 7 logos intocados mudaram de
antialiasing. Mantendo a dimensao IDENTICA, essa classe de bug **nao pode
acontecer** -- nao e cuidado, e impossibilidade. O ganho continua sendo 93-97%,
porque o que pesa no PNG e a codificacao, nao o tamanho.

Tambem NAO deduplica: converter ja derruba as copias identicas de ~7,7 MB para
~0,4 MB, e mexer em familia de `srcset` para economizar 0,4 MB seria risco sem
premio. Duplicata fica registrada em docs/BACKLOG-TECNICO.md.

QUALIDADE
---------
`QUALIDADE = 86`. Medido convertendo e pesando: as pesadas caem 93-97%. Imagem com
transparencia mantem o canal alfa (WebP suporta).

REFERENCIAS
-----------
Reescreve em .html/.css/.js/.xml/.json, na forma normal E na forma com barras
ESCAPADAS (`2024\/03\/foo.png`), que e como o JSON-LD do Yoast escreve URL --
testar so a forma normal foi o que fez o script da onda 61 dizer "0 paginas
reescritas" com a referencia ainda no lugar (licao da 61b). O PNG so e apagado
depois que NENHUMA das formas sobra em lugar nenhum.
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
    raise SystemExit("precisa do Pillow (pip install Pillow)")

PISO = 120 * 1024
QUALIDADE = 86
TEXTO = (".html", ".css", ".js", ".xml", ".txt", ".json")


def formas(rel):
    """Toda forma em que uma referencia a `rel` pode aparecer no texto."""
    return [rel, "/" + rel, "/mirow-site/" + rel,
            rel.replace("/", "\\/"), ("/" + rel).replace("/", "\\/")]


def carregar_textos(pub):
    d = {}
    for dp, _sub, fs in os.walk(pub):
        if os.sep + ".git" in dp:
            continue
        for nome in fs:
            if nome.endswith(TEXTO):
                fp = os.path.join(dp, nome)
                with io.open(fp, encoding="utf-8", errors="ignore") as f:
                    d[fp] = f.read()
    return d


def referenciados(textos):
    """Caminhos de imagem que aparecem no texto, resolvidos para rel-de-public.

    Le o TAG inteiro nao importa: aqui basta o conjunto de caminhos citados, e
    todo `srcset` cita cada variante explicitamente."""
    # LINEAR: acha a extensao e caminha para tras. Regex de classe negada
    # non-greedy (`[^...]+?\.png`) NAO TERMINA sobre o bundle-js.js minificado de
    # 1,5 MB -- ja custou uma medicao de 30 min hoje, e eu repeti aqui.
    achados = set()
    PARA = set(' "\'(),\\\n\t{}[];=|<>')   # sem ':' — ele parte "https://host/..."
    fim = re.compile(r'\.png(?![a-z0-9])', re.I)
    for txt in textos.values():
        t = txt.replace("\\/", "/")
        for m in fim.finditer(t):
            i, j = m.start(), m.end()
            while i > 0 and t[i - 1] not in PARA:
                i -= 1
            ref = t[i:j].split("?")[0]
            if not ref or ref.startswith("."):
                continue
            if ref.startswith("/mirow-site/"):
                ref = ref[len("/mirow-site/"):]
            elif ref.startswith("http"):
                mm = re.match(r'https?://[^/]+/(.*)$', ref)
                if not mm:
                    continue
                ref = mm.group(1)
                if ref.startswith("mirow-site/"):
                    ref = ref[len("mirow-site/"):]
            achados.add(ref.lstrip("/"))
    return achados


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    check = "--check" in sys.argv
    limite = None
    for a in sys.argv:
        if a.startswith("--limite="):
            limite = int(a.split("=", 1)[1])
    pub = resolve_public(sys.argv[1])

    textos = carregar_textos(pub)
    citados = referenciados(textos)

    alvos = []
    for rel in sorted(citados):
        fp = os.path.join(pub, rel.replace("/", os.sep))
        if os.path.exists(fp) and os.path.getsize(fp) > PISO:
            alvos.append((os.path.getsize(fp), rel))
    alvos.sort(reverse=True)
    if limite:
        alvos = alvos[:limite]

    if not alvos:
        print("0 mudanca(s) -- nenhum PNG referenciado acima de %d KB" % (PISO // 1024))
        return

    print("%d PNG(s) alvo, %.1f MB" % (len(alvos), sum(t for t, _ in alvos) / 1048576.0))
    if check:
        for t, rel in alvos[:12]:
            print("  %8.0f KB  %s" % (t / 1024.0, rel))
        print("[--check] nada gravado")
        return

    antes = depois = 0
    convertidos = 0
    tocados = {}
    for tam, rel in alvos:
        fp = os.path.join(pub, rel.replace("/", os.sep))
        rel_webp = rel[:-4] + ".webp"
        fp_webp = os.path.join(pub, rel_webp.replace("/", os.sep))

        if not os.path.exists(fp_webp):
            im = Image.open(fp)
            # preserva alfa; RGBA e P-com-transparencia viram RGBA, o resto RGB
            if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                im = im.convert("RGBA")
            else:
                im = im.convert("RGB")
            # SEM resize: a dimensao e exatamente a mesma do PNG
            im.save(fp_webp, "WEBP", quality=QUALIDADE, method=6)

        # reescreve referencias, nas duas formas
        pares = list(zip(formas(rel), formas(rel_webp)))
        for caminho in list(textos):
            t = textos[caminho]
            novo = t
            for de, para in pares:
                if de in novo:
                    novo = novo.replace(de, para)
            if novo != t:
                textos[caminho] = novo
                tocados[caminho] = novo

        antes += tam
        depois += os.path.getsize(fp_webp)
        convertidos += 1

    for caminho, conteudo in tocados.items():
        with io.open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(conteudo)

    # so agora apaga o PNG, e so se nenhuma forma sobrou em lugar nenhum
    apagados = 0
    tudo = "\n".join(textos.values())
    for _tam, rel in alvos:
        fp = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(fp):
            continue
        if any(f in tudo for f in formas(rel)):
            print("  ! ainda referenciado, nao apago: %s" % rel)
            continue
        os.remove(fp)
        apagados += 1

    print("%d convertido(s), %d PNG removido(s), %d arquivo(s) de texto reescrito(s)"
          % (convertidos, apagados, len(tocados)))
    print("%.1f MB -> %.1f MB  (corte de %.1f MB, %.0f%%)"
          % (antes / 1048576.0, depois / 1048576.0,
             (antes - depois) / 1048576.0, 100.0 * (1 - depois / float(antes))))


if __name__ == "__main__":
    main()
