# -*- coding: utf-8 -*-
u"""137 — fecha a #241 (2º link) e registra a verificação da #68 (IMP).

Uso: python tools_onda6/137_imprensa_oglobo_e_imp.py <raiz-que-contem-public>

A. O SEGUNDO LINK DA IMPRENSA (#241)
------------------------------------
O Mario passou o link. Conferido em 19/08/2026 na própria página:

    O Globo · 05/10/2025 · "Mercado de carro elétrico no país tem potencial de
    movimentar R$ 200 bi por ano a partir de 2030"

**A data era outra, pela terceira vez neste levantamento.** O consolidado dizia
07/10/2025; a URL e a página dizem **05/10**. As três divergências de data que
apareceram (este, o Transporte Moderno e o item do Valor) têm a mesma origem: o
consolidado registrou a data do **post no LinkedIn**, não da publicação.

Citação medida no corpo da matéria: *"…estudo do Acende Brasil conclui que esse
novo ecossistema de negócios da eletrificação pode movimentar R$ 200 bilhões por
ano, **num cálculo da consultoria Mirow & Co.**"* — a firma entra como autora do
cálculo, e o logo do O Globo já existe no repo.

B. O PIN DA IMP CONSULTING (#68) — VERIFICADO, E FICA ONDE ESTÁ
---------------------------------------------------------------
O Mario mandou o imprint e disse para eu mesmo achar. Achei, e o resultado
**contraria a minha própria suspeita**: eu tinha levantado a hipótese de que Viena
estivesse errada porque o Prof. Stephan Friedrich é professor em **Bremen**.

O que as duas fontes dizem:

* **imprint** (`impconsulting.com/imprint`) — duas sedes REGISTRADAS:
  Claudius-Keller-Str. 3a, 81669 **München** (HRB 188164) e Rennweg 23, 6020
  **Innsbruck** (FN 168938p). Nenhuma é Viena.
* **site** (`impconsulting.com`) — **quatro escritórios**: Innsbruck, **Viena
  (Am Hof 4/4, 1010 Wien)**, Munique, Appenzell (Suíça) — e **São Paulo**
  (Rua Cardeal Arcoverde, 2365, Pinheiros).

Logo: **Viena é escritório real da IMP**, e o pin está factualmente correto. O que
faltava não era a cidade — era a **evidência registrada**, e é isso que este
script grava no mestre, para a pergunta não voltar.

Bremen é onde ele **dá aula**, não onde a IMP fica. A minha suspeita confundiu
vínculo acadêmico com sede da firma.

**Fato novo que ninguém pediu e vale saber: a IMP tem escritório em São Paulo**,
na mesma cidade do escritório da Mirow. Não muda o mapa (o pin marca a sede do
parceiro, e um parceiro global com escritório no Brasil marcado no Brasil apagaria
a informação de alcance internacional, que é o ponto do mapa), mas é dado de
relacionamento que o Mario pode querer usar.

Idempotente: rodar 2x reporta 0 mudanças.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public  # noqa: E402

BASE = os.path.join(os.path.expanduser("~"), "OneDrive - Mirow", "Mirow & Co",
                    "05_Marketing", "05_NovoMarketing", "08_Site")
M_MATERIAS = os.path.join(BASE, "2026-08-19_imprensa-materias-curadoria.json")
M_REDE = os.path.join(BASE, "2026-08-04_rede-parceiros-curadoria.json")

URL = ("https://oglobo.globo.com/economia/negocios/noticia/2025/10/05/"
       "mercado-de-carro-eletrico-no-pais-tem-potencial-de-movimentar-"
       "r-200-bi-por-ano-a-partir-de-2030.ghtml")

MATERIA = {
    "data": "2025-10-05",
    "veiculo": u"O Globo",
    "titulo": (u"Mercado de carro elétrico no país tem potencial de movimentar "
               u"R$ 200 bi por ano a partir de 2030"),
    "url": URL,
    "quem": u"Mirow & Co. (estudo)",
    "tema": u"Eletromobilidade",
    "verificado": "lido",
    "fonte_do_titulo": u"og:title medido em 2026-08-19",
    "nota": (u"issue #241: o consolidado do Felipe registrava este item sem link e "
             u"datado 07/10/2025 — a URL e a página dizem 05/10. Terceira vez neste "
             u"levantamento em que a data anotada era do post no LinkedIn, não da "
             u"publicação. Citação medida no corpo: “estudo do Acende Brasil "
             u"conclui que esse novo ecossistema de negócios da eletrificação pode "
             u"movimentar R$ 200 bilhões por ano, num cálculo da consultoria "
             u"Mirow & Co.” — a firma entra como autora do cálculo. Link "
             u"fornecido pelo Mario em 19/08."),
}

NOTA_IMP = (
    u"Cidade VERIFICADA em 19/08/2026 (issue #68) e mantida. O imprint "
    u"(impconsulting.com/imprint) lista duas sedes REGISTRADAS — Claudius-Keller-Str. "
    u"3a, 81669 München (HRB 188164) e Rennweg 23, 6020 Innsbruck (FN 168938p) — e "
    u"nenhuma delas é Viena; mas o site apresenta QUATRO escritórios: Innsbruck, "
    u"Viena (Am Hof 4/4, 1010 Wien), Munique e Appenzell (Suíça), mais São Paulo "
    u"(Rua Cardeal Arcoverde, 2365, Pinheiros). Viena é escritório real, então o pin "
    u"está correto. A dúvida original vinha de o Prof. Stephan Friedrich ser "
    u"professor em Bremen — Bremen é onde ele dá aula, não onde a IMP fica; a "
    u"suspeita confundia vínculo acadêmico com sede da firma. NOTA DE "
    u"RELACIONAMENTO: a IMP tem escritório em São Paulo, mesma cidade do escritório "
    u"da Mirow.")


def main(argv):
    resolve_public(argv[1] if len(argv) > 1 else ".")   # valida a raiz
    mudou = 0

    # ------------------------------------------------------- A. a materia
    with io.open(M_MATERIAS, encoding="utf-8") as f:
        mat = json.load(f)
    if URL in [m["url"] for m in mat["materias"]]:
        print(u"  = materia do O Globo ja estava no mestre")
    else:
        mat["materias"].append(MATERIA)
        mat["materias"].sort(key=lambda x: (x["data"], x["veiculo"]), reverse=True)
        mat["_atualizado"] = "2026-08-19"
        with io.open(M_MATERIAS, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(mat, ensure_ascii=False, indent=1) + u"\n")
        print(u"  + O Globo 05/10/2025 no mestre (%d materias no total)"
              % len(mat["materias"]))
        mudou += 1

    # ------------------------------------------------------- B. a nota da IMP
    with io.open(M_REDE, encoding="utf-8") as f:
        rede = json.load(f)
    itens = rede if isinstance(rede, list) else rede.get(
        "parceiros", rede.get("itens", []))
    achou = False
    for p in itens:
        if p.get("nome", "").startswith("IMP"):
            achou = True
            if p.get("verificacao_cidade") == NOTA_IMP:
                print(u"  = nota da IMP ja estava no mestre")
            else:
                p["verificacao_cidade"] = NOTA_IMP
                mudou += 1
                print(u"  + verificacao da cidade da IMP registrada no mestre")
    if not achou:
        raise SystemExit(u"nao achei a IMP no mestre da rede")
    if mudou:
        if isinstance(rede, dict):
            rede["_atualizado"] = "2026-08-19"
        with io.open(M_REDE, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(rede, ensure_ascii=False, indent=1) + u"\n")

    print(u"\n%d mudanca(s). Agora rode: python tools/gen_imprensa.py ." % mudou)


if __name__ == "__main__":
    main(sys.argv)
