# mirow-site — protótipo do novo mirow.com.br

> Protótipo funcional do site da Mirow & Co. reconstruído em **Astro + conteúdo em
> markdown + deploy automático** (GitHub Pages). Objetivo: validar que conseguimos operar
> o site com domínio total do código — postagens rápidas, SEO/GEO, multi-idioma — sem
> depender de dev externo para conteúdo. Contexto: issue
> [#42](https://github.com/mirow-co/mirow-marketing/issues/42) do repo `mirow-marketing`.

## Como publicar conteúdo (o teste principal)

1. Edite ou crie um arquivo `.md` em `src/content/insights/<idioma>/` (ou `practices/`)
2. Commit + push na `main`
3. O GitHub Actions builda e publica sozinho (~1 min)

Exemplo de novo insight (`src/content/insights/pt/meu-estudo.md`):

```markdown
---
title: "Título do estudo"
description: Resumo de uma linha para SEO e para o card.
date: "2026-07-24"
---

Texto do artigo em markdown...
```

Crie o par em `en/` com o mesmo nome de arquivo para a versão em inglês.

## Estrutura

| Onde | O quê |
|---|---|
| `src/content/insights/{en,pt}/` | Artigos/estudos (1 arquivo .md por idioma) |
| `src/content/practices/{en,pt}/` | Páginas de práticas |
| `src/data/leaders.json` | Líderes (nome, cargo, bio EN/PT) |
| `src/i18n.ts` | Textos de interface (nav, formulários, home) |
| `src/layouts/Base.astro` | Layout global: header, footer, paleta Mirow, schema.org |
| `src/pages/` | Templates das páginas (raramente precisam mudar) |

## Rodar local

```
npm install
npm run dev
```

## O que este protótipo demonstra (e o que ainda falta)

Demonstra: identidade Mirow (navy/ciano/Arial) · EN/PT com hreflang · postagem via
markdown · schema.org JSON-LD · páginas estáticas rápidas (Core Web Vitals) · formulários
de contato e carreiras (mock).

Falta para produção: formulários reais (função serverless → e-mail sócios/RH, integração
Microsoft 365/Graph) · migração completa do conteúdo (8 práticas, 11 insights, história,
reconhecimentos) · alemão (DE) · mapa de redirects 301 do WordPress · domínio próprio
(troca de `base` no `astro.config.mjs`) · decisão sobre o módulo de
carreiras/recrutamento legado (arquivos de candidatos no WP — LGPD).

## Identidade (R4 Mirow)

Paleta: navy `#020E66` · dark `#071C25` · ciano `#00ADEC` · azul-claro `#AAD5E8` ·
cinza `#7F7F7F`. Fonte: Arial. Logo: `Mirow & Co.` (imagem oficial em `public/`).
