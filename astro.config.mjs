import { defineConfig } from 'astro/config';

// GitHub Pages (project site): https://mirow-co.github.io/mirow-site/
// Na virada para o dominio proprio: site: 'https://mirow.com.br', base: '/'
export default defineConfig({
  site: 'https://mirow-co.github.io',
  base: '/mirow-site',
  trailingSlash: 'always',
});
