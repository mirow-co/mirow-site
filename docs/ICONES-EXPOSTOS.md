# Ícones e imagens que o site expõe para fora

> Levantamento medido em 20/08/2026 sobre as **109 páginas de conteúdo** do `sitemap.xml`
> (os 177 stubs de redirect ficam fora por construção). Nasceu de uma pergunta do Mario —
> *"que símbolo é esse que aparece do lado do nosso site no google??"* — e virou inventário
> porque ele pediu: *"não apenas o favicon, mas toda identidade visual do site nos ícones
> que ele oferece (link que aparece para whatsapp, etc.)"*.
>
> Regra de leitura: **superfície** é onde o público vê; **tag** é o que a declara; a coluna
> de medição é pixel contado, não declaração lida (P2.1).

---

## O quadro geral

| # | Superfície (onde o público vê) | Tag / mecanismo | Arquivo | Estado |
|---|---|---|---|---|
| 1 | Aba do navegador · resultado do Google | `<link rel="icon" sizes="32x32">` | `cropped-favicon-mirow-32x32.png` | ✅ onda 68 |
| 2 | Aba em tela retina · atalho Android | `<link rel="icon" sizes="192x192">` | `cropped-favicon-mirow-192x192.png` | ✅ onda 68 |
| 3 | Favorito legado · `/favicon.ico` pedido por tag | `<link rel="shortcut icon">` | `themes/mirow/favicon.ico` | ✅ onda 68 |
| 4 | `/favicon.ico` pedido **por convenção** | nenhuma tag — o navegador e o crawler batem no caminho | `favicon.ico` (raiz) | ✅ onda 68 (**não existia**) |
| 5 | Tela de início do iPhone/iPad | `<link rel="apple-touch-icon">` | `cropped-favicon-mirow-180x180.png` | ✅ onda 68 |
| 6 | Bloco do menu Iniciar do Windows | `<meta name="msapplication-TileImage">` | `cropped-favicon-mirow-270x270.png` | ✅ onda 68 |
| 7 | **Preview de link: WhatsApp, LinkedIn, Slack, Telegram, iMessage** | `<meta property="og:image">` | 30 imagens distintas | ⚠️ ver §2 |
| 8 | Cartão do X/Twitter | `twitter:card` = `summary_large_image` | `twitter:image` **ausente** | ⚠️ ver §3 |
| 9 | Painel de conhecimento do Google | JSON-LD `Organization.logo` | `logo_mirow_azul_e_branco1svg.svg` | ⚠️ ver §4 |
| 10 | Barra de endereço do Chrome no Android | `<meta name="theme-color">` | — | ❌ ausente nas 109 |
| 11 | Cor do bloco do Windows | `<meta name="msapplication-TileColor">` | — | ❌ ausente nas 109 |
| 12 | Aba fixada do Safari | `<link rel="mask-icon">` | — | ❌ ausente nas 109 |
| 13 | Nome e ícone ao instalar no Android | `<link rel="manifest">` | — | ❌ ausente nas 109 |
| 14 | Marca visível no cabeçalho | `<h1><img>` | `marca-mirow-co.svg` | ✅ (alt corrigido na onda 60) |

---

## §1 — O que a onda 68 consertou, e a lição de classe

O favicon era a **wordmark inteira** — `MIROW & CO.`, 11 caracteres — espremida no quadro
do ícone. Medido, em tinta branca sobre o quadro:

| Arquivo | Antes | Depois |
|---|---|---|
| `…-32x32.png` | **0,00%** | 7,62% |
| `…-180x180.png` | — | 10,10% |
| `…-192x192.png` | **0,29%** (caixa de 125×**11** px) | 10,51% |
| `…-270x270.png` | — | 10,41% |
| `themes/mirow/favicon.ico` | 16×16 só | 16+32+48, 8,59% |
| `favicon.ico` (raiz) | **404** | 16+32+48, 8,59% |

**Zero por cento.** O 32×32 não tinha um único pixel acima de 200 de brilho: a 32px cada
caractere recebe ~3px e o antialias apaga tudo. O ícone servido era um quadrado navy vazio,
que o Google ainda recorta em círculo — por isso o próprio dono da marca não o reconheceu.

A fonte nova é `LogoNeg.png` (1150×1150, navy `#020E66` medido, alfa 255 em todo pixel),
copiada para `tools_onda6/dados/marca-mirow-m-neg.png`. O gerador é
`tools_onda6/138_favicon_marca.py`, idempotente, e confere dimensão e tinta **do que gravou**.

> **A lição transferível: favicon não aceita wordmark.** O que cabe em 16px é UM glifo. Não
> é preferência estética, é aritmética de pixel por caractere. E o contra-exemplo está no
> mesmo repo: o `og-mirow.png` (§2) é a wordmark, e ali está **certo**, porque o cartão de
> preview renderiza a ~400px. O mesmo desenho, duas superfícies, dois vereditos — o que
> decide é o tamanho de render, nunca "é o nosso logo".

Asserção: **S171**, que mede a **tinta** de todo ícone declarado (lendo a lista do próprio
HTML, não de constante) e exige o frame de 48px no `.ico`. Cobrar o nome do arquivo passaria
verde no dia em que alguém regenerasse os ícones da wordmark outra vez.

---

## §2 — `og:image`: o preview de WhatsApp (o buraco maior)

São **30 imagens distintas** em 109 páginas. Três problemas, em ordem de gravidade:

**(a) 6 páginas não têm `og:image` nenhuma.** Compartilhadas no WhatsApp, saem sem imagem:

```
/pt/imprensa/            /en/press/               /de/presse/
/pt/politica-de-privacidade/   /en/privacy-policy/   /de/datenschutzrichtlinie/
```

As três de imprensa são as que mais doem: a onda 65 acabou de levar a vitrine de 29 para 43
matérias, e é justamente a página que se manda para jornalista.

**(b) 6 páginas de líder usam a foto do líder a 232×246.** Abaixo do que o cartão grande
pede; o preview cai para miniatura ou não aparece.

| Página | `og:image` | Dimensão |
|---|---|---|
| líderes (6 páginas) | `Andreas-Mirow.webp`, `Felipe-Diniz-1.webp`, `Michael-Munch.png`, `prof.webp`, `Raoni-Moraes.png`, `Renato-Alvarenga-1.png` | **232×246** |

**(c) imagens de artigo enormes e com recorte descontrolado** como `og:image`:

| Arquivo | Dimensão | Peso |
|---|---|---|
| `Imagem1-scaled.jpg` | 2560×1475 | **927 KB** |
| `Automotive-industry-scaled.jpg` | 2560×1920 | 686 KB |
| `energia-1.jpg` | 2560×1707 | 679 KB |
| `embedded-finance.jpg` | 2560×1362 | 268 KB |

São os mesmos arquivos da dívida de imagem de artigo já registrada no
`BACKLOG-TECNICO.md`. A 2560×1920 (4:3) o cartão recorta o centro e o resultado é
imprevisível — o padrão é **1200×630**, que é o que as 3 homes já usam corretamente
(`og-mirow.png`).

**(d) `og:image:alt` em 0 de 109 páginas.**

---

## §3 — `twitter:card` promete o que não entrega

As 109 páginas declaram `twitter:card = summary_large_image`, e **nenhuma** tem
`twitter:image`. O X cai no `og:image`, então funciona onde há — e nas 6 páginas da §2(a)
não mostra nada.

---

## §4 — Duas `Organization` disputando o painel de conhecimento

Achado novo, e liga direto no trabalho de GEO da onda 59 e no perfil do Google Business:

| Nó | `@id` | Tem `logo`? | Tem endereço/descrição? |
|---|---|---|---|
| do Yoast | `/pt/#organization` (URL **relativa**) | ✅ `logo_mirow_azul_e_branco1svg.svg` | ❌ |
| nosso, onda 59 | `https://mirow.com.br/#organization` | ❌ **ausente** | ✅ |

São **duas entidades** no grafo, não uma. O nó rico — o que a onda 59 escreveu com sede,
descrição, fundação, sócios — é exatamente o que **não** declara logo; e o nó que declara
logo aponta para um SVG com `width: 210, height: 297`, proporção de folha A4, o que não é
forma de logo.

Consequência prática: quando o Google monta o painel, não há um único nó que diga ao mesmo
tempo quem somos e qual é a nossa marca.

---

## Ordem sugerida para as próximas ondas

1. **`og:image` nas 6 páginas sem nenhuma** — usa o `og-mirow.png` que já existe. É a
   correção de menor custo e maior alcance das listadas aqui.
2. **Unificar as duas `Organization`** — `logo` e `image` no nó da onda 59, num raster
   1200×630 ou quadrado, com URL absoluta.
3. **`theme-color` + `msapplication-TileColor`** em navy `#020E66` — duas linhas de `<meta>`,
   e é a identidade na barra do Chrome no celular.
4. **`og:image` dedicado para as páginas de líder** — 1200×630 com a foto e o nome, em vez
   do retrato de 232×246.
5. **`manifest` + `mask-icon`** — o rabo da lista, cosmético para nós hoje.
6. **`og:image` dos artigos** — cai junto com a dívida de imagem de artigo do
   `BACKLOG-TECNICO.md`, não vale onda própria.

---

## Como refazer esta medição

```bash
python tools/verificacoes.py . --so=S171
```

E o inventário completo (as 14 superfícies, página a página) sai do script de varredura
descrito no handoff da onda 68.
