/* onda67 / issue #104 — busca estatica no cliente.
 *
 * O campo de busca do tema postava `?s=` para `action="/"`. Num WordPress o
 * servidor responde; no espelho estatico do GitHub Pages nao ha quem responda, e
 * o visitante caia na raiz. Este arquivo faz a busca acontecer no navegador:
 * le `public/busca-indice.json` (gerado por tools/gen_busca.py do sitemap.xml) e
 * pontua os resultados.
 *
 * Sem dependencia: nenhum npm, nenhum servico externo, nenhuma chave.
 *
 * Decisoes que valem registro:
 *  - O indice so e baixado quando HA termo na URL. Quem abre /pt/insights/ sem
 *    buscar nada nao paga 126 KB.
 *  - Filtra por IDIOMA da pagina: buscar "pricing" em /pt/ nao devolve a pagina
 *    alema. Cada item do indice carrega o `lang` do proprio <html>.
 *  - Normaliza acento nos DOIS lados (termo e conteudo), senao "estrategia" nao
 *    acha "estrategia" com acento -- que e como as paginas estao escritas.
 *  - Pontuacao simples e explicavel: titulo vale 10, texto vale 1, e casar a
 *    frase inteira vale um bonus. Nao ha ranking oculto para depurar depois.
 */
(function () {
  'use strict';

  var CAMINHO = '/busca-indice.json';

  var T = {
    pt: {
      para: 'para', nada: 'Nada encontrado para',
      dica: 'Tente um termo mais curto, ou veja os Insights e a Imprensa.',
      um: 'resultado', varios: 'resultados', carregando: 'Buscando…',
      erro: 'Nao foi possivel carregar a busca agora.'
    },
    en: {
      para: 'for', nada: 'Nothing found for',
      dica: 'Try a shorter term, or browse Insights and Press.',
      um: 'result', varios: 'results', carregando: 'Searching…',
      erro: 'Could not load search right now.'
    },
    de: {
      para: 'fuer', nada: 'Nichts gefunden fuer',
      dica: 'Versuchen Sie einen kuerzeren Begriff, oder sehen Sie Insights und Presse.',
      um: 'Ergebnis', varios: 'Ergebnisse', carregando: 'Suche laeuft…',
      erro: 'Suche konnte nicht geladen werden.'
    }
  };

  function idioma() {
    var l = (document.documentElement.getAttribute('lang') || 'pt')
      .slice(0, 2).toLowerCase();
    return T[l] ? l : 'pt';
  }

  /* Acento fora dos dois lados. Sem isto, "estrategia" digitado sem acento nao
   * acha "estrategia" escrito com acento -- e o site esta todo com acento. */
  function normal(s) {
    return (s || '').toString().toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, '');
  }

  function termoDaUrl() {
    var m = /[?&]s=([^&]*)/.exec(window.location.search);
    if (!m) return '';
    try { return decodeURIComponent(m[1].replace(/\+/g, ' ')).trim(); }
    catch (e) { return m[1].replace(/\+/g, ' ').trim(); }
  }

  function pontuar(item, palavras, frase) {
    var t = normal(item.t), x = normal(item.x), p = 0, achou = 0;
    for (var i = 0; i < palavras.length; i++) {
      var w = palavras[i];
      if (!w) continue;
      var nt = t.split(w).length - 1;
      var nx = x.split(w).length - 1;
      if (nt || nx) achou++;
      p += nt * 10 + Math.min(nx, 6);
    }
    /* toda palavra tem de aparecer: senao buscar "pricing b2b" devolveria
     * qualquer pagina que mencione so "b2b" */
    if (achou < palavras.filter(Boolean).length) return 0;
    if (frase && (t.indexOf(frase) >= 0 || x.indexOf(frase) >= 0)) p += 25;
    return p;
  }

  function escapar(s) {
    return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  /* Trecho em volta da primeira ocorrencia, com o termo destacado. O indice
   * guarda o texto sem acento? Nao -- guarda COM acento, e a busca compara na
   * versao normalizada; por isso o corte usa o indice achado no normalizado e
   * fatia o ORIGINAL na mesma posicao (mesmo comprimento, caractere a caractere). */
  function trecho(texto, palavras) {
    var n = normal(texto), pos = -1;
    for (var i = 0; i < palavras.length && pos < 0; i++) {
      if (palavras[i]) pos = n.indexOf(palavras[i]);
    }
    if (pos < 0) pos = 0;
    var ini = Math.max(0, pos - 70);
    var bruto = texto.slice(ini, ini + 220);
    if (ini > 0) bruto = '…' + bruto;
    if (ini + 220 < texto.length) bruto += '…';
    var saida = escapar(bruto);
    for (var j = 0; j < palavras.length; j++) {
      var w = palavras[j];
      if (!w || w.length < 2) continue;
      /* destaca sem acento no padrao: constroi classe de caractere tolerante */
      var alvo = new RegExp('(' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
      saida = saida.replace(alvo, '<mark>$1</mark>');
      var comAcento = new RegExp('(' + w.split('').map(function (c) {
        var mapa = { a: '[aàáâãä]', e: '[eèéêë]',
                     i: '[iìíîï]', o: '[oòóôõö]',
                     u: '[uùúûü]', c: '[cç]' };
        return mapa[c] || c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      }).join('') + ')', 'gi');
      saida = saida.replace(comAcento, function (m0) {
        return m0.indexOf('<mark>') >= 0 ? m0 : '<mark>' + m0 + '</mark>';
      });
    }
    return saida;
  }

  function render(caixa, termo, achados, tt) {
    if (!achados.length) {
      caixa.innerHTML = '<p class="onda67-busca__vazio"><strong>' + tt.nada +
        ' “' + escapar(termo) + '”.</strong> ' + tt.dica + '</p>';
      return;
    }
    var palavras = normal(termo).split(/\s+/).filter(Boolean);
    var html = '<p class="onda67-busca__contagem">' + achados.length + ' ' +
      (achados.length === 1 ? tt.um : tt.varios) + ' ' +
      tt.para + ' “' + escapar(termo) + '”</p><ul class="onda67-busca__lista">';
    for (var i = 0; i < achados.length; i++) {
      var it = achados[i].item;
      html += '<li class="onda67-busca__item"><a class="onda67-busca__link" href="' +
        escapar(it.u) + '"><span class="onda67-busca__titulo">' +
        escapar(it.t || it.u) + '</span><span class="onda67-busca__trecho">' +
        trecho(it.x, palavras) + '</span></a></li>';
    }
    caixa.innerHTML = html + '</ul>';
  }

  function iniciar() {
    var form = document.querySelector('form.search-form');
    var caixa = document.getElementById('onda67-busca-resultados');
    if (!form || !caixa) return;

    var lang = idioma(), tt = T[lang];
    var termo = termoDaUrl();

    var campo = form.querySelector('input[name="s"]');
    if (campo && termo) campo.value = termo;
    if (!termo) return;                     /* sem termo, nao baixa o indice */

    caixa.innerHTML = '<p class="onda67-busca__contagem">' + tt.carregando + '</p>';

    var req = new XMLHttpRequest();
    req.open('GET', CAMINHO + '?v=' + (window.ONDA67_V || '1'), true);
    req.onreadystatechange = function () {
      if (req.readyState !== 4) return;
      if (req.status !== 200) {
        caixa.innerHTML = '<p class="onda67-busca__vazio">' + tt.erro + '</p>';
        return;
      }
      var dados;
      try { dados = JSON.parse(req.responseText); }
      catch (e) {
        caixa.innerHTML = '<p class="onda67-busca__vazio">' + tt.erro + '</p>';
        return;
      }
      var palavras = normal(termo).split(/\s+/).filter(Boolean);
      var frase = palavras.length > 1 ? normal(termo) : '';
      var achados = [];
      for (var i = 0; i < dados.itens.length; i++) {
        var it = dados.itens[i];
        if (it.l !== lang) continue;        /* busca por idioma */
        var p = pontuar(it, palavras, frase);
        if (p > 0) achados.push({ item: it, p: p });
      }
      achados.sort(function (a, b) { return b.p - a.p; });
      render(caixa, termo, achados, tt);
    };
    req.send();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
})();
