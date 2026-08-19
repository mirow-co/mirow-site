# CLAUDE.md — repo `mirow-co/mirow-site` ("novo site" da Mirow & Co.)

> Leia este arquivo INTEIRO antes de tocar em qualquer coisa. Ele existe porque o processo
> anterior perdeu pedidos do Mario e poluiu a máquina com 9 pastas paralelas. As regras abaixo
> não são estilo — são o contrato de trabalho (plano `2026-07-30_plano-processo-e-melhorias-site_v1.html`
> no repo privado `mirow-co/mirow-marketing`, pasta `03_Planos/`).

## O que é este repo

Espelho estático do site `mirow.com.br` (que era WordPress), servido pelo GitHub Pages.
**O cutover já aconteceu** (DNS virado em 11/08/2026, onda 47): o endereço de produção é
**https://mirow.com.br/pt/** — medido em 12/08/2026, responde `200` com `Server: GitHub.com`.
**Staging: https://staging.mirow.com.br/pt/** (desde 12/08/2026) — repo
`mirow-co/mirow-site-staging`, publicado por `tools/deploy-staging.ps1` (copia `public/`,
injeta `noindex, nofollow` em toda página, `robots.txt` com `Disallow: /`, sem sitemap;
o branch `main` de lá é artefato de build, força-push a cada publicação, nunca editar).
O antigo `mirow-co.github.io/mirow-site/` NÃO serve de staging: responde 301 para
`mirow.com.br` (efeito do domínio custom no Pages). **Fluxo de validação do Andreas:**
mudança de posicionamento publica primeiro no staging → OK do Andreas → deploy normal
na produção. O WordPress fica só como rollback (issue #204, até ~25/08). 286 páginas
HTML em `public/`, 3 idiomas (pt/en/de).

**INVARIANTE DO STAGING (regra do Mario, 18/08/2026): o staging nunca fica ATRÁS da
produção.** No mínimo igual, e normalmente à frente — ele é onde o que ainda não foi
publicado espera OK. Staging defasado é pior que staging inexistente: quem abre acha que
está vendo o site mais o pedido novo, e está vendo um site velho. Consequência prática:
**toda publicação em produção republica o staging** (do mesmo `main`, mais o que estiver
pendente de OK). Medido em 18/08: staging em `v=64` contra produção em `v=69`, cinco ondas
atrás — `edp.webp` dava 404 lá. Verificável comparando a `VERSAO` carimbada nas duas.

## REGRA Nº ZERO — o tema é intocável

O tema visual do espelho WordPress (o que está dentro de `public/`) é **DEFINITIVO**. Decisão do
Mario em 30/07/2026, depois de rejeitar e dar rollback numa reescrita de tema inteira (onda 4).

- Só se muda **conteúdo** e **CSS mínimo**, sempre **por cima** do tema original.
- Todo CSS novo vive em **blocos marcados** dentro de
  `public/wp-content/uploads/2026/07/onda6/onda6.css` — nunca num arquivo novo, nunca editando
  o CSS do tema. Marcadores: `/* onda<N>:<chave>:ini */ … /* onda<N>:<chave>:fim */`
  (o helper `tools_onda6/_onda7_css.py:escrever_bloco_css` faz isso).
- **A camada Astro (`src/`, `astro.config.mjs`, `dist/`) está FORA do deploy e não volta.**
  É resquício do protótipo rejeitado. Não construir nada nela.

> **ATENÇÃO — a regra está em revisão (Mario, 19/08/2026).** Ele autorizou **reconstruir o
> tema** numa sessão dedicada, com o objetivo de um site **fluido**: uma construção só que
> serve qualquer tamanho de tela, em vez de breakpoints com pixels calibrados à mão. Até
> essa sessão começar, **a regra continua valendo integralmente** — nenhuma onda de
> conteúdo deve tocar no tema "adiantando" a reconstrução. Contexto, riscos e a abordagem
> proposta estão em [`docs/HANDOFF-2026-08-19_b.md`](docs/HANDOFF-2026-08-19_b.md).

## Processo — P1 a P4 (o "nunca mais esquecer")

### P1 — 1 pedido = 1 issue. Nada fora de issue.
Todo pedido do Mario vira issue no repo **privado** `mirow-co/mirow-marketing`, label `site-onda`,
com o texto dele **verbatim**, página(s)-alvo, critério de aceite objetivo e persona.
**Nenhum agente implementa nada que não esteja numa issue.** Onda nasce de uma lista de issues e
termina com checklist issue a issue (✔/✘ com evidência).
O corpo da issue NUNCA vai para este repo — ele é **público**; razão interna fica no privado.

### P2 — Suite de verificações executável (a peça central)
`tools/verificacoes.py` é a suíte de testes do site. Cada pedido aceito vira **asserção**.

```bash
python tools/verificacoes.py .
```

- Roda **inteira, antes de todo deploy**. Uma asserção quebrada = **deploy bloqueado**
  (o `tools/deploy.ps1` chama a suíte e aborta em falha).
- Toda onda nova **ADICIONA** asserções. Só se remove asserção com decisão explícita do Mario.
- Asserções ainda não implementáveis entram como `PENDENTE` (não como sucesso silencioso).

#### P2.1 — MEDIR O EFEITO, NÃO A DECLARAÇÃO (a regra mais importante da suíte)

> **Asserção que confere o que está escrito passa enquanto o site está errado.**

Aprendido **quatro vezes numa só sessão** (05/08, ondas 33b, 35 e 37), sempre do mesmo jeito: a
asserção olhava a string, ou olhava um recorte estreito, e o navegador fazia outra coisa.

| Asserção que não media o efeito | O que o navegador realmente fazia | O conserto |
|---|---|---|
| `M01` procurava o **nome** do arquivo de medição no HTML | o `src` era `/wp-content/...`, sem o prefixo `/mirow-site/` → **404 em 143 páginas**, e a M01 passava | `S123` resolve o caminho e exige que o arquivo **exista no disco** |
| o CSS **declarava** `font-weight:800` nos big numbers | 800 não é carregado (`wght@…;700;900`) → o navegador desenhava **900/Black** | `V21` mede o peso **computado**; `S127` proíbe declarar peso fora do conjunto que o `<head>` carrega |
| `S125` cobrava a string `desenharLogo(` | o logo virou elemento SVG e a função sumiu — a asserção quebrou o deploy por **motivo certo, alvo errado** | passou a cobrar o que importa: o `<path>` usa a constante `M_PATH`, e a `V22` mede o elemento renderizado |
| `V07` dizia "números do hero com no máximo 2 linhas" mas media **só `pt/` em 1920x1080** | uma legenda **alemã** estava em **3 linhas em 1400px, no ar**, e a V07 passava verde | `V07` cobre **4 homes × 4 larguras** |

**A quarta linha é a mais perigosa das quatro:** a asserção não estava errada, estava
**estreita**. Título que promete um invariante geral e teste que cobre um caso particular é pior
que não ter teste, porque dá confiança falsa. Ao escrever asserção, o escopo do teste tem de
cobrir o escopo do título — ou o título tem de dizer o recorte (como em `V15`, "em 1400px").

**A regra, na prática:** ao escrever asserção, pergunte *"o que o navegador faz com isso?"*, não
*"o que está escrito?"*. Em ordem de preferência:

1. **Computado/renderizado** — `getComputedStyle`, `getBoundingClientRect`, hover real, ciclo de
   animação, imagem com `complete && naturalWidth>0`. É o padrão das asserções `V*`.
2. **Recalcular e comparar** — refazer a conta e conferir contra o que está no arquivo
   (`S116` reprojeta os pins, `S120` regera o sitemap inteiro, `S125` recompara o path da marca).
3. **Resolver a referência** — não basta o nome aparecer: o caminho tem de resolver e o arquivo
   existir (`S123`, `E05`).
4. **Atacar a causa-raiz, não só o sintoma** — quando um bug tem uma classe, escreva a asserção
   da classe. A `S127` não protege os big numbers: proíbe **qualquer** peso órfão, e lê o
   conjunto disponível do próprio `<head>`, então acompanha se a fonte mudar.

**Corolário — valores gêmeos.** Nunca declarar o mesmo valor em dois lugares. Quatro bugs da
onda 31 e o peso da onda 35 eram valores gêmeos que divergiram sem ninguém ver. Ao mudar um valor
que outra onda definiu, **edite no lugar** (com comentário datado) em vez de somar um bloco de
override.

### P3 — Fonte única de dados
Dado curado mora em **um** arquivo mestre, no repo privado, e o HTML é **gerado** dele.
Caso que originou a regra: a Sotreq ficou fora da barra de clientes porque a decisão do sócio
foi para a memória e o `clients.json` seguiu com o status velho.

| Dado | Mestre (privado, `mirow-marketing`) | Gerador |
|---|---|---|
| Clientes da barra de logos | `08_Site/2026-07-30_clients-curadoria-interna.json` | `tools/gen_clients.py` |
| Parceiros da Nossa Rede (nome, cidade, **lat/lon**, link, logo) | `08_Site/2026-08-04_rede-parceiros-curadoria.json` | `tools/gen_rede.py` |

### P4 — Comunicação de status inequívoca
Todo fim de onda: tabela "pedido → estado", com **só 3 estados**:
**NO AR** (verificado ao vivo) · **PRONTO, aguardando OK do Mario** · **NÃO FEITO** (com motivo).
Nunca dizer "pronto" sem dizer qual dos três. **Publicar só com OK explícito do Mario sobre os
screenshots.**

## Pasta única — proibido criar pastas/worktrees paralelos

`C:\dev\mirow-site` é a **única** pasta. Trabalho em branches normais dentro dela.
Proibido: `git worktree` persistente, cópias `mirow-site-*`, pastas de serve (`_serve9`),
junctions de deploy. Elas já causaram QA em cima da árvore errada.
Para servir local em QA, **use o `ServidorLocal` da própria suíte** — não suba um `http.server`
na mão. As páginas referenciam tudo em `/mirow-site/...`; servir `public/` na raiz dá **404 em
todo CSS/JS** e a página renderiza sem estilo (aconteceu em 05/08 e produziu um contact sheet
inteiro inválido). O `ServidorLocal` monta a junction `mirow-site -> public` num diretório
temporário, e o `__exit__` derruba o servidor e remove a junction:

```python
import sys; sys.path.insert(0, "tools")
from verificacoes import Navegador, ServidorLocal
with ServidorLocal("public") as srv, Navegador() as nav:
    nav.abrir("%s/pt/" % srv.base())          # base() já traz o prefixo
    print(nav.js("getComputedStyle(document.querySelector('h2')).fontWeight"))
```

Os scripts de `tools_onda6/qa/` recebem **URL**: passe `srv.base()`, nunca uma porta própria.
Se ainda assim subir um servidor à mão, confirme que morreu com
`Get-NetTCPConnection -LocalPort <porta> -State Listen` — um `curl` logo após o kill ainda
responde 200 e engana.

## Mudanças de conteúdo — scripts idempotentes

Toda mudança é um **script Python idempotente** em `tools_onda6/`, numerado sequencialmente
(`NN_descricao.py`, hoje até o 28).

- Argumento = raiz que contém `public/` (use `resolve_public` do `_onda7_css`).
- **Rodar 2× tem que dar o mesmo resultado** (segundo run reporta 0 mudanças).
- Sempre UTF-8 (`io.open(..., encoding='utf-8')`, `newline=''` na escrita — ver helpers `ler`/`gravar`).
- Idioma da página: `idioma_da_pagina(html)` (cookie do Polylang; detectar por caminho falha).
- Prefixo de URL do espelho: `base_prefix(html)` (é `/mirow-site/`).
- `tools_onda6/27_cache_busting.py` **roda SEMPRE por último** e a constante `VERSAO` dele é
  incrementada **a cada onda publicada**. Estado em 30/07/2026: `VERSAO = 8`, carimbado nas 275
  páginas. Sem isso o navegador serve CSS velho e o bug parece ser de layout.

## Ritmo de onda (#195 — as alavancas do aulão de tempos, 07/08)

Medido nas ondas 41–42: o que estica uma onda é (a) asset externo hostil,
(b) rodar a suíte completa várias vezes e (c) espera morta de deploy. Regras:

1. **Suíte seletiva durante o desenvolvimento** — `python tools/verificacoes.py . --so=<filtro>`
   ou `--rapido` para iterar. A suíte COMPLETA roda **uma vez, no gate do deploy**
   (o deploy.ps1 a força — esse gate não afrouxa).
2. **Asset externo = agentes em paralelo (R2)** — pedido com logos/imagens/dados
   de terceiros dispara 3–5 agentes de busca simultâneos (Wikimedia, sites
   oficiais, archive.org) ENQUANTO o fluxo principal edita código. A caça serial
   da onda 41 custou ~50 min; não repetir.
3. **Ondas homogêneas** — separar pedidos texto/CSS (rápidos) dos com asset ou
   estrutura (lentos); os rápidos não esperam os lentos.
4. **Fechamento com um comando:**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/fechar-onda.ps1 -Paginas pt/,pt/imprensa/
```

   Encadeia cache-bust → contact sheets das páginas-alvo → deploy (suíte completa
   no gate) → acompanhamento do build do Pages **com 1 retry automático** se vier
   `errored` (caso real da onda 41, transitório) → verificação da versão ao vivo.
   `-DryRun` testa a cadeia sem publicar; `-SemSheets` para onda sem layout.
   O que fica fora de propósito: commit do main e governança no repo privado.

**Nota .ps1:** os scripts PowerShell deste repo são **ASCII puro** (sem acento,
sem travessão). Sem BOM, o PS 5.1 lê o arquivo como ANSI e um travessão UTF-8
vira aspas curvas que FECHAM a string — parse error a dezenas de linhas de
distância do culpado (aconteceu no fechar-onda.ps1, 07/08).

## Deploy

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/deploy.ps1
```

- O branch **`gh-pages` é artefato de build**: é `public/` **verbatim**. Nunca editar à mão.
- O script: roda `tools/verificacoes.py` → aborta se falhar → monta a árvore num diretório
  temporário → commita e empurra `gh-pages`.
- `public/.nojekyll` é obrigatório (sem ele o Pages ignora pastas com `_`).
- `public/index.html` é o redirect da raiz do Pages.
- Propagação do Pages leva ~1 min; conferir **ao vivo** antes de dizer NO AR.
- `-DryRun` monta e verifica sem empurrar.

## QA

Ferramentas em `tools_onda6/qa/` (Chrome via CDP, screenshot real):

| Script | Para quê | Args úteis |
|---|---|---|
| `shot.py` | screenshot full-page | `aos-off` (**quase sempre necessário** — o tema esconde seções fora da viewport via AOS), `viewport`, `h=NNN` |
| `click_test.py` | clique real | — |
| `shot_hover.py` | estado de hover real | — |
| `shot_modal.py`, `shot_menu.py` | modais e menus | — |
| `breakpoints.py` | contact sheet multi-breakpoint (320/390/768/1024/1366/1920) num HTML único com métricas (overflow-x + culpados, telas de dobra, elementos zerados) | `aos-off`, `bp=…`, saída em `_qa_breakpoints/` (gitignored) |

**Regra P4 ampliada (03/08):** nenhuma onda vira "PRONTO, aguardando OK" sem o **contact sheet**
(`breakpoints.py`) da(s) página(s)-alvo anexado junto dos screenshots. Culpado de overflow achado
no contact sheet é candidato natural a asserção V-nova na suíte.

**Design system:** ler `docs/DESIGN-SYSTEM.md` **antes de escrever qualquer CSS novo** — tokens
reais do tema (cores, fontes Archivo/Libre Franklin, breakpoints 992/1200), componentes canônicos
e o passo a passo de capturar referência visual de outro site via CDP (sem playwright).

## Histórico das ondas (o que já está NO AR)

| Onda | O que entregou |
|---|---|
| 5 | Barra de logos de clientes; 3 cards de práticas; limpeza de posts/depoimentos da home |
| 6 | Quadro de líderes; João Daniel Ramos; história até 2026; jQuery reposto |
| 7 | Hero compacto; menus; página "Nossa rede"; líderes da home vira link |
| 8 | Primeira dobra exata (hero + barra = 1 tela, 0px de sobra, medida em runtime); 4 contatos no hero; Elmar Gans completo |
| 8.1 | Cache-busting `?v=8` nas 275 páginas; pills do hero maiores; 4 contatos como ícones no header |
| 8.2 | Slogan mais alto e mais espaçado, com "Resultado" parado no pixel |
| **9** | **PRONTA, NÃO publicada** — branch `onda9/contato-e-rede`: contato sem escritórios (S-07) + mapa único com hover card (S-14). Publica na onda 11. |
| **18** | **NO AR** (03/08) — os 24 pedidos do Mario numa sessão (S-50..S-73, issues #108–#131): LinkedIn real no card de líder; botão de voltar ao topo nas 275; idiomas do rodapé abrindo para cima; barras com texto/ícones maiores; "Práticas" em linha com `|` cinza; contato (título, Empresa, telefone opcional, mensagem-padrão, botão ciano); carreiras (título legível, sem "já é cliente?", botão de inscrição no fim); imprensa em lista branca com ícone do veículo; insights coloridos; `nosso-trabalho` → `nossos-valores` com redirect; planeta com 19 setores orbitando na home; menos vão líderes→reconhecimentos; e-mail com assunto/corpo; big numbers no tamanho do slogan. Suíte: 88 asserções. |

| **26** | **NO AR** (04/08, gh-pages `509a588`, v=24) — 7 pedidos do Mario (S-97..S-103, issues #155–#161): "Ver todos os líderes" em navy; **o site inteiro em UMA fonte** (Titillium Web — as 3 famílias do tema nunca eram carregadas, ver `docs/DESIGN-SYSTEM.md` §2); submenu Práticas no tamanho de Sobre nós (19px, revoga a S-94/S-88); rodapé sem filete antes da política; e-mail de Andreas e Felipe nos cards de líder da home; imprensa com a linha inteira clicável; práticas sem Elmar, com Andreas e Felipe (36 páginas). Suíte: 120 asserções. |

| **27** | **NO AR** (04/08, gh-pages `1bf8f66`, v=25) — 2 pedidos (S-104/S-105, #162/#163): menu na ordem Sobre nós · Práticas · Insights · **Imprensa · Carreiras** · Contato (header e clone do rodapé juntos) e a barra com **fundo navy sólido em toda página** — o HTML dela sempre foi idêntico nas 275; o que mudava era o fundo, porque o tema a deixa transparente e ela exibia o hero navy / a foto da interna / o gradiente claro. Suíte: 123 asserções, com a **V14** medindo a assinatura *renderizada* da barra em 8 páginas de templates diferentes. **3 achados abertos, aguardando decisão do Mario:** #164 (EN/DE com 5 itens de menu — falta Imprensa, página só existe em PT) · #165 (216 das 283 páginas são o mesmo conteúdo em URLs diferentes; canonical correto, problema de experiência) · #166 (26 páginas abrem sem banner). |
| **28** | **NO AR** (04/08, gh-pages `3cc94c3`, v=26) — S-109 (#167): os dois painéis de submenu com a **mesma altura**. Sobre nós abria 159px e Práticas 129px porque a margem da lista (40px do tema x 6px da S-65) e o padding do link (6px x 2px) nunca foram igualados; agora 133px nos dois, em pt/en/de e em 1400/1200/1024px. Suíte: 125 asserções — V15/V16 fazem **hover de verdade** (`Navegador.hover`, novo) e exigem diferença ≤ 2px. |
| **29** | **NO AR** (04/08, gh-pages `3e5b59c`, v=27) — os 3 achados da onda 27 (S-106/S-107/S-108, #164/#165/#166): **imprensa em EN e DE** (`/en/press/`, `/de/presse/`; menu com 6 itens nas três, seletor de idiomas ligando as três) · **uma URL por página** — 145 duplicatas viraram redirect para a canônica (descobertas pelo próprio `canonical`) e os links internos de 199 páginas foram reescritos, inclusive os do menu; o espelho passa a ser **125 páginas de conteúdo + 160 redirects** · **abertura padrão**: 8 páginas ganharam faixa navy e **12 páginas VAZIAS** (stubs de arquivo do WordPress, `<main>` sem texto) viraram redirect. Suíte: 128 asserções — a S107 cobra que nenhuma página linke para um stub (nenhum clique com 2 saltos). |
| **30** | **NO AR** (04/08, gh-pages `e26fc82`, v=28) — S-110 (#168): os **4 títulos da home numa classe só** (`.onda30-titulo-secao`) com tamanho, cor, estilo, margem e responsivo; os quatro passam a `h2` e a `data-aos="fade-up"` — o de Setores nunca teve animação porque nasceu na onda 18 fora do tema. A regra de 4 seletores da S-85 sai: uma fonte de verdade. Suíte: 130 asserções — a **V17** mede o computado dos quatro E o ciclo do AOS (os quatro saem de opacity 0 e animam ao rolar). |
| **31+32** | **NO AR** (04/08, gh-pages `fb0658f`, v=31) — Nossa Rede refeita (S-111..S-116, #169–#174, fecha a #140): **logos de verdade** dos 6 parceiros no lugar dos favicons de 128px · **mapas gerados de geometria real** (Natural Earth 1:110m, domínio público, projeção Mercator, `tools/gen_rede.py` + `tools_onda6/dados/`) em vez do SVG desenhado à mão · **pins calculados da lat/lon** com a mesma projeção do mapa (o PSE caía no mar porque a posição era percentual escrito à mão) · chips maiores com haste inclinada e layout anticolisão · sem a lista abaixo dos mapas · Europa preenchendo a caixa (99% do palco, medido). Dado curado no mestre do repo privado (`08_Site/2026-08-04_rede-parceiros-curadoria.json`) — P3. Suíte: **136 asserções**; a S116 RECALCULA a projeção e compara com o HTML. **Achado para o Andreas:** `portasconsulting.com` recusa conexão e redireciona para `caaportas.com` — a firma virou **CAA Portas**; o link do site estava quebrado. |
| **32** | S-117 (#175): o chip do logo vai para o **lugar livre mais próximo** do ponto da cidade — busca em anel (16 direções, raio crescente até 96px) no lugar da escadinha só para cima, que jogava o Batten longe da Alemanha. Pode cair sobre a França ou o mar, como o Mario autorizou; a haste inclinada liga chip e cidade. Medido: o mais distante a **80px** (era ~180px) e **zero sobreposição** (V20). |
| **33** | **NO AR** (05/08, v=32) — lote de limpeza: 5 issues antigas, todas verificáveis (S-118..S-122, #66/#81/#70/#71/#69/#106). **Quem saiu sai do site**: as 28 URLs de perfil de Giulia, Lucas Duarte, Mariana e Matheus viram redirect para a página de líderes do idioma (num salto só — 12 eram conteúdo, 16 eram stub apontando para o conteúdo), os **4 modais órfãos** de ex-líderes saem da `en/homepage` (medido: 0 referência ao id de cada um fora dele mesmo — HTML morto que só o robô lia) e a **autoria** dos 8 artigos em PT passa de Giulia Turcato para **Andreas Mirow e Felipe Diniz** nas 4 formas em que o Yoast a escreve (`meta author`, `twitter:data1`, nó Article e nó Person do JSON-LD). **`sitemap.xml` passa a existir** com as 113 páginas de conteúdo, gerado do `rel=canonical` (os 160 stubs ficam fora: são `noindex`, e listar noindex no sitemap é erro no Search Console) e o `robots.txt` — que apontava para um `sitemap-index.xml` inexistente desde a #46 — aponta para ele. **A raiz do Pages vai para `/pt/`**, não `/en/`. **As 6 imagens das práticas foram recuperadas** do WordPress vivo (`mirow.com.br/wp-content/...`, 124–191 KB cada) em vez de apagadas — as 6 exceções `S-20` saem de `FALTAS_CONHECIDAS` e a E05 volta a cobrá-las de verdade. **37 `<link>` de RSS mortos** (`/feed/`) removidos; o markup do ChatGPT nas páginas DE já não existia (item obsoleto da #106). Suíte: **147 asserções** (eram 142). As S118 e S120 **recalculam** (a lista de ex-líderes e o sitemap inteiro) e comparam com o disco, no padrão da S116. |
| **33b** | **NO AR** (05/08, v=32) — dois achados da própria onda 33, corrigidos a pedido do Mario (S-123/S-124). **O asset de medição 404ava em 143 páginas**: os stubs da S-107 o referenciavam como `/wp-content/...`, sem o prefixo `/mirow-site/`, porque o `base_prefix()` deduz o prefixo de uma referência a wp-content que o stub mínimo não tem. A **M01 passava do mesmo jeito** — ela procura o nome do arquivo na string, não o caminho resolvido; a **S123** agora exige que todo asset próprio tenha o prefixo E exista no disco. **O `hreflang` das páginas de imprensa apontava para a política de privacidade**: a S-106 criou `en/press/` e `de/presse/` de um molde alheio e o bloco de hreflang veio junto, então o Google recebia que a imprensa em inglês era a versão inglesa da política; `pt/imprensa/` não tinha nenhum. As três passam a se apontar (**S124**). **Correção de registro:** não é verdade que o site não tem hreflang — 106 das 113 páginas de conteúdo têm, e corretamente (a busca que disse o contrário assumia `rel` antes de `href`; o tema escreve `href` no meio). Das 7 sem, 4 são artigos só em PT (sem tradução, então sem alternativa a declarar) e 1 é a `en/homepage` (decisão aberta na #65). Suíte: **149 asserções**. |
| **34** | **NO AR** (05/08, gh-pages `bca52a8`, v=32) — S-125 (#178): o **"m" da Mirow no centro do hero**, como fonte das linhas dinamicas. Tudo dentro de `onda17-horizonte.js`; nenhum HTML ou CSS novo. **O glifo vem da marca oficial em vetor** (primeiro `<path>` de `marca-mirow-co.svg`), nao da imagem do LinkedIn que o pedido citava — aquela e um JPEG de 200x200 com token que expira, e sairia borrada num elemento que o pedido quer grandioso. A **S125 recompara** os dois paths. **O centro nao e o do palco:** medido, um logo de 300px centrado em `W/2` em 1400px fica com 270px atras do card do slogan e 30px no azul aberto — sai torto; entao o centro e o meio do **vao entre `.hero-texto` e `.hero-numeros`**, medido do DOM (3 idiomas, toda largura), com fallback ao centro do palco quando os cards empilham (<=1200px). **As linhas foram apertadas de `v*38` para `v*10`**: as 29 origens passam a cair dentro do logo e a sair de dentro dele. Escala 300px/alpha 0.68 no desktop -> 92px/0.40 no estreito, onde entra como marca d'agua ATRAS do texto em vez de atropela-lo (em 390px fica quase invisivel — deliberado, e o ponto mais provavel de revisao). Contact sheet 320-1920: 0px de overflow. Suite: **150 assercoes**. |
| **35** | S-126 (#179): os **big numbers do hero sem bold**. O pedido do Mario foi "nao seja bold, esta muito gordinho" — e o achado explica o sintoma: o CSS pedia `font-weight:800`, mas **800 nao esta entre os pesos carregados** (o `<head>` pede `wght@200;300;400;600;700;900`). O navegador arredondava para cima e os numeros saiam em **900/Black** — o peso mais gordo da familia, que ninguem escreveu. Comparados lado a lado num render real, 800 e 900 sao identicos. Peso vai a **400 (Regular)**, que existe de verdade; tamanho (62px) e cor (ciano) nao mudam. Corrigido **no lugar**, dentro do bloco `onda10:hero-numeros`, e nao num bloco de override — dois lugares declarando o mesmo `font-weight` e a classe de bug dos "valores gemeos" da onda 31. Os outros 3 `font-weight:800` do CSS (eyebrow, botao do pin e num da lista da Nossa Rede) passaram a declarar **900**, que e o que o navegador ja lhes dava: CSS honesto, **zero mudanca visual**. Duas assercoes: a **V21** mede o peso COMPUTADO nas 4 homes (era ali que o bug morava) e a **S127** pega a causa-raiz — nenhum `font-weight` pode pedir peso fora do conjunto que o `<head>` carrega, lendo o conjunto do proprio `<head>`. Suite: **152 assercoes**. v=33. |
| **36** | S-127 (#180): o **"m" solido, branco e NA FRENTE**. Pedido do Mario: "nao seja transparente, seja branco solido e na frente de tudo que estiver atras". O glifo **saiu do canvas** e virou **elemento SVG** em `z-index:10` — na frente dos cards (z=4), atras do header (z=20). Canvas nao servia: ele mora no `.banner__background` (z=1), e mover o canvas inteiro poria a grade e os cometas por cima do texto. O halo ciano fica no canvas, atras. **O conflito que o pedido criou:** translucido e atras, sobrepor texto era inofensivo; **opaco e na frente, sobrepor APAGA**. Medido com os 300px fixos da S-125: cobria 200x27px de "Focamos em estrategia, compras e go-to-market..." em 992px, 3 linhas do subtitulo em 390px, e o botao do WhatsApp em 320px. Solucao: o tamanho passa a ser **derivado do vao livre entre os cards**, medido do DOM — nunca maior que o vao menos 16px, no maximo 300px, e **oculto** se o vao < 90px. "Nao cobrir texto" vira garantia por construcao. Assercao **V22**: 0 colisao com glifo em 9 larguras (320-2560), medindo caixas TIGHT por linha (`Range.getClientRects`), mais fill branco puro, opacidade 1 e z-index > 4. A **S125 foi atualizada** junto (cobrava `desenharLogo(`, que deixou de existir) — a suite bloqueou o deploy e apontou. |
| **37** | S-128 (#181): **as caixas do hero estreitadas** para o M ter espaco. Pedido do Mario: "ficou muito larga a caixa transparente dos lados, sobra pouco espaco para o M". O card do slogan estava **superdimensionado**: medido nos 4 homes, `.hero-texto` vai de **780 -> 580px** (em 560 o subtitulo alemao quebra em 3 linhas). Vao central em 1400px: **140px -> 320px**, e o logo volta de 124px para **300px**; em 1200px ele passa a aparecer (162px). **Achado no caminho:** a pilha de numeros **ALARGOU** (400 -> 420px) porque a legenda alema "der Projekte werden fuer Kunden mit einem Jahresumsatz..." estava em **3 LINHAS em 1400px, no ar** — e a **V07 passava verde** porque testava so `pt/` em 1920x1080, embora o titulo dela prometa "no maximo 2 linhas" sem qualificar. Quarto caso do **P2.1** na mesma sessao. A V07 passa a cobrir **4 homes x 4 larguras**. Tambem sairam dois **valores gemeos mortos** da onda 16 (`width:330px` e `380px` de `.hero-numeros`, ambos sobrescritos pela onda 18). Consequencia cosmetica: as 4 pilulas de contato quebram em 2 fileiras (2+2 em de/, 3+1 em pt/); 0px de overflow no contact sheet. Suite: **153 assercoes**. |
| **38** | S-129 (#182): **o M menor, sem encostar nos cards**. Na onda 37 o tamanho era `vao - 16`, o que em 1400px dava **300px num vao de 320px** — o M ficava a 10px de cada card. O Mario, olhando o 1920: "o M pode ser menor, nao precisa ficar encostando nas laterais dos cards. eu gostei mais desse aqui". O diagnostico: o problema nunca foi o teto de 300px, foi o calculo **colar** o logo nas bordas quando o vao aperta — em 1920px o mesmo calculo deixava ~260px de ar por lado, e era essa proporcao que ele aprovou. Agora o tamanho e uma **fracao do vao (0,6)**, com teto 300px e piso 80px: em **>=1600px nada muda** (a fracao passa do teto, o cap manda, o aprovado fica intacto) e em 1400px cai para **192px com 64px de folga por lado**. A **V22** ganhou a medida de folga (>=24px de cada card, em toda largura onde o logo aparece). Tambem foram fundidos os dois comentarios que descreviam o mesmo calculo de formas diferentes — P2.1 aplicado a comentario, nao so a valor. Suite: **153 assercoes**. |
| **39** | S-130 (#183): **tres acertos de respiro no hero**, os tres pedidos do Mario vendo o hero publicado. (1) **Pilulas 2+2** — eram `flex-wrap` e caiam **3+1 em pt/en** e 2+2 em de/; o alemao acertava **por acidente**, porque os rotulos dele sao mais longos. Virou grid de 2 colunas: WhatsApp/E-mail em cima, LinkedIn/Instagram embaixo, deliberado nos 4 idiomas. Fecha a pendencia cosmetica da #181. (2) **Card da direita por idioma** — a sobra existia porque **um numero unico servia o pior caso**. Medido: pt/en mantem 2 linhas com **370px**, o alemao precisa de **420px**. Cada idioma passa a ter a largura justa (`html[lang^="de"]`), e a sobra em pt @1400 cai de **71px para 21px**. Efeito colateral bem-vindo: o vao cresce e o M aproveita sozinho (222px em pt, 192px em de) — nao foi preciso mexer no logo. (3) **A faixa de clientes cede espaco ao hero** — `padding-top` 40 -> 24px; o hero vai de 663 para **679px** e a imagem de fundo se expande junto. A dobra segue exata porque o `onda8-dobra.js` a **re-mede em runtime**. A **V23** nova (pilulas em [2,2] e sobra <= 30px, medidas no render) **pegou um valor gemeo no ato**: o override de `>=1440px` deixava o card em 390/440 e a sobra em 36-41px. Medido, o 370/420 do breakpoint de 1200 serve ate 1920px+ — os dois overrides de 1440 (o da onda 18 e o que a onda 39 quase repetiu) sairam. Suite: **154 assercoes**. |
| **40** | S-131 (#184): **Instagram junto do LinkedIn**, nao alinhado ao E-mail. O grid de 2 colunas da onda 39 resolvia as fileiras, mas as colunas **compartilham largura**: a coluna 1 ficava do tamanho de "Falar no WhatsApp" e o Instagram comecava naquela borda, a ~90px do vizinho. Eu havia resolvido o sintoma com uma ferramenta que trouxe um alinhamento que ninguem pediu. A lista **volta ao `flex-wrap`** do tema e o 2+2 vem de um **item de quebra** (`<li class="hero-contatos__quebra">`, `flex-basis:100%;height:0`) inserido depois da 2a pilula por `tools_onda6/93_quebra_pilulas_contato.py` (idempotente, e reposiciona a quebra se estiver fora de lugar). Pseudo-elemento nao serviria: `::before`/`::after` de um `li` sao filhos DELE, nao da `ul`, e nao entram no fluxo do flex. Medido em pt/en/de @1920 e 1400: fileiras [2,2] e os **dois gaps iguais em 12px**. A **V23** passa a comparar os dois gaps (diferenca > 4px acusa) — o teste que pega exatamente a volta a um layout em colunas. Suite: **154 assercoes**. |
| — | **Merge do PR #12** (medição do Marcell) na onda 31: os dois lados somados em `verificacoes.py` (S111–S116 + M01–M05) e em `27_cache_busting.py` (`onda17-horizonte.js` + `onda31-medicao.js`). **Lição:** publiquei `gh-pages` de um `main` local não empurrado e criei a divergência — **empurrar primeiro, publicar depois**. |
| **59** | **NO AR** (18/08, gh-pages `207d5b89`, v=66) — o **handoff GEO do Felipe** de 11/08 (#230–#233). Ele mediu o que os assistentes de IA respondem sobre a Mirow: "consultoria **alemã** com escritório em **Barcelona**", sócios tirados de site de CNPJ, e 1 em 3 tentativas confundindo a firma com o **Miro**. Não é alucinação — é inferência do que está publicado (as bios citam Berlim, Bremen, CFO para Alemanha/Áustria/Suíça, mestrado em Barcelona) na ausência de um fato de sede legível por máquina. **JSON-LD** `Organization`+`ProfessionalService` + **6 `Person`** nas 3 listagens de líderes, com `jobTitle`/`description`/`sameAs` **gerados dos próprios cards** da listagem (P3) e `url` apontando para a página individual · **slug** `/pt/lider/591/` → `/pt/lider/michael-munch/`, com stub `noindex`, sitemap e hreflang reescritos e **zero** referência interna · **meta description** nas 3 homes e nas 3 listagens (a da home pt é o texto do Felipe verbatim) · **cargo + bio + LinkedIn nas 18 páginas individuais de líder**, que traziam só o nome e um formulário — o robô visitava e não aprendia nada. **`foundingDate` ficou FORA de propósito:** não é dado publicado, e o próprio site diz 2012 (nasceu *Portas Consulting Brasil*) e 2013 (virou *Mirow & Co.*) — pergunta aberta para o Felipe. **Elmar Gans e João Daniel Ramos ficaram fora do schema por decisão do Felipe** (mudança de situação em curso; e o `@id` exige URL própria). Suíte: **S149–S152**, e as quatro medem efeito — a S149 **parseia** o JSON e exige que cada `url` resolva num arquivo que existe e não seja stub; a S152 **recalcula** a bio a partir da listagem e compara. |
| **60** | **NO AR** (18/08, gh-pages `207d5b89`, v=66) — os dois relatórios **PageSpeed** de 18/08 (#236). **O desktop tira 95 e o mobile 75**, e isso reordenou o plano: render-blocking, cache e imagem **não aparecem** no relatório desktop, então performance aqui é problema de celular fraco, não do site. O achado mais grave não estava no relatório: o **`<h1>` das 109 páginas dizia "Stratigital"** — nome do tema/agência anterior no `alt` da logo —, ou seja, o cabeçalho de nível 1 de todo o site anunciava a marca errada para robô e leitor de tela. Também: `aria-label` nos 2 botões sem nome acessível (era a única falha da categoria **Agentic Browsing**, que mede se um agente de IA entende a página) · `alt` em **toda** imagem do site — o relatório citou 4, a asserção da classe achou **124**, nas páginas de prática e carreiras que ele nunca visitou · os **6 selos de reconhecimento** com o nome **lido de dentro da própria imagem** (o `title` traz slug e um arquivo se chama `image-52.png`) · `dashicons.min.css` (36 KiB) fora das 109 e `formidableforms.css` (23 KiB) fora das 54 sem formulário, **decidido por medição** e mantido nas 55 que usam — ~3 s de bloqueio a menos no celular · o **único erro de console** morto com placeholder transparente para os 4 assets que o CSS pede e que **nunca foram espelhados** (a textura nunca carregou, então o visual aprovado em 59 ondas já é o visual sem ela) · `width`/`height` nos logos da barra, o **único** culpado de CLS que o relatório mediu. Causa-raiz corrigida no `06_quadro_lideres.py`, que criava o card sem `alt` desde a onda 6. Suíte: **S153–S158** (195 asserções). **Não acionável, medido:** `Cache-Control: max-age=600` é fixo do Pages, e é o item de maior economia declarada (1.516 KiB); zero header de segurança; sem brotli; stub responde 200, não 301 — os quatro só saem com CDN. Ver `docs/BACKLOG-TECNICO.md`. |
| **59-sede** | **PRONTA, aguardando OK do Andreas** — branch `onda59-sede` (`896ef7d0`), publicada em **staging.mirow.com.br** (#234). A frase *"A Mirow & Co. é uma consultoria estratégica brasileira, com sede no Rio de Janeiro"* abre a seção "Nossas áreas de expertise" nas 3 homes e a Nossa História nos 3 idiomas. **Não vai no hero:** ali estourava a dobra exata em **31px** (V01–V03 e V30 pegaram). **Sem ponto final na home** — a V31 (onda 58) pegou a primeira versão no gate. É mudança de posicionamento, então segue o fluxo staging → Andreas → produção. |
| **60b** | **NO AR** (18/08, v=67) — dois consertos e um fato novo. **(1) O placeholder que pintou o site de VERMELHO.** O `texture-7.png` que a onda 60 criou para matar o 404 era um base64 que eu colei de memoria como "1x1 transparente": era um pixel **vermelho com alfa 127**. Como os 22 seletores do tema usam `background-size:cover`, esse unico pixel se esticou e pintou a home, os insights, as paginas de lider e o menu de vermelho, **em producao**. Eu havia "conferido" o arquivo checando que era PNG valido e 1x1 — **medi a existencia, nao o efeito**, e a S157 fazia o mesmo. Agora o PNG e **gerado byte a byte** e o script **rele o que gravou**; a **S159** decodifica o pixel de todo placeholder e exige alfa 0 (testada com o pixel vermelho de volta: acusa). **(2) Duas cidades, dois papeis — e a distincao E o conteudo.** **SEDE = assento juridico, CNPJ ativo, RIO DE JANEIRO** (Rua Lauro Muller, 116, CEP 22290-160) → vive no `address`. **FILIAL = onde o time trabalha, SAO PAULO** (Av. Ibirapuera, 2033 — conj. 133, CEP 04029-100) → vive no `location`. `foundingDate` = **2012-04-12** (a onda 59 o omitia de proposito, por nao ser dado publicado) e `foundingLocation` = **Rio**, porque a firma nasceu la em 2012 como *Portas Consulting Brasil* — e o campo que explica as mencoes ao Rio. **A prosa dizer "com sede no Rio de Janeiro" na `description` e nas 3 `meta description` esta CERTO** e nao deve ser "corrigido": a sede e mesmo o Rio. **A politica de privacidade nao foi tocada** — ali o endereco e o legal, amarrado ao CNPJ; mexer e decisao juridica. A S149 cobra os dois enderecos nos seus lugares. **AVISO ao proximo agente:** esta linha afirmava "a sede e Sao Paulo, nao o Rio", e em 19/08 isso me fez auditar a producao, concluir "contradicao entre a prosa e o schema" e abrir issue (#244, fechada como invalida) propondo trocar copy que estava correta. O codigo nunca errou — o comentario da S149 registra a autocorrecao; era a documentacao que estava velha. **Ler a S149 antes de "consertar" endereco.** |
| **61** | **NO AR** (18/08, v=68) — as imagens do PageSpeed, e uma limpeza que apareceu no caminho. **`edp.svg` 414 KB → `edp.webp` 35 KB**: nao era vetor, eram **quatro bitmaps embutidos** em base64 sobre clipPath/gradiente, para um logo exibido a **81x30 px**. **`mercedes-benz.svg` 298 KB → 17 KB**: vetor de verdade, mas **489 paths e 160 KB so de coordenadas**. As 4 fotos de lider, os 6 selos e o `taesa.png` viraram WebP (658 KB → 110 KB). E **181 imagens ORFAS removidas (25,9 MB)** — nenhuma pagina, CSS ou JS as referenciava. **A licao que custou mais tempo:** usei "3x o exibido" no raster (edp 243x90) e a largura renderizada caiu de **81,38 para 81,00 px** — depois do load quem define a caixa e o **aspecto real do arquivo**, nao os atributos `width`/`height` do HTML. Como a fileira e **centrada**, isso redistribuiu tudo e **7 logos que eu nunca toquei** mudaram de antialiasing (2,25% dos pixels da barra). Conserto: gerar na **razao exata** do original, dividindo pelo maximo divisor comum (3426x1263 → 1142x421; 1400x354 → 700x177; taesa tem gcd 1, ficou no tamanho e so trocou de formato). Diff final: **0,27%**, so nos dois logos trocados — verificado com `tools_onda6/qa/comparar_regiao.py`, que fotografa a regiao antes/depois e compara pixel a pixel via `git stash`. Tambem: `en/press/` e `de/presse/` anunciavam a **politica de privacidade** no `og:description` (com CNPJ e endereco) — residuo do molde da onda 29, a mesma origem do bug de hreflang da 33b. Suite: **S160** (home sem imagem >120 KB e nenhuma orfa grande) e **S161** (so WebP referenciado, e existente); a **H04** passou a aceitar webp — ela cobra o CLIENTE na barra, nao o formato. **Fica para a onda 62:** ~167 imagens de ARTIGO referenciadas acima de 120 KB, somando ~50 MB (uma de 3,5 MB), incluindo banners duplicados de 822-915 KB. Ver `docs/BACKLOG-TECNICO.md`. |
| **62a** | **NO AR** (18/08, gh-pages `a716a953`, v=70) — **o espelho caiu de 262 MB para 132 MB**, e nada que o visitante vê mudou. Verificado ao vivo: os 5 caminhos removidos em **404**, os 2 que ficaram em **200 com o Content-Length certo**, `de/karrieren/` servindo o caminho novo com `readyState 4` / `currentTime 0,8 s` / 1280×720 sem erro de mídia, e **screenshot da home conferido** (erro 12). **Staging republicado no mesmo v=70** — o check novo do `deploy.ps1` acusou `staging v=64 × produção v=70` e foi o que lembrou. Eu fui medir o ganho da onda 62 (imagens de artigo) e o somatório acusou **43 MB de "imagem" na página de carreiras**; fui conferir e não era imagem: **185 MB do espelho são MP4**, ou seja **~70% do site era vídeo**, e a varredura de órfãs da onda 61 nunca olhou — ela só conhece extensão de imagem. **87 MB eram órfãos** (`video-bg-home.mp4` 41,7 MB, `video-bg-home-1.mp4` e `-1-1.mp4` 22,9 MB cada, os dois últimos idênticos entre si) com **zero referência em qualquer arquivo**; **49 MB eram cópia byte-idêntica** de vídeo em uso — nos dois casos era a **página alemã** apontando para a cópia de `2024/04` enquanto pt/en usavam a mais antiga. `tools_onda6/124_videos_orfaos_e_duplicatas.py` reescreve as 2 referências alemãs e remove os 5 arquivos; idempotente (2º run = 0 mudanças), e **verifica no momento de rodar** que o alvo não tem referência (caminho E basename) e que a duplicata é md5-idêntica — não confia em levantamento anterior. Forma escapada (`2024\/04\/`) tratada junto, a lição da 61b. **O que sobra é o problema de verdade, medido AO VIVO:** `pt/carreiras/` transfere **44 MB para abrir**, dos quais **40.530 KB** são o MP4 (`performance.getEntriesByType('resource')`) — `autoplay muted loop`, 1280×720, 25,4 s, ~**13 Mbps** para um loop de fundo mudo. Recomprimir a ~1,5 Mbps corta ~36 MB **numa página**, mais que a onda 62 de imagens inteira nas 109; precisa de **ffmpeg**, que não está na máquina. Suíte: **S162**, que cobra a CLASSE (nenhuma mídia órfã, nenhum par md5-idêntico, toda referência resolve) e foi **testada nos 3 braços com o problema de volta — acusa cada um**. |
| **62b** | **NO AR** (18/08, gh-pages `d5e75c39`, v=71) — **o vídeo de carreiras de 39,7 para 4,3 MB**, e nada que a página mostra mudou. Medido AO VIVO: `pt/carreiras/` transferia **44 MB** para abrir (40.530 KB o MP4) e agora transfere **8,7 MB** (4.368 KB o MP4), com o vídeo tocando (`readyState 4`, `currentTime` correndo, 1280×720, sem erro de mídia). O arquivo estava a **13.115 kb/s** para 1280×720 / 25,4 s **sem trilha de áudio** — ~10× o que um loop de fundo mudo atrás de overlay navy precisa. **Alvo escolhido por medição:** CRF 26 → 4,3 MB (−89%) com **SSIM 0,94** contra o original; CRF 30 dava 2,73 MB / 0,91. A primeira comparação de SSIM, feita no vídeo inteiro, deu **0,77 com o arquivo MENOR pontuando melhor** — impossível, era dessincronia de quadros (344 × 314); refeita quadro a quadro no mesmo instante, ficou coerente, e o número errado nunca foi reportado. `tools_onda6/125_video_carreiras_comprimido.py` é idempotente **pelo bitrate** (acima de 3.000 kb/s recomprime, abaixo reporta 0) e **confere o que gravou** — tamanho e bitrate — antes de trocar o arquivo bom pelo novo. Usa o ffmpeg estático do pacote `imageio-ffmpeg`, porque não há ffmpeg na máquina. **`S162` ganha o 4º braço: nenhuma mídia acima de 8 MB**, testado com o arquivo de 39,7 MB de volta — acusa. `public/` cai de 132 para **97 MB**. **Contexto da decisão:** o Mario pediu antes uma ilustração SVG animada no lugar do vídeo (duas pessoas subindo uma escada); as 3 direções foram geradas e ele recusou ("ficou muito ruim e infantil"). O gerador ficou em `tools_onda6/qa/gen_escada_svg.py` e as variantes em `~/.gstack/projects/mirow-co-mirow-site/designs/`, caso a ideia volte com desenho profissional. |
| **62c** | **NO AR** (18/08, v=72) — **155 PNG viram WebP e o espelho fecha o dia em 63 MB**, tendo começado em 262. Pedido do Mario: "vamos atacar os pngs" — medido antes, os PNG eram **159 dos 169 arquivos acima de 120 KB e 47,4 dos 51,1 MB**, e os 10 JPEG restantes ficaram fora porque JPEG já comprimido corta só 17-42%. **A decisão que define a onda: só troca de FORMATO, nunca de dimensão.** Na onda 61 o raster a "3× o exibido" derrubou a largura renderizada do logo da EDP de 81,38 para 81,00 px — depois do load quem define a caixa é o **aspecto real do arquivo**, não os atributos `width`/`height` — e, com a fileira centrada, 7 logos intocados mudaram de antialiasing. Mantendo a dimensão idêntica essa classe **não pode** acontecer: não é cuidado, é impossibilidade. Verificado depois: **dimensão mudou em 0 de 158**. **Qualidade medida, não declarada:** cada WebP comparado com o PNG do git, **compostos sobre fundo** — diferença média global de **0,94 de 255 (0,37%)**, pior imagem com média 2,4. A primeira medição acusou 40 níveis em 6 imagens: era artefato meu, comparar o RGB **sob pixel transparente** de imagem RGBA não significa nada. 45,5 MB → 12,8. Suíte: **S163** cobra a CLASSE (nenhum PNG referenciado acima de 120 KB, todo webp resolve) e por isso se mantém sozinha, ao contrário da S161, que lista arquivo por arquivo. **O gate barrou duas vezes, as duas com razão:** a **S119** cobrava as 6 imagens das práticas pelo nome `.png` e pelo magic de PNG (motivo certo, alvo errado — o caso da S125 na onda 33b; passou a aceitar os dois formatos, como a H04 fez na 61), e a **S160** expôs `bg-banner-our-work.png` (427 KB) como órfã: ela só não aparecia porque a varredura decide por **basename**, e a cópia de `2023/03` cobria a de `2024/04`; convertida a primeira, a segunda apareceu pelo que sempre foi. É a dívida **D8** se manifestando a favor. **Dois bugs meus, ambos repetição de lição já escrita:** regex de classe negada non-greedy travou no `bundle-js.js` minificado (a mesma que custou 30 min de manhã), e o conjunto de terminadores incluía `:`, o que partia `https://host/x.png` no `https:` — isso escondeu do script os 3 PNG referenciados só no JSON-LD e fez a S163 acusar ausente um arquivo que estava no disco. |
| **62d** | **NO AR** (19/08, v=73) — os dois bloqueadores de render que **não** são do tema. O PageSpeed lista 4, somando 520 ms; dois são `bundle-css`/`bundle-js` e esperam decisão sobre a REGRA Nº ZERO. **`addtoany.min.css`** (36 KB, **283 ms**, o pior isolado) saiu de 54 páginas e ficou nas 55 que usam o botão — medido, não listado, pelo mesmo `115_css_morto.py` da onda 60, **estendido em vez de duplicado**; as 3 homes não usavam. **`onda31-medicao.js`** (236 ms) entrava sem `defer`, então o navegador parava de montar a página para executar 5,7 KB de GA4 antes de desenhar; com `defer` baixa em paralelo — seguro porque é uma IIFE que só instala `dataLayer`/`gtag` e não usa `document.write`. **`onda6.css` (142 ms) FICA:** são 82 KB que estilizam o hero, e tirá-lo do caminho crítico troca LCP por FOUC. **Por que isso é o que importa aqui:** o elemento de LCP da home é **TEXTO** — o relatório nomeia `div.hero-texto > p` com *Element render delay* e **nenhuma fase de carga de recurso**. Não há imagem no caminho crítico, e é por isso que remover 200 MB de mídia nas ondas 62a-c não tinha como mover essa nota. Verificado no navegador: `defer=true`, `dataLayer` com 5 itens e `gtag` presentes; as páginas com addtoany seguem com 3 botões de 32px. |
| **63** | **NO AR** (19/08, v=73) — **o card do hero parou de escrever texto sobre texto no mobile** (foto do iPhone do Mario). `.onda53-slogan h2{margin-bottom:-20px}` valia em **toda largura**, mas foi calibrado na tinta do desktop, onde o slogan é 62px/160% e sobra **~18,6px de entrelinha morta** por lado. Abaixo de 992px a fonte cai para 38px/116% e a entrelinha morta vira **~3px** — os mesmos 20px comiam **27px do parágrafo** (tinta de "Resultados" acabava em y=327, parágrafo começava em y=300). O eyebrow tinha o mesmo mal, com 1px de folga. Os dois negativos foram **escopados a ≥992px, editados NO LUGAR** (valores gêmeos), e o mobile ganhou ritmo próprio: parágrafo 13px abaixo da tinta, desktop **idêntico**. **V36** nova mede a **TINTA** (`Range.getClientRects`), não a caixa — a caixa de linha mente quando o `line-height` é grande, que é a própria armadilha do bug — em **4 larguras × 3 homes**, seguindo a lição da V07. Ela pegou o eyebrow a 1px em 768px, que o olho não pegou. **Achado de tabela no caminho:** ao consertar a S145 (que procurava `<script src=` literal e parou de casar com o `defer` — erro 10, 3ª vez no dia), apareceram **três backspaces literais (0x08) dentro de regex** na suíte, dois deles vindos da onda 60b pela armadilha de heredoc. Regex com backspace **nunca casa**: a **S72** inteira passava **vazia** desde então, e o braço da **S159** que confere placeholder SVG estava morto — justamente a asserção criada contra o pixel vermelho. Corrigidos com classe explícita; S72 testada removendo o assunto de um link (acusa); braço SVG **corrigido, não exercitado** (não há placeholder SVG hoje). Suíte: **202 OK**. |
| **64** | **NO AR** (19/08, v=74) — **a barra do topo parou de ficar branca no celular depois de fechar o menu** (relato do Mario). A hipótese óbvia foi **medida e descartada**: a classe `menu--mobile-opened` sai corretamente ao fechar. Quem pintava era `.header .menu:hover{background:#fff}` (onda 27) — no desktop é proposital, porque o painel do submenu é branco; em tela de toque **não existe sair do hover**, e depois do tap no hambúrguer o navegador segura o `:hover` até o próximo toque em outro lugar: logo branco sobre barra branca. Conserto: `@media (hover:hover) and (pointer:fine)` — não é largura nem número mágico, é a condição que a regra sempre pressupôs. **A V37 nasceu errada e só não foi publicada assim porque o teste negativo pegou:** na 1ª versão eu ligava também `setEmitTouchEventsForMouse`, que converte hover em toque, e a asserção ficava **verde com o bug de volta**. Notas de método: o headless reporta `(hover:hover) and (pointer:fine)` como **true**; `setEmulatedMedia` com `features` não funcionou; `setTouchEmulationEnabled` funciona e **gruda na sessão**, por isso a V37 abre navegador próprio. Suíte: **203 OK**. |
| **65** | **NO AR** (19/08, v=75) — **a página de imprensa sai de 29 para 43 matérias**, e a lista deixa de ser HTML à mão. O levantamento do Felipe (18/08) cruzou a página, 9 anos do grupo de WhatsApp e leitura direta: a vitrine estava **seis meses atrasada** (última entrada 10/02/2026). Entraram as **14 matérias com URL**, todas conferidas com HTTP 200 — e **4 dos 14 títulos do CSV dele eram paráfrase**, não o que a matéria publicou (Exame, Logweb, Revista Amazônia, Youtopia); vai ao ar o título medido no `og:title`/`h1`, e o CSV foi devolvido corrigido porque **alimenta proposta comercial**, não só o site (#240). **Os erros no ar eram TRÊS, não dois:** o item “Armazenamento de energia” tinha **veículo, logo E data** errados (é Valor/Revista Energia, `datePublished` 2024-05-10, saía como Estadão 28/05) e o de 02/03/2024 é **Empresas & Negócios**, não Folha — este último nem estava no pedido. **A falha de processo é o que importa:** a `S57b` cobra literalmente *“o logo segue o veículo, não o link”* e passava **verde** nos dois, porque o logo batia com o rótulo e o rótulo era o errado — ela comparava dois campos NOSSOS entre si e nunca nenhum deles com o **host do link**, o único dado da linha que não escrevemos. P2.1 outra vez. Agora a lista é **gerada** de um mestre P3 (`tools/gen_imprensa.py` + `08_Site/2026-08-19_imprensa-materias-curadoria.json`), no molde do `gen_clients.py` — era o **7º** script a mexer nessa lista à mão. **10 veículos novos**: 8 com wordmark oficial (WebP na **dimensão exata**, a regra da onda 62c; medida a **tinta sobre fundo branco** de cada um, 24,8% a 57,8%), Broadcast reusa o Estadão, e **Revista Amazônia vai de texto por decisão**: o site dela só publica wordmark BRANCO, e inverter a marca de terceiro não é nossa decisão. Suíte: **S165** (o veículo bate com o host — dois braços, “um host um veículo” derivado do próprio dado e “o nome aparece no host” com exceção declarada) e **S166** (**recalcula** a lista do mestre e compara, padrão S116/S120); a `V26` foi **estendida no lugar** — o `10` hardcoded saiu e a contagem vem do mestre. **Os quatro cenários negativos foram exercitados** e cada um acusa. **O gate barrou, com razão:** a `S146` cobrava “a coluna Vaivém no TOPO”, e o comentário dela já declarava o gêmeo entre parênteses — *“(é o mais recente do acervo)”*; com 7 matérias posteriores o item caiu para 8º corretamente. Passou a medir o invariante que “topo” representava: a posição é igual ao número de matérias mais novas. Terceira vez nesta classe (S125 na 33b, S119 na 62c). Contact sheet: **0px de overflow** em 6 larguras × 3 páginas. Suíte: **205 OK**. |
Backlog aberto: issues `site-onda` (S-01..S-19) no `mirow-co/mirow-marketing`.
Backlog técnico (o que não dá para fazer no Pages, o que espera decisão): `docs/BACKLOG-TECNICO.md`.

## Erros a NÃO repetir

1. Implementar de memória → sempre da issue, com o texto verbatim do Mario.
2. Confiar em arquivo de dados sem conferir a decisão registrada (caso Sotreq).
3. Dizer "pronto" sem distinguir NO AR × aguardando OK.
4. Criar pasta/worktree e não limpar.
5. QA sem asserção de regressão do acumulado.
6. Inserir `<link>`/`<script>` sem `?v=` (cache serve versão velha).
7. Acreditar em screenshot sem checar qual pasta o servidor local está servindo.
   Em 05/08 subi `http.server --directory public` **sem o prefixo `/mirow-site/`**: todo CSS/JS
   absoluto deu 404, as páginas renderizaram **sem estilo** e o contact sheet acusou um
   "PROBLEMA" que não existia. Para QA use o **`ServidorLocal` da própria suíte** — ele monta a
   junction `mirow-site -> public` num temp e a remove ao sair.
8. Escrever asserção que confere a **declaração** em vez do **efeito** — ver **P2.1**, a regra
   mais importante da suíte. É o erro que mais passou desapercebido aqui.
9. Editar CSS/JS de asset e **não incrementar a `VERSAO`** do cache busting: o navegador serve o
   arquivo velho e a correção "não funciona" no ar (a onda 35 quase publicou assim).
10. **Regex de markup próprio com a tag literal (`<h4>`), sem tolerar atributo novo.** Na onda 60
    isto quebrou **três coisas de uma vez**, todas porque um `aria-level="3"` entrou no `<h4>`:
    o reconhecedor de card do `06_quadro_lideres.py` (que então achou que os cards não existiam,
    trocou os `<button>` por `<div>` e **apagou os 4 modais de bio da home**), a `S128` e a `S101`
    (que passou a ler o nome do líder como `?`). Escreva `<h4[^>]*>`. A exceção legítima é quando
    a *ausência* do atributo é justamente o gatilho — o `114_a11y_atributos.py` usa `<h4>` literal
    de propósito, para não reaplicar o que já aplicou.
11. **Rodar script de onda inicial isoladamente numa onda nova.** O `06_quadro_lideres.py`
    reconstrói a região dos líderes e descarta o que ondas posteriores penduraram ali como irmão
    do card: rodado sozinho em 18/08, apagou os links de LinkedIn da onda 18 (4 → 1). Quem pegou
    foi a **S50**, no gate. Se precisar rodar, rodar depois dele, na ordem,
    `68_home_lideres_e_espacos.py` e `105_email_andreas_e_felipe.py`.

12. **Declarar um asset "transparente"/"vazio" sem DECODIFICAR o pixel.** Em 18/08 eu colei um
    base64 de memória como "PNG 1×1 transparente" para matar um 404. Era um pixel **vermelho com
    alfa 127**, e como os 22 seletores do tema usam `background-size:cover`, esse 1×1 se esticou e
    pintou a home, os insights, as páginas de líder e o menu de **vermelho, em produção**. Eu
    "conferi" o arquivo checando que era PNG válido e 1×1 — medi a existência, não o efeito, e a
    `S157` fazia o mesmo. Agora o PNG é **gerado byte a byte** e a **S159** decodifica o pixel de
    todo placeholder. **E: depois de todo deploy, olhar um screenshot da home.** Este bug morreria
    em 5 segundos com um olho na página; nenhuma das 195 asserções o pegou.

13. **Escrever regex (ou qualquer backslash) por heredoc do bash NESTE ambiente.** O `\b` chega
    ao arquivo como **backspace literal (0x08)** e o `\\` é comido. Regex com backspace **nunca
    casa** — e não quebra com estardalhaço: a asserção fica **verde medindo o vazio**. Em 19/08
    isso já estava no repo em **dois** lugares, vindos da onda 60b: a **S72** inteira passava
    vazia (o `finditer` nunca casava, então o laço nunca rodava) e o braço da **S159** que confere
    placeholder SVG estava morto — justamente a asserção criada contra o pixel vermelho. Eu criei
    um terceiro no mesmo dia. **Para código com backslash, use as ferramentas Write/Edit, nunca
    heredoc**; e prefira classe explícita (`[ ]`, `[ />]`) a `\b`. Para caçar: procurar
    `chr(8)` no arquivo. Na mesma família: `python -c "..."` com aspas aninhadas e
    `git commit -m "...(\"texto\")..."` — as aspas internas fecharam o argumento e o commit
    inteiro se perdeu dentro do commit seguinte. **Mensagem de commit longa vai por `-F -`.**

14. **Ler número de um relatório sem conferir O QUE ele mediu.** Em 19/08 li 64/95 de um
    PageSpeed salvo e afirmei que as três ondas não tinham movido a nota. O `fetchTime` era de
    **antes das ondas** e os assets medidos eram **`v=64`** contra `v=72` em produção — o Google
    devolveu análise em cache. **Todo relatório salvo: conferir `fetchTime` e a versão dos assets
    citados antes de tirar conclusão.** Vale para PageSpeed, export de analytics, planilha de
    cliente. É o erro 12 aplicado a artefato de terceiro, e a variante interna dele é entregar um
    artefato que você não mediu: provei a animação no quadro que referenciava os SVG como arquivo
    e mandei ao Mario a versão com base64, que ele abriu e viu **três painéis vazios** (as aspas
    duplas do `url("data:...")` fechavam o atributo `style="..."`).

15. **Comparar imagem RGBA sem compor sobre um fundo.** O RGB debaixo de pixel transparente não
    significa nada: a primeira medição de qualidade da onda 62c acusou **40 níveis de diferença
    em 6 imagens intactas**. Compostas sobre fundo, 0,16. Sempre `Image.new(fundo)` + `paste(im,
    mask=im)` antes de qualquer diff.

## Ritmo do gate (onda 60c) — rodar só o que a mudança pede

A fase estática são **1,2 s** para 162 asserções. O tempo do gate morava nos **111 page loads**,
que dormiam **6 s cegos** cada. Duas mudanças, com o mesmo veredito (196 OK):

- **Espera por estabilidade, não por relógio.** O `Navegador.abrir` espera uma impressão digital
  do layout (geometria + opacidade dos elementos animados) parar de mudar em duas amostras
  seguidas. Gate: **~12 min → ~4 min**. Só `readyState`+fontes **não basta** — a `V30` acusava o
  selo fora de lugar porque ele ainda animava. `--espera-fixa` volta ao antigo, para comparar.
- **Etapas.** Cada asserção declara área: `texto`, `css`, `asset`, `estrutura`, `schema`,
  `medicao`. No laço de trabalho:

```bash
python tools/verificacoes.py . --desde=HEAD --tempos
```

  `--desde=<ref>` descobre as etapas a partir do que mudou no git (e **ignora** arquivo que só
  levou carimbo de cache — sem esse filtro, acusaria 291 arquivos a cada onda; com ele, 12).
  `--para=texto,css` força as etapas. `--tempos` lista as asserções mais lentas.
  **Regra de segurança: asserção NÃO mapeada roda SEMPRE** — o mapa só pode acelerar, nunca
  esconder. O `deploy.ps1` continua rodando **tudo**.

## Governança a cada marco

Comentar a issue `mirow-co/mirow-marketing#42`, atualizar `00_Admin/gestao-projeto.html` no repo
privado (carimbo de data) e commitar. **Nunca `git add -A` no repo de marketing** (regra
pós-vazamento de dado de cliente — lá se adiciona arquivo por arquivo).
