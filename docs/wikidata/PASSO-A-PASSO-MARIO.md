# Wikidata explicado em 2 minutos — e os seus 4 passos

> Escrito em 25/08/2026 para o Mario. Se você só quer saber o que fazer, pule para
> **"Os seus 4 passos"**. Companheiros deste arquivo:
> `2026-08-25_aquecimento-conta.md` (a lista de cliques) e
> `2026-08-25_lote-rascunho.md` (o rascunho técnico, não precisa ler).

## O que é o Wikidata

A Wikipédia é a enciclopédia de **textos**. O Wikidata é a base de **fatos** que fica atrás
dela: uma ficha por coisa do mundo, com campos preenchidos — nome, país, ano de fundação,
site oficial. Cada ficha tem um código, tipo `Q42`.

Quem lê essas fichas: a própria Wikipédia, o Google (aquele painel que aparece à direita da
busca) e os assistentes de IA. É lá que a máquina confere duas coisas: **que uma entidade
existe** e **que ela é diferente de outra de nome parecido**.

## Por que isso é problema nosso hoje

Medi hoje: buscar "Mirow & Co" no Wikidata devolve **zero resultados**. Não existe ficha da
firma. O que existe com o nome Mirow é uma **cidade alemã**, um **sobrenome alemão**, um
povoado e um **castelo polonês**.

Então, quando um assistente de IA precisa dizer o que é a Mirow & Co., ele não tem uma ficha
nossa para consultar — e cola no que encontra. É daí que sai a descrição de "consultoria
alemã" que a gente vem caçando desde o handoff do Felipe.

O conserto é criar a nossa ficha **com o CNPJ dentro**. O Wikidata tem um campo próprio para
CNPJ. Como CNPJ é único no Brasil, ele funciona como impressão digital: a partir dele a firma
passa a ser uma entidade distinta, e nenhuma máquina consegue mais nos confundir com a cidade
alemã ou com o Miro.

## Por que não é só "criar a ficha e pronto"

Duas travas, e nenhuma delas é técnica do nosso lado:

**1. A conta precisa amadurecer.** O Wikidata é editado por voluntários, e por isso existe
regra anti-robô: a ferramenta que cria fichas **em lote** (é assim que entram as fichas das
pessoas, de uma vez) só aceita conta com **pelo menos 50 edições** e cuja **primeira edição
tenha 4 dias ou mais**. A conta `dev@mirow.com.br` foi criada em 24/08 e ainda tem **zero**
edição. Enquanto ela não amadurecer, o cronograma não anda — e conta criada no dia da
publicação simplesmente não roda o lote.

**2. O cartão CNPJ.** No Wikidata, fato sobre você mesmo precisa de fonte de fora: o nosso
site não vale como prova do nosso próprio CNPJ nem da data de fundação. O cartão CNPJ da
Receita vale, é grátis e sai na hora.

## Os seus 4 passos

### Passo 1 — hoje, 10 minutos: fazer as primeiras edições

É o passo que **inicia o relógio de 4 dias**. Quanto mais cedo, melhor.

1. Entrar em `wikidata.org` com a conta `dev@mirow.com.br`.
2. Abrir o arquivo `docs/wikidata/2026-08-25_aquecimento-conta.md`.
3. Em cada linha da tabela: clicar no link, colar no campo a descrição da última coluna,
   clicar em **Definir descrição**. Uns 10 segundos por linha.
4. Fazer umas 15 ou 20 hoje. Não precisa terminar.

O link de cada linha abre um formulário com **um campo e um botão**, já em português — não
tem nada para procurar na tela.

**O que você vai estar editando:** rios brasileiros que estão sem descrição em português.
São edições pequenas e úteis de verdade — o tipo (rio) e o estado vêm do próprio dado da
ficha, então não tem como errar. Isso importa: conta que enche o Wikidata de lixo é
bloqueada, e aí perdemos a conta em vez de amadurecê-la.

### Passo 2 — amanhã e depois: chegar a 50 edições

Mesma coisa do passo 1, em 2 ou 3 sessões. A lista tem 60 linhas para dar folga (e existem
397 candidatos, se precisar de mais).

### Passo 3 — hoje ou amanhã, 5 minutos: emitir o cartão CNPJ

No site da Receita Federal, gratuito. Salve o PDF e me diga onde ele está. Ele é a fonte de
duas informações da ficha: o **CNPJ** e a **data de fundação**.

Atenção a uma possibilidade: se a data do cartão for diferente de **12/04/2012** (o que o
site publica hoje), **o cartão manda** — e aí a correção é no site, não na ficha.

### Passo 4 — 1 minuto: me responder uma pergunta

**A sede da firma, na ficha, é São Paulo (Av. Ibirapuera, 2033), certo?**

Pergunto porque o site publica **os dois** endereços: o do Rio (Rua Lauro Müller) como
endereço legal do CNPJ, e o de São Paulo como escritório. No Wikidata os dois cabem, em
campos diferentes — **sede = São Paulo** e **local de fundação = Rio de Janeiro**. Só preciso
do seu "sim", porque errar esse campo é exatamente o que alimenta o "eles são alemães".

## Depois dos seus 4 passos, quem faz o quê

| Quem | O quê |
|---|---|
| **Andreas** | manda o checklist de CV dele (e diz em qual universidade foi o 2º mestrado, aquele do Fulbright — é a única lacuna que sobrou no site) |
| **eu** | gero o arquivo do lote com todas as fichas, campo a campo, cada afirmação com a sua fonte |
| **você** | confere o arquivo campo a campo contra os CVs |
| **Felipe** | aprova por escrito — sem isso nada é publicado |
| **você** | cria a ficha da empresa pela tela (é uma só) e roda o lote das pessoas |
| **eu** | acrescento no site o link para a nossa ficha do Wikidata (isso vira uma onda normal) |

Eu não publico nada no Wikidata — a regra é do pacote do Felipe e eu concordo com ela.
E nunca entram na ficha: data de nascimento completa, CPF, e-mail, telefone ou endereço
residencial de ninguém.

## O que muda quando terminar

Passa a existir uma ficha pública dizendo: *Mirow & Co., consultoria brasileira, CNPJ tal,
fundada em 2012, sede em São Paulo, site mirow.com.br* — com as fichas dos sócios ligadas a
ela. É esse registro que o Google e os assistentes de IA leem quando alguém pergunta quem
somos. A medição comparativa está marcada para **10/09**, com as mesmas 8 perguntas do
protocolo do Felipe.

## Glossário (5 palavras que aparecem nos outros arquivos)

| Palavra | O que é |
|---|---|
| **item** (ou ficha) | uma coisa no Wikidata; tem código `Q` + número |
| **propriedade** | um campo da ficha; tem código `P` + número (ex.: `P6204` é o CNPJ) |
| **declaração** | um campo preenchido com um valor e a fonte dele |
| **QuickStatements** | a ferramenta que cria/edita várias fichas de uma vez; é ela que exige as 50 edições e os 4 dias |
| **SPARQL** | a linguagem de consulta do Wikidata; foi como eu montei a lista de rios e medi que a firma não existe lá |
