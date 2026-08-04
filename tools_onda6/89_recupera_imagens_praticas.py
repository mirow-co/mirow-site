# -*- coding: utf-8 -*-
"""89 — onda 33, S-119 (#69): recupera as 6 imagens das paginas de pratica.

Uso:
    python tools_onda6/89_recupera_imagens_praticas.py <raiz-que-contem-public> [--dry-run]

Seis paginas de pratica em PT referenciam imagens sob `novo/wp-content/uploads/2023/`
que nunca vieram no espelho — apareciam como imagem quebrada para quem visita. A
assercao E05 as carregava como excecao declarada (`FALTAS_CONHECIDAS`, motivo "S-20").

A issue dava duas saidas: recuperar do WordPress ou remover as `<figure>`. Medido em
04/08: as 6 estao VIVAS no WordPress do dominio, que ainda serve `mirow.com.br` (ver
#100) — HTTP 200, 124 KB a 191 KB. Entao recupera-se o conteudo em vez de apaga-lo.

O mapeamento de caminho e o detalhe que importa: no espelho o prefixo e
`novo/wp-content/...`, no WordPress vivo e `wp-content/...` na raiz do dominio.
O `novo/` e heranca de quando o site novo morava em /novo/ — nao ha pasta `novo/`
no servidor de hoje.

Idempotente: baixa so o que falta no disco; no segundo run reporta 0.

Depende de rede. Se o WordPress sair do ar (cutover da #42) e alguma imagem ainda
faltar, o script avisa e a E05 volta a acusar — que e o comportamento certo: a falha
fica visivel em vez de virar excecao silenciosa.
"""
import io
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public  # noqa: E402

ORIGEM = "https://mirow.com.br/"

# Os 6 caminhos, exatamente como as paginas os referenciam (relativos a public/).
IMAGENS = [
    "novo/wp-content/uploads/2023/04/strategic_ideation_formulation_execution-1.png",
    "novo/wp-content/uploads/2023/05/2-inovacao-modelo-de-negocio-radar-de-tendencias-workshop-ecossistema-1024x503.png",
    "novo/wp-content/uploads/2023/05/3-marketing-vendas-pricing-go-to-market-CX-forca-de-vendas-digital-1024x545.png",
    "novo/wp-content/uploads/2023/05/4-operacoes-supply-chain-SOP-CSC-procurement-estoques-1024x435.png",
    "novo/wp-content/uploads/2023/05/7-transformacao-metodologia-agil-gestao-da-mudanca-governanca-quick-wins-1024x521.png",
    "novo/wp-content/uploads/2023/05/8-adaptacao-climatica-sustentabilidade-net-zero-ESG-descarbonizacao-carbono-1024x552.png",
]

MINIMO = 10 * 1024   # PNG de 1024px abaixo disso e pagina de erro, nao imagem


def url_de(rel):
    """`novo/wp-content/...` no espelho -> `wp-content/...` na raiz do WordPress."""
    assert rel.startswith("novo/")
    return ORIGEM + rel[len("novo/"):]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    dry = "--dry-run" in sys.argv

    baixadas, ja_tinha, falhas = 0, 0, []
    for rel in IMAGENS:
        destino = os.path.join(pub, rel.replace("/", os.sep))
        if os.path.exists(destino) and os.path.getsize(destino) >= MINIMO:
            ja_tinha += 1
            continue
        url = url_de(rel)
        if dry:
            print("    baixaria %s" % url)
            baixadas += 1
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mirow-site/onda33"})
            dados = urllib.request.urlopen(req, timeout=60).read()
        except Exception as e:
            falhas.append((rel, repr(e)))
            continue
        if len(dados) < MINIMO:
            falhas.append((rel, "resposta de %d bytes — pagina de erro, nao imagem"
                           % len(dados)))
            continue
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with io.open(destino, "wb") as f:
            f.write(dados)
        baixadas += 1
        print("    %7d bytes  %s" % (len(dados), rel.split("/")[-1]))

    print("imagens recuperadas: %d | ja no disco: %d | falhas: %d%s"
          % (baixadas, ja_tinha, len(falhas), " (dry-run)" if dry else ""))
    for rel, motivo in falhas:
        print("  FALHA %s: %s" % (rel.split("/")[-1], motivo))
    if falhas:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
