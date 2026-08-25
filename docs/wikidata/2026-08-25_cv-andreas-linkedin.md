# CV do Andreas Mirow — lido do LinkedIn em 25/08/2026

> Fonte: <https://www.linkedin.com/in/andreas-mirow/> (perfil dele, seções *Education* e
> *Experience*), lido pelo navegador com a sessão do Mario. É **fonte autodeclarada** — boa o
> bastante para o `alumniOf` do site (foi o critério usado nas ondas 72/72b) e aceitável no
> Wikidata com a referência apontando para o perfil.

## A lacuna do handoff está resolvida

O 2º mestrado é do **Stevens Institute of Technology** (Hoboken, Nova Jersey, EUA) —
`Q657222` no Wikidata. No LinkedIn ele aparece como texto dentro da entrada da TU Berlin:
*"Scholarship and Master of Technology Management of the Stevens Institute of Technology"*,
o que casa com o "Gestão de Tecnologia, EUA, Fulbright" que o site já dizia. **Sem ano
declarado.**

## Formação

| Instituição | Grau / curso | Período | QID |
|---|---|---|---|
| Technische Universität Berlin | Diplom, Wirtschaftsingenieurwesen (engenharia de produção) | 1985–1990 | `Q51985` |
| Stevens Institute of Technology | Master of Technology Management (com bolsa) | sem ano declarado | `Q657222` |
| Escola Suíço-Brasileira, Rio de Janeiro | ensino básico | — | (não entra) |

## Experiência

| Cargo | Empresa | Período |
|---|---|---|
| Founder, Managing Partner | Mirow & Co. | jun/2012 – hoje (Grande Rio) |
| Principal | McKinsey | set/2001 – jun/2012 · responsável pelo escritório do Rio (2009–2012), Partner em Atlanta (2009), líder global da prática de papel e celulose |
| Mgr. of Sales and Marketing and Corporate Planning | Aracruz Celulose S.A. | ago/1996 – ago/2001 |
| Senior Associate | Booz Allen Hamilton | 1990 – 1995 |

## O que fazer com isso

1. **Site (onda 73):** acrescentar Stevens ao `alumniOf` dele na constante `ALUMNI` do
   `tools_onda6/111_geo_jsonld_lideres.py`. Segue o mesmo padrão de Stephan e Renato na onda
   72b — e, como lá, **o Mario confirma com ele antes**.
2. **Wikidata:** `P69` (educado em) → `Q51985` e `Q657222`; `P108` (empregador) → Mirow (quando
   o item existir), McKinsey, Aracruz, Booz Allen; referência = o perfil do LinkedIn.
3. **Pedir a ele, só isso:** o **ano** do mestrado no Stevens, e se quer que a experiência
   anterior (McKinsey, Aracruz, Booz Allen) entre no dado estruturado do site — hoje não está.
