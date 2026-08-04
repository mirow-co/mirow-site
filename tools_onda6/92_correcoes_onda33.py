# -*- coding: utf-8 -*-
"""92 — onda 33b, S-123 e S-124: dois achados da propria onda 33.

Uso:
    python tools_onda6/92_correcoes_onda33.py <raiz-que-contem-public> [--dry-run]

S-123 — o asset de medicao 404a em 125 stubs
    Os stubs da S-107 referenciam a medicao como `/wp-content/uploads/...` — SEM o
    prefixo `/mirow-site/`. No GitHub Pages isso e 404: a medicao nunca carrega
    naquelas 125 paginas. A assercao M01 passa do mesmo jeito porque procura o NOME
    do arquivo na string, nao o caminho resolvido.

    Causa: o `base_prefix()` do helper deduz o prefixo de uma referencia a
    wp-content na propria pagina — e o stub minimo, por definicao, nao tem nenhuma.
    Quem escreveu o stub herdou o prefixo vazio.

    (Achado ao escrever os 28 stubs da S-118 nesta mesma onda, que ja nasceram com o
    prefixo certo. E da frente de medicao, mas e uma troca de string de uma linha e o
    conserto nao muda politica nenhuma — so faz o que ja estava escrito funcionar.)

S-124 — hreflang das paginas de imprensa aponta para a politica de privacidade
    A S-106 (onda 29) criou `en/press/` e `de/presse/` a partir do molde de outra
    pagina e o bloco de hreflang veio junto: as duas declaram como suas alternativas
    `pt/politica-de-privacidade/`, `en/privacy-policy/` e `de/datenschutzrichtlinie/`.
    E `pt/imprensa/` nao tem hreflang nenhum.

    Ou seja: o Google recebe que a pagina de imprensa em ingles e a versao inglesa da
    politica de privacidade. As tres passam a se apontar entre si.

    NAO e verdade que o site nao tem hreflang: 106 das 113 paginas de conteudo tem, e
    corretamente. Das 7 sem, 4 sao artigos so em PT (sem traducao, entao sem
    alternativa a declarar — esta certo assim), 1 e a `en/homepage` (duplicata, decisao
    aberta na #65) e 2 sao as de imprensa que este script conserta.

Idempotente: os dois passos so trocam o que esta errado; no segundo run reporta 0.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

PREFIXO = "/mirow-site/"

# S-123: o src errado -> o certo. Restrito ao asset de medicao para nao tocar em
# mais nada por acidente.
MEDICAO_ERRADA = '<script src="/wp-content/uploads/2026/07/onda6/onda31-medicao.js'
MEDICAO_CERTA = '<script src="%swp-content/uploads/2026/07/onda6/onda31-medicao.js' % PREFIXO

# S-124: as tres paginas de imprensa, por idioma.
IMPRENSA = [("pt", "pt/imprensa/"), ("en", "en/press/"), ("de", "de/presse/")]

BLOCO_HREFLANG = "".join(
    '<link rel="alternate" href="%s%s" hreflang="%s" />\n' % (PREFIXO, caminho, lang)
    for lang, caminho in IMPRENSA)


def corrige_medicao(pub, dry):
    n = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if not nome.endswith(".html"):
                continue
            p = os.path.join(dirpath, nome)
            h = ler(p)
            if MEDICAO_ERRADA not in h:
                continue
            novo = h.replace(MEDICAO_ERRADA, MEDICAO_CERTA)
            n += 1
            if not dry:
                gravar(p, novo)
    print("S-123 medicao com prefixo corrigido em %d pagina(s)%s"
          % (n, " (dry-run)" if dry else ""))


def corrige_hreflang(pub, dry):
    # remove qualquer hreflang existente das 3 paginas e escreve o bloco certo,
    # logo antes do </head> — assim vale tanto para quem tinha errado quanto para
    # quem nao tinha nenhum.
    rex = re.compile(r'[ \t]*<link rel="alternate" href="[^"]*" hreflang="[^"]*"[^>]*>'
                     r'[ \t]*\r?\n?')
    n = 0
    for _lang, caminho in IMPRENSA:
        p = os.path.join(pub, caminho.replace("/", os.sep), "index.html")
        if not os.path.exists(p):
            print("  AVISO: %s nao existe" % caminho)
            continue
        h = ler(p)
        limpo = rex.sub("", h)
        if BLOCO_HREFLANG in limpo:
            novo = limpo
        else:
            novo = limpo.replace("</head>", BLOCO_HREFLANG + "</head>", 1)
        if novo == h:
            continue
        n += 1
        if not dry:
            gravar(p, novo)
    print("S-124 hreflang das paginas de imprensa corrigido em %d pagina(s)%s"
          % (n, " (dry-run)" if dry else ""))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    dry = "--dry-run" in sys.argv
    corrige_medicao(pub, dry)
    corrige_hreflang(pub, dry)


if __name__ == "__main__":
    main()
