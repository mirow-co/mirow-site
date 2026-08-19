# Plano — onda 65 (imprensa, produção) e a reconstrução fluida (só staging)

> Escrito em 19/08/2026, antes de tocar em código, a pedido do Mario. Parte do
> [`HANDOFF-2026-08-19_b.md`](HANDOFF-2026-08-19_b.md) e dos dois arquivos que o Felipe
> mandou por e-mail (`2026-08-18_mirow-na-imprensa-consolidado.md` e
> `2026-08-18_mirow-imprensa-links.csv`).
>
> Duas fases, deliberadamente separadas: **A** é conteúdo e vai ao ar; **B** é tema e
> **não** vai ao ar sem o OK dele sobre o staging.

---

## Estado deste plano (atualizado 19/08/2026, depois da Fase A)

**FASE A: NO AR** — v=75, `gh-pages` `b8592f91`, verificado ao vivo (43 itens nas três
páginas, os 8 logos novos servindo 200, staging republicado no mesmo v=75). Suíte
**205 OK**. Issues #237–#243 no `mirow-co/mirow-marketing`.

**FASE B: não começou.** É o assunto da próxima sessão.

### Decisões do Mario, 19/08

| # | Decisão | O que ele escolheu |
|---|---|---|
| **D1** | gerador P3 ou 7º script à mão | **gerador** (implementado) |
| **D2** | Certificação B entra na imprensa | **entra** (no ar) |
| **D3** | rótulo da Broadcast | **“Broadcast (Estadão)”** com `estadao.svg`, exceção declarada na S165 |
| **D4** | os 2 links faltantes | **issue** (#241), não bloqueiam |
| **D5** | escopo da Fase B | **só a nossa camada + overrides**, sem tocar no bundle do tema |
| **D6** | família `F` antes de migrar | **NÃO** — ir direto, `F` só onde quebrar |
| **D7** | data do item do Valor | **10/05/2024** (o `datePublished` da fonte), com nota no mestre |
| **novo** | o que julgar no staging | **home (pt/en/de) + imprensa** |

### A consequência de D6, dita na cara

Sem a família `F` escrita antes, as 25 asserções `V` que prendem o pixel do modelo antigo
vão falhar **de propósito** durante a migração, e não haverá número que separe *“mudei
porque quis”* de *“quebrei sem ver”*. O julgamento passa a ser **a olho**.

O que eu faço para compensar, sem contrariar a decisão (nada disto é asserção `F` — é o
P4 que o repo já exige):

1. **Baseline visual antes de tocar em CSS** — home (pt/en/de) e imprensa fotografadas em
   9 larguras no `main`, guardadas em `_baseline/` (gitignored). É o antes/depois que o
   Mario vai olhar, e é o que transforma “ficou igual” em imagem comparável.
2. **Baseline de texto renderizado** — o `innerText` de cada página-alvo antes e depois.
   Se o texto é idêntico, tudo que mudou é apresentação. Custa segundos e é a única coisa
   que eu não abro mão, porque conteúdo perdido numa migração de CSS é irreversível sem
   ninguém notar.
3. **Triagem explícita das `V`** — cada `V` que mudar de estado vai numa tabela dizendo se
   prendia pixel do modelo antigo ou se é regressão. Nunca “rebaselinei”.

Se em algum ponto a migração ficar difícil de julgar sem número, a recomendação volta à
mesa — mas por dado, não por insistência.

---

## O que eu já MEDI antes de planejar (não é levantamento do Felipe repetido)

| O que | Resultado |
|---|---|
| Itens na lista hoje | **29** em cada uma das 3 páginas (`pt/imprensa`, `en/press`, `de/presse`), HTML idêntico entre elas — os títulos ficam no idioma do veículo, não são traduzidos |
| As 14 URLs novas com link | **14 de 14 responderam 200** (curl com UA de navegador, seguindo redirect) |
| Títulos reais × títulos do CSV do Felipe | **4 divergem** — ver tabela abaixo |
| Erros de rótulo já no ar | **3**, não 2 (o consolidado achou 2) |
| Logos de veículo que faltam | **10** dos veículos novos; 3 veículos já vivem hoje com fallback de texto |
| `:hover` sem guarda de capacidade no nosso CSS | **78 regras** — é a classe do bug da onda 64, 78 vezes |
| Superfície da camada nossa | `onda6.css` = 85 KB, 59 blocos marcados, **758 valores em px**, ~60 media queries em 19 condições distintas (5 delas por **altura**), **0 `clamp()`**, **0 `@container`** |
| Bundle do tema | `bundle-css.css` **1,1 MB** + `bundle-js.js` **1,6 MB** |
| Páginas | 109 de conteúdo + 177 stubs de redirect |

### Os 4 títulos que o CSV do Felipe traz diferentes do que a matéria publicou

Medido abrindo cada página (a Exame só entrega o texto depois do JavaScript, então foi lida
com o navegador headless da própria suíte):

| Veículo | No CSV do Felipe | O que a matéria publicou |
|---|---|---|
| Exame, 24/03/2026 | "Do aluguel à revenda: Localiza detalha plano para rodar 10 mil carros da BYD no Brasil" | **"Do aluguel à revenda: o plano da Localiza para rodar 10 mil carros híbridos e elétricos da BYD"** |
| Logweb, 16/03/2026 | "Aluguel de caminhões e *truck as a service*: juros e o estudo da Mirow" | **"Juros altos aceleram virada no modelo de posse de caminhões no Brasil, aponta estudo da Mirow & Co."** |
| Revista Amazônia, 19/07/2024 | "Hidrogênio verde: carga tributária no Brasil" | **"Consumo Interno de Hidrogênio Verde no Brasil Tem Alta Carga Tributária"** |
| Youtopia, 10/07/2026 | "Electromovilidad y redes eléctricas: el desafío de América Latina — ADELATAM 2026" | **"Electromovilidad y redes eléctricas, el gran desafío en América Latina"** |

O CSV é ótimo como levantamento, mas os títulos dele são paráfrase em 4 casos. Vai para o
site o que a matéria publicou. **Vale avisar o Felipe** — o arquivo dele é a fonte para
propostas comerciais, e um título parafraseado num slide de credenciais é um problema maior
que no site.

**De bônus, verificado na Exame:** a citação existe mesmo — *"Estudos das consultorias
Acende Brasil e Mirow & Co. projetam que o ecossistema de eletrificação pode movimentar
R$ 200 bilhões por ano até 2030"*. Era um item 💬 (relato de colega) no consolidado; agora
é 🔎.

### Os 3 erros que já estão no ar (o consolidado achou 2)

| Item | O que está publicado | O que é |
|---|---|---|
| 28/05/2024 "Armazenamento de energia trava aportes consistentes" | rótulo **Estadão** + logo do Estadão + data **28/05/2024** | o link é do **Valor** (Revista Energia) e o `datePublished` da própria página é **2024-05-10**. Três campos errados num item só: veículo, logo e data |
| 02/03/2024 "Descarbonização: onde investir…" | rótulo **Folha de S.Paulo** + logo da Folha | o link é do **jornal Empresas & Negócios**. O consolidado do Felipe já lista certo; é o site que está errado |
| 01/02/2025 Estadão × 30/01/2025 The Economist | dois itens | **é a mesma reportagem**, a do Estadão é a republicação. O Felipe pediu para sinalizar; **já está sinalizado** — o título do item do Estadão começa com "The Economist:". Nada a fazer aqui, só registrar |

**A lição de processo:** existe uma asserção (`S57b`) que cobra exatamente *"o logo segue o
veículo, não o link"*. Ela passa verde nos dois itens errados, porque o logo bate com o
rótulo — e o rótulo é que está errado. É P2.1 outra vez: a asserção media a coerência
interna de dois campos nossos, e nunca comparou nenhum dos dois com o **host do link**, que
é o único dado que não mentimos para nós mesmos. Isso vira asserção nova (S165 abaixo).

---

# FASE A — onda 65: a página de imprensa (vai ao ar)

## A.1 A decisão de arquitetura: gerador, não o 7º script à mão

Hoje a lista é HTML escrito à mão em 3 arquivos, e cada item novo virou um script próprio:
`45_`, `70_`, `84_`, `98_`, `106_`, `120_`. Este seria o **7º**. E o resultado desse modelo
está medido acima: 3 campos errados em 2 itens, sobrevivendo meses.

O P3 já resolveu isso duas vezes (barra de clientes, Nossa Rede) e **metade já existe para
imprensa**: `08_Site/2026-08-06_imprensa-veiculos-curadoria.json` no repo privado é o mestre
dos **logos**, e `98_imprensa_logos.py` gera essa parte. Falta o mestre dos **itens**.

**Proposta:** `tools/gen_imprensa.py` + mestre novo no repo privado
`08_Site/2026-08-19_imprensa-materias-curadoria.json`, no molde exato do `gen_clients.py`:

- uma entrada por matéria: `data`, `veiculo`, `titulo`, `url`, `quem`, `tema`,
  `verificado` (`lido` / `site` / `relato`), `fonte_do_titulo`, `nota`;
- o gerador ordena por data decrescente, monta os `<li>` e **escreve as 3 páginas**;
- grava `tools/imprensa-publicada.json` (só o que a suíte precisa ler, nada interno) —
  mesmo padrão de `clients-publicados.json` e `rede-publicada.json`;
- **sai com código 1** se uma matéria referenciar veículo que não está no mestre de logos,
  ou logo que não existe no disco. Não silencia.

Com isso, adicionar matéria passa a ser editar uma linha de dado, e a asserção pode
**recalcular** a lista e comparar — a forma mais forte de P2.1, a mesma da `S116` (reprojeta
os pins) e `S120` (regera o sitemap).

**Custo honesto:** o gerador é ~2 h de trabalho contra ~40 min do script à mão. Eu recomendo
pagar, porque a alternativa é splicing manual de 14 itens × 3 páginas mais 3 correções
cirúrgicas — exatamente o processo que produziu os 3 erros.

## A.2 O que entra

**29 → 43 itens.** As 14 matérias com URL verificada, com o título real:

| Data | Veículo | Logo | Obs |
|---|---|---|---|
| 10/07/2026 | Youtopia (Equador) | **novo** | título real, não o do CSV |
| 15/04/2026 | O Globo | existe | Felipe nominal |
| 06/04/2026 | TN Petróleo | **novo** | estudo próprio |
| 24/03/2026 | Exame | **novo** | título real; citação confirmada por leitura |
| 16/03/2026 | Logweb | **novo** | título real, bem melhor que o do CSV |
| 05/03/2026 | Broadcast (Estadão) | **novo** ou `estadao.svg` — decisão | Felipe nominal |
| 23/02/2026 | Balcão Automotivo | **novo** | Elmar |
| 29/04/2025 | Cenário Energia | **novo** | Felipe nominal, gás natural |
| 02/04/2025 | Cenário Energia | (mesmo) | Certificação B — ver decisão D2 |
| 30/01/2025 | Autoindústria | **novo** | Schiemer |
| 11/10/2024 | O Globo | existe | Felipe nominal |
| 19/07/2024 | Ipesi | **novo** | repercussão do estudo tributário |
| 19/07/2024 | Revista Amazônia | **novo** | título real |
| 29/05/2024 | Estadão (Mobilidade) | `estadao.svg` | 4 nomes da casa |

**Ficam de fora, sem link:** 06/02/2026 (juros/montadoras de caminhões) e 07/10/2025
(O Globo, cruzamento elétrico × automotivo). O consolidado registra que nos dois casos só
existe o post do LinkedIn. **Item sem link não entra numa lista cujo item inteiro é um
link** (`S102` cobra isso). Vira issue de recuperação.

**Mais as 3 correções** da tabela acima.

## A.3 Os 10 logos novos

Mesmo método da onda 41, registrado no mestre com a `fonte` de cada um (R1): asset oficial
do header do veículo, ou Wikimedia Commons quando houver, com licença anotada.

**Isto é a parte lenta da onda** — o CLAUDE.md já registra que a caça serial de logos custou
~50 min na onda 41. Duas consequências no plano:

1. **A onda não fica bloqueada nisso.** O fallback de texto já existe e já está no ar em 3
   veículos (epbr, CZ Insights, Money Times). Veículo cujo logo não sair limpo entra com
   wordmark tipográfico e uma linha no mestre dizendo por quê.
2. Os logos são buscados **em paralelo com** a escrita do gerador, não depois.

## A.4 Asserções novas (P2.1 — medir o efeito, atacar a classe)

| ID | O que cobra | Por que é a classe, não o sintoma |
|---|---|---|
| **S165** | o veículo de cada item é **coerente com o host do link**, por um mapa host→veículo derivado do próprio mestre, com exceções **declaradas** (republicação/sindicação, ex. Broadcast em `broadcast.com.br` rotulado como Estadão) | é a asserção que os 2 itens errados burlaram por 12+ meses. Não confere dois campos nossos entre si: confere o nosso campo contra o dado externo |
| **S166** | a lista das 3 páginas é **recalculada do mestre** e comparada; as 3 são idênticas entre si; ordem de data decrescente; 0 URL duplicada; todo logo referenciado existe no disco | padrão `S116`/`S120`. Torna impossível a lista divergir do dado curado |
| **V26** (estendida, não nova) | os 43 itens renderizam sem overflow-x e com **logo carregado** (`complete && naturalWidth>0`) nas 3 línguas | a V26 já faz isso para 29 itens; **estender no lugar** em vez de somar uma V38 — regra dos valores gêmeos |

**O que NÃO entra na suíte, de propósito:** checagem de HTTP 200 das URLs externas. Rede
externa dentro do gate o torna lento e não-determinístico, e um veículo fora do ar por 5
minutos bloquearia deploy. Fica como script à parte, rodado por onda:
`tools_onda6/qa/checar_links_imprensa.py`, gravando `verificado_em` no mestre. O gate cobra
que o campo existe e não está velho demais — não faz a chamada.

## A.5 Roteiro de A

1. Issues no `mirow-co/mirow-marketing` (P1): 1 issue por pedido, texto do Felipe verbatim
   — inclusões, as 3 correções, o gerador, os 2 links a recuperar.
2. Mestre novo no repo privado, a partir do CSV **com os títulos reais medidos**.
3. `tools/gen_imprensa.py` + 10 logos (em paralelo).
4. `S165`, `S166`, `V26` estendida.
5. `tools_onda6/27_cache_busting.py`: `VERSAO = 75`.
6. Gate completo (`tools/verificacoes.py .`) → **185 asserções**, 0 falha.
7. Contact sheet de `pt/imprensa`, `en/press`, `de/presse` (`breakpoints.py`) — P4 exige
   antes de dizer PRONTO.
8. **Screenshot da home conferido a olho** — erro 12 do CLAUDE.md.
9. `tools/fechar-onda.ps1 -Paginas pt/imprensa/,en/press/,de/presse/`.
10. Conferir ao vivo, **republicar o staging** (invariante), governança no repo privado.
11. `/handoff`.

**Teste negativo obrigatório:** antes de publicar, reverter cada um dos 3 erros de rótulo e
conferir que a `S165` **acusa**. Asserção que nunca foi vista falhando não vale (a lição da
V37, ontem).

---

# FASE B — a reconstrução fluida (só staging)

## B.0 A pergunta que precisa de resposta antes de qualquer código

"Reconstruir o tema" tem dois significados muito diferentes, com risco e retorno muito
diferentes:

| | O que é | Risco | O que o visitante ganha |
|---|---|---|---|
| **(i) Fluidificar a NOSSA camada** | os 85 KB de `onda6.css`, 59 blocos, 758 px, 78 `:hover` sem guarda | **baixo** — não toca no tema, não fere a REGRA Nº ZERO, reversível com `git checkout main` | **quase toda a home**: hero, barra de clientes, títulos de seção, planeta de setores, cards de líder, lista de imprensa são nossos |
| **(ii) Substituir o tema** | 1,1 MB de CSS + 1,6 MB de JS gerados pelo WordPress | **alto** — é o território exato do rollback de 30/07 (onda 4) | páginas internas (práticas, líderes, carreiras, contato), header e rodapé, que hoje são do tema |

O handoff recomenda começar por (i), e eu concordo — mas com o teto dito na cara: **(i)
transforma a home e não conserta as páginas internas.** Se o julgamento do Mario for feito
na home (que é o que ele abre no iPhone), (i) é suficiente para decidir. Se ele quiser
avaliar o site todo fluido, aí é (ii), e (ii) é outra conversa de risco.

**Minha recomendação:** Fase B = **(i) integral + overrides fluidos por cima do tema nas
páginas-alvo**, ainda dentro dos blocos marcados. Isso cabe na regra atual ("sempre por
cima do tema"), é reversível por definição, e produz algo que o Mario consegue julgar.
Só depois do "ficou legal" se discute (ii).

## B.1 O guard-rail que faz "morre ali" ser verdade por construção

O `deploy.ps1` publica **o `public/` do disco**, não do `main`. Quer dizer: rodar deploy com
o branch da reconstrução checkado **põe o tema novo em produção**. Hoje nada impede isso —
o script só recusa se o branch for `gh-pages`.

**Primeiro commit da Fase B, antes de qualquer CSS:**

- `deploy.ps1` **aborta se o branch não for `main`** (com um `-Forcar` explícito para a
  exceção consciente);
- `fechar-onda.ps1` herda o guard (ele encadeia o deploy);
- `deploy-staging.ps1` **imprime branch + `VERSAO`** que está publicando, para nunca haver
  dúvida do que está no staging.

Sem isso, "o teste custou apenas o nosso trabalho" depende de ninguém errar um comando. Com
isso, depende do script. É a diferença entre cuidado e impossibilidade.

## B.2 O ativo que falta: a família `F`, escrita ANTES de tocar no tema

Hoje a suíte tem **25 asserções `V`** que medem render. Elas são o que impede a
reconstrução de quebrar o visual sem ninguém ver — mas boa parte delas **prende o pixel do
modelo antigo** (`font-weight` 400, card de 370/420px, folga ≥24px do M, número em no máximo
2 linhas). Migrar para fluido vai fazer várias falharem **de propósito**, e aí some a rede:
não se distingue mais "mudou porque eu quis" de "quebrou".

A saída é uma família nova de asserções que descreve **comportamento**, não valor — e que
por isso passa nos dois mundos. Escritas no `main`, **verificadas verdes no site aprovado de
hoje**, e só então a migração começa. É caracterização, não teste novo.

| ID | O que mede | Por que existe |
|---|---|---|
| **F01** | 0 overflow-x em N páginas × 9 larguras (320→2560) | é a métrica que o contact sheet já calcula; promovida a gate |
| **F02** | nenhum par de textos com **tinta** sobreposta (`Range.getClientRects`, generalizando a V36) | o bug da onda 63, na forma geral |
| **F03** | nenhum texto abaixo de X px computado; nenhum contraste < 4.5 | fluido tende a encolher texto onde ninguém olhou |
| **F04** | nenhum alvo clicável < 24×24 px | idem, no toque |
| **F05** | nenhum texto cruzando a borda do próprio container / truncado | R15 §Legibilidade, na web |
| **F06** | a dobra da home continua **1 tela cheia sem buraco** em N alturas | é o componente mais calibrado do site; o invariante sobrevive, o pixel não |
| **F07** | **o texto renderizado de cada página é idêntico** entre `main` e o branch | prova que a reconstrução mudou apresentação e **não** conteúdo. Barato e altíssimo valor |
| **F08** | toda regra `:hover` está sob `@media (hover:hover)` — hoje **78 não estão** | a classe do bug da onda 64. Varredura estática, roda em 1 s |
| **F09** | **continuidade**: propriedades-chave (corpo do h1, gap das grades, largura dos cards) variam de forma contínua e monótona de 320 a 2560 em passos de 40 px, sem salto acima de X% entre dois passos vizinhos | **é esta que define "fluido" em número.** Salto grande entre duas larguras vizinhas é literalmente o penhasco de breakpoint que o Mario quer eliminar. Hoje ela **falha** no site atual — e é a única `F` que deve nascer vermelha, como alvo |

Mais uma **baseline visual**: `tools_onda6/qa/baseline.py` fotografa N páginas × 9 larguras
no `main`, guarda em `_baseline/` (gitignored), e o branch compara pixel a pixel — o
`comparar_regiao.py` já faz isso por região via `git stash`; é generalizar. É o que produz o
antes/depois que o Mario vai olhar.

## B.3 A ordem da migração (branch `tema-fluido`)

Do menos calibrado para o mais, cada passo com a suíte `F` verde e o diff visual medido:

| # | Passo | Efeito visual pretendido | Guarda |
|---|---|---|---|
| 1 | **Tokens**: escala fluida de tipo e de espaço como custom properties, num bloco marcado novo. Nada consome ainda | **zero** | diff de pixel ≈ 0 prova que a máquina liga sem mexer em nada |
| 2 | **Tipografia**: pares desktop/mobile → `clamp()` | some o degrau de 62→38px | F09 melhora; F01–F05 verdes |
| 3 | **Espaçamentos**: margens negativas calibradas → derivadas da tipografia (`calc((1em - 1lh)/2)`) | o `-20px` da onda 63 deixa de existir como número | **F02** é a guarda exata deste passo |
| 4 | **Grades**: colunas por faixa → `repeat(auto-fit, minmax(…, 1fr))` (práticas, líderes, insights, setores) | as fileiras deixam de "pular" | F09, F01 |
| 5 | **Container queries** nos componentes que vivem em larguras diferentes | card se adapta ao espaço dele, não à janela | F09 |
| 6 | **Capacidade, não tamanho**: os 78 `:hover` sob `@media (hover:hover)` | conserta a classe da onda 64 no site todo | **F08** |
| 7 | **POR ÚLTIMO: hero + dobra exata + o "m"** (`onda8-dobra.js`, V05/V29/V30, o cálculo do vão) | é a maior densidade de calibração do site | F06 + todas as V do hero |

**Nota técnica a verificar, não assumir:** `clamp()`, `aspect-ratio`, `dvh` e container
queries são antigos e seguros. **`1lh` é o mais novo do conjunto** — o Chrome desta máquina
(151) suporta, medido, mas isso não diz nada sobre quem visita o site. O passo 3 sai com
fallback em `@supports`, e antes dele vale olhar de que navegador vem o visitante da Mirow
(o Search Console começou a acumular CrUX agora — dado que o handoff registra como ainda
inexistente).

## B.4 O ciclo de julgamento

```
branch tema-fluido  ──►  VERSAO = 76  ──►  deploy-staging.ps1  ──►  staging.mirow.com.br
                                                                          │
produção segue em v=75, intocada  ◄───────────────────────────────────────┘
```

O que vai junto para o Mario:

- link do staging;
- **contact sheet antes/depois**, 320→2560, das páginas-alvo, lado a lado;
- resultado da `F` (deve estar verde, com a **F09 saindo do vermelho** — é o número que
  mostra que ficou fluido);
- **tabela de triagem das `V`**: cada `V` que mudou, classificada em *"prendia o pixel do
  modelo antigo, substituída pela invariante X"* ou *"regressão, consertada"*. Nunca
  "re-baselinei".

**Sim** → merge no `main`, bump da `VERSAO`, gate completo, `deploy.ps1`, republicar staging.
**Não** → `deploy-staging.ps1` a partir do `main` (staging volta a igualar produção), branch
fica no repo como registro. Produção não foi tocada em nenhum momento.

## B.5 Riscos, ditos com todas as letras

1. **Deploy do branch errado.** O maior risco desta fase, e o único que atinge produção.
   Mitigado pelo B.1 — e o B.1 é o primeiro commit, não uma boa intenção.
2. **Produção precisar de correção urgente durante a Fase B.** Regra: todo deploy de
   produção durante a fase → rebase de `tema-fluido` no `main` e **republicar o staging**,
   senão o staging fica atrás (o invariante do Mario, quebrado em 18/08 e medido: staging
   v=64 contra produção v=69).
3. **A suíte `V` calibrada no modelo velho.** Endereçado pela família `F` (B.2). Se o Mario
   preferir pular o B.2 para ver algo mais rápido, o custo é explícito: a reconstrução passa
   a ser avaliada só a olho, e "não mudou nada" volta a ser fé em vez de número.
4. **`onda8-dobra.js` mede em runtime e escreve altura em pixel** — ele briga com CSS
   fluido por natureza. Por isso é o passo 7, e por isso a F06 existe antes.
5. **O teto de (i)**, repetido: páginas internas continuam com os breakpoints do tema. Se o
   julgamento do Mario for "a home ficou boa mas /pt/contato/ continua igual", a resposta
   correta é "sim, era o combinado" — não uma correria dentro do tema.

## B.6 O que eu recomendo decidir agora

| # | Decisão | Minha recomendação |
|---|---|---|
| **D1** | Gerador (P3) ou 7º script à mão na imprensa? | **Gerador.** ~1 h a mais, e é o que impede o 4º erro de rótulo |
| **D2** | A Certificação B (02/04/2025) entra na imprensa? O Felipe acha que é mais "sobre nós" | **Entra.** É aparição na imprensa numa página chamada "Mirow na imprensa"; custo zero |
| **D3** | Broadcast: rótulo "Broadcast (Estadão)" com logo do Estadão, ou wordmark próprio? | **"Broadcast (Estadão)" com logo do Estadão** — o leitor reconhece o grupo, e a exceção fica declarada na S165 |
| **D4** | Tentar recuperar os 2 links faltantes agora ou virar issue? | **Issue.** Buscar link de matéria a partir de um post de LinkedIn é caça de tempo indeterminado; não deve atrasar 14 inclusões prontas |
| **D5** | Fase B: escopo (i) ou (i)+(ii)? | **(i) + overrides fluidos nas páginas-alvo.** Julgável, reversível, sem ferir a regra zero |
| **D6** | Escrever a família `F` antes de migrar? | **Sim.** É o que separa esta tentativa da onda 4 |
| **D7** | Data do item do Valor: 10/05/2024 (o `datePublished` da página) ou 28/05/2024 (o que está no ar e no consolidado)? | **10/05/2024**, com nota no mestre — é o dado que a fonte publica. Se o 28/05 for a data da revista impressa, o Felipe confirma |
