# -*- coding: utf-8 -*-
"""Onda 42 / S-138 (issue mirow-marketing#191): a barra de navegação do rodapé
sai do site.

Pedido do Mario (06/08): "me falaram para aposentar a barra inferior da
página ... gostei da ideia". Com a barra superior fixa (S-137), o clone do
rodapé perdeu a função — era o atalho de navegação de quem chegava ao fim da
página.

Remove o bloco <!-- onda15:rodape-barra --> ... <!-- /onda15:rodape-barra -->
de toda página de conteúdo. A linha legal (política de privacidade) fica.
A asserção S36 (clone idêntico byte a byte) é aposentada junto — decisão
explícita do Mario, registrada na #191.

Uso: python tools_onda6/100_aposentar_rodape_barra.py <raiz>
"""
import os
import re
import sys

from _onda7_css import resolve_public, ler, gravar

INI = "<!-- onda15:rodape-barra -->"
FIM = "<!-- /onda15:rodape-barra -->"
REX = re.compile(re.escape(INI) + r".*?" + re.escape(FIM), re.S)


def main(root):
    pub = resolve_public(root)
    mudadas = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            p = os.path.join(dirpath, nome)
            h = ler(p)
            if INI not in h:
                continue
            novo = REX.sub("<!-- onda42:rodape-barra-aposentada (#191) -->", h)
            gravar(p, novo)
            mudadas += 1
    print("%d pagina(s) sem a barra do rodape" % mudadas)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
