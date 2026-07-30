// Canais oficiais de contato do site (MMK-CONV006-C19/C20/C21 — conversa Andreas/Mario 29/07/2026).
// Fonte: 02_Dados/Dissecados/MMK-CONV006-2026-07/knowledge_chunks.json
//
// REGRA: nao inventar dado de contato. Todo campo aqui precisa vir de decisao registrada.
// - whatsapp: numero do Andreas, confirmado em C20/C21.
// - linkedin / instagram: confirmados em C21.
// - email: PENDENTE C21 — o proprio Andreas marcou "verificar email de contato para
//   projetos" na conversa. Enquanto for `null`, o site NAO deve exibir link de e-mail
//   (evita mailto quebrado ou endereco inventado). Quando o Andreas decidir, preencher
//   aqui e o rail/pagina de contato passam a mostrar o icone automaticamente.
import type { Lang } from '../i18n';

export const CONTACTS = {
  whatsapp: {
    number: '5521999947429',
    display: '+55 21 99994-7429',
    urlFor: (lang: Lang) =>
      `https://wa.me/5521999947429?text=${encodeURIComponent(
        lang === 'pt'
          ? 'Olá! Vim pelo site da Mirow & Co. e gostaria de conversar.'
          : 'Hello, I found Mirow & Co. through the website and would like to talk.'
      )}`,
  },
  linkedin: 'https://www.linkedin.com/company/mirow-co-/',
  instagram: 'https://www.instagram.com/mirowandco',
  // PENDENTE C21 — nao preencher sem decisao explicita do Andreas.
  email: null as string | null,
};
