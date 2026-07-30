import type { Lang } from '../i18n';

// Setores prioritarios Mirow (nomes factuais). A prosa/tese de cada setor
// entra depois via curadoria; aqui so a estrutura + agregacao de insights.
export const sectors: { slug: string; name: Record<Lang, string> }[] = [
  { slug: 'energy', name: { en: 'Energy', pt: 'Energia' } },
  { slug: 'automotive', name: { en: 'Automotive', pt: 'Automotivo' } },
  { slug: 'pulp-paper', name: { en: 'Pulp & Paper', pt: 'Papel & Celulose' } },
];
