# Como criar o item da Mirow & Co. no Wikidata — guia para quem nunca usou

> **FEITO em 31/08/2026: o item é [Q141241992](https://www.wikidata.org/wiki/Q141241992).**
> O Mario criou e preencheu as 7 declarações, com referência nas 4 que vêm do registro da
> Receita — conferido por mim na API. Ficaram **duas correções pequenas**, na seção
> "O que ficou para arrumar", no fim deste guia. O guia continua aqui porque serve de
> modelo para o próximo item que a firma criar.

> Escrito em 31/08/2026 para o Mario, olhando a interface real, logado na conta **DevMirow**.
> Tempo: 20 a 30 minutos, sem pressa. Nada aqui é irreversível: **tudo no Wikidata tem
> histórico e pode ser desfeito**, como na Wikipédia.

## Antes de começar — o estado da conta, medido hoje

| O quê | Valor |
|---|---|
| Usuário | **DevMirow** |
| Edições | **50** |
| Conta criada | 25/08/2026 03:09 UTC |
| Primeira edição | 25/08/2026 21:36 UTC |
| Grupo | **`autoconfirmed`** ✅ |

O `autoconfirmed` é o carimbo que o Wikidata dá quando a conta passa dos 4 dias e das edições
mínimas. **Está concedido** — o QuickStatements (o lote das pessoas) já aceita a conta. Esse era
o relógio que estávamos esperando, e ele fechou.

## O vocabulário, em 4 palavras

| Palavra | O que é |
|---|---|
| **Item** (ou objeto) | a ficha de uma coisa. Tem código `Q` + número. A da Mirow ainda não existe |
| **Rótulo** | o nome da coisa. O nosso: `Mirow & Co.` |
| **Descrição** | uma linha que distingue de homônimos. É por isso que ela existe |
| **Declaração** | um campo preenchido: *propriedade* (código `P`) + valor. Ex.: `P6204` (CNPJ) = 15353236000189 |

E **referência** é a fonte de uma declaração — de onde você tirou aquilo. É o que separa um item
sério de um item que alguém apaga depois.

---

## Passo 1 — criar o item (2 minutos)

Abra **<https://www.wikidata.org/wiki/Special:NewItem?uselang=pt>** (o `?uselang=pt` deixa a
interface em português). O formulário tem quatro campos e um botão **Criar**:

| Campo | O que preencher |
|---|---|
| Língua | `pt` |
| **Rótulo** | `Mirow & Co.` |
| **Descrição** | `consultoria estratégica brasileira` |
| Nomes alternativos | `Mirow & Co. do Brasil Consultoria Ltda\|Mirow and Co.\|Mirow` |

Os nomes alternativos são separados por **barra vertical** (`|`), como o próprio formulário diz.

> ⚠️ **A barra vertical só funciona NESTE formulário de criação.** Na tabela "em mais línguas"
> de um item que já existe, o campo de nomes alternativos **não divide** pela barra: ele grava
> a linha inteira, com as barras, como um apelido só. Foi o que aconteceu em 31/08 (ver
> "O que ficou para arrumar"). Lá, cada apelido entra **um por vez**.

Clique em **Criar**. Pronto: o item existe e ganhou um número `Q`. **Anote esse número** — é ele
que vai substituir o `QMIROW` no lote das pessoas.

### Logo depois, acrescente a etiqueta em inglês e alemão

Na página do item, a primeira caixa mostra uma tabela de línguas com um link **editar** à
direita. Clique e preencha:

| Língua | Rótulo | Descrição |
|---|---|---|
| inglês | `Mirow & Co.` | `Brazilian strategy consulting firm` |
| alemão | `Mirow & Co.` | `brasilianische Strategieberatung` |

Isso importa mais do que parece: é a descrição em inglês que um assistente de IA lê quando
alguém pergunta em inglês quem somos — e é exatamente onde hoje ele inventa "alemã".

---

## Passo 2 — as declarações (o miolo)

Abaixo dos rótulos há a seção **Declarações**. No fim dela existe um link
**+ adicionar declaração**. O fluxo é sempre o mesmo, e você vai repeti-lo 8 vezes:

1. Clicar em **+ adicionar declaração**;
2. no campo da esquerda, digitar a propriedade (pode digitar o código `P6204` ou o nome
   `CNPJ`) e **escolher na lista** que aparece;
3. no campo da direita, digitar o valor e, quando o valor for outro item, **escolher na lista**
   (o número `Q` aparece ao lado — confira que é o certo);
4. clicar em **publicar**.

**Nunca aceite a primeira sugestão sem olhar o `Q`.** Escolher o item errado é o único erro
chato de desfazer aqui.

### As 8 declarações, na ordem

| # | Propriedade | Valor | Observação |
|---|---|---|---|
| 1 | `P31` instância de | **`Q2089936`** (*consulting company*) | diz o que a coisa é |
| 2 | `P6204` CNPJ | `15353236000189` | **só dígitos**, sem ponto, barra ou traço. É a âncora que nos separa da cidade alemã |
| 3 | `P17` país | **`Q155`** (Brasil) | |
| 4 | `P571` data de fundação | `12 de abril de 2012` | ver a nota sobre datas abaixo |
| 5 | `P1448` nome oficial | `MIROW & CO. DO BRASIL CONSULTORIA LTDA` | escolha a língua `pt` no seletor que aparece |
| 6 | `P159` sede | **`Q8678`** (Rio de Janeiro) | é a sede do CNPJ, como você definiu |
| 7 | `P856` site oficial | `https://mirow.com.br/pt/` | |
| 8 | `P112` fundador | *o item do Andreas* | **deixe por último**: só depois que o lote das pessoas rodar é que esse item existe |

**Sobre a data (nº 4):** o Wikidata pede a precisão. Digite `2012-04-12` e confira que ele
entendeu **12 April 2012** (dia), não "2012" (ano). Se ele mostrar só o ano, apague e digite de
novo no formato `12 April 2012`.

---

## Passo 3 — a referência (é isto que faz o item sobreviver)

Cada declaração tem, embaixo dela, **0 referência** com uma setinha. Clique ali, depois em
**+ adicionar referência**, e preencha **duas** propriedades na mesma referência:

| Propriedade | Valor |
|---|---|
| `P854` URL de referência | `https://minhareceita.org/15353236000189` |
| `P813` data de consulta | `31 de agosto de 2026` |

Faça isso, **no mínimo**, nas declarações **2 (CNPJ), 4 (data de fundação), 5 (nome oficial) e
6 (sede)** — são as que vêm do registro da Receita. Para a **7 (site oficial)** a referência
pode ser o próprio site.

Por que essa URL e não um PDF: medi como o Wikidata referencia CNPJ nas 900 e poucas afirmações
que já existem lá — **862 usam URL + data de consulta**, contra 59 de outras formas. URL estável
com data é o padrão da casa. O cartão CNPJ continua sendo um reforço bem-vindo se alguém
contestar, mas não é pré-requisito de nada.

---

## Passo 4 — me avisar o número `Q`

Com o `Q` da empresa em mãos, eu troco as 5 ocorrências de `QMIROW` no lote das pessoas
([`2026-08-26_lote-wikidata.txt`](2026-08-26_lote-wikidata.txt)), você confere pela tabela do
[COMO-CONFERIR](2026-08-26_lote-COMO-CONFERIR.md), o Felipe aprova por escrito, e o lote roda.

---

## Se algo der errado

- **Errou um valor?** Clique em **editar** na própria declaração, corrija e publique. Se quiser
  apagar, o mesmo modo de edição tem **remover**.
- **Criou duas fichas sem querer?** Não apague: as duas se **fundem** em
  `Special:MergeItems`, que preserva o histórico das duas.
- **Alguém marcou o item para exclusão?** Acontece quando o item não tem referência de fonte
  independente. É por isso que o passo 3 não é opcional — e por isso vale, depois, acrescentar
  como referência duas ou três matérias de imprensa do nosso levantamento.
- **Na dúvida sobre um `Q`**, abra `https://www.wikidata.org/wiki/Q<numero>` e leia a descrição
  antes de usar.

## O que ficou para arrumar no Q141241992 (duas coisas pequenas)

Estado medido na API em 31/08/2026 — **as 7 declarações estão certas** (`P31` `Q2089936`,
`P6204` 15353236000189, `P17` `Q155`, `P571` 12/04/2012 com precisão de dia, `P1448` a razão
social, `P159` `Q8678` Rio de Janeiro, `P856` o site), e as 4 que vêm do registro da Receita
estão com `P854` + `P813` como deviam. Só sobrou isto:

**1. `P856` (site oficial) está DUPLICADO.** Há duas declarações com o mesmo valor
`https://mirow.com.br/pt/`: uma com referência e outra **sem nenhuma**. Apague a que está sem
referência — abra a declaração, **editar**, **remover**.

**2. Um apelido malformado, em 3 línguas.** Em `inglês`, `inglês americano` e `padrão para
todas as línguas`, existe um apelido literal
`Mirow & Co. do Brasil Consultoria Ltda|Mirow and Co.|Mirow` — com as barras dentro. É culpa da
instrução deste guia (ver o aviso no Passo 1): a barra só divide no formulário de criação.
Em `português` e `português do Brasil` ficou correto, com os três apelidos separados.

Conserto: na tabela de línguas, **editar**, apagar esse apelido comprido nas três línguas e
deixar `Mirow & Co. do Brasil Consultoria Ltda`, `Mirow and Co.` e `Mirow` como três apelidos
separados (nas línguas onde já estão separados, não mexa).

**Opcionais, quando der vontade:** `P1454` (forma jurídica) = *sociedade limitada*, e `P452`
(indústria) = consultoria de gestão — os dois saem do mesmo registro da Receita que já
referenciamos. E `P112` (fundador) quando o item do Andreas existir.

## O que NÃO fazer

- Não preencher **nacionalidade, data de nascimento, CPF, e-mail, telefone ou endereço** de
  pessoa nenhuma. Nada disso entra, em item nenhum.
- Não escrever texto de marketing na descrição: ela é uma linha curta que distingue de
  homônimos, não uma frase de posicionamento. `consultoria estratégica brasileira` basta.
- Não inventar valor que a gente não mediu. Campo ausente é melhor que campo errado — é a mesma
  regra que a gente segue no site.
