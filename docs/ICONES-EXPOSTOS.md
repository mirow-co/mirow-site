# Ícones e imagens que o site expõe para fora

> **NO AR desde 20/08/2026** (produção e staging em `v=83`, suíte 215 OK no gate do deploy).
>
> Levantamento e correção de 20/08/2026, sobre as **109 páginas de conteúdo** do
> `sitemap.xml` (os 177 stubs de redirect ficam fora por construção). Nasceu de uma pergunta
> do Mario — *"que símbolo é esse que aparece do lado do nosso site no google??"* — e o pedido
> seguinte foi: *"não apenas o favicon, mas toda identidade visual do site nos ícones que ele
> oferece (link que aparece para whatsapp, etc.)"*, e depois *"corrija tudo já, de uma vez"*.
>
> Regra de leitura: **superfície** é onde o público vê; **tag** é o que a declara; toda coluna
> de medição é pixel contado ou arquivo aberto, nunca declaração lida (P2.1).

---

## As 14 superfícies, e o estado de cada uma

| # | Superfície (onde o público vê) | Tag / mecanismo | Estado |
|---|---|---|---|
| 1 | Aba do navegador · resultado do Google | `<link rel="icon" sizes="32x32">` | ✅ onda 68 |
| 2 | Aba retina · atalho Android | `<link rel="icon" sizes="192x192">` | ✅ onda 68 |
| 3 | Favorito legado | `<link rel="shortcut icon">` (`.ico`) | ✅ onda 68 |
| 4 | `/favicon.ico` pedido **por convenção** | nenhuma tag | ✅ onda 68 (**era 404**) |
| 5 | Tela de início do iPhone/iPad | `<link rel="apple-touch-icon">` | ✅ onda 68 |
| 6 | Bloco do menu Iniciar do Windows | `<meta name="msapplication-TileImage">` | ✅ onda 68 |
| 7 | **WhatsApp · LinkedIn · Slack · Telegram · iMessage** | `<meta property="og:image">` | ✅ onda 68 |
| 8 | Cartão do X/Twitter | `twitter:card` + `twitter:image` | ✅ onda 68 |
| 9 | Painel de conhecimento do Google | JSON-LD `Organization.logo` | ✅ onda 68 |
| 10 | Barra de endereço do Chrome no Android | `<meta name="theme-color">` | ✅ onda 68 (**era ausente**) |
| 11 | Cor do bloco do Windows | `<meta name="msapplication-TileColor">` | ✅ onda 68 (**era ausente**) |
| 12 | Aba fixada do Safari | `<link rel="mask-icon">` | ✅ onda 68 (**era ausente**) |
| 13 | Instalar no Android (nome + ícone) | `<link rel="manifest">` | ✅ onda 68 (**era ausente**) |
| 14 | Marca visível no cabeçalho | `<h1><img>` `marca-mirow-co.svg` | ✅ (alt corrigido na onda 60) |

Sentinelas: **S171** (tinta dos ícones), **S172** (cartão de link), **S173** (identidade do
navegador), **S174** (uma `Organization` só).

---

## §1 — Favicon: a wordmark tinha 0,00% de tinta

Era a wordmark inteira — `MIROW & CO.`, 11 caracteres — espremida no quadro do ícone.

| Arquivo | Antes | Depois |
|---|---|---|
| `…-32x32.png` | **0,00%** de tinta branca | 7,62% |
| `…-180x180.png` | — | 10,10% |
| `…-192x192.png` | **0,29%** (caixa de 125×**11** px) | 10,51% |
| `…-270x270.png` | — | 10,41% |
| `themes/mirow/favicon.ico` | 16×16 só | 16+32+48, 8,59% |
| `favicon.ico` (raiz) | **404** | 16+32+48 |

A 32px cada caractere recebe ~3px e o antialias apaga tudo: o ícone servido era um quadrado
navy **vazio**, que o Google ainda recorta em círculo. Fonte nova: `LogoNeg.png` (navy
`#020E66` medido, alfa 255 em todo pixel), em `tools_onda6/dados/marca-mirow-m-neg.png`.

> **A lição, e ela é geral: favicon não aceita wordmark.** O que cabe em 16px é UM glifo — é
> aritmética de pixel por caractere, não gosto. O contra-exemplo mora no mesmo repo: o
> `og-mirow.png` de 1200×630 **é** a wordmark e ali está **certo**, porque o cartão renderiza a
> ~400px. Mesmo desenho, duas superfícies, dois vereditos; o que decide é o tamanho de render.

---

## §2 — `og:image`: o preview de WhatsApp

Três defeitos, e o do meio é o instrutivo.

**(a) 6 páginas não tinham `og:image` nenhuma** — `/pt/imprensa/`, `/en/press/`, `/de/presse/`
e as 3 políticas de privacidade. Compartilhadas no WhatsApp saíam sem imagem, e imprensa é a
página que se manda para jornalista. Passam a usar o `og-mirow.png`.

**(b) 58 páginas declaravam metadado que mentia sobre o próprio arquivo.** Quase todas diziam
`og:image:type = image/png` para arquivo que hoje é **WebP** — resíduo das ondas 61/62c, que
converteram a imagem e não mexeram na tag. E as 3 homes diziam `width 663 / height 394` para o
`og-mirow.png`, que é **1200×630**, com `type image/jpeg` para um **PNG**. Valor gêmeo
clássico: a dimensão vivia em dois lugares e divergiu calada. Como o scraper do Facebook usa
o width/height declarado para decidir se desenha o cartão grande, a home pedia cartão grande e
se descrevia como pequena.

Agora width/height/type são **recalculados do arquivo aberto** a cada execução do
`141_cartao_de_link.py`. Não existe número digitado — a classe de divergência não pode voltar.

**(c) 20 `og:image` fora do padrão de cartão** ganharam derivada 1200×630 controlada por nós,
em vez de deixar o scraper recortar às cegas. A regra é explícita: mais de 200 KB, ou mais
largo que 1600px, ou razão fora de 1,905 por mais de 15%, ou formato que não seja JPEG/PNG.

| Original | Era | Virou |
|---|---|---|
| `Imagem1-scaled.jpg` | 2560×1475, **927 KB** | 1200×630, 113 KB |
| `Automotive-industry-scaled.jpg` | 2560×1920 (4:3), 686 KB | 1200×630, 117 KB |
| `energia-1.jpg` | 2560×1707, 679 KB | 1200×630, 115 KB |
| `imagem_gerada-….webp` | 1792×493 (**razão 3,63**) | 1200×630, 116 KB |

O arquivo original **não** é substituído — segue servindo a página. Só o `og:image` muda.

**(d) `og:image:alt` e `twitter:image`** entraram nas 109 (eram 0). O alt é derivado do que a
página já diz: nome e cargo nas de líder, `Mirow & Co.` no cartão institucional, o `og:title`
sem o sufixo do site nas demais.

### As 18 páginas de líder ganharam cartão próprio

Usavam o **retrato a 232×246** — abaixo do mínimo do cartão grande, nas mesmas páginas que
declaram `summary_large_image`. Agora há 6 cartões 1200×630 (o cargo está em inglês nas três
línguas, então pt/en/de compartilham), em Titillium Web extraída dos `.woff2` do próprio repo,
com nome, cargo, foto e a marca. JPEG q90, ~50 KB.

A foto entra a **1,4×** (324×344), não esticada para 630px de altura: não existe original maior
no espelho, e 2,7× de upscale num rosto que representa um sócio fica borrado.

---

## §3 — De quatro `Organization` para uma

O site declarava **quatro** entidades de organização ao Google:

| Nó | `@id` | `logo`? | endereço/descrição? |
|---|---|---|---|
| Yoast, pt | `/pt/#organization` | ✅ | ❌ |
| Yoast, en | `/en/#organization` | ✅ | ❌ |
| Yoast, de | `/de/#organization` | ✅ | ❌ |
| onda 59 | `https://mirow.com.br/#organization` | ❌ | ✅ |

Quatro `@id` são quatro entidades, não uma vista de quatro ângulos. Nenhuma dizia ao mesmo
tempo quem somos **e** qual é nossa marca. Agora todas apontam para o `@id` canônico, e o nó
rico (endereço, descrição, fundação, sócios) passou a ser escrito também nas **3 homes** — ele
só vivia nas 3 listagens de líder, a dois cliques da entrada.

O `logo` também mudou de arquivo. O anterior era `logo_mirow_azul_e_branco1svg.svg`, e aquele
arquivo tem `viewBox="0 0 210 297"` com `width="210mm" height="297mm"` — é uma prancha **A4**,
não um logo. Era por isso que a dimensão declarada parecia torta: descrevia a folha, não a
marca. Agora é o raster quadrado do "m", 512×512, o mesmo glifo do favicon e do manifest.

---

## §4 — Michael Munch saiu do site

Pedido do Mario no meio da onda: *"inclusive pode retirar o michael munch totalmente da
pagina, de tudo. ele nao trabalha mais aqui desde ontem"* (deixou a firma em 19/08/2026).
Mesma regra da onda 33 — "quem saiu sai do site" —, com uma diferença que mudou o trabalho:
os 4 daquela onda já estavam fora da listagem e do JSON-LD; ele estava **dentro**.

Pegada medida antes de mexer, **16 arquivos**: 3 páginas de perfil, 3 listagens (card + nó
`Person`), 3 homes (nó `Person`, que entrou nesta mesma onda), 5 stubs, `sitemap.xml`,
`busca-indice.json` e 2 assets. Depois: **zero referência** em `public/`, e balanço de `<div>`
preservado em todas as 6 páginas tocadas (medido antes/depois contra o `git`).

Três coisas que o pedido revelou e que valem mais que a remoção em si:

1. **O modal de bio sobrevive à remoção do card** — são elementos separados, e foi o achado
   da onda 33 se repetindo. Pior: o **id do modal difere entre as línguas** (`modal_591` em
   pt, `modal_michael-munch` em en/de), porque a troca de slug da onda 59 só tocou o PT. Uma
   primeira versão do script fixava o id e limpou **1 de 6 páginas**. Agora o modal é
   localizado pelo **conteúdo**, com varredura balanceada de `<div>`.
2. **A meta description das 3 listagens tinha a lista de líderes hardcoded** — valor gêmeo
   com o `PAGINAS` do `110`, a fonte que o JSON-LD e os cartões usam. O card saiu do HTML, o
   `Person` saiu do JSON-LD, e as 3 frases seguiram anunciando o nome dele. Agora são
   **montadas** a partir de `PAGINAS`.
3. **A `S151` estava cega há um mês.** Ela cobrava que nada referenciasse o slug antigo
   `591`, e a página do Michael o referenciava em **8 lugares** do JSON-LD do Yoast — desde a
   onda 59, **escapados** como `https:\/\/…\/591\/`. A asserção procurava a forma limpa.
   Quem os revelou foi o `143`, ao reserializar o JSON com `json.dumps` do Python, que não
   escapa barra. A `S151` trocou de sujeito e agora cobra os 8 caminhos como stub de um salto.

## §4 — O que ficou de fora, e por quê

- **`og:image` com `?v=`**: as derivadas e os cartões **não** entram no cache busting. O
  scraper indexa pela URL; trocar a URL a cada onda invalidaria preview que já funciona.
- **O `logo_mirow_azul_e_branco1svg.svg`** não foi apagado — só deixou de ser citado no schema.
- **`/pt/#primaryimage`** e outros `ImageObject` de artigo seguem com URL relativa. É
  pré-existente, não é superfície de ícone, e não estava no pedido.

---

## Como refazer a medição

```bash
python tools/verificacoes.py . --so=S17
```

E a sequência que produz o estado atual, na ordem (o 141 depende dos dois primeiros):

```bash
python tools_onda6/138_favicon_marca.py . && python tools_onda6/139_og_cards_lideres.py . && python tools_onda6/140_og_image_derivada.py . && python tools_onda6/111_geo_jsonld_lideres.py . && python tools_onda6/141_cartao_de_link.py . && python tools_onda6/142_identidade_navegador.py . && python tools_onda6/143_schema_organizacao_unica.py . && python tools_onda6/27_cache_busting.py .
```
