/* Medicao Mirow & Co. — GA4 (issue mirow-marketing#3)
 *
 * Arquivo unico compartilhado pelas paginas publicadas em public/. O deploy do
 * GitHub Pages publica public/, nao o dist/ do Astro, entao a medicao do site no
 * ar mora aqui. O componente src/components/Analytics.astro cobre as rotas Astro
 * e so passa a valer quando o build do Astro virar a fonte do deploy.
 *
 * Duas propriedades durante a transicao:
 *   G-VK4QHHHS5X — herdada do WordPress (veio no espelho do mirow.com.br). Dono
 *                  ainda nao confirmado. Mantida para nao interromper a serie.
 *   G-5VTS0MZK79 — propriedade institucional Mirow, criada em 2026-08-03.
 * Measurement ID e publico por natureza, por isso vive no codigo (nao e segredo, R11).
 *
 * Consentimento: Consent Mode v2 com default 'denied', mesma postura ja decidida
 * no PR #6 deste repo. Com analytics_storage negado o GA4 roda cookieless: os
 * eventos chegam, mas sem identificacao persistente do visitante, o que degrada
 * usuarios unicos e atribuicao. Passar para 'granted' depende do banner de
 * cookies, que segue como decisao aberta do Mario na #3. Quando o banner existir,
 * ele chama: gtag('consent', 'update', { analytics_storage: 'granted' }).
 */
(function () {
  'use strict';

  var IDS = ['G-VK4QHHHS5X', 'G-5VTS0MZK79'];
  var BASE = ''; // vira '' na virada de dominio (issue #42)

  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = window.gtag || gtag;

  gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied',
    wait_for_update: 500
  });
  gtag('js', new Date());

  var path = location.pathname;
  if (BASE && path.indexOf(BASE) === 0) path = path.slice(BASE.length) || '/';

  var lang = /^\/(pt|en|de)(\/|$)/.exec(path);
  lang = lang ? lang[1] : 'pt';

  function pageType(p) {
    if (/^\/(pt|en|de)?\/?$/.test(p)) return 'home';
    if (/\/(contato|contact|kontakt)\//.test(p)) return 'contato';
    if (/\/(carreiras|careers|karriere)\//.test(p)) return 'carreiras';
    if (/\/(pratica|practice|branchen)\//.test(p)) return 'pratica';
    if (/\/(lider|leader)\//.test(p)) return 'perfil';
    if (/\/(analises|insights)\//.test(p)) return 'lista-insights';
    if (/\/imprensa\//.test(p)) return 'imprensa';
    if (/\/mirow-cx-index\//.test(p)) return 'ferramenta';
    return 'insight';
  }

  var PAGE_TYPE = pageType(path);
  var COMMON = { page_type: PAGE_TYPE, idioma: lang };

  IDS.forEach(function (id) {
    gtag('config', id, COMMON);
  });

  function track(name, params) {
    var p = { page_type: PAGE_TYPE, idioma: lang };
    for (var k in params) if (Object.prototype.hasOwnProperty.call(params, k)) p[k] = params[k];
    gtag('event', name, p);
  }

  /* Canal de contato. Proxy mais direto de "conversas geradas", que e a metrica
     que importa (ver CLAUDE.md do mirow-marketing). */
  function canalDe(href) {
    if (/^mailto:/i.test(href)) return 'email';
    if (/wa\.me|whatsapp/i.test(href)) return 'whatsapp';
    if (/linkedin\.com/i.test(href)) return 'linkedin';
    if (/instagram\.com/i.test(href)) return 'instagram';
    if (/^tel:/i.test(href)) return 'telefone';
    return null;
  }

  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest('a[href]') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';

    var canal = canalDe(href);
    if (canal) { track('contato_click', { canal: canal, destino: href }); return; }

    if (/\.pdf(\?|#|$)/i.test(href)) {
      track('download_pdf', { arquivo: href.split('/').pop().split('?')[0] });
      return;
    }

    if (/forms\.office\.com|forms\.microsoft\.com|forms\.gle/i.test(href)) {
      track('saida_forms', { destino: href });
      return;
    }

    // Saida para dominio externo que nao seja nenhum dos casos acima.
    if (/^https?:\/\//i.test(href) && href.indexOf(location.host) === -1) {
      track('saida_externa', { destino: href });
    }
  }, true);

  /* Envio de formulario. Captura no document para funcionar com qualquer
     ferramenta que renderize um <form> na propria pagina. NAO dispara se o
     formulario da #64 vier como iframe de terceiro (Forms, Typeform e afins):
     nesse caso o submit acontece dentro do iframe e o evento a usar e o
     saida_forms acima, ou uma pagina de obrigado propria. */
  document.addEventListener('submit', function (ev) {
    var f = ev.target;
    if (!f || f.tagName !== 'FORM') return;
    var persona = PAGE_TYPE === 'carreiras' ? 'candidato'
      : PAGE_TYPE === 'contato' ? 'cliente'
      : 'indefinido';
    track('form_submit', { persona: persona, form_id: f.getAttribute('id') || f.getAttribute('name') || 'sem-id' });
  }, true);

  /* Profundidade de leitura, so em pagina de artigo: separa visita de leitura. */
  if (PAGE_TYPE === 'insight') {
    var marcos = [50, 90];
    var vistos = {};
    var ticking = false;

    function checarScroll() {
      ticking = false;
      var doc = document.documentElement;
      var alcance = doc.scrollHeight - window.innerHeight;
      if (alcance <= 0) return;
      var pct = ((window.pageYOffset || doc.scrollTop) / alcance) * 100;
      marcos.forEach(function (m) {
        if (pct >= m && !vistos[m]) {
          vistos[m] = true;
          track('leitura_artigo', { profundidade: m });
        }
      });
      if (vistos[90]) window.removeEventListener('scroll', onScroll);
    }

    function onScroll() {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(checarScroll);
    }

    window.addEventListener('scroll', onScroll, { passive: true });
  }
})();
