// Smoke test do public/assets/mirow-analytics.js sem browser: stub minimo de DOM,
// executa o arquivo e inspeciona o que entrou no dataLayer.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const SRC = readFileSync(
  new URL('../public/assets/mirow-analytics.js', import.meta.url),
  'utf8'
);

function run(pathname, { clickHref = null, submit = false, scrollTo = null } = {}) {
  const listeners = { click: [], submit: [], scroll: [] };
  const win = {
    dataLayer: undefined,
    location: { pathname, host: 'mirow-co.github.io' },
    innerHeight: 800,
    pageYOffset: 0,
    addEventListener: (t, fn) => (listeners[t] ||= []).push(fn),
    removeEventListener: () => {},
    requestAnimationFrame: (fn) => fn(),
  };
  win.window = win;
  const doc = {
    documentElement: { scrollHeight: 4000, scrollTop: 0 },
    addEventListener: (t, fn) => (listeners[t] ||= []).push(fn),
  };
  const ctx = { window: win, document: doc, location: win.location, Date, Object, RegExp };
  vm.createContext(ctx);
  vm.runInContext(SRC, ctx);

  if (clickHref) {
    const a = { getAttribute: (k) => (k === 'href' ? clickHref : null) };
    const ev = { target: { closest: (sel) => (sel === 'a[href]' ? a : null) } };
    listeners.click.forEach((fn) => fn(ev));
  }
  if (submit) {
    const form = { tagName: 'FORM', getAttribute: () => 'form-contato' };
    listeners.submit.forEach((fn) => fn({ target: form }));
  }
  if (scrollTo !== null) {
    win.pageYOffset = scrollTo;
    listeners.scroll.forEach((fn) => fn());
  }
  return win.dataLayer.map((a) => Array.from(a));
}

function show(titulo, dl) {
  console.log(`\n### ${titulo}`);
  for (const e of dl) {
    const [k, a, b] = e;
    console.log(`  ${k} ${a ?? ''} ${b ? JSON.stringify(b) : ''}`);
  }
}

let falhas = 0;
function ok(cond, msg) {
  console.log(`  ${cond ? 'OK  ' : 'FALHA'} ${msg}`);
  if (!cond) falhas++;
}

// 1. Home PT: consent default + as duas propriedades configuradas
let dl = run('/mirow-site/pt/');
show('home pt', dl);
ok(dl[0][0] === 'consent' && dl[0][1] === 'default', 'consent default e o primeiro push');
ok(dl[0][2].analytics_storage === 'denied', 'analytics_storage denied');
const configs = dl.filter((e) => e[0] === 'config').map((e) => e[1]);
ok(configs.includes('G-VK4QHHHS5X'), 'configura a propriedade herdada');
ok(configs.includes('G-5VTS0MZK79'), 'configura a propriedade nova');
ok(dl.find((e) => e[0] === 'config')[2].page_type === 'home', 'page_type = home');
ok(dl.find((e) => e[0] === 'config')[2].idioma === 'pt', 'idioma = pt');

// 2. Clique de WhatsApp em pagina de contato
dl = run('/mirow-site/pt/contato/', { clickHref: 'https://wa.me/5511999999999' });
const ct = dl.find((e) => e[0] === 'event' && e[1] === 'contato_click');
show('clique whatsapp em /contato/', dl.filter((e) => e[0] === 'event'));
ok(!!ct && ct[2].canal === 'whatsapp', 'contato_click com canal whatsapp');
ok(!!ct && ct[2].page_type === 'contato', 'page_type = contato');

// 3. Submit em carreiras marca persona candidato
dl = run('/mirow-site/en/careers/', { submit: true });
const fs_ = dl.find((e) => e[0] === 'event' && e[1] === 'form_submit');
show('submit em /careers/', dl.filter((e) => e[0] === 'event'));
ok(!!fs_ && fs_[2].persona === 'candidato', 'form_submit persona candidato');
ok(!!fs_ && fs_[2].idioma === 'en', 'idioma = en');

// 4. Link do Forms e PDF
dl = run('/mirow-site/pt/', { clickHref: 'https://forms.office.com/r/abc123' });
ok(!!dl.find((e) => e[1] === 'saida_forms'), 'saida_forms disparado');
dl = run('/mirow-site/pt/', { clickHref: '/mirow-site/wp-content/uploads/estudo.pdf' });
ok(!!dl.find((e) => e[1] === 'download_pdf'), 'download_pdf disparado');

// 5. Scroll de leitura so em artigo (3200 de alcance -> 1600 = 50%)
dl = run('/mirow-site/pt/preco-que-vale-ouro/', { scrollTo: 1700 });
const rd = dl.find((e) => e[1] === 'leitura_artigo');
show('scroll 53% em artigo', dl.filter((e) => e[0] === 'event'));
ok(!!rd && rd[2].profundidade === 50, 'leitura_artigo 50 em pagina de insight');
dl = run('/mirow-site/pt/contato/', { scrollTo: 1700 });
ok(!dl.find((e) => e[1] === 'leitura_artigo'), 'leitura_artigo NAO dispara fora de artigo');

// 6. Dominio proprio (base vazia) continua classificando
dl = run('/pt/contato/', { clickHref: 'mailto:contato@mirow.com.br' });
const em = dl.find((e) => e[1] === 'contato_click');
ok(!!em && em[2].canal === 'email', 'mailto vira canal email');

console.log(`\n${falhas === 0 ? 'TODOS OS CHECKS PASSARAM' : falhas + ' FALHA(S)'}`);
process.exit(falhas ? 1 : 0);
