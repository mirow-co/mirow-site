# -*- coding: utf-8 -*-
r"""125_video_carreiras_comprimido.py — recomprime o video de fundo de carreiras.

    python tools_onda6/125_video_carreiras_comprimido.py <raiz-que-contem-public> [--check]

Idempotente: se o arquivo ja esta abaixo do teto de bitrate, reporta 0 mudancas.

PEDIDO (Mario, 18/08/2026): "me deixe com o video comprimido na pagina, apenas."
Decisao dele depois de ver a alternativa em SVG animado e recusar ("ficou muito ruim
e infantil"). Entao NAO se troca o que aparece na pagina -- so o peso do arquivo.

O PROBLEMA, MEDIDO AO VIVO ANTES DE MEXER
-----------------------------------------
`pt/carreiras/` transferia **44 MB** para abrir, dos quais **40.530 KB** eram o MP4
(`performance.getEntriesByType('resource')`, campo transferSize). O arquivo estava
a **13.115 kb/s** para 1280x720 / 25,4 s, e **nao tem trilha de audio** -- ou seja,
~10x o necessario para um loop de fundo mudo atras de um overlay navy.

A ESCOLHA DO ALVO, MEDIDA E NAO ESTIMADA
----------------------------------------
Transcodificado e pesado, com SSIM contra o original quadro a quadro no mesmo
instante (a comparacao de video inteiro deu numero incoerente por dessincronia de
quadros -- 344 x 314 -- e foi descartada):

    CRF 26  ->  4,26 MB  (-89%)  SSIM 0,94   <- escolhido, e o que o Mario aprovou
    CRF 30  ->  2,73 MB  (-93%)  SSIM 0,91
    VP9 36  ->  2,91 MB  (-93%)

FERRAMENTA
----------
`ffmpeg` nao esta instalado na maquina. Este script usa o binario estatico do
pacote `imageio-ffmpeg` (pip install imageio-ffmpeg), que instala em nivel de
usuario e nao precisa de admin.
"""
import io
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public

ALVO = "wp-content/uploads/2023/04/video-bg-carreiras.mp4"
TETO_KBPS = 3000          # acima disto, recomprime; abaixo, ja esta feito
CRF = "26"


def ffmpeg():
    try:
        import imageio_ffmpeg
    except ImportError:
        raise SystemExit("precisa do binario: pip install imageio-ffmpeg")
    return imageio_ffmpeg.get_ffmpeg_exe()


def bitrate_kbps(exe, caminho):
    saida = subprocess.run([exe, "-hide_banner", "-i", caminho],
                           stderr=subprocess.PIPE, stdout=subprocess.PIPE).stderr
    m = re.search(rb"bitrate: (\d+) kb/s", saida)
    return int(m.group(1)) if m else None


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    check = "--check" in sys.argv
    pub = resolve_public(sys.argv[1])
    fp = os.path.join(pub, ALVO.replace("/", os.sep))
    if not os.path.exists(fp):
        raise SystemExit("nao achei %s" % ALVO)

    exe = ffmpeg()
    antes_bytes = os.path.getsize(fp)
    antes_kbps = bitrate_kbps(exe, fp)
    print("hoje: %.1f MB, %s kb/s" % (antes_bytes / 1048576.0, antes_kbps))

    if antes_kbps is not None and antes_kbps <= TETO_KBPS:
        print("0 mudanca(s) -- ja esta sob o teto de %d kb/s" % TETO_KBPS)
        return
    if check:
        print("[--check] recomprimiria para CRF %s" % CRF)
        return

    tmp = fp + ".novo.mp4"
    cmd = [exe, "-hide_banner", "-loglevel", "error", "-y", "-i", fp,
           "-an",                              # nao ha audio; explicito de proposito
           "-c:v", "libx264", "-crf", CRF, "-preset", "slow",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp]
    subprocess.check_call(cmd)

    # confere o que gravou ANTES de trocar: arquivo ilegivel ou vazio nao entra
    depois_bytes = os.path.getsize(tmp)
    depois_kbps = bitrate_kbps(exe, tmp)
    if depois_bytes < 100000 or depois_kbps is None or depois_kbps > antes_kbps:
        os.remove(tmp)
        raise SystemExit("recompressao suspeita (%d bytes, %s kb/s) -- nao troquei"
                         % (depois_bytes, depois_kbps))

    os.remove(fp)
    os.rename(tmp, fp)
    print("agora: %.1f MB, %s kb/s  (corte de %.1f MB, %.0f%%)"
          % (depois_bytes / 1048576.0, depois_kbps,
             (antes_bytes - depois_bytes) / 1048576.0,
             100.0 * (1 - depois_bytes / float(antes_bytes))))
    print("1 mudanca")


if __name__ == "__main__":
    main()
