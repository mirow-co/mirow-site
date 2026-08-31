# -*- coding: utf-8 -*-
"""Onda 75: a materia da IstoE Dinheiro morreu, e o link vai para o arquivo.

Medido em 31/08/2026, tres vezes e por dois caminhos: a URL responde 301 e o
destino do 301 responde 404. O dominio esta VIVO (raiz 200), entao nao e queda
de servidor -- a materia saiu do ar. O Wayback Machine tem snapshot de
06/12/2023, e e para la que o link passa a apontar.

Por que arquivo em vez de remover a linha: a materia EXISTIU e faz parte do
levantamento de imprensa; remove-la reescreveria o historico. E o R9 aplicado ao
link ("URLs morrem; PDFs ficam") -- aqui, o snapshot faz o papel do PDF.

CUIDADO -- este script conserta o ARTEFATO, nao a fonte. O mestre das materias
vive no repo privado (08_Site/2026-08-19_imprensa-materias-curadoria.json) e o
`tools/gen_imprensa.py` regenera as 3 paginas a partir dele. Enquanto o mestre
nao for corrigido la, o proximo gen_imprensa TRAZ A URL MORTA DE VOLTA. A S179
existe para gritar quando isso acontecer.

Nao mexido de proposito: as duas materias da epbr. As duas dao 522, mas a RAIZ
do dominio tambem da 522 -- e o site que esta fora do ar, nao o link. Reconferir
depois.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_css = __import__("_onda7_css")
ler, gravar = _css.ler, _css.gravar

MORTA = "https://istoedinheiro.com.br/com-white-martins-brasil-entra-na-trilha-do-hidrogenio-verde/"
ARQUIVO = ("https://web.archive.org/web/20231206004028/"
           "https://istoedinheiro.com.br/com-white-martins-brasil-entra-na-trilha-do-hidrogenio-verde/")


def main(raiz):
    raiz = os.path.abspath(raiz)
    mudados = 0
    for base, _dirs, arquivos in os.walk(os.path.join(raiz, "public")):
        for arq in arquivos:
            if not arq.endswith(".html"):
                continue
            p = os.path.join(base, arq)
            h = ler(p)
            # ATENCAO: ARQUIVO CONTEM MORTA como substring (o Wayback prefixa a URL
            # original). Um replace cego re-embrulha o link a cada execucao -- a 1a
            # versao deste script fez exatamente isso, e a 2a run gerou
            # `web/.../https://web.archive.org/web/.../https://istoedinheiro...`.
            # Por isso o guarda: se ja esta arquivado, nao mexe.
            if MORTA in h and ARQUIVO not in h:
                gravar(p, h.replace(MORTA, ARQUIVO))
                mudados += 1
                print(u"  %s" % os.path.relpath(p, raiz).replace(os.sep, "/"))
    # o JSON que a suite le tambem carrega a URL
    pj = os.path.join(raiz, "tools", "imprensa-publicada.json")
    d = json.load(io.open(pj, encoding="utf-8"))
    n = 0
    for m in d:
        if m.get("url") == MORTA:
            m["url"] = ARQUIVO
            n += 1
    if n:
        io.open(pj, "w", encoding="utf-8", newline="").write(
            json.dumps(d, ensure_ascii=False, indent=2) + u"\n")
        print(u"  tools/imprensa-publicada.json (%d)" % n)
    print(u"149: %d pagina(s) + %d entrada(s) no JSON" % (mudados, n))
    return mudados + n


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
