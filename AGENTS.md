# AGENTS.md — repo `mirow-co/mirow-site` ("novo site" da Mirow & Co.)

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
`mirow.com.br` (efeito do domínio custom no Pages). **QUEM DECIDE, CLÁUSULA PÉTREA (Mario, 19/08/2026):** neste projeto quem aprova é
**o Mario, e só ele**. Não existe "aguardando OK do Andreas" nem gate de terceiro de
espécie alguma — palavras dele: *"nao tem essa de ficar esperando andreas dar ok.
mostre sempre para mim e eu dou o ok. o andreas nao tem nada a ver com o que fazemos
aqui"*. O fluxo é: **eu mostro ao Mario** (screenshot, staging, número medido) e **ele**
dá o OK. O staging serve para ELE ver antes de ir ao ar, não para pedir licença a
outra pessoa.

> Este parágrafo substitui um que dizia o contrário ("Fluxo de validação do Andreas:
> … → OK do Andreas → deploy"). Era ele que me fazia reincidir: eu lia o contrato,
> obedecia e achava que estava sendo disciplinado. **Andreas e Felipe seguem sendo
> FONTE** (levantamento de imprensa, handoff GEO, bio de líder) — o que não existe é
> Andreas como aprovador. O WordPress fica só como rollback (issue #204, até ~25/08). 3 idiomas (pt/en/de);
a contagem de páginas está em "Estado do site", abaixo.

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
(`NN_descricao.py`; o próximo número é o maior de `ls tools_onda6/` mais um).

- Argumento = raiz que contém `public/` (use `resolve_public` do `_onda7_css`).
- **Rodar 2× tem que dar o mesmo resultado** (segundo run reporta 0 mudanças).
- Sempre UTF-8 (`io.open(..., encoding='utf-8')`, `newline=''` na escrita — ver helpers `ler`/`gravar`).
- Idioma da página: `idioma_da_pagina(html)` (cookie do Polylang; detectar por caminho falha).
- Prefixo de URL do espelho: `base_prefix(html)` (é `/mirow-site/`).
- `tools_onda6/27_cache_busting.py` **roda SEMPRE por último** e a constante `VERSAO` dele é
  incrementada **a cada onda publicada** — o valor corrente está na própria constante, não
  aqui. Sem isso o navegador serve CSS velho e o bug parece ser de layout.

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

## Estado do site (medido em 25/08/2026)

**Produção e staging em `v=88`** (onda 73 publicada em 25/08 com o OK do Mario), conferido ao
vivo nas duas pontas.
`public/` = **64 MB** (era 262 MB antes das ondas 61–62c). **287 arquivos HTML**: ~107 de
conteúdo e ~180 stubs de redirect; o `sitemap.xml` lista **106 URLs** — só conteúdo, porque
stub é `noindex` e listar noindex no sitemap é erro no Search Console. Suíte: **219 asserções,
0 falha**.

**Cuidado com dois esquemas de numeração parecidos:** `S-07`, `S-117` **com hífen** são
*pedidos* do Mario (rastreados nas issues); `S107`, `S117` **sem hífen** são *asserções* da
suíte. Não há relação entre os números — e `S117` nem existe, embora o pedido `S-117` exista.

## Histórico das ondas

A narrativa de cada onda — achado, medição, conserto e o que ficou de fora — está em
**[`docs/HISTORICO-ONDAS.md`](docs/HISTORICO-ONDAS.md)**, verbatim. Saiu daqui porque era
**65% dos 74 KB** deste arquivo, e arquivo longo é arquivo ignorado. **Quando precisar do
"por quê" de uma decisão antiga, é lá.** Ondas 10–17, 19–25 e 41–58 nunca tiveram linha; para
elas a fonte é o `git log`.

**Tudo até a onda 71 está NO AR.** A única exceção é a **onda 9** (branch
`onda9/contato-e-rede`), pronta e nunca publicada.

> **ATENÇÃO — os rótulos 68 e 68b estão usados DUAS VEZES no `git log`, e a culpa é
> minha.** Em 20/08 eu rotulei o trabalho de ícones como "onda 68/68b" sem conferir o
> log, e os números já pertenciam ao bloco "Como usamos IA" das práticas. Para
> distinguir:
>
> | Rótulo | O que é | Commits |
> |---|---|---|
> | 68 · 68b · 69 | "Como usamos IA" nas 3 práticas core + a frase de sede a produção | `12959a87` `6855276d` `1d581af1` `613ee7ce` |
> | 70 · 71 | os 2 links da imprensa (#241) e os marcos 2024-2026 travados (#68) | `fc71cc32` `93ce0989` |
> | 68 · 68b *(reuso)* | as 14 superfícies de ícone e a saída do Michael Munch | `0857364c` `14d0fe8f` `c0433010` `dfdedc9c` |
>
> **A onda 72 (a–d) está NO AR** (bio nova do Felipe, alumniOf dos 5, meta description
> dos líderes, modal redesenhado — ver `docs/HANDOFF-2026-08-25.md`). **A próxima é a
> 73.** Antes de rotular, `git log --oneline -20 | grep -i onda`.

Mapa por tema, para saber onde procurar e qual sentinela guarda o quê:

| Tema | Ondas | Sentinelas |
|---|---|---|
| Hero, dobra exata, o "m" da marca no palco | 8 · 8.1 · 8.2 · 34–40 · 63 · 66 | `V07` `V22` `V23` `V30` `V36` |
| Menu, barra do topo, rodapé, hover em toque | 7 · 18 · 26 · 27 · 28 · 64 | `V14` `V37` |
| Uma URL por página (canonical, stub, sitemap) | 29 · 33 | `S107` `S120` |
| Quem saiu sai do site | 33 · 68b | `S118` `S151` |
| Nossa Rede: mapa de geometria real, pin da lat/lon | 31 · 32 | `S111`–`S113` `S116` `V20` |
| Imagem e mídia: peso, formato, órfãos, vídeo | 60 · 61 · 62a–62d | `S157`–`S163` |
| GEO / schema / assistentes de IA | 59 · 59-sede · 60b · 67 | `S149`–`S152` `S168` |
| Ícones expostos e cartão de preview de link | 68 | `S171`–`S174` |
| Imprensa gerada de mestre P3 | 65 | `S165` `S166` |
| Busca estática no cliente | 67 | `S167` `V38` |
| Acessibilidade e PageSpeed | 60 · 62d | `S153`–`S158` |
| "Como usamos IA" nas práticas core | 68 · 68b · 69 | `S169` `V39` |
| Imprensa: links recuperados e marcos travados | 70 · 71 | `S170` |
| Bio do Felipe, alumniOf dos 5, meta description, modal de líder | 72 · 72b–d | `S175` `V40` |
| LinkedIn dos líderes num mestre, e a experiência anterior deles no grafo | 73 | `S176` `S177` |

**Antes de tratar qualquer coisa como pendente, medir no HTML.** Em 20/08 a linha da `59-sede`
dizia "aguardando OK" sobre uma frase que estava no ar havia semanas, e isso quase me fez
preservar no staging uma pendência inexistente.

Backlog aberto: issues `site-onda` no `mirow-co/mirow-marketing`.
Backlog técnico: [`docs/BACKLOG-TECNICO.md`](docs/BACKLOG-TECNICO.md) · superfícies de ícone:
[`docs/ICONES-EXPOSTOS.md`](docs/ICONES-EXPOSTOS.md) · design system:
[`docs/DESIGN-SYSTEM.md`](docs/DESIGN-SYSTEM.md).


## Erros a NÃO repetir

Os 18 abaixo já aconteceram aqui. Os de 12 a 18 são a mesma família e a mais perigosa:
**verificação que passa verde sem medir nada.**

1. Implementar de memória → sempre da issue, com o texto verbatim do Mario.
2. Confiar em arquivo de dados sem conferir a decisão registrada (caso Sotreq).
3. Dizer "pronto" sem distinguir NO AR × aguardando OK.
4. Criar pasta/worktree e não limpar.
5. QA sem asserção de regressão do acumulado.
6. Inserir `<link>`/`<script>` sem `?v=` — o cache serve a versão velha.
7. **Servir `public/` na raiz para QA.** Todo CSS/JS absoluto dá 404, a página renderiza sem
   estilo e o contact sheet acusa problema inexistente (05/08). Use o **`ServidorLocal` da
   própria suíte**, que monta a junction `mirow-site -> public` e a remove ao sair.
8. **Asserção que confere a declaração em vez do efeito** — ver **P2.1**. É o erro que mais
   passou desapercebido aqui.
9. **Editar asset e não incrementar a `VERSAO`** do cache busting: a correção "não funciona"
   no ar (a onda 35 quase publicou assim).
10. **Regex de markup próprio com a tag literal (`<h4>`).** Um `aria-level="3"` novo no `<h4>`
    quebrou três coisas de uma vez na onda 60 — inclusive **apagou os 4 modais de bio da home**,
    porque o `06_quadro_lideres.py` concluiu que os cards não existiam. Escreva `<h4[^>]*>`.
    Exceção legítima: quando a *ausência* do atributo é o gatilho (`114_a11y_atributos.py`).
11. **Rodar script de onda inicial isoladamente.** O `06_quadro_lideres.py` reconstrói a região
    dos líderes e descarta o que ondas posteriores penduraram ali: rodado sozinho em 18/08,
    apagou os LinkedIn da onda 18 (4 → 1); a `S50` pegou no gate. Se precisar, rodar depois
    dele `68_home_lideres_e_espacos.py` e `105_email_andreas_e_felipe.py`, nessa ordem.
12. **Declarar asset "transparente"/"vazio" sem DECODIFICAR o pixel.** Colei um base64 "1×1
    transparente" que era um pixel **vermelho com alfa 127**; como 22 seletores do tema usam
    `background-size:cover`, ele pintou a home, os insights e o menu de **vermelho, em
    produção**. Eu havia conferido que era PNG válido e 1×1 — medi a existência, não o efeito,
    e a `S157` fazia o mesmo. Hoje a `S159` decodifica o pixel de todo placeholder.
    **E: depois de todo deploy, olhar um screenshot da home** — este bug morria em 5 segundos
    com um olho na página, e nenhuma asserção o pegou.
13. **Escrever regex (ou qualquer backslash) por heredoc do bash NESTE ambiente.** O `\b` chega
    como **backspace literal (0x08)** e o `\\` é comido. Regex com backspace **nunca casa**, e
    não quebra com estardalhaço: a asserção fica **verde medindo o vazio**. Já estava no repo em
    dois lugares (a `S72` inteira passava vazia; o braço SVG da `S159` estava morto — justamente
    a asserção criada contra o pixel vermelho). **Código com backslash vai por Write/Edit, nunca
    heredoc**; prefira classe explícita (`[ ]`) a `\b`; para caçar, procure `chr(8)` no arquivo.
    Mesma família: `python -c` com aspas aninhadas, e `git commit -m` com aspas internas —
    **mensagem longa vai por `-F -`**.
14. **Ler número de relatório sem conferir O QUE ele mediu.** Afirmei que três ondas não moveram
    o PageSpeed lendo um relatório cujo `fetchTime` era anterior a elas, medindo assets `v=64`
    contra `v=72` em produção. **Todo relatório salvo: conferir data e versão dos assets antes
    de concluir** — vale para PageSpeed, analytics, planilha de cliente. A variante interna é
    entregar artefato que você não mediu: provei uma animação numa versão e mandei outra ao
    Mario, que abriu e viu três painéis vazios.
15. **Comparar imagem RGBA sem compor sobre um fundo.** O RGB debaixo de pixel transparente não
    significa nada: a primeira medição da onda 62c acusou 40 níveis de diferença em 6 imagens
    intactas; compostas, 0,16. Sempre `Image.new(fundo)` + `paste(im, mask=im)` antes do diff.
16. **Dizer que um ícone "tem o logo" sem medir a TINTA no tamanho servido.** O favicon era a
    wordmark `MIROW & CO.` inteira e a 32px tinha **0,00%** de pixel branco — quadrado navy
    vazio, no ar, por anos. O arquivo *continha* o logo e abria bem no visualizador; faltava
    medir no tamanho de render (11 caracteres em 32px dão ~3px cada). Quem descobriu foi o
    **Mario perguntando que símbolo era aquele** ao lado do nosso site no Google. **Todo ícone
    se mede na largura em que a superfície o desenha** — e o veredito muda com o tamanho: a
    MESMA wordmark é defeito no favicon e **correta** no `og-mirow.png` de 1200×630. `S171`.
17. **Verificação cujo ALCANCE é menor que o invariante que ela promete.** Não é medir a
    declaração (P2.1) — é medir o efeito no lugar errado, ou num recorte dele. Quatro instâncias
    na onda 68, todas achadas por cenário negativo e nenhuma pelo caso positivo:
    · **só os nós de topo de uma árvore JSON** — o Yoast aninha o `ImageObject` do logo dentro
      de `Organization.logo`; o script corrigiu 3 de 109 e a `S174` ficou verde com o arquivo do
      logo apagado. **Varredura de árvore é recursiva ou é ilusão.**
    · **a string em vez do valor** — procurar `/pt/#organization` no arquivo enquanto 106 páginas
      usavam a forma absoluta, escapada como `https:\/\/`. Re-parsear o JSON resolve.
    · **"um por página" ≠ "o mesmo em todas as páginas"** — a `S174` aceitava página com `@id`
      diferente usado de forma consistente.
    · **o atributo esconde o alcance** — o carimbo de cache só casava `href=`/`src=`, e o
      `msapplication-TileImage` usa `content=`: era o único favicon saindo sem `?v=`.
    Mesma família da `V07` (dizia "os números do hero" e media só `pt/` em 1920) e da `S57b`
    (dizia "o logo segue o veículo" e comparava dois campos nossos entre si). **Pergunte onde o
    dado pode estar que você não está olhando, e exercite o cenário negativo** — o positivo não
    distingue "passou" de "não mediu".
18. **Escrever em asserção um número que descreve o CONTEÚDO do site.** Quantas páginas, quantos
    líderes, em que posição — é valor gêmeo, e diverge na primeira onda que muda o conteúdo. A
    onda 68 fechou com **6 asserções vermelhas e zero defeito**: 3 páginas viraram stub, o total
    caiu de 109 para 106, e a `S149` cobrava literalmente `!= 6` líderes. O comentário da própria
    tabela `MARCADORES` registrava que o número já fora corrigido à mão nas ondas **29, 33 e
    57** — esta seria a quarta. O invariante nunca foi "109 páginas", era "todas as páginas de
    conteúdo". Hoje os pisos são sentinelas (`TODAS`, `PT_EN`) resolvidas em runtime e a contagem
    de líderes vem do `PAGINAS` do `110`. **O título conta como asserção:** o da `S149` dizia
    "6 líderes" e virou "os líderes do cadastro", como a `S146` e a `S85` já tinham exigido.


## Ritmo do gate (onda 60c) — rodar só o que a mudança pede

Medido em 06/08/2026: a fase estática são **1,2 s**, e o tempo do gate morava nos page loads,
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

**O repo de marketing não está clonado nesta máquina.** O comentário na issue e o fechamento
dela saem pelo `gh` sem clonar; o **painel `gestao-projeto.html` não**, porque é um HTML de
~110 KB e editá-lo pela API sem vê-lo renderizado é chute. Em 20/08 eu deixei o painel sem
atualizar por isso, e disse. Se for atualizá-lo, clone o repo e olhe a página primeiro — bumpar
só o carimbo de data faz o painel alegar frescor que ele não tem.
