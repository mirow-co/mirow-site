// Industrias em que a Mirow atua.
//
// Fonte dos nomes EN/PT: pagina "Our work" / "Nosso trabalho" do site atual
// (public/en/about-us/our-work/index.html e public/pt/sobre-nos/nosso-trabalho/index.html,
// bloco "Industries — Solutions for a variety of industries"). Os 19 nomes foram
// preservados literalmente para nao alterar posicionamento sem decisao de socio.
// DE traduzido (a pagina DE equivalente nao existe no dump do WordPress).
//
// C15 (MMK-CONV006, conversa Andreas 29/07/2026): as industrias saem de "Our work"
// e passam a ser apresentadas como planetas em orbita, com drill-down para os
// clientes daquela industria. `ring` define a orbita:
//   1 = territorios fortes da Mirow (Papel & Celulose, Energia, Automotivo)
//   2 = demais industrias
// `clientSectors` casa com o campo `sector.en` de src/data/clients.json.

export type IndustryLang = 'en' | 'pt' | 'de';

export interface Industry {
  slug: string;
  ring: 1 | 2;
  name: Record<IndustryLang, string>;
  /** Valores de sector.en em clients.json que pertencem a esta industria. */
  clientSectors: string[];
  /** Slug em src/data/sectors.ts, quando ja existe pagina de setor. */
  sectorPage?: string;
}

export const industries: Industry[] = [
  // --- Orbita 1: territorios fortes ---
  {
    slug: 'forestry-pulp-paper',
    ring: 1,
    name: {
      en: 'Forestry, Pulp and Paper',
      pt: 'Florestal, papel e celulose',
      de: 'Forst, Zellstoff und Papier',
    },
    clientSectors: ['Pulp & Paper', 'Wood Products & Coverings'],
    sectorPage: 'pulp-paper',
  },
  {
    slug: 'electric-energy',
    ring: 1,
    name: { en: 'Electric Energy', pt: 'Energia elétrica', de: 'Elektrische Energie' },
    clientSectors: ['Energy', 'Energy (Transmission)'],
    sectorPage: 'energy',
  },
  {
    slug: 'automotive',
    ring: 1,
    name: { en: 'Automotive', pt: 'Automotivo', de: 'Automobil' },
    clientSectors: ['Automotive'],
    sectorPage: 'automotive',
  },

  // --- Orbita 2 ---
  {
    slug: 'oil-and-gas',
    ring: 2,
    name: { en: 'Oil and Gas', pt: 'Óleo e gás', de: 'Öl und Gas' },
    clientSectors: ['Fuel Distribution'],
  },
  {
    slug: 'mining-and-steel',
    ring: 2,
    name: { en: 'Mining and Steel', pt: 'Mineração e siderurgia', de: 'Bergbau und Stahl' },
    clientSectors: [],
  },
  {
    slug: 'chemicals',
    ring: 2,
    name: { en: 'Chemicals', pt: 'Químicos', de: 'Chemie' },
    clientSectors: ['Fertilizers / Chemicals'],
  },
  {
    slug: 'utilities',
    ring: 2,
    name: { en: 'Utilities', pt: 'Utilidades', de: 'Versorgungswirtschaft' },
    clientSectors: [],
  },
  {
    slug: 'agribusiness',
    ring: 2,
    name: { en: 'Agribusiness', pt: 'Agronegócio', de: 'Agrarwirtschaft' },
    clientSectors: [],
  },
  {
    slug: 'machinery-and-equipment',
    ring: 2,
    name: {
      en: 'Machinery and Equipment',
      pt: 'Máquinas e equipamentos',
      de: 'Maschinen und Anlagen',
    },
    clientSectors: ['Heavy Equipment'],
  },
  {
    slug: 'transportation-and-logistics',
    ring: 2,
    name: {
      en: 'Transportation and Logistics',
      pt: 'Transporte e logística',
      de: 'Transport und Logistik',
    },
    clientSectors: ['Ports & Logistics', 'Ports'],
  },
  {
    slug: 'infrastructure-and-cement',
    ring: 2,
    name: {
      en: 'Infrastructure and Cement',
      pt: 'Infraestrutura e cimento',
      de: 'Infrastruktur und Zement',
    },
    clientSectors: [],
  },

  // --- Orbita 2 (continuacao) ---
  {
    slug: 'financial-services',
    ring: 2,
    name: { en: 'Financial Services', pt: 'Serviços financeiros', de: 'Finanzdienstleistungen' },
    clientSectors: ['Financial Services', 'Insurance'],
  },
  {
    slug: 'private-equity',
    ring: 2,
    name: { en: 'Private Equity', pt: 'Private Equity', de: 'Private Equity' },
    clientSectors: [],
  },
  {
    slug: 'retail-and-consumer-goods',
    ring: 2,
    name: {
      en: 'Retail and Consumer Goods',
      pt: 'Varejo e bens de consumo',
      de: 'Handel und Konsumgüter',
    },
    clientSectors: [],
  },
  {
    slug: 'technology',
    ring: 2,
    name: { en: 'Technology', pt: 'Tecnologia', de: 'Technologie' },
    clientSectors: [],
  },
  {
    slug: 'telecom',
    ring: 2,
    name: { en: 'Telecom', pt: 'Telecom', de: 'Telekommunikation' },
    clientSectors: [],
  },
  {
    slug: 'healthcare',
    ring: 2,
    name: { en: 'Healthcare', pt: 'Saúde', de: 'Gesundheitswesen' },
    clientSectors: [],
  },
  {
    slug: 'education',
    ring: 2,
    name: { en: 'Education', pt: 'Educação', de: 'Bildung' },
    clientSectors: [],
  },
  {
    slug: 'sports-media-entertainment',
    ring: 2,
    name: {
      en: 'Sports, Media and Entertainment',
      pt: 'Esportes, mídia e entretenimento',
      de: 'Sport, Medien und Unterhaltung',
    },
    clientSectors: [],
  },
];
