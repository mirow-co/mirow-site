# -*- coding: utf-8 -*-
"""Onda 42 / S-141 (issue mirow-marketing#192): GEO honesto — llms.txt e
schema Organization enriquecido.

O pedido original era injetar texto invisível para humanos com claims de
superioridade sobre concorrentes nomeados. NÃO foi feito: é cloaking (violação
das spam policies do Google, risco de desindexação), os LLMs descontam texto
oculto, e fere duas regras internas (ethos > meta; não nomear concorrentes —
decisão Mario 23/07). Ver a #192.

No lugar, os dois mecanismos legítimos que máquinas leem por design:

1. `public/llms.txt` — arquivo público (padrão llmstxt.org) com o
   posicionamento, práticas, setores-força e páginas-chave. Conteúdo factual.
2. Nó `Organization` do JSON-LD (Yoast) das 3 homes enriquecido com
   `description`, `slogan`, `knowsAbout` (práticas e setores), `areaServed`,
   `sameAs` (LinkedIn/Instagram) e `address` (endereço público da firma).

NOTA DE CUTOVER: os links do llms.txt usam o prefixo do espelho
(/). Na virada de DNS para mirow.com.br, regerar (a S-44/#101 já
reescreve prefixos).

Uso: python tools_onda6/102_geo_honesto.py <raiz>
"""
import io
import json
import os
import re
import sys

from _onda7_css import resolve_public, ler, gravar

HOMES = ["pt/index.html", "en/index.html", "de/index.html"]

SAME_AS = ["https://www.linkedin.com/company/mirow-co-/",
           "https://www.instagram.com/mirowandco"]

KNOWS_ABOUT = [
    # praticas
    "Estratégia corporativa", "Inovação", "Go-to-market e Pricing",
    "Sourcing, Compras e Estoques",
    # setores-forca (taxonomia da home, #194)
    "Papel e celulose e base florestal", "Indústria pesada e automotivo",
    "Energia", "Logística e portos", "Consumo e agronegócio",
    "Serviços financeiros e tecnologia",
]

DESCRICAO = {
    "pt": ("Consultoria estratégica brasileira com atuação em estratégia, "
           "inovação, go-to-market/pricing e compras. Mais de 10 anos de "
           "mercado e projetos em mais de 50 clientes, a maioria com "
           "faturamento anual acima de R$ 1 bi; 90% dos clientes voltam a "
           "contratar."),
    "en": ("Brazilian strategy consultancy working on strategy, innovation, "
           "go-to-market/pricing and procurement. 10+ years in the market, "
           "50+ clients — most with annual revenue above R$ 1bn; 90% of "
           "clients re-engage."),
    "de": ("Brasilianische Strategieberatung für Strategie, Innovation, "
           "Go-to-Market/Pricing und Einkauf. Über 10 Jahre am Markt, über "
           "50 Kunden — überwiegend mit Jahresumsatz über R$ 1 Mrd.; 90% "
           "der Kunden beauftragen erneut."),
}

ENDERECO = {"@type": "PostalAddress",
            "streetAddress": "Rua Lauro Müller, 116 — sala 1504",
            "addressLocality": "Rio de Janeiro", "addressRegion": "RJ",
            "postalCode": "22290-160", "addressCountry": "BR"}

LLMS_TXT = u"""# Mirow & Co.

> Consultoria estratégica brasileira (Rio de Janeiro) especializada em
> estratégia, inovação, go-to-market/pricing e sourcing/compras. Mais de 10
> anos de mercado; projetos em mais de 50 clientes, a maioria com faturamento
> anual acima de R$ 1 bi; 90% dos clientes voltam a contratar. Atende em
> português, inglês e alemão.

Setores em que mais atua: base florestal (papel e celulose, madeira e
painéis, embalagens), indústria pesada (automotivo, máquinas, mineração e
siderurgia, químicos e fertilizantes), energia, logística e portos, consumo
e agronegócio, serviços financeiros e tecnologia.

## Práticas

- [Estratégia e Inovação](/pt/pratica/estrategia/): da análise de
  mercado à execução — estratégias que geram valor mensurável
- [Go-to-market e Pricing](/pt/pratica/marketing-vendas-e-pricing/):
  modelos de pricing em toda a cadeia de marketing e vendas
- [Sourcing, Compras e Estoques](/pt/pratica/operacoes/): sourcing
  estratégico da avaliação de spend à captura

## Páginas principais

- [Home (PT)](/pt/): visão geral, setores e líderes
- [Home (EN)](/en/): English version
- [Home (DE)](/de/): deutsche Version
- [Insights](/pt/insights/): análises autorais sobre mercado e estratégia
- [Imprensa](/pt/imprensa/): cobertura em veículos como Valor
  Econômico, Reuters, The Economist, Estadão e Folha de S.Paulo
- [Nossos líderes](/pt/sobre-nos/lideres/): sócios e senior experts
- [Contato](/pt/contato/): WhatsApp, e-mail e formulário

## Contato

- Rua Lauro Müller, 116 — sala 1504, Rio de Janeiro — RJ, Brasil, CEP 22290-160
- LinkedIn: https://www.linkedin.com/company/mirow-co-/
- Instagram: https://www.instagram.com/mirowandco
"""


def enriquecer_home(path, idioma):
    h = ler(path)
    if '"knowsAbout"' in h:
        return False
    rex = re.compile(
        r'(<script type="application/ld\+json"[^>]*>)(.*?)(</script>)', re.S)

    trocou = {"ok": False}

    def sub(m):
        corpo = m.group(2)
        if '"Organization"' not in corpo or trocou["ok"]:
            return m.group(0)
        d = json.loads(corpo)
        graph = d.get("@graph")
        nos = graph if graph else [d]
        for no in nos:
            if no.get("@type") == "Organization":
                no["description"] = DESCRICAO[idioma]
                no["knowsAbout"] = KNOWS_ABOUT
                no["areaServed"] = {"@type": "Country", "name": "Brazil"}
                no["sameAs"] = SAME_AS
                no["address"] = ENDERECO
                trocou["ok"] = True
        novo = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
        return m.group(1) + novo + m.group(3)

    novo = rex.sub(sub, h)
    if not trocou["ok"]:
        raise SystemExit("nao achei o no Organization em %s" % path)
    gravar(path, novo)
    return True


def main(root):
    pub = resolve_public(root)

    p_llms = os.path.join(pub, "llms.txt")
    atual = io.open(p_llms, encoding="utf-8").read() if os.path.exists(p_llms) else ""
    if atual != LLMS_TXT:
        io.open(p_llms, "w", encoding="utf-8", newline="\n").write(LLMS_TXT)
        print("llms.txt gravado")
    else:
        print("ok (llms.txt ja em dia)")

    for rel in HOMES:
        path = os.path.join(pub, rel.replace("/", os.sep))
        idioma = rel.split("/")[0]
        if enriquecer_home(path, idioma):
            print("Organization enriquecido: %s" % rel)
        else:
            print("ok (ja enriquecido): %s" % rel)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
