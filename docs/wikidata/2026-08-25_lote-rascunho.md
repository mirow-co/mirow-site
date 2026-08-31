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

---

## Atualização de 25/08/2026, fim do dia — as 50 edições estão feitas

O Mario completou **50 contribuições em 25/08**. Falta só o outro lado da regra: a
**1ª edição precisa ter 4 dias**. Como ela é de 25/08, o QuickStatements deve liberar em
**29/08/2026** (mesma hora da 1ª edição). Nada a fazer nesse intervalo além dos itens que
não dependem do relógio (cartão CNPJ, resposta sobre a sede, CV do Andreas).

**A conferir por medição** quando eu tiver o nome de usuário da conta (o e-mail não serve
para consultar): contagem de edições e o carimbo de hora da primeira, via
`Special:Contributions` / `list=usercontribs`. Enquanto não medir, a data acima é cálculo,
não fato verificado.

## Instituições — QIDs resolvidos na API em 25/08/2026

Vêm do `alumniOf` que já está publicado no site (constante `ALUMNI` do
`tools_onda6/111_geo_jsonld_lideres.py`, ondas 72 e 72b), então já passaram pela sua
confirmação com cada sócio.

| Pessoa | Instituição (como está no site) | QID |
|---|---|---|
| Andreas Mirow | Universidade Técnica de Berlim | `Q51985` |
| Felipe Diniz | University of Chicago | `Q131252` |
| Felipe Diniz | Fundação Getulio Vargas — EPGE | `Q5508996` (a FGV; a EPGE não tem item próprio conferido) |
| Raoni Morais | Instituto Militar de Engenharia | `Q1665208` |
| Raoni Morais | Universitat de Barcelona | `Q219615` |
| Raoni Morais | UFRJ | `Q586904` |
| Prof. Dr Stephan Friedrich | Universität Karlsruhe | `Q309988` (KIT) — **conferir**: o KIT é a entidade pós-fusão de 2009; pode existir item histórico separado para a Universität Karlsruhe. A API ficou limitada por excesso de requisições hoje |
| Prof. Dr Stephan Friedrich | Universität Mannheim | `Q317070` |
| Renato Alvarenga | Carnegie Mellon University — Tepper | `Q190080` (a universidade; a Tepper pode ter item próprio, a conferir) |
| Renato Alvarenga | Universidade de Brasília | `Q1330634` |

Falta, para fechar o lote das pessoas: o QID da **empresa** (só existe depois da criação à
mão), a ocupação (`P106`) e o CV do **Andreas** — inclusive a instituição do 2º mestrado.

## Sede — DECIDIDO pelo Mario em 25/08/2026

- **Sede do CNPJ: Rio de Janeiro** (Rua Lauro Müller, 116 — sala 1504). Fonte: cartão CNPJ,
  quando emitido; hoje o site já publica esse endereço na política de privacidade.
- **Escritório: São Paulo**, Av. Ibirapuera, 2033 — conjunto 133. Fonte: site.
- **Local de fundação: Rio de Janeiro** (`P740`), que é o que a Nossa História conta.

Na ficha entram as duas afirmações de local, cada uma com a sua fonte, em vez de escolher uma e
esconder a outra — é assim que o Wikidata trata pessoa jurídica com endereço legal num lugar e
operação em outro. A pergunta aberta na versão anterior deste arquivo está, portanto, fechada.

---

## Atualização de 31/08/2026 — o cartão CNPJ NÃO é obrigatório, e o dado já está medido

O Mario perguntou se o cartão era mesmo *sine qua non*. Não é, e eu estava repetindo o pacote
sem ter medido alternativa. Duas medições:

**1. O dado é público e legível por máquina.** A base do CNPJ da Receita Federal é dado aberto, e
há espelhos com URL estável por CNPJ. Consultados hoje, os dois concordam entre si:

| Campo | Valor | O que ele resolve |
|---|---|---|
| `cnpj` | 15353236000189 | `P6204` |
| `razao_social` | MIROW & CO. DO BRASIL CONSULTORIA LTDA | `P1448` (nome oficial); a etiqueta segue "Mirow & Co." |
| `data_inicio_atividade` | **2012-04-12** | `P571` — **bate exatamente** com o que o site publica |
| `descricao_situacao_cadastral` | ATIVA (desde 2012-04-12) | qualificador de estado, se quisermos |
| `natureza_juridica` | Sociedade Empresária Limitada | `P1454` (forma jurídica) |
| `cnae_fiscal` | 7020400 — consultoria em gestão empresarial | corrobora `P452` (indústria) |
| endereço | Rua Lauro Müller, 116, sala 1504, Botafogo, Rio de Janeiro/RJ, CEP 22290-160 | a sede do CNPJ, que o Mario confirmou |
| `capital_social` | 100.000 | opcional |

Fontes: `brasilapi.com.br/api/cnpj/v1/<cnpj>` e `minhareceita.org/<cnpj>` — os dois espelham o
dado aberto oficial e devolveram os mesmos valores. **Não havia divergência para arbitrar:** a
data de fundação do site já estava certa.

**2. A forma de referência que o Wikidata realmente usa para o CNPJ não é um PDF.** Medido por
SPARQL nas afirmações `P6204` existentes: **862** referências usam `P854` (URL de referência) com
`P813` (data de consulta), contra **59** com `P248` (citado em). Ou seja: URL estável + data de
consulta é o padrão da casa, e é o que este lote vai usar.

**O que o cartão ainda acrescenta, e por isso vale pedir sem pressa:** um PDF datado, emitido
pela própria Receita, para o caso de alguém contestar a afirmação depois. É reforço, não
pré-requisito. **O caminho crítico do Wikidata deixa de depender dele.**

**O que passa a ser o próximo passo real:** criar o item da empresa (à mão, pela interface) com
`P6204`, `P571`, `P1448`, `P1454`, `P159`, `P856`, referenciando a URL do espelho consultado com
a data de hoje — e então trocar as 5 ocorrências de `QMIROW` no lote das pessoas pelo QID novo.
