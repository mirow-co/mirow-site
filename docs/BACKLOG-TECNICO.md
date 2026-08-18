# Backlog técnico — o que não dá para fazer agora, e o que não dá para fazer neste site

> Levantado em **18/08/2026**, ao fim das ondas 59 e 60, a pedido do Mario. Consolida o que
> sobrou dos dois insumos daquela sessão: o **handoff GEO do Felipe** (11/08) e os **dois
> relatórios PageSpeed Insights** (mobile e desktop, 18/08).
>
> **Regra deste arquivo:** cada linha diz o que **mediu** a limitação, não o que se supõe dela.
> Item sem medição vai marcado como não medido. Ao fechar um item, apagar a entrada e registrar
> a onda no `CLAUDE.md`.

---

## Como ler

| Classe | Significado |
|---|---|
| **A — Impossível no GitHub Pages** | Só sai com mudança de hospedagem (CDN na frente ou servidor próprio). Nenhum esforço nosso dentro do espelho resolve. |
| **B — Bloqueado pela REGRA Nº ZERO** | Tecnicamente pronto para fazer; espera decisão explícita do Mario sobre tocar em arquivo do tema. |
| **C — Espera dado ou decisão de terceiro** | Falta um fato que não está publicado, ou o OK de alguém (Felipe, Andreas). |
| **D — Dá para fazer, só não couberam** | Sem bloqueio nenhum; ficaram para uma onda seguinte por escopo. |
| **E — Dívida estrutural do espelho** | Consequência de o site ser espelho estático de um WordPress. Some numa reconstrução, não numa onda. |

---

## Classe A — impossível no GitHub Pages

### A1. Cache de 10 minutos em todos os assets próprios
- **O que o Google pede:** "Use efficient cache lifetimes — economia de **1.516 KiB**". É o item
  de **maior número** de todo o relatório mobile.
- **Medido em 18/08:** `curl -sI` no bundle do tema devolve `Cache-Control: max-age=600`. O
  GitHub Pages não expõe configuração de cabeçalho — não há `.htaccess`, `_headers` nem painel.
- **A ironia:** o espelho já carimba `?v=NN` em todo asset a cada onda
  (`tools_onda6/27_cache_busting.py`). Temos a disciplina que justificaria cache de um ano, e não
  temos onde declará-la.
- **O que destravaria:** Cloudflare de graça na frente do Pages (resolve cache **e** todos os
  itens A2–A4 de uma vez), ou sair do Pages.

### A2. Nenhum header de segurança
- **O que o Google lista:** as 5 auditorias de *Trust and Safety* — CSP contra XSS, HSTS,
  isolamento de origem com COOP, anti-clickjacking com XFO/CSP, e Trusted Types.
- **Medido em 18/08:** `curl -sI https://mirow.com.br/pt/` não devolve **nenhum** de
  `strict-transport-security`, `content-security-policy`, `x-frame-options`,
  `cross-origin-opener-policy`, `referrer-policy`, `permissions-policy`,
  `x-content-type-options`. Zero.
- **Ressalva honesta:** a extração dos PDFs perdeu o estado (passou/falhou) dessas 5 auditorias,
  então não afirmo que o Google as reprovou — mas a ausência dos headers está medida.
- **Por que é classe A:** header é resposta HTTP; site estático não escolhe a resposta do
  servidor. `<meta http-equiv>` cobre CSP parcialmente e **nada** de HSTS/COOP/XFO.
- **O que destravaria:** CDN ou hospedagem própria.

### A3. Redirect de verdade (301) nos 160 stubs
- **Hoje:** cada URL antiga é uma página HTML com `meta http-equiv="refresh"` + `canonical` +
  `noindex` (convenção das ondas 29/33). **Medido:** `pt/lider/591/` responde **200**, não 301.
- **Custo real:** o robô baixa uma página inteira para descobrir que deve ir a outra; e o
  navegador do visitante pisca. Funciona — o Google respeita canonical + refresh — mas é
  inferior.
- **O que destravaria:** qualquer hospedagem que emita 301 (CDN com regras de redirect resolve).

### A4. Brotli
- **Medido:** pedindo `Accept-Encoding: br`, o Pages devolve **gzip**. Brotli comprimiria o
  bundle de CSS/JS uns 15–20% melhor que gzip, de graça.
- **O que destravaria:** CDN.

> **Nota única para A1–A4:** os quatro têm a **mesma** solução, e é uma decisão de arquitetura,
> não uma tarefa de onda. Vale reabrir quando houver dado de campo mostrando que a visita
> repetida ou o mobile importam de verdade para o público da Mirow.

---

## Classe B — bloqueado pela REGRA Nº ZERO (decisão do Mario)

### B1. Minificar `bundle-js.js` (1,60 MB no disco) e `bundle-css.css` (1,11 MB)
- **O que o Google pede:** 403 KiB de minificação de JS + 154 KiB de CSS. O JS é o nó que define
  a latência crítica de **991 ms**, gera tarefa longa de 147 ms e **todos** os *forced reflows*
  da página. O CSS bloqueia o desenho por **2.980 ms**.
- **Minificar não muda um pixel** — é o mesmo código sem espaços e sem comentários. O que trava é
  que mexe em arquivo do tema, e a regra nasceu de um rollback de reescrita de tema.
- **Recomendação atual (mudou em 18/08):** **esperar o dado de campo.** O relatório desktop tira
  **95** de performance, com LCP de 0,7 s, e nenhum destes itens tem peso lá. O ganho é só em
  celular fraco com rede lenta. O Search Console vai acumular CrUX agora que a propriedade está
  verificada e dizer de que aparelho o visitante chega.
- **Se for feito, as salvaguardas:** original preservado no git (rollback num comando), script
  idempotente numerado como todos os outros, e a suíte completa no gate — incluindo os checks
  visuais que medem a dobra exata em 4 larguras.
- **Ressalva de número:** a economia real é **menor** que os 403 KiB anunciados, porque o gzip já
  está ligado (o bundle de 1,6 MB chega em 483 KB). Não medi quanto sobra depois do gzip.

### B2. Remover o CSS não usado de dentro do bundle (203 KiB, 98,8% do arquivo)
- **Recomendação: não fazer**, em nenhum cenário, do jeito que o relatório sugere. Os 98,8%
  foram calculados **só na home**, e o mesmo arquivo serve as 109 páginas. Cortar com base numa
  página é repetir o erro da onda 37, que estourou a dobra por medir só o `pt/`.
- **O que faria sentido:** cobertura de código nas 109 páginas antes de cortar uma linha. É
  projeto, não onda.

### B3. Ordem de cabeçalhos com a tag correta
- **Hoje:** os `<h4>` que apareciam depois de um `<h2>` ganharam `aria-level="3"` (onda 60), que
  corrige a semântica para leitor de tela e para o Lighthouse **sem** mexer no visual.
- **Por que não trocamos a tag:** o CSS do tema estiliza `h4` **por tag** (`h4{...}`), então
  `<h3>` mudaria a aparência.
- **Pendência de verificação:** não medi se o Lighthouse aceita `aria-level` nesta auditoria.
  Confirmar na próxima rodada de PageSpeed; se não aceitar, o conserto de verdade exige mexer no
  CSS do tema e vira classe B.

---

## Classe C — espera dado ou decisão de terceiro

### C1. ~~`foundingDate`~~ — RESOLVIDO em 18/08
- O Mario confirmou: **12/04/2012**. Está no schema como `"foundingDate": "2012-04-12"`, e a
  S149 passou a **exigir** o valor (antes ela proibia o campo, por não ser dado publicado).
- `foundingLocation` **continua Rio de Janeiro** — a firma nasceu lá em 2012 como *Portas
  Consulting Brasil*, e a Nossa História do site diz isso. É o campo que explica as menções ao
  Rio sem afirmar sede no Rio.

### C2. Elmar Gans no schema — **Felipe**
- Deixado fora de propósito ("há mudança de situação em curso"). Ele **continua** na listagem de
  líderes e nos cards da home. Se entrar, é uma linha no mesmo formato.

### C3. João Daniel Ramos no schema — **Felipe/Mario**
- Fora porque o `@id` exige URL própria e ele não tem página individual. Se ganhar página, entra.

### C4. Frase de sede em texto corrido — **Andreas**
- **Está pronta e no staging**, no branch `onda59-sede`: abre a seção "Nossas áreas de expertise"
  nas 3 homes e a Nossa História nos 3 idiomas.
- Saiu do hero porque **estourava a dobra exata em 31px** (medido pelos checks V01–V03 e V30).
- É mudança de posicionamento, então segue o fluxo: staging → OK do Andreas → produção.

### C5. Endereço da sede — CORRIGIDO em 18/08, com duas pendências
- **Fato novo do Mario:** o escritório é **Av. Ibirapuera, 2033 — conjunto 133, São Paulo/SP**.
  **Não existe mais escritório no Rio**, mas o **CNPJ do Rio continua ativo**.
- Corrigido no schema das 3 listagens, na descrição da Organization e na `meta description` das
  3 homes (`tools_onda6/119_sede_sao_paulo.py`). A S149 agora **cobra** São Paulo/SP.
- **Pendência 1 — CEP.** Saiu do schema: o Mario não passou o CEP novo e a regra é não inventar
  (o antigo, 22290-160, era do Rio). Uma linha para reinserir quando ele passar.
- **Pendência 2 — política de privacidade (pt/en/de).** Ali o endereço é o **legal**, amarrado ao
  CNPJ ("inscrita no CNPJ sob o n° 15.353.236/0001-89, com endereço na Rua Lauro Müller, 116,
  sala 1504, Rio de Janeiro/RJ"). Como o CNPJ do Rio segue ativo, **não** foi alterado — mudar
  texto jurídico é decisão do Mario/jurídico, não conserto de conteúdo.
- **Achado colateral:** `en/press/` e `de/presse/` carregam esse mesmo parágrafo de privacidade,
  e o `pt/imprensa/` **não**. Provável resíduo do molde da onda 29 (a mesma origem do bug de
  `hreflang` que a onda 33b consertou). Vale uma limpeza.

### C6. Nome dos 6 selos de reconhecimento — **Mario**
- O `alt` deles foi escrito lendo o que está **dentro de cada imagem** (não deduzido do nome do
  arquivo, que num caso é `image-52.png`): CDP - Disclosure Insight Action, UN Global Compact,
  Seven to Watch, Science Based Targets, Consulting Fastest Growing Firms, Great Place to Work.
- Se algum estiver errado, é uma linha em `tools_onda6/118_alt_restante.py`.

### C7. Wikidata — **Felipe/Mario**
- Item 4 do handoff, e o único que nunca foi do site. Hoje "Mirow" no Wikidata devolve a cidade
  alemã, o sobrenome, um povoado e um castelo polonês. Exige conta de uma pessoa da firma.
- Issue [#235](https://github.com/mirow-co/mirow-marketing/issues/235).

### C8. Dado de campo (CrUX) — **o tempo**
- Os dois relatórios dizem **"No Data"**: a propriedade do Search Console acabou de ser
  verificada. Sem isso, não sabemos se o público da Mirow chega de celular (onde a nota é 75) ou
  de desktop (onde é 95) — e é essa resposta que decide o B1.

---

## Classe D — onda 61, FEITA em 18/08

### D1–D3. ~~Imagens~~ — RESOLVIDO
- **`clientes/edp.svg` 414 KB → `edp.webp` 35 KB.** Não era vetor: eram **quatro bitmaps
  embutidos** em base64 sobre clipPath/gradiente, para um logo exibido a **81×30 px**.
- **`clientes/mercedes-benz.svg` 298 KB → `mercedes-benz.webp` 17 KB.** Vetor de verdade, mas
  **489 paths e 160 KB só de coordenadas** para exibir 119×30.
- **4 fotos de líder e 6 selos → WebP**, e `taesa.png` → WebP: 658 KB → 110 KB.
- **181 imagens órfãs removidas (25,9 MB)** — nenhuma página, CSS ou JS as referenciava. Peso
  morto herdado do WordPress.
- **Total: ~27,5 MB a menos no espelho**, sendo ~1,1 MB no que a home baixa.

**A lição que custou mais tempo — dimensão de raster e reflow sub-pixel.** Ao trocar SVG por
WebP eu usei "3× o tamanho exibido" (edp: 243×90). A largura renderizada caiu de **81,38 para
81,00 px**, porque depois do load quem define a caixa é o **aspecto real do arquivo** — os
atributos `width`/`height` do HTML são só dica de pré-load. Como a fileira de logos é
**centrada**, os 0,38px se redistribuíram e **7 logos que eu nunca toquei** mudaram de
antialiasing (2,25% dos pixels da barra). Conserto: gerar o raster na **razão exata** do
original, dividindo pelo máximo divisor comum (edp 3426×1263 → **1142×421**; mercedes 1400×354 →
**700×177**; taesa tem gcd 1, então ficou no tamanho original, só trocou de formato). Depois
disso o diff caiu para **0,27%**, confinado aos dois logos realmente trocados.

**O preço dessa escolha:** `edp.webp` tem 1142×421 para exibir 81×30 — 14× maior em pixels do que
o necessário, porque é a menor dimensão com a razão exata. Em bytes são 35 KB (contra 414 KB), o
que é o que importa na transferência. Se algum dia valer os 29 KB, dá para usar 244×90 aceitando
um reflow de 0,04px.

### D4. ~~Asserção de imagem maior que o exibido~~ — substituída por algo melhor
A **S160** cobra dois invariantes que valem mais: **nenhuma imagem que a home pede passa de
120 KB**, e **nenhuma imagem órfã acima de 120 KB** (impede os 25,9 MB de voltarem).

### D5. Duas tarefas longas nossas — em aberto
`onda8-dobra.js` (99 ms) e `onda17-horizonte.js` (81 ms mobile / 57 ms desktop) aparecem na lista
de *long tasks* dos dois relatórios. Não são o gargalo, mas são **nossos** — dá para mexer sem
tocar no tema.

### D6. Imagens grandes de ARTIGO — onda 62 (o maior naco que sobrou)
Depois da limpeza, ainda há **~167 imagens referenciadas acima de 120 KB, somando ~50 MB**. Não
estão na home, então não afetam o PageSpeed dela, mas pesam nas páginas de insight, líder e
carreiras:

| Arquivo | Peso | Onde |
|---|---|---|
| `2026/01/GRANDE-02-scaled.png` | **3.583 KB** | artigo |
| `2024/12/imagem_gerada-e1734389796400.png` | 1.374 KB | artigo |
| `2024/03/Imagem1-scaled.jpg` | 927 KB | artigo |
| `2024/04/banner-bg-carreiras-1.png` e `-2.png` | 915 KB cada | banner de carreiras |
| `2024/04/banner-bg-leaders.png` e `-1.png` | 822 KB cada | banner de líderes |

Os banners repetidos (`-1`, `-2`) são o caso mais fácil: são o mesmo fundo duplicado. A
**S160 não cobre estes de propósito** — para não virar alarme crônico que se aprende a ignorar.

## Classe E — dívida estrutural do espelho

### E1. Formulários sem backend
- O tema carrega o CSS do plugin Formidable em **55 páginas** que têm markup de formulário, mas o
  espelho não tem PHP: o envio real virou e-mail nas ondas 18/45.
- Consequência: os assets de formulário (`ajax_loader.gif`, `form-success.gif`,
  `form-select-arrow.svg`) nunca foram espelhados. A onda 60 pôs **placeholders transparentes** —
  o que preserva exatamente a aparência atual, já que eles nunca carregaram.
- **Se algum dia o formulário voltar a ser real**, esses placeholders precisam virar os assets
  verdadeiros. Está registrado no cabeçalho de `tools_onda6/116_texture_placeholder.py`.

### E2. `texture-7.png` — a textura de fundo perdida
- O CSS do tema pede esse arquivo em **22 seletores** (`.wrap-gradient-1`, `.wrap-gradient-2`,
  `.home-experience::after`, `.menu__nav`, `.blog-single__content`, …). Ele **nunca** foi
  espelhado: não está em nenhum commit, e responde 404 no ar.
- **A consequência mais importante:** todo o visual aprovado nas 59 ondas já era **sem** a
  textura. Restaurar a original mudaria a aparência de 22 seletores de uma vez — isso passa a ser
  decisão de design do Mario, não conserto de bug.
- A onda 60 pôs placeholder transparente: mata o 404 sem mudar pixel.

### E3. Seis referências mortas em CSS que ninguém pede
- `chosen-sprite.png`, `chosen-sprite@2x.png` (biblioteca `chosen`), `mundi-ptbr.jpeg`,
  `mundi-en.jpg`, `mundi-de.jpg` (mapas-múndi do submenu antigo), `dashicons.eot`,
  `dashicons.ttf`.
- **Medido:** nenhuma das classes desses seletores existe em página alguma, e o
  `dashicons.min.css` deixou de ser carregado na onda 60. Nenhuma delas é buscada pelo navegador
  — foi por isso que o Google reportou **um** erro de console, e não sete.
- **Por isso a asserção S157 mede alcançabilidade do seletor**, não existência no disco. Some
  numa limpeza de tema, não numa onda.

### E4. Nomes de arquivo herdados sem significado
- `image-52.png` é o selo do Great Place to Work; `teste-1.png` a `teste-16.png` são ilustrações
  de caso nas páginas de prática. Renomear exigiria reescrever referência em 30+ páginas por um
  ganho só de legibilidade do repo.

### E5. WebMCP / Agentic Browsing
- Categoria **nova** do Lighthouse ("still under development and subject to change"), que mede se
  um agente de IA consegue operar a página — inclui anotar formulários com WebMCP.
- Hoje marcada "não aplicável" nos dois relatórios. Vale acompanhar: é a mesma família do trabalho
  GEO do Felipe, e a auditoria de `llms.txt` (que **passa**) já está lá.

### E6. A camada Astro
- `src/`, `astro.config.mjs` e `dist/` seguem no repo como resquício do protótipo rejeitado da
  onda 4. Estão fora do deploy e não voltam. Apagar é limpeza de repo, sem efeito no site.

---

## Dívida de medição — registrar para não repetir

1. **Toda medição de PageSpeed daqui para frente é mobile _e_ desktop.** Esta sessão mediu
   primeiro só o mobile e o plano saiu enviesado: os itens de performance mais caros
   simplesmente não existem no desktop, que tira 95. Um só form factor engana.
2. **Não implementar da lista do Google de cima para baixo.** O item do topo (cache, 1.516 KiB)
   é justamente o único impossível nesta hospedagem. Conferir a viabilidade antes da ordem.
3. **A asserção acha mais que o relatório.** O PageSpeed citou 4 imagens sem `alt`; a asserção
   que cobra a classe do defeito achou **124**, em páginas que o relatório nunca visitou. Escrever
   a asserção da classe, não do caso.
4. **Repetir a medição GEO em 10/09/2026** (D+30), mesmo protocolo do Felipe: mesmas 8 perguntas,
   mesmo assistente, sessão deslogada. Baseline a bater: descoberta 0/15 e 8 de 9 respostas sem
   citar o site próprio.
