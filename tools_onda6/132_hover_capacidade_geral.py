# -*- coding: utf-8 -*-
u"""132 — onda 66: TODO `:hover` da nossa camada passa a exigir mouse.

Uso: python tools_onda6/132_hover_capacidade_geral.py <raiz-que-contem-public>

POR QUE
-------
Onda 64: a barra do topo ficava BRANCA no celular depois de fechar o menu, e o logo
branco desaparecia. A causa era `.header .menu:hover{background:#fff}` — no desktop
proposital, porque o painel do submenu é branco; em tela de toque **não existe sair
do hover**, então depois do tap o navegador segura o `:hover` até o próximo toque em
outro lugar.

Aquela onda consertou **uma** regra. Medido depois: sobravam **78 regras `:hover`**
na nossa camada sem guarda de capacidade. Todas pressupõem mouse, e em tela de toque
todas grudam do mesmo jeito. Consertar a instância e deixar a classe é o antipadrão
que o P2.1 nomeia.

COMO
----
Cada bloco de regra cujo seletor contém `:hover` (e que ainda não esteja sob
`@media (hover:hover)`) é envolvido em:

    @media (hover:hover) and (pointer:fine){ ... }

Não é media query de largura nem número mágico: é a condição que a regra sempre
pressupôs, agora escrita. Um tablet com mouse recebe hover; um desktop com tela de
toque e mouse também. O que deixa de receber é o dedo.

O QUE FICA FORA, DE PROPÓSITO
-----------------------------
* `:hover` dentro de `@media (hover:hover)` — já está guardado (as 2 da onda 64).
* `:hover` dentro de `@media print`.
* `:focus`, `:focus-visible`, `:active` — teclado e toque DEPENDEM deles; guardar
  seria tirar acessibilidade em nome de arrumação.
* Regras em que `:hover` aparece junto de `:focus` no MESMO seletor
  (`a:hover,a:focus{...}`): envolver mataria o estado de foco no celular. Essas
  são RELATADAS para tratamento manual, não tocadas.

Idempotente: rodar 2x reporta 0 mudanças.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public  # noqa: E402

CSS_REL = os.path.join("wp-content", "uploads", "2026", "07", "onda6", "onda6.css")
GUARDA = "@media (hover:hover) and (pointer:fine)"


def blocos_de_topo(css):
    u"""Devolve (inicio, fim, seletor, corpo) de cada bloco no NIVEL DE TOPO.

    Nao usa regex de bloco: `@media` aninha, e regex de chaves casaria errado.
    Percorre contando profundidade, ignorando chaves dentro de comentario e string.
    """
    saida = []
    i, n = 0, len(css)
    prof = 0
    ini_sel = 0
    ini_corpo = None
    while i < n:
        if css.startswith("/*", i):
            j = css.find("*/", i + 2)
            i = (j + 2) if j >= 0 else n
            continue
        c = css[i]
        if c == "{":
            prof += 1
            if prof == 1:
                ini_corpo = i
        elif c == "}":
            prof -= 1
            if prof == 0 and ini_corpo is not None:
                sel = css[ini_sel:ini_corpo]
                saida.append((ini_sel, i + 1, sel, css[ini_corpo:i + 1]))
                ini_sel = i + 1
                ini_corpo = None
        i += 1
    return saida


def main(argv):
    pub = resolve_public(argv[1] if len(argv) > 1 else ".")
    caminho = os.path.join(pub, CSS_REL)
    css = io.open(caminho, encoding="utf-8").read()

    alvos, com_foco, ja_guardados, dentro_media = [], [], 0, []

    for ini, fim, sel, corpo in blocos_de_topo(css):
        selx = sel.strip()
        if selx.startswith("@"):
            # bloco de media/supports: ver se tem :hover dentro
            if ":hover" in corpo:
                if "hover:hover" in selx:
                    ja_guardados += corpo.count(":hover")
                elif "print" in selx:
                    pass
                else:
                    dentro_media.append((selx.split("{")[0].strip()[:64],
                                         corpo.count(":hover")))
            continue
        if ":hover" not in selx:
            continue
        if re.search(r":focus|:active", selx):
            com_foco.append(selx.replace("\n", " ").strip()[:90])
            continue
        alvos.append((ini, fim))

    if not alvos and not dentro_media:
        print(u"nada a fazer: 0 regra :hover de topo sem guarda")

    # aplica de tras para frente, para os offsets nao andarem
    for ini, fim in sorted(alvos, reverse=True):
        trecho = css[ini:fim]
        css = css[:ini] + ("\n%s{%s}" % (GUARDA, trecho.strip())) + css[fim:]

    if alvos:
        with io.open(caminho, "w", encoding="utf-8", newline="") as f:
            f.write(css)

    # rele e reconte (nao declarar, medir)
    de_volta = io.open(caminho, encoding="utf-8").read()
    restantes = []
    for ini, fim, sel, corpo in blocos_de_topo(de_volta):
        selx = sel.strip()
        if selx.startswith("@") or ":hover" not in selx:
            continue
        if re.search(r":focus|:active", selx):
            continue
        restantes.append(selx.replace("\n", " ").strip()[:70])

    print(u"%d regra(s) :hover de topo envolvida(s) em %s" % (len(alvos), GUARDA))
    print(u"%d :hover ja estavam sob a guarda (ondas anteriores)" % ja_guardados)
    if dentro_media:
        print(u"\n%d media query(ies) com :hover dentro — NAO tocadas (envolver "
              u"@media em @media exige reescrever a condicao):" % len(dentro_media))
        for cond, q in dentro_media:
            print(u"    %-64s %d :hover" % (cond, q))
    if com_foco:
        print(u"\n%d regra(s) com :hover JUNTO de :focus/:active — NAO tocadas de "
              u"proposito (envolver mataria o foco no celular):" % len(com_foco))
        for s in com_foco[:10]:
            print(u"    %s" % s)
    if restantes:
        print(u"\nERRO: sobraram %d regra(s) de topo sem guarda: %s"
              % (len(restantes), restantes[:5]))
        raise SystemExit(1)
    print(u"\nconferido apos gravar: 0 regra :hover de topo sem guarda")


if __name__ == "__main__":
    main(sys.argv)
