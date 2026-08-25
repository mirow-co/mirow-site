# Wikidata — rascunho do lote (empresa + pessoas) e checklist de CV

> Preparado em 25/08/2026, **antes** dos gates. Nada aqui foi publicado: o Claude não
> publica no Wikidata. Ordem que o pacote do Felipe manda: aquecer conta → cartão CNPJ →
> CV → lote → Mario confere → **Felipe aprova por escrito** → publicar.

## Linha de base medida hoje (25/08/2026)

| Medição | Resultado |
|---|---|
| `wbsearchentities` por "Mirow & Co" (pt) | **0 resultados** — a firma não existe no Wikidata |
| SPARQL por `P6204 = 15353236000189` (nosso CNPJ) | **0 resultados** — ninguém reivindicou o identificador |

É a métrica binária do handoff de 18/08 ("não existe → existe"), agora com o "não existe"
registrado com data e método.

## Propriedades confirmadas na API (não deduzidas)

| Propriedade | Id | Uso |
|---|---|---|
| CNPJ | `P6204` | âncora brasileira; separa da cidade alemã, do sobrenome e do Miro |
| instância de | `P31` → `Q2089936` (*consulting company*) | tipo do item da empresa |

## Item da EMPRESA — o que já tem fonte publicada

Fonte de tudo abaixo: o próprio site (`https://mirow.com.br/pt/`, JSON-LD medido hoje).
Site é fonte fraca para identificador e data — por isso as duas últimas linhas esperam o cartão.

| Campo | Valor | Fonte |
|---|---|---|
| Rótulo (pt/en/de) | Mirow & Co. | site |
| Descrição pt | consultoria estratégica brasileira | site |
| Descrição en | Brazilian strategy consulting firm | site |
| `P31` instância de | `Q2089936` consulting company | — |
| `P17` país | `Q155` Brasil | site |
| `P856` site oficial | https://mirow.com.br/pt/ | site |
| `P112` fundado por | item do Andreas Mirow (a criar) | site (`founder` no JSON-LD) |
| `P6204` CNPJ | 15.353.236/0001-89 | **espera o cartão CNPJ** (o site cita o número na política de privacidade, mas é fonte fraca) |
| `P571` data de fundação | 2012-04-12 (segundo o site) | **espera o cartão CNPJ**; se divergir, o cartão manda e o site é corrigido |
| `P159` sede | **PERGUNTA ABERTA — ver abaixo** | — |

### A pergunta que precisa de você antes do lote: qual é a sede?

Medi hoje na home em pt: o JSON-LD publica **dois** endereços — o nó do Yoast traz
`Rua Lauro Müller, 116 — sala 1504, Rio de Janeiro/RJ` como `address`, e o nosso nó traz
`Av. Ibirapuera, 2033 — conjunto 133, São Paulo/SP` como `location` ("Escritório São Paulo"),
com `foundingLocation` no Rio. O backlog (C5) registra que o escritório físico é São Paulo e
que o CNPJ do Rio segue ativo — o endereço do Rio é o **legal**.

No Wikidata isso se resolve sem ambiguidade: `P159` (sede) = São Paulo, `P740`
(local de fundação) = Rio de Janeiro. Só preciso do seu OK sobre qual vai como sede,
porque afirmação errada nesse campo é exatamente o que alimenta o "somos alemães".

## Pessoas — checklist de CV para pedir a cada sócio

Um e-mail curto por pessoa, respondendo em linha. **Nunca** entram data de nascimento
completa, CPF, e-mail, telefone nem endereço residencial.

1. Nome como quer ser citado.
2. Cargo atual na Mirow & Co. e ano de entrada.
3. Formação: instituição, curso, ano de conclusão (graduação e pós).
4. Empregadores anteriores relevantes, com período.
5. Um link público que sirva de fonte (perfil no LinkedIn, matéria de imprensa, paper).
6. Idiomas.

Quem já está coberto: o Felipe mandou a lista dele em 24/08 (virou o `alumniOf` e o
`knowsAbout` da onda 72). O Andreas tem um 2º mestrado ("Gestão de Tecnologia, EUA,
Fulbright") **sem instituição nomeada** — é a única lacuna conhecida do schema do site, e a
mesma pergunta serve para o Wikidata.

## Formato do lote (QuickStatements v1) — modelo, ainda sem valores

O item da empresa é criado **à mão** pela interface (o pacote pede isso). As pessoas vão em
lote, uma linha por afirmação, com a fonte na própria linha (`S248`/`S854`):

```
CREATE
LAST	Lpt	"Nome da Pessoa"
LAST	Dpt	"consultor(a) brasileiro(a)"
LAST	P31	Q5
LAST	P106	<QID da ocupação>
LAST	P108	<QID da Mirow>	S854	"<URL da fonte>"
LAST	P69	<QID da instituição>	S854	"<URL da fonte>"
```

Gero o arquivo final quando (a) o CV chegar e (b) o item da empresa existir — o `P108`
precisa do QID dela.

## O que fica travado, e em quem

| Passo | Em quem | Destrava o quê |
|---|---|---|
| 1ª edição + 50 edições na conta | **Mario** (lista pronta em `2026-08-25_wikidata-aquecimento-conta.md`) | o QuickStatements |
| Cartão CNPJ (Receita, gratuito) | **Mario** | `P6204` e `P571` com fonte forte |
| OK sobre a sede (`P159`) | **Mario** | o campo que mais importa contra o "somos alemães" |
| CV de Andreas (e do 2º mestrado) | **Andreas** | o item dele e o `P112` da empresa |
| Aprovação escrita do lote | **Felipe** | a publicação |
| `sameAs` do Wikidata no JSON-LD do site | eu, depois dos QIDs | vira onda própria (73+) |
