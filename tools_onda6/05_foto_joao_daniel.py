# -*- coding: utf-8 -*-
"""
05_foto_joao_daniel.py — prepara a foto do Joao Daniel Ramos no padrao dos outros lideres.

Uso:  python tools_onda6/05_foto_joao_daniel.py <raiz-da-arvore> [caminho-da-foto-origem]

- Origem padrao: OneDrive 02_People/01_Fotos/Fotos individuais/
  Joao_Daniel_Ramos_2-removebg-preview.png (com acentos no nome real).
- Destino: public/wp-content/uploads/2026/07/joao-daniel-ramos.png
- Tratamento igual ao dos outros lideres do grid: 232x246 px, fundo branco,
  enquadramento de cabeca/ombros alinhado ao topo (mesma proporcao dos PNGs
  Andreas-Mirow.png, Renato-Alvarenga-1.png etc.).
- Idempotente: se o destino ja existe com o tamanho certo, nao refaz.
"""
import os
import sys

LARGURA, ALTURA = 232, 246
DESTINO_REL = "wp-content/uploads/2026/07/joao-daniel-ramos.png"
ORIGEM_PADRAO = os.path.join(
    os.path.expanduser("~"),
    "OneDrive - Mirow", "Mirow & Co", "02_People", "01_Fotos", "Fotos individuais",
    u"João_Daniel_Ramos_2-removebg-preview.png")


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    origem = sys.argv[2] if len(sys.argv) > 2 else ORIGEM_PADRAO
    destino = os.path.join(pub, DESTINO_REL.replace("/", os.sep))

    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Pillow nao instalado: pip install Pillow")

    if os.path.exists(destino):
        with Image.open(destino) as im:
            if im.size == (LARGURA, ALTURA):
                print("foto ja pronta: %s (%dx%d)" % (DESTINO_REL, LARGURA, ALTURA))
                return
    if not os.path.exists(origem):
        raise SystemExit("foto de origem nao encontrada: %s" % origem)

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with Image.open(origem) as src:
        src = src.convert("RGBA")
        fundo = Image.new("RGBA", src.size, (255, 255, 255, 255))
        fundo.alpha_composite(src)
        foto = fundo.convert("RGB")
        # escala pela largura e alinha no topo (cabeca em cima, como nos outros)
        nova_alt = max(1, int(round(foto.height * LARGURA / float(foto.width))))
        foto = foto.resize((LARGURA, nova_alt), Image.LANCZOS)
        tela = Image.new("RGB", (LARGURA, ALTURA), (255, 255, 255))
        if nova_alt >= ALTURA:
            tela.paste(foto.crop((0, 0, LARGURA, ALTURA)), (0, 0))
        else:
            tela.paste(foto, (0, 0))
        tela.save(destino, "PNG", optimize=True)
    print("foto escrita: %s (%dx%d)" % (DESTINO_REL, LARGURA, ALTURA))


if __name__ == "__main__":
    main()
