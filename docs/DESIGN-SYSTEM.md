# DESIGN-SYSTEM.md — tokens e componentes do site mirow.com.br

> **Leia este arquivo antes de escrever qualquer CSS novo.** Ele descreve o tema espelhado
> (REGRA Nº ZERO: o tema é intocável — só se escreve CSS **aditivo**, em blocos marcados no
> `onda6.css`). Este doc é o contrato que impede a IA de inventar cor, fonte ou espaçamento.
> Formato inspirado no padrão DESIGN.md para agentes (developersdigest.tech/blog/design-md-for-ai-agents).

## 1. Paleta (do tema + camada onda6)

| Token | Hex | Uso canônico |
|---|---|---|
| `--primaryColor` | `#020E66` | Navy Mirow: fundos, títulos em página clara, barra do header |
| `--secondaryColor` | `#0E41A7` | Azul médio: hover de link do tema, gradientes |
| Ciano Mirow | `#00ADEC` | Acento da camada onda6: hovers, números, destaques |
| Azul-claro Mirow | `#AAD5E8` | Linhas separadoras, títulos suaves (rgba .25 nas bordas) |
| `--whiteColor` | `#FFFFFF` | Texto sobre navy |
| `--blackColor` | `#212121` | Texto sobre claro |
| Gradiente de página | `#A2BAE4 → #2D47B0 → #020E66` | `wrap-gradient-*` do tema (não recriar na mão) |
| Vidro fosco | `rgba(255,255,255,.10)` + `blur(6px)` | Painéis de leitura do hero (onda15) |
| Marcas (hover contatos) | WA `#25D366` · LinkedIn `#0A66C2` · IG `#E1306C` · e-mail `#00ADEC` | onda16 (S-42) |

**Proibido:** cores fora desta tabela; verde/amarelo/vermelho decorativos; trocar o gradiente do tema.

## 2. Tipografia (do tema — NÃO é a identidade Arial dos decks!)

| Token | Valor | Uso |
|---|---|---|
| `--fontFamily` | `"Archivo", sans-serif` | Títulos (h1/h2), números do hero |
| `--secondaryFontFamily` | `"Libre Franklin", sans-serif` | Corpo, subtítulos, pills, labels |
| `--tertiaryFontFamily` | `"Roboto Serif", sans-serif` | Raro (citações) |
| Tamanhos-base | `--titleSize:25` · `--subtitleSize:20` · `--textSize:14` | O tema escala por media query |

**Proibido:** introduzir família nova (nem Arial — Arial é identidade de *deck*, não do site);
tamanhos soltos fora da escala visível na página em que se está mexendo.

## 3. Breakpoints do tema

| Corte | Papel |
|---|---|
| `min-width: 992px` | O grande divisor mobile/desktop do tema (194 usos) — siga-o |
| `min-width: 1200px` | Ajustes wide (hero-numeros só existe aqui pra cima) |
| `max-height: 820-839px` | Telas baixas (1366×768): a camada onda6 aperta o hero |

QA responsivo: `python tools_onda6/qa/breakpoints.py <url>` gera o contact sheet
(320/390/768/1024/1366/1920 — 320 é o piso WCAG 1.4.10 de reflow sem scroll horizontal).

## 4. Componentes canônicos (HTML existente — copie destes, não invente)

| Componente | Onde ver | Classes |
|---|---|---|
| Hero da home | `public/pt/index.html` ~l.190 | `.banner`, `.hero-texto` (painel de vidro), `.hero-contatos__link` (pills), `.hero-numeros` (pilha à direita) |
| Barra superior / rodapé gêmeo | qualquer página | `.menu`, `.menu__contatos-link`, `.rodape-barra` (clone literal — asserção S36) |
| Barra de logos de clientes | homes | `.clientes-logos` (gerada de `clients.json` — P3, nunca editar à mão) |
| Cards de práticas | homes | `.home-experience` |
| Formulário de contato | `public/contato/` | `form_contact-form*` + `mirow-forms.js` (Web3Forms) |

## 5. Regras de escrita de CSS (a camada onda6)

1. Todo CSS novo vive em bloco marcado `/* onda<N>:<chave>:ini|fim */` dentro de
   `public/wp-content/uploads/2026/07/onda6/onda6.css`, escrito via
   `tools_onda6/_onda7_css.py:escrever_bloco_css` — nunca em arquivo novo, nunca no CSS do tema.
2. Especificidade: vença o tema por seletor mais específico; `!important` só onde o tema já força.
3. Todo hover novo tem transição (`300ms ease-in-out` é o padrão do tema).
4. Depois de qualquer mudança: bump `VERSAO` no `27_cache_busting.py` + rodar; senão o navegador
   serve CSS velho e o bug "parece" de layout.
5. Antes de "PRONTO, aguardando OK": suíte `tools/verificacoes.py` verde + contact sheet de
   breakpoints da(s) página(s)-alvo.

## 6. Capturando referência visual de outro site

Para replicar uma seção de referência (workflow validado, sem playwright — CDP puro basta):
1. Screenshot: `python tools_onda6/qa/shot.py <url-da-referencia> ref.png 1920`.
2. Estilos computados de uma seção: `Runtime.evaluate` com
   `JSON.stringify(Object.fromEntries(['color','font-family','font-size','padding','background'].map(p=>[p,getComputedStyle(document.querySelector('SELETOR'))[p]])))`
   usando a classe `WS` do `shot.py`.
3. A referência informa **estrutura e ritmo**, nunca cores/fontes — as nossas vêm das tabelas acima.
