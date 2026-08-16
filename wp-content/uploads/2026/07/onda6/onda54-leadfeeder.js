/* Leadfeeder Lite (Dealfront) — identificacao de visitante em nivel EMPRESA
 * (mirow-marketing#222, decisao do Mario em 2026-08-14).
 *
 * Escolhido depois de o Data Reveal ser reprovado no probe do mesmo dia: aquele
 * enviava o conteudo INTEIRO do formulario de contato — nome, e-mail, telefone e
 * mensagem — sem o visitante clicar em enviar. Evidencia em
 * 05_Analises/2026-08-14_data-reveal-o-que-o-tracker-envia.md (repo privado).
 *
 * O Leadfeeder e outra coisa por construcao: identifica a EMPRESA por IP reverso,
 * nunca a pessoa (a doc deles e explicita que so ha vinculo com individuo via
 * integracao de CRM — que nao vamos ligar). Plano Lite: gratuito permanente,
 * 100 empresas/mes, 7 dias de historico.
 *
 * ISSO NAO NOS DISPENSA DE MEDIR. A licao de 14/08 e que declaracao de fornecedor
 * nao e evidencia: o probe (scratchpad/probe_reveal.py, reaproveitavel) roda contra
 * pt/contato/ ANTES de publicar, e so entao ATIVO vira true.
 *
 * Por que um asset nosso em vez do snippet solto nas paginas:
 *  - o injetor escreve UMA linha por pagina; trocar de fornecedor mexe em 1 arquivo;
 *  - o opt-out precisa rodar ANTES do tracker, e aqui ele roda;
 *  - ATIVO e um interruptor de 1 linha: se der problema no ar, desliga e publica
 *    sem ter de tocar em 112 paginas;
 *  - o carimbo ?v= do 27_cache_busting.py so vale para asset nosso.
 */
(function () {
  'use strict';

  /* URL COMPLETA do script, copiada do painel: engrenagem > Company >
   * Website Tracker > Copy to Clipboard. O id da conta ja vem embutido nela —
   * por isso UMA constante so, e nao id + base separados: dois lugares
   * declarando o mesmo valor e a classe de bug "valores gemeos" da onda 31.
   * Nao adivinhar o formato: colar o que o painel der. */
  var SCRIPT_URL = 'https://sc.lfeeder.com/lftracker_v1_ywVkO4XlVW14Z6Bj.js';

  /* Vira true depois de o probe passar e o Mario dar o OK. */
  var ATIVO = true;

  var CHAVE_OPTOUT = 'mirow:leadfeeder:optout';

  /* Opt-out — a mitigacao que o site oferece sozinho.
   * 1. escolha explicita do visitante, gravada pela pagina de politica de privacidade;
   * 2. Global Privacy Control, sinal de opt-out ja reconhecido como manifestacao
   *    de vontade em varias jurisdicoes.
   * Deliberadamente NAO olhamos navigator.doNotTrack: abandonado pelo W3C e hoje
   * ligado de fabrica em navegadores inteiros — e configuracao, nao vontade. */
  function optOut() {
    if (navigator.globalPrivacyControl === true) return true;
    try {
      return window.localStorage.getItem(CHAVE_OPTOUT) === '1';
    } catch (e) {
      /* Safari privado lanca em localStorage. Sem leitura possivel, o default e
       * NAO rastrear: na duvida, a favor do titular. */
      return true;
    }
  }

  /* Exposto para a politica de privacidade ligar num botao. */
  window.mirowLeadfeederOptOut = function (ligar) {
    var sair = ligar !== false;
    try {
      if (sair) window.localStorage.setItem(CHAVE_OPTOUT, '1');
      else window.localStorage.removeItem(CHAVE_OPTOUT);
    } catch (e) { /* sem storage, nada a gravar */ }
    return sair;
  };

  window.mirowLeadfeederAtivo = false;

  if (!ATIVO) return;         /* desligado ate o probe passar */
  if (!SCRIPT_URL) return;    /* sem conta: no-op */
  if (optOut()) return;

  /* Fila `ldfdr` do snippet oficial: o tracker espera que ela exista antes de
   * carregar, para nao perder chamadas feitas enquanto o script esta a caminho.
   * Replicada tal como o painel entrega — nao simplificar. */
  window.ldfdr = window.ldfdr || function () {
    (window.ldfdr._q = window.ldfdr._q || []).push([].slice.call(arguments));
  };

  var s = document.createElement('script');
  s.src = SCRIPT_URL;
  s.async = true;
  document.head.appendChild(s);
  window.mirowLeadfeederAtivo = true;
})();
