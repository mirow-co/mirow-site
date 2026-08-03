"""Troca o gtag inline do espelho do WordPress pelo script de medicao compartilhado.

Idempotente: rodar N vezes tem o mesmo efeito de rodar uma. Rodar de novo depois de
qualquer novo lote de paginas vindas do dump.

    python tools/ga4_tag.py           # aplica
    python tools/ga4_tag.py --check   # so relata, nao escreve

Contexto: o GitHub Pages publica public/, nao o dist/ do Astro, entao a medicao das
paginas no ar precisa estar no HTML de public/. Ver issue mirow-marketing#3 e o
cabecalho de public/assets/mirow-analytics.js.
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUBLIC = RAIZ / "public"
BASE = "/mirow-site"  # vira "" na virada de dominio (issue #42)

# Bloco gtag inline que veio no espelho do mirow.com.br (identico nos 272 arquivos).
GTAG_INLINE = re.compile(
    r"[ \t]*<!-- Google tag \(gtag\.js\) -->\s*"
    r"<script async src=\"https://www\.googletagmanager\.com/gtag/js\?id=G-[A-Z0-9]+\"></script>\s*"
    r"<script>.*?gtag\('config', 'G-[A-Z0-9]+'\);\s*</script>\s*",
    re.S,
)

MARCA = "assets/mirow-analytics.js"

BLOCO = (
    "  <!-- Medicao Mirow (GA4) - issue mirow-marketing#3. Config e eventos em "
    f"{BASE}/{MARCA} -->\n"
    f'  <script src="{BASE}/{MARCA}"></script>\n'
    '  <script async src="https://www.googletagmanager.com/gtag/js?id=G-VK4QHHHS5X"></script>\n'
)


def main() -> int:
    check = "--check" in sys.argv
    arquivos = sorted(PUBLIC.rglob("*.html"))
    if not arquivos:
        print(f"nenhum .html em {PUBLIC}")
        return 1

    trocados = ja_ok = sem_gtag = redirect = 0
    problemas = []

    for f in arquivos:
        s = f.read_text(encoding="utf-8", errors="strict")

        if MARCA in s:
            ja_ok += 1
            continue

        # Stub de redirecionamento (meta refresh): o navegador sai antes de qualquer
        # medicao valer, e o pageview seria contado na pagina de destino. Fica de fora.
        if re.search(r'<meta\s+http-equiv=["\']refresh["\']', s, re.I) and "<head" not in s.lower():
            redirect += 1
            continue

        # Remove o bloco inline e reinsere a medicao logo depois do <meta charset>.
        # Ordem importa: o charset tem que continuar dentro dos primeiros 1024 bytes,
        # senao o navegador pode decidir a codificacao antes de ler a declaracao.
        novo, n = GTAG_INLINE.subn("", s, count=1)
        ancora = re.search(r"<meta[^>]+charset[^>]*>", novo, re.I) or re.search(r"<head[^>]*>", novo, re.I)
        if not ancora:
            problemas.append(f"{f.relative_to(RAIZ)}: sem <head> nem <meta charset>")
            continue
        novo = novo[: ancora.end()] + "\n" + BLOCO.rstrip("\n") + novo[ancora.end():]
        if n:
            trocados += 1
        else:
            sem_gtag += 1

        if not check:
            f.write_text(novo, encoding="utf-8")

    print(f"arquivos .html:        {len(arquivos)}")
    print(f"gtag inline trocado:   {trocados}")
    print(f"sem gtag, injetado:    {sem_gtag}")
    print(f"ja tinham a marca:     {ja_ok}")
    print(f"stub de redirect:      {redirect}")
    if problemas:
        print(f"problemas:             {len(problemas)}")
        for p in problemas[:10]:
            print(f"  - {p}")
    if check:
        print("\n(--check: nada foi escrito)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
