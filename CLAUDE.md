# CLAUDE.md — repo `mirow-co/mirow-site` ("novo site" da Mirow & Co.)

> Leia este arquivo INTEIRO antes de tocar em qualquer coisa. Ele existe porque o processo
> anterior perdeu pedidos do Mario e poluiu a máquina com 9 pastas paralelas. As regras abaixo
> não são estilo — são o contrato de trabalho (plano `2026-07-30_plano-processo-e-melhorias-site_v1.html`
> no repo privado `mirow-co/mirow-marketing`, pasta `03_Planos/`).

## O que é este repo

Espelho estático do site `mirow.com.br` (que era WordPress), servido pelo GitHub Pages em
https://mirow-co.github.io/mirow-site/pt/ . O WordPress vai ser **desligado**; este repo é o site.
275 páginas HTML em `public/`, 3 idiomas (pt/en/de).

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

### P3 — Fonte única de dados
Dado curado mora em **um** arquivo mestre, no repo privado, e o HTML é **gerado** dele.
Caso que originou a regra: a Sotreq ficou fora da barra de clientes porque a decisão do sócio
foi para a memória e o `clients.json` seguiu com o status velho.

| Dado | Mestre (privado, `mirow-marketing`) | Gerador |
|---|---|---|
| Clientes da barra de logos | `08_Site/2026-07-30_clients-curadoria-interna.json` | `tools/gen_clients.py` |

### P4 — Comunicação de status inequívoca
Todo fim de onda: tabela "pedido → estado", com **só 3 estados**:
**NO AR** (verificado ao vivo) · **PRONTO, aguardando OK do Mario** · **NÃO FEITO** (com motivo).
Nunca dizer "pronto" sem dizer qual dos três. **Publicar só com OK explícito do Mario sobre os
screenshots.**

## Pasta única — proibido criar pastas/worktrees paralelos

`C:\dev\mirow-site` é a **única** pasta. Trabalho em branches normais dentro dela.
Proibido: `git worktree` persistente, cópias `mirow-site-*`, pastas de serve (`_serve9`),
junctions de deploy. Elas já causaram QA em cima da árvore errada.
Se precisar servir local para QA: `python -m http.server` a partir da raiz que contém `public/`
e **matar o processo ao terminar** (conferir se não há um órfão servindo pasta errada antes de
acreditar em qualquer screenshot).

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

| **26** | **PRONTA, aguardando OK** (04/08) — 7 pedidos do Mario (S-97..S-103, issues #155–#161): "Ver todos os líderes" em navy; **o site inteiro em UMA fonte** (Titillium Web — as 3 famílias do tema nunca eram carregadas, ver `docs/DESIGN-SYSTEM.md` §2); submenu Práticas no tamanho de Sobre nós (19px, revoga a S-94/S-88); rodapé sem filete antes da política; e-mail de Andreas e Felipe nos cards de líder da home; imprensa com a linha inteira clicável; práticas sem Elmar, com Andreas e Felipe (36 páginas). Suíte: 120 asserções. |

Backlog aberto: issues `site-onda` (S-01..S-19) no `mirow-co/mirow-marketing`.

## Erros a NÃO repetir

1. Implementar de memória → sempre da issue, com o texto verbatim do Mario.
2. Confiar em arquivo de dados sem conferir a decisão registrada (caso Sotreq).
3. Dizer "pronto" sem distinguir NO AR × aguardando OK.
4. Criar pasta/worktree e não limpar.
5. QA sem asserção de regressão do acumulado.
6. Inserir `<link>`/`<script>` sem `?v=` (cache serve versão velha).
7. Acreditar em screenshot sem checar qual pasta o servidor local está servindo.

## Governança a cada marco

Comentar a issue `mirow-co/mirow-marketing#42`, atualizar `00_Admin/gestao-projeto.html` no repo
privado (carimbo de data) e commitar. **Nunca `git add -A` no repo de marketing** (regra
pós-vazamento de dado de cliente — lá se adiciona arquivo por arquivo).
