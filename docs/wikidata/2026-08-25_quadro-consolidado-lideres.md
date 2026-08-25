# Formação e experiência dos 5 líderes — quadro consolidado (25/08/2026)

> Coletado dos perfis do LinkedIn de cada um, com a sessão do Mario, por quatro subagentes em
> paralelo (o Andreas foi lido antes, no fluxo principal). Um arquivo por pessoa nesta pasta,
> com o detalhe. **Fonte autodeclarada** — o mesmo critério das ondas 72/72b.
>
> **Nada disto está no ar.** Publicar no site depende do OK do Mario, pessoa por pessoa.

## O que o site publica hoje × o que o LinkedIn diz

| Pessoa | `alumniOf` no ar | O LinkedIn acrescenta | Divergência |
|---|---|---|---|
| Andreas Mirow | TU Berlin | **Stevens Institute of Technology** (o "2º mestrado, EUA, Fulbright" que estava sem instituição) | — |
| Felipe Diniz | Chicago · FGV | **PUC-Rio** (BA em Economia, 1994–1998) | — |
| Raoni Morais | IME · Barcelona · UFRJ | — | **o IME não aparece na Education dele** (só 2 entradas: Barcelona e UFRJ) |
| Prof. Dr Stephan Friedrich | Karlsruhe · Mannheim | **Innsbruck · St. Gallen · Berkeley** (estadias de pesquisa, não diplomas) | o QID de Karlsruhe é o **pré-fusão**, não o do KIT |
| Renato Alvarenga | CMU–Tepper · UnB | — | — (e a **Tepper tem item próprio** no Wikidata) |

## QIDs conferidos por mim, não só reportados pelos agentes

Reconferidos em `wbgetentities` depois de os agentes voltarem:

| QID | Rótulo na API |
|---|---|
| `Q29426438` | University of Karlsruhe — *"university in Karlsruhe (1967–2009), replaced by KIT"* |
| `Q7701381` | Tepper School of Business — *"business school of Carnegie Mellon University"* |
| `Q1857293` | Pontifical Catholic University of Rio de Janeiro |
| `Q673354` | University of St. Gallen |
| `Q875788` | University of Innsbruck |
| `Q500692` | University of Bremen |
| `Q657222` | Stevens Institute of Technology |

As duas dúvidas que ficaram abertas no rascunho do lote estão **fechadas**:

- **Karlsruhe:** usar `Q29426438` (a universidade de 1967 a 2009), não `Q309988` (o KIT). O
  Stephan entrou em 1983 — a fusão que criou o KIT é de 2009.
- **Tepper:** existe item próprio, `Q7701381`. Não é preciso recorrer à universidade-mãe.

## Achado colateral, medido: o link do LinkedIn do Stephan está MORTO no site

A URL que o site publica — `linkedin.com/in/prof-dr-stephan-friedrich-von-den-eichen-681883139`
— redireciona para `linkedin.com/404/` (*"This page doesn't exist"*), verificado no navegador
em 25/08. O perfil correto é o mesmo slug **sem o sufixo numérico**:
`linkedin.com/in/prof-dr-stephan-friedrich-von-den-eichen/`.

Está em **12 arquivos** (4 por idioma, nos três). Vira onda: uma troca de string, mais uma
asserção que resolva o link em vez de só conferir que ele existe (P2.1 — o defeito é
exatamente do tipo "a string está lá e não leva a lugar nenhum").

## O que fica pendente de decisão do Mario

1. **Publicar o enriquecimento** do `alumniOf` (Stevens, PUC-Rio, e as estadias do Stephan se
   ele quiser) — a onda em si é pequena; a decisão é confirmar com cada pessoa, como foi feito
   na 72b.
2. **O IME do Raoni:** o site afirma, o LinkedIn não. Não é erro necessariamente (é comum não
   listar a graduação), mas afirmação nossa sobre a formação de alguém pede confirmação dele.
3. **A experiência anterior** (McKinsey, Aracruz, Booz Allen, Monitor Deloitte, Arthur D.
   Little, Malik MZSG, Schlumberger etc.) **não está** no dado estruturado do site hoje. Se
   entrar, é `worksFor`/histórico no JSON-LD e `P108` no Wikidata.
4. **QIDs de empresa** ainda não resolvidos: Monitor Deloitte é ambíguo entre dois itens, e a
   IMP (Innovative Management Partner) não tem item.
