# CV do Stephan Friedrich von den Eichen — lido do LinkedIn em 25/08/2026

> Fonte: <https://www.linkedin.com/in/prof-dr-stephan-friedrich-von-den-eichen/> (perfil dele,
> seções *Education* e *Experience*), lido pelo navegador com a sessão do Mario. É **fonte
> autodeclarada** — boa o bastante para o `alumniOf` do site (mesmo critério das ondas 72/72b) e
> aceitável no Wikidata com a referência apontando para o perfil.

**Nota sobre a URL:** o link informado na tarefa
(`.../prof-dr-stephan-friedrich-von-den-eichen-681883139`) dá **404** no LinkedIn — o slug
correto, achado via busca por nome (mútuas com Andreas Mirow e Renato Alvarenga), é
`https://www.linkedin.com/in/prof-dr-stephan-friedrich-von-den-eichen/`.

## O veredito Karlsruhe × KIT

Ele estudou **Wirtschaftsingenieurwesen** na Universität Karlsruhe a partir de **1983** —
antes da fusão de 2009 que criou o KIT. O Wikidata tem os dois itens separados:

- `Q29426438` — **University of Karlsruhe**, descrito literalmente como "university in
  Karlsruhe (1967–2009), replaced by KIT". **Este é o item correto** para o vínculo dele.
- `Q309988` — Karlsruhe Institute of Technology (KIT), a entidade pós-fusão. **Não usar** para
  o período dele.

## O vínculo com Bremen é docência, não formação

Confirmado na página *Experience*, não em *Education*: **"Honorarprofessur für BWL, insb.
Organisations-, Management- & Geschäftsmodellinnovation"**, Universität Bremen, 2014–presente,
Grande Bremen. É cargo de professor honorário — entra na tabela de Experiência abaixo, e
**não deve entrar no `alumniOf`**.

## Formação

Todas as cinco entradas do LinkedIn aparecem com data final "Present" (Atual) — é o próprio
perfil que está assim, sem data de conclusão declarada; reproduzido literalmente.

| Instituição | Grau / curso | Período | QID |
|---|---|---|---|
| Universität Karlsruhe | Wirtschaftsingenieurwesen (engenharia de produção) — grau não declarado | 1983–atual (sem data de conclusão declarada) | `Q29426438` (University of Karlsruhe, 1967–2009, pré-fusão — não confundir com KIT `Q309988`) |
| University of Mannheim | Betriebswirtschaftslehre (administração de empresas) — grau não declarado | 1985–atual (sem data de conclusão declarada) | `Q317070` |
| Universität Innsbruck | Forschungsaufenthalt (estadia de pesquisa) | 1990–atual (sem data de conclusão declarada) | `Q875788` |
| University of St.Gallen | Forschungsaufenthalt (estadia de pesquisa) | 1991–atual (sem data de conclusão declarada) | `Q673354` |
| University of California, Berkeley | Forschungsaufenthalt (estadia de pesquisa) | 1992–atual (sem data de conclusão declarada) | `Q168756` |

## Experiência

| Cargo | Empresa | Período |
|---|---|---|
| Managing Partner IMP Gruppe (Sprecher der Geschäftsführung / porta-voz da diretoria) | Innovative Management Partner (IMP) | 2014 – hoje · München, Innsbruck, Wien, Zürich, São Paulo |
| Managing Partner IMP | Innovative Management Partner (IMP) | 2010 – 2014 |
| Honorarprofessur für BWL, insb. Organisations-, Management- & Geschäftsmodellinnovation (professor honorário de Administração, com foco em inovação organizacional, de gestão e de modelo de negócio) | Universität Bremen (`Q500692`) | 2014 – hoje · Grande Bremen |
| Partner & Mitglied der Geschäftsleitung Malik MZSG (sócio e membro da diretoria) | Malik (`Q33121466` — Malik Management, Switzerland) | 2006 – 2009 · St. Gallen |
| Partner und Leiter Geschäftsbereich "Strategy & Organisation" (sócio e líder da área "Estratégia & Organização") | Arthur D. Little (`Q709066`) | 2003 – 2006 · Wiesbaden, München |

## O que fazer com isso

1. **Site — o `alumniOf` já publicado está certo, com uma correção de QID.** O site (ondas
   72/72b) já lista Universität Karlsruhe e Universität Mannheim para ele. Confirmado nos dois
   no LinkedIn. **Se o dado estruturado hoje usa `Q309988` (KIT) para Karlsruhe, precisa trocar
   para `Q29426438`** (University of Karlsruhe, pré-fusão) — o Mario confirma antes de mudar.
2. **Bremen não entra no `alumniOf`.** É cargo (Honorarprofessur), não formação — mesmo padrão
   de cuidado já usado para não confundir docência com diploma.
3. **Wikidata:** `P69` (educado em) → `Q29426438` e `Q317070`; `P108` (empregador) →
   Innovative Management Partner (sem QID achado), Universität Bremen (`Q500692`, como
   professor honorário), Malik Management (`Q33121466`), Arthur D. Little (`Q709066`);
   referência = o perfil do LinkedIn.
4. **Não declarado no perfil:** grau/título formal em Karlsruhe e Mannheim (só o curso/área
   aparece, sem "Diplom" ou equivalente explícito); datas de conclusão de todas as cinco
   entradas de formação (todas mostram "Present"); QID para "Innovative Management Partner"
   (não encontrado no Wikidata — pode não ter item próprio).
