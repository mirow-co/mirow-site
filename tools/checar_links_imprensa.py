# -*- coding: utf-8 -*-
"""Confere, ao vivo, se cada materia do levantamento de imprensa ainda abre.

    python tools/checar_links_imprensa.py .

NAO entra no gate do deploy, e de proposito: exige rede, e o resultado depende do
servidor do veiculo naquele minuto. Rodar de vez em quando (trimestral) ou quando
alguem reclamar de link quebrado.

Como ler a saida:
  200/202        vivo
  401/403        vivo, mas bloqueia robo (Reuters, The Economist). NAO e link morto.
  404/410        materia saiu do ar -> arquivar no Wayback (ver 149_imprensa_link_morto.py)
  000/5xx        servidor fora do ar AGORA. Conferir a RAIZ do dominio antes de
                 concluir qualquer coisa: em 31/08/2026 as duas materias da epbr
                 deram 522 e a raiz tambem -- era o site inteiro, nao o link.
"""
import io
import json
import os
import subprocess
import sys

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
VIVOS = ("200", "202", "401", "403")


def codigo(url):
    p = subprocess.run(["curl", "-sSL", "-o", os.devnull, "-w", "%{http_code}",
                        "--max-time", "25", "-A", UA, url], capture_output=True)
    return p.stdout.decode().strip() or "000"


def main(raiz):
    pj = os.path.join(os.path.abspath(raiz), "tools", "imprensa-publicada.json")
    materias = json.load(io.open(pj, encoding="utf-8"))
    suspeitas, dominios = [], {}
    for i, m in enumerate(materias, 1):
        c = codigo(m["url"])
        marca = "ok " if c in VIVOS else "!! "
        print(u"%s%2d/%d  %s  %-22s %s" % (marca, i, len(materias), c,
                                           m["veiculo"][:22], m["url"][:60]))
        if c not in VIVOS:
            suspeitas.append((c, m))
    print(u"\n%d de %d fora do esperado" % (len(suspeitas), len(materias)))
    for c, m in suspeitas:
        dom = m["url"].split("/")[2]
        if dom not in dominios:
            dominios[dom] = codigo("https://%s/" % dom)
        veredito = ("o DOMINIO tambem esta fora (%s) -- provavel queda de servidor"
                    % dominios[dom]) if dominios[dom] not in VIVOS else \
                   "o dominio responde -- e a MATERIA que saiu do ar"
        print(u"  %s %s | %s\n     %s" % (c, m["veiculo"], veredito, m["url"]))
    return 1 if any(c in ("404", "410") for c, _ in suspeitas) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
