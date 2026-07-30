import type { UiLang } from '../i18n';

// Os tres pontos cardinais da pagina inicial (MMK-CONV006 C12): a roda de 8
// pontos vira 3 — Estrategia (sempre primeiro), Pricing e Compras — e os cards
// ficam SEMPRE visiveis, sem depender de clique. Cada card carrega, acoplado
// abaixo dele, o testemunho de um cliente daquele tema (C13).
//
// Rastreabilidade (R1): os exemplos de atuacao e os testemunhos abaixo sao
// texto ja publico do site mirow.com.br (paginas de praticas e bloco
// "Depoimentos" da pagina inicial atual, versoes PT e EN). Os testemunhos ja
// nascem anonimizados na fonte — identificam projeto e industria, nunca a
// empresa. A versao DE e traducao nossa (o site DE atual nao tem o bloco).

type I18nText = Record<UiLang, string>;

export type Cardinal = {
  slug: string; // slug da pratica correspondente em src/content/practices
  href: string | null; // rota Astro; null quando a pratica ainda nao tem pagina
  title: I18nText;
  tagline: I18nText;
  examples: Record<UiLang, string[]>;
  testimonial: {
    quote: I18nText;
    project: I18nText;
    industry: I18nText;
  };
};

export const cardinals: Cardinal[] = [
  {
    slug: 'strategy',
    href: '/practices/strategy/',
    title: {
      en: 'Strategy',
      pt: 'Estratégia',
      de: 'Strategie',
    },
    tagline: {
      en: 'We support companies across industries on their most complex strategic challenges — from market analysis and strategy design through to the implementation of the initiatives that create value.',
      pt: 'Apoiamos empresas de diversas indústrias nos seus desafios estratégicos mais complexos — da análise de mercado e formulação da estratégia à implementação das iniciativas que geram valor.',
      de: 'Wir begleiten Unternehmen verschiedener Branchen bei ihren komplexesten strategischen Herausforderungen — von der Marktanalyse und Strategieentwicklung bis zur Umsetzung der wertschaffenden Initiativen.',
    },
    examples: {
      en: [
        'Growth strategy for a pulp and paper leader, with potential revenue upside of more than 60% identified',
        'New distributed generation business for an energy client, with potential of R$ 1 B in additional company valuation',
      ],
      pt: [
        'Estratégia de crescimento para uma líder de papel e celulose, com potencial de aumento de receita acima de 60% identificado',
        'Novo negócio de geração distribuída para um cliente de energia, com potencial de R$ 1 B de aumento no valuation da empresa',
      ],
      de: [
        'Wachstumsstrategie für einen führenden Zellstoff- und Papierhersteller, mit identifiziertem Umsatzpotenzial von über 60%',
        'Neues Geschäftsfeld für dezentrale Energieerzeugung bei einem Energiekunden, mit einem Potenzial von 1 Mrd. R$ zusätzlicher Unternehmensbewertung',
      ],
    },
    testimonial: {
      quote: {
        en: 'Mirow delivers a type of project that doesn’t stay in the drawer. The cost reduction solutions identified in the work are highly likely to be implemented, as they are well aligned with our implementation team in terms of both the levers and the execution approach.',
        pt: 'A Mirow entrega um tipo de projeto que não fica na gaveta. As soluções de redução de custos que surgiram no trabalho devem acontecer, pois as alavancas e o “como” foram muito bem alinhados com a nossa equipe de implementação.',
        de: 'Mirow liefert Projekte, die nicht in der Schublade landen. Die im Projekt entwickelten Lösungen zur Kostensenkung werden umgesetzt, weil sowohl die Hebel als auch das „Wie“ sehr gut mit unserem Umsetzungsteam abgestimmt waren.',
      },
      project: { en: 'Strategy project', pt: 'Projeto de estratégia', de: 'Strategieprojekt' },
      industry: { en: 'Education sector', pt: 'Setor de educação', de: 'Bildungssektor' },
    },
  },
  {
    slug: 'pricing',
    href: null, // PENDENTE: pagina de pratica de Pricing ainda nao existe em src/content/practices
    title: {
      en: 'Pricing',
      pt: 'Pricing',
      de: 'Pricing',
    },
    tagline: {
      en: 'We work across the commercial chain — pricing, go-to-market, customer experience and sales force effectiveness — so that price stops being a discount negotiation and becomes a management decision.',
      pt: 'Atuamos em toda a cadeia comercial — precificação, go-to-market, experiência do cliente e efetividade da força de vendas — para que o preço deixe de ser negociação de desconto e volte a ser decisão de gestão.',
      de: 'Wir arbeiten entlang der gesamten Vertriebskette — Preisgestaltung, Go-to-Market, Kundenerlebnis und Vertriebseffektivität — damit Preis keine Rabattverhandlung mehr ist, sondern eine Managemententscheidung.',
    },
    examples: {
      en: [
        'Pricing redesign for an international automotive company, with R$ 50 MM per year of impact on EBIT',
        'Full redesign of the customer journey and experience for an LPG distributor',
      ],
      pt: [
        'Reformulação do pricing de uma empresa internacional do setor automotivo, com R$ 50 MM por ano de impacto no EBIT',
        'Redesenho completo da jornada e da experiência do cliente para um distribuidor de GLP',
      ],
      de: [
        'Neugestaltung des Pricings eines internationalen Automobilunternehmens, mit 50 Mio. R$ EBIT-Effekt pro Jahr',
        'Vollständige Neugestaltung der Customer Journey und des Kundenerlebnisses für einen LPG-Distributor',
      ],
    },
    testimonial: {
      quote: {
        en: 'One of the great differentials of Mirow’s work was the seniority of the team that accompanied the day-to-day work and the deliverables. Mirow brings extensive market knowledge and experience to projects, with professionals who are consistently committed to delivery.',
        pt: 'Um dos grandes diferenciais do trabalho da Mirow foi a senioridade da equipe que acompanhou o dia a dia e as entregas. A Mirow agrega muito conhecimento de mercado e transmite muita experiência nos projetos, com profissionais sempre muito comprometidos com a entrega.',
        de: 'Einer der großen Unterschiede in der Arbeit von Mirow war die Seniorität des Teams, das das Tagesgeschäft und die Ergebnisse begleitet hat. Mirow bringt viel Marktkenntnis und Erfahrung in die Projekte ein, mit Fachleuten, die konsequent auf die Umsetzung verpflichtet sind.',
      },
      project: {
        en: 'Marketing & sales project',
        pt: 'Projeto de marketing e vendas',
        de: 'Marketing- und Vertriebsprojekt',
      },
      industry: {
        en: 'Natural gas industry',
        pt: 'Indústria de gás natural',
        de: 'Erdgasindustrie',
      },
    },
  },
  {
    slug: 'sourcing',
    href: null, // PENDENTE: pagina de pratica de Compras ainda nao existe em src/content/practices
    title: {
      en: 'Sourcing',
      pt: 'Compras',
      de: 'Einkauf',
    },
    tagline: {
      en: 'We turn sourcing into a lever of strategy: category strategy, clean sheet, renegotiation and supply chain redesign, with the savings quantified before anyone sits at the negotiation table.',
      pt: 'Transformamos compras em alavanca de estratégia: estratégia por categoria, clean sheet, renegociação e redesenho da cadeia de suprimentos, com o ganho quantificado antes de alguém sentar à mesa de negociação.',
      de: 'Wir machen den Einkauf zu einem Hebel der Strategie: Kategoriestrategie, Clean Sheet, Neuverhandlung und Neugestaltung der Lieferkette — mit quantifizierten Einsparungen, bevor jemand am Verhandlungstisch sitzt.',
    },
    examples: {
      en: [
        'Definition of the supply strategy for one of the largest oil and gas companies in Brazil',
        'Supply chain transformation of a coatings manufacturer through S&OP and strategic sourcing, with expected impact of R$ 15 MM per year',
      ],
      pt: [
        'Definição da estratégia de suprimentos de uma das principais empresas de óleo e gás do Brasil',
        'Transformação do supply chain de um fabricante de revestimentos via S&OP e strategic sourcing, com impacto previsto de R$ 15 MM por ano',
      ],
      de: [
        'Definition der Beschaffungsstrategie für eines der größten Öl- und Gasunternehmen Brasiliens',
        'Transformation der Lieferkette eines Beschichtungsherstellers über S&OP und Strategic Sourcing, mit einem erwarteten Effekt von 15 Mio. R$ pro Jahr',
      ],
    },
    testimonial: {
      quote: {
        en: 'Mirow demonstrates excellent adaptability in designing customized solutions for the client’s reality and in line with business needs. The analysis was of high quality and enabled the quantification of financial opportunities.',
        pt: 'A Mirow demonstra excelente capacidade de adaptação para desenhar soluções customizadas para a realidade do cliente e alinhadas às necessidades do negócio. A qualidade das análises foi muito boa e permitiu quantificar financeiramente as oportunidades.',
        de: 'Mirow zeigt eine ausgezeichnete Fähigkeit, Lösungen passgenau auf die Realität des Kunden und die Anforderungen des Geschäfts zuzuschneiden. Die Qualität der Analysen war sehr gut und erlaubte es, die Chancen finanziell zu quantifizieren.',
      },
      project: { en: 'Operations project', pt: 'Projeto de operações', de: 'Operations-Projekt' },
      industry: {
        en: 'Wood products industry',
        pt: 'Indústria de produtos de madeira',
        de: 'Holzwerkstoffindustrie',
      },
    },
  },
];
