# -*- coding: utf-8 -*-
"""71 — S-70 / issue #128: as 5 CONSTELACOES de setores ao redor da Mirow, na home.

Uso:
    python tools_onda6/71_home_planeta_setores.py <raiz-que-contem-public>

HISTORICO DO PEDIDO (3 versoes, mesma issue)
--------------------------------------------
v1 (onda 18) "planeta com os diversos setores orbitando esse planeta ... junto com
   'nossas areas de expertise'" -> 3 aneis girando com 19 chips.
v2 (onda 19) "tem muito overlap ... podemos fazer um search por paginas com
   constelacoes para agruparmos industrias semelhantes em grupos de constelacoes"
   -> 5 grupos em slots fixos, em lista. Matou o overlap, mas ficou uma lista.
v3 (onda 20) "quero que sejam constelacoes ultramodernas mesmo, com cada grupo
   sendo uma esfera central enquanto os outros temas se conectam a ela. elas devem
   circundar mirow & co. a letra precisa ser mais facilmente legivel contra o
   background. texto preto sobre esse azul e dificil de ler. texto azul sobre azul
   dificil tambem."
   -> grafo de esferas em ceu escuro.
v4 (onda 21) "ainda nao ficou bom. remova isso e coloque de alguma forma 5 cards com
   cada grupo de industrias listado, sem planeta nem nada disso. faca no tema do
   resto da pagina."
   -> FIM da metafora visual. 5 cards no tema do site, e ponto. O que sobrevive das
      3 tentativas anteriores e a unica coisa que era conteudo, nao efeito: o
      AGRUPAMENTO dos 19 setores em 5 grupos (que segue aguardando OK do Mario).
v5 (esta)    "remova o '5 setores', '4 setores', etc. torne o texto 'Setores em que
   atuamos' em branco mais ou menos no mesmo estilo que 'Lideres', remova o subtexto
   '19 industrias, agrupadas em 5 frentes de atuacao'. coloque as industrias na ordem
   de frequencia em que mais atuamos, veja os dados a partir do mirow RAG."

COMO A ORDEM DE FREQUENCIA FOI OBTIDA (R1 - transparencia)
----------------------------------------------------------
O MCP mirow-rag NAO tem endpoint de contagem: `buscar_conhecimento_mirow` devolve
chunks (top_k <= 30), nunca agregados. O proxy disponivel e a LISTA DE CLIENTES do
acervo (`listar_clientes`, ~330 nomes, consultada em 2026-08-04): cada cliente foi
classificado em um dos 19 setores do site, e a contagem por setor virou o ranking
do dicionario FREQ. E um proxy - "quantos clientes do acervo pertencem ao setor" -,
nao horas nem receita.

Sanidade do topo: bate com o que a propria firma afirma. Uma proposta Klabin de 2019
no acervo diz textualmente "consultoria estrategica com raizes no setor florestal,
tendo trabalhado com as 10 maiores empresas do ramo", e o CLAUDE.md do projeto de
marketing lista como territorios fortes Papel & Celulose, Energia e Automotivo.

LIMITE CONHECIDO: a classificacao dos ~330 clientes e do Claude, nao do Mario. Casos
de fronteira foram decididos pela atividade dominante (Raizen -> oleo e gas, nao
agro; Bayer e Syngenta -> agronegocio; Dexco e TANAC -> base florestal). Discordando
da ordem, e trocar numero no FREQ.

PESQUISA DE REFERENCIA (03/08/2026)
-----------------------------------
Padrao pedido = hub-and-spoke / node-link graph, o visual de "rede de nos
brilhantes". O que as fontes convergem:
  - fundo ESCURO com esferas translucidas e linhas finas luminosas; um hub central
    mais brilhante que os outros (efeito starburst) — colecoes de referencia de
    "glowing network of interconnected nodes" e material de topologia no Dribbble
  - COR distingue cluster, TAMANHO distingue importancia/centralidade, e animacao
    serve para sugerir fluxo (guias de knowledge-graph visualization: yFiles,
    Tom Sawyer, Datavid)
  - layouts force-directed existem justamente para evitar sobreposicao de no; aqui
    a geometria e calculada a mao em Python, o que da o mesmo efeito de forma
    deterministica (e reproduzivel entre builds)
  - ESA Star Mapper (TULP), levantado na v2, segue valendo para a parte de
    "constelacao": estrela pequena, linha fina, nome do grupo como etiqueta fixa.

DECISOES DESTA VERSAO
---------------------
1. LEGIBILIDADE (o pedido explicito): a secao passa a ter seu proprio CEU ESCURO
   (painel navy #020E66 -> #071C25 com estrelas fracas). Todo texto vira branco ou
   azul-claro #AAD5E8. Nao ha mais texto preto nem navy sobre o azul medio do
   gradiente do tema — era isso que estava ilegivel.
2. Cada grupo e uma ESFERA (hub) com brilho proprio; os setores do grupo sao nos
   menores ligados a ela por linha fina. As 5 esferas circundam a esfera central
   MIROW & CO., ligadas a ela por linha tracejada.
3. Tudo em SVG unico com viewBox — escala sem quebrar, sem lib, sem imagem.
   Geometria calculada aqui, com os rotulos empilhados por hub: overlap continua
   impossivel por construcao.
4. Os icones dos setores SAIRAM. Num grafo de nos o "no" e a estrela; e o icone
   SVG do tema ja tinha custado a armadilha do plugin svgs-inline (precisa de
   ?ver=1, ver assercao H09). Menos peca, menos modo de falha.
5. O pulso das esferas respeita prefers-reduced-motion. Abaixo de 992px o SVG sai
   e entra a lista empilhada (mesmo conteudo, texto branco no mesmo ceu).

Idempotente: bloco entre marcadores.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (escrever_bloco_css, gravar, idioma_da_pagina, ler,  # noqa: E402
                        resolve_public)

MARK_INI = "<!-- onda18:planeta-setores -->"
MARK_FIM = "<!-- /onda18:planeta-setores -->"

# nome do setor por idioma, na ordem original do bloco de industrias
NOMES = {
    "pt": [u"Automotivo", u"Agronegócio", u"Educação", u"Varejo e bens de consumo",
           u"Energia elétrica", u"Óleo e gás", u"Químicos", u"Utilidades",
           u"Esportes, mídia e entretenimento", u"Florestal, papel e celulose",
           u"Infraestrutura e cimento", u"Máquinas e equipamentos",
           u"Mineração e siderurgia", u"Private Equity", u"Serviços financeiros",
           u"Saúde", u"Tecnologia", u"Telecom", u"Transporte e logística"],
    "en": [u"Automotive", u"Agribusiness", u"Education", u"Retail and Consumer Goods",
           u"Electric Energy", u"Oil and Gas", u"Chemicals", u"Utilities",
           u"Sports, Media and Entertainment", u"Forestry, Pulp and Paper",
           u"Infrastructure and Cement", u"Machinery and Equipment",
           u"Mining and Steel", u"Private Equity", u"Financial Services",
           u"Healthcare", u"Technology", u"Telecom", u"Transportation and logistics"],
    "de": [u"Automobil", u"Landwirtschaft", u"Bildung", u"Einzelhandel und Konsumgüter",
           u"Elektrizität", u"Öl und Gas", u"Chemikalien", u"Utilities",
           u"Sport, Medien und Unterhaltung", u"Forstwirtschaft, Papier und Zellstoff",
           u"Infrastruktur und Zement", u"Maschinen und Ausrüstungen",
           u"Bergbau und Stahlindustrie", u"Private Equity", u"Finanzdienstleistungen",
           u"Gesundheit", u"Technologie", u"Telekommunikation", u"Transport und Logistik"],
}

# nome da constelacao por idioma
GRUPOS = {
    "pt": [u"Energia & Recursos", u"Indústria & Base florestal", u"Consumo & Agro",
           u"Tecnologia & Mídia", u"Capital & Serviços"],
    "en": [u"Energy & Resources", u"Industry & Forest-based", u"Consumer & Agri",
           u"Technology & Media", u"Capital & Services"],
    "de": [u"Energie & Ressourcen", u"Industrie & Forstbasis", u"Konsum & Agrar",
           u"Technologie & Medien", u"Kapital & Dienstleistungen"],
}
# frequencia = nº de clientes do acervo mirow-rag classificados no setor
# (indice na lista de 19 -> contagem). Ver "COMO A ORDEM ..." no cabecalho.
FREQ = {
    3: 30,   # Varejo e bens de consumo
    9: 26,   # Florestal, papel e celulose
    1: 24,   # Agronegocio
    4: 19,   # Energia eletrica
    18: 19,  # Transporte e logistica
    14: 17,  # Servicos financeiros
    10: 16,  # Infraestrutura e cimento
    5: 15,   # Oleo e gas
    0: 14,   # Automotivo
    12: 12,  # Mineracao e siderurgia
    15: 12,  # Saude
    13: 9,   # Private Equity
    6: 9,    # Quimicos
    16: 9,   # Tecnologia
    2: 8,    # Educacao
    17: 5,   # Telecom
    7: 5,    # Utilidades
    8: 4,    # Esportes, midia e entretenimento
    11: 4,   # Maquinas e equipamentos
}

# indice (na lista de 19) dos setores de cada constelacao
MEMBROS = [
    [5, 4, 7, 12, 6],      # oleo e gas, energia eletrica, utilidades, mineracao, quimicos
    [9, 11, 0, 10, 18],    # florestal, maquinas, automotivo, infra, transporte
    [3, 1, 15, 2],         # varejo, agro, saude, educacao
    [16, 17, 8],           # tecnologia, telecom, esportes/midia
    [14, 13],              # servicos financeiros, private equity
]

def _ordenar_por_frequencia():
    """Ordena os setores DENTRO de cada grupo e os GRUPOS entre si, por frequencia."""
    grupos = [sorted(m, key=lambda i: -FREQ.get(i, 0)) for m in MEMBROS]
    ordem = sorted(range(len(grupos)),
                   key=lambda g: -sum(FREQ.get(i, 0) for i in grupos[g]))
    return [grupos[g] for g in ordem], ordem


TITULO = {
    "pt": (u"Setores em que atuamos",
           u"19 indústrias, agrupadas em 5 frentes de atuação"),
    "en": (u"Industries we serve",
           u"19 industries, grouped into 5 areas of focus"),
    "de": (u"Branchen, in denen wir arbeiten",
           u"19 Branchen, gruppiert in 5 Schwerpunkte"),
}

# rotulo da contagem dentro do card: (singular, plural)
CONTA = {
    "pt": (u"setor", u"setores"),
    "en": (u"industry", u"industries"),
    "de": (u"Branche", u"Branchen"),
}

CSS = """/* ---- S-77 (#128 v4): 5 cards de grupos de setores ---------------------
   O Mario encerrou a metafora visual: "remova isso e coloque ... 5 cards com cada
   grupo de industrias listado, sem planeta nem nada disso. faca no tema do resto
   da pagina." Entao aqui nao ha SVG, esfera, orbita nem ceu escuro — e o mesmo
   vocabulario dos 3 cards de praticas da propria secao: caixa navy, titulo
   branco, itens claros. Sobre o fundo claro do gradiente, navy tem contraste de
   sobra (o problema anterior era texto navy SOBRE o azul medio, nao a caixa). */
.onda18-orbe{position:relative;z-index:6;margin:56px 0 0}
/* titulo no mesmo tratamento do "Nossos Lideres" da propria home:
   branco-azulado #e9f0ff, display grande, alinhado a esquerda */
.onda18-orbe__titulo{color:#e9f0ff;font-size:64px;font-weight:700;line-height:1.05;
  margin:0 0 30px;text-align:left}
.onda18-orbe__cards{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;
  list-style:none;margin:0;padding:0}
.onda18-const{background:#020E66;border-top:3px solid #00ADEC;
  padding:20px 18px 22px;display:flex;flex-direction:column;
  transition:transform 220ms ease,box-shadow 220ms ease}
.onda18-const:hover{transform:translateY(-4px);
  box-shadow:0 14px 30px rgba(2,14,102,.28)}
.onda18-const__nome{display:block;color:#fff;font-size:17px;font-weight:700;
  line-height:1.25;margin:0 0 14px;padding:0 0 12px;
  border-bottom:1px solid rgba(0,173,236,.45)}
.onda18-const__lista{list-style:none;margin:0;padding:0}
.onda18-const__item{position:relative;padding-left:16px;margin:0 0 8px;
  color:#fff;font-size:14px;font-weight:400;line-height:1.35}
.onda18-const__item:last-child{margin-bottom:0}
.onda18-const__item::before{content:"";position:absolute;left:0;top:7px;
  width:6px;height:6px;background:#00ADEC}
@media only screen and (max-width: 1200px){
  .onda18-orbe__cards{grid-template-columns:repeat(3,1fr)}
}
@media only screen and (max-width: 991px){
  .onda18-orbe__titulo{font-size:44px}
}
@media only screen and (max-width: 767px){
  .onda18-orbe__titulo{font-size:32px;margin-bottom:20px}
  .onda18-orbe__cards{grid-template-columns:1fr;gap:12px}
}
"""


def cards(lang):
    """5 cards, um por grupo. Setores e grupos na ordem de frequencia (FREQ)."""
    nomes = NOMES.get(lang, NOMES["pt"])
    grupos = GRUPOS.get(lang, GRUPOS["pt"])
    membros_ord, ordem = _ordenar_por_frequencia()
    out = ['<ul class="onda18-orbe__cards">']
    for pos, membros in enumerate(membros_ord):
        itens = "".join('<li class="onda18-const__item">%s</li>' % nomes[i]
                        for i in membros)
        out.append('<li class="onda18-const">'
                   '<span class="onda18-const__nome">%s</span>'
                   '<ul class="onda18-const__lista">%s</ul></li>'
                   % (grupos[ordem[pos]], itens))
    out.append('</ul>')
    return "".join(out)


def bloco(lang):
    titulo = TITULO.get(lang, TITULO["pt"])[0]
    return ('%s<section class="onda18-orbe"><div class="container"><div class="row">'
            '<div class="col"><h2 class="onda18-orbe__titulo">%s</h2>%s'
            '</div></div></div></section>%s'
            % (MARK_INI, titulo, cards(lang), MARK_FIM))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    total = sum(len(m) for m in MEMBROS)
    if total != 19:
        raise SystemExit("os 5 grupos somam %d setores, deveriam somar 19" % total)
    if len(MEMBROS) != len(GRUPOS["pt"]):
        raise SystemExit("MEMBROS tem %d grupos e GRUPOS tem %d nomes"
                         % (len(MEMBROS), len(GRUPOS["pt"])))

    mudou = escrever_bloco_css(pub, "planeta-setores", CSS, onda="onda18")
    print("bloco onda18:planeta-setores %s" % ("gravado" if mudou else "ja estava igual"))

    alterados = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if "<!-- /onda6:praticas -->" not in h:
                continue
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            lang = idioma_da_pagina(h)
            novo_bloco = bloco(lang)

            if MARK_INI in h:
                velho = h[h.index(MARK_INI):h.index(MARK_FIM) + len(MARK_FIM)]
                novo = h.replace(velho, novo_bloco, 1)
            else:
                ini = h.find('<section class="home-experience">')
                if ini < 0:
                    continue
                fim = h.find("</section>", ini)
                if fim < 0:
                    continue
                fim += len("</section>")
                novo = h[:fim] + "\n" + novo_bloco + h[fim:]
            if novo != h:
                gravar(p, novo)
                alterados += 1
                print("  %s (%s, 5 cards, 19 setores por frequencia)" % (rel, lang))
    print("resumo: %d home(s) com os 5 cards de setores" % alterados)


if __name__ == "__main__":
    main()
