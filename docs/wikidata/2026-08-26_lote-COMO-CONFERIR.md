# Lote das 5 pessoas — como conferir antes de rodar

> Arquivo do lote: [`2026-08-26_lote-wikidata.txt`](2026-08-26_lote-wikidata.txt) — 67 linhas,
> 5 itens, formato QuickStatements v1. **Nada foi publicado**: o Claude não publica no Wikidata.
>
> Gates do pacote do Felipe, na ordem: (1) ~~o item da **empresa** é criado à mão~~ **feito,
> `Q141241992`**; (2) ~~trocar o placeholder~~ **feito**; (3) o Mario confere campo a campo
> contra os CVs; (4) **o Felipe aprova por escrito**; (5) só então o lote roda.

## O item da empresa existe: **Q141241992** (31/08/2026)

O placeholder acabou: as 5 ocorrências de `QMIROW` já foram trocadas por **`Q141241992`** no
arquivo do lote. Nada mais a substituir antes de colar no QuickStatements.

## O que cada pessoa recebe

| Pessoa | `P69` educado em | `P108` empregador (além da Mirow) |
|---|---|---|
| Andreas Mirow | TU Berlin `Q51985` · Stevens `Q657222` | McKinsey `Q310207` · Aracruz `Q624652` · Booz Allen `Q893221` |
| Felipe Diniz | Chicago `Q131252` · FGV `Q5508996` · PUC-Rio `Q1857293` | McKinsey `Q310207` · Booth `Q2963304` |
| Prof. Dr. Stephan Friedrich von den Eichen | Karlsruhe pré-fusão `Q29426438` · Mannheim `Q317070` | Univ. Bremen `Q500692` · Malik `Q33121466` · Arthur D. Little `Q709066` |
| Raoni Morais | Barcelona `Q219615` · UFRJ `Q586904` | SLB/Schlumberger `Q1425316` |
| Renato Alvarenga | Tepper `Q7701381` · UnB `Q1330634` | Enel Distribución Chile `Q5779688` · McKinsey `Q310207` |

Todos recebem também `P31 → Q5` (ser humano) e `P106 → Q16849727` (*business consultant*), com
datas de início e fim (`P580`/`P582`) nos vínculos de emprego, na precisão que o LinkedIn dá
(mês, ou ano quando só o ano é declarado).

## O que NÃO entrou, de propósito

- **Nenhum dado pessoal sensível:** sem data de nascimento, CPF, e-mail, telefone ou endereço.
- **Sem nacionalidade (`P27`)**, porque não temos fonte para isso — e é justamente o campo que,
  preenchido no chute, recria o problema que estamos consertando.
- **Empregadores sem item no Wikidata:** Catavento, o consórcio do Rio (CIRJ), RC Alvarenga,
  Cam, Ampla, Arcoplan, IBP e a IMP (Innovative Management Partner) do Stephan. Afirmação que
  aponta para nada não ajuda a máquina.
- **Monitor Deloitte** ficou fora porque há **dois** itens candidatos no Wikidata e escolher no
  chute é pior que omitir. Resolver e acrescentar depois, se valer.
- **O IME do Raoni** fica fora do lote até aparecer no perfil dele (ele vai incluir). No site
  ele **está**, com a sua confirmação.

## A fraqueza conhecida deste lote: a fonte

Toda afirmação leva `S854` apontando para o **perfil do LinkedIn** da pessoa. Isso é fonte
**autodeclarada**, e no Wikidata item de pessoa cuja única referência é o próprio LinkedIn pode
ser contestado por falta de notabilidade — o risco não é o lote falhar, é o item ser proposto
para exclusão depois.

O reforço natural é o **CSV de imprensa** (43 matérias, mestre no repo privado): referência de
terceiro é o que sustenta notabilidade. O arquivo publicado que temos aqui
(`tools/imprensa-publicada.json`) traz data, veículo, título e URL, mas **não traz autor** —
então não consigo, deste lado, dizer quais matérias citam quem. Quem tem o mestre da curadoria
resolve isso em minutos, e vale fazer **antes** de rodar o lote, não depois.
