export const LANGS = ['en', 'pt'] as const;
export type Lang = (typeof LANGS)[number];

// O alemao ja tem traducao pronta abaixo, mas a rota /de/ so entra no ar quando
// 'de' for adicionado a LANGS — o que depende da traducao das colecoes de
// conteudo (insights/practices). Ate la o dicionario DE fica versionado e pronto.
export type UiLang = Lang | 'de';

export const t: Record<UiLang, Record<string, string>> = {
  en: {
    'nav.practices': 'Practices',
    'nav.insights': 'Insights',
    'nav.leaders': 'Leaders',
    'nav.careers': 'Careers',
    'nav.contact': 'Contact Us',
    'nav.sectors': 'Sectors',
    'sectors.title': 'Perspectives by sector',
    'sectors.sub': 'Our insights organized by the industries we serve',
    'hero.kicker': 'Strategic management consulting',
    'hero.title': 'Embrace to Enhance',
    'hero.sub':
      'We are a strategic management consulting firm that uses innovative approaches and works in close collaboration with our clients to solve their key challenges and deliver sustainable results',
    'hero.lead':
      'We are a strategy consulting firm. We work side by side with top management on strategy, pricing and sourcing — and we stay until the decision turns into result',
    'hero.contact.label': 'Talk to us directly',
    'hero.contact.whatsapp': 'WhatsApp',
    'hero.contact.email': 'Email',
    'hero.contact.form': 'Contact form',
    'home.clients.label': 'Companies that rely on Mirow & Co.',
    'home.clients.note':
      'Some of the clients for whom we have delivered projects, listed with our partners’ authorisation',
    'home.cardinals': 'Strategy, pricing and sourcing',
    'home.cardinals.sub':
      'We are a strategy consulting firm — and pricing and sourcing are where strategy turns into money',
    'home.cardinals.more': 'Explore this practice',
    'testimonial.label': 'What our clients say',
    'home.practices': 'Our areas of expertise',
    'home.principle':
      'What matters most to a client is seeing who we work with, not the awards we hold',
    'home.recognitions': 'Recognitions',
    'rec.gptw.title': 'Great Place to Work — seven years in a row',
    'rec.gptw.desc':
      'Mirow & Co. has carried the Great Place to Work seal every year since 2018: a collaborative environment, built on respect and fairness, that our own team is proud to belong to',
    'rec.seven.title': 'Seven to Watch — Consulting Magazine',
    'rec.seven.desc':
      'In 2018 Consulting Magazine named Mirow & Co. one of the seven most promising consulting firms in the world, and the only one from Latin America on the list',
    'rec.growth.title': 'Among the fastest-growing consulting firms in the world',
    'rec.growth.desc':
      'In 2019 Consulting Magazine listed Mirow & Co. among the twenty fastest-growing consulting firms worldwide, after organic revenue growth of more than 200% over three years',
    'rec.source': 'Source: Recognitions page, Mirow & Co.',
    'home.leaders': 'Our leaders',
    'home.leaders.all': 'Meet the whole leadership team',
    'home.figures': 'Our figures',
    'fig.source': 'Source: Mirow & Co. project base',
    'fig.clients': 'clients served',
    'fig.reengage': 'client re-engagement rate',
    'fig.revenue': 'of projects for clients with annual turnover above R$ 1 billion',
    'fig.years': 'years in the market',
    'home.insights': 'Latest insights',
    'home.insights.all': 'See all insights',
    'cta.contact': 'How can we assist you?',
    'cta.careers': 'Transform your career',
    'insights.title': 'Insights',
    'insights.sub': 'Studies and perspectives from our practices',
    'insights.download': 'Read the full study',
    'leaders.title': 'Meet our leadership team',
    'leaders.sub':
      'Our leadership includes professionals with extensive experience, both in management consulting and in executive positions across various sectors',
    'contact.title': 'Contact us',
    'contact.sub': 'Get in touch with our team — your message goes directly to our partners',
    'form.name': 'Name',
    'form.email': 'Email',
    'form.phone': 'Telephone',
    'form.company': 'Company name',
    'form.message': 'Message',
    'form.send': 'Send message',
    'form.demo':
      'Prototype: in production this form sends an email directly to the partners (serverless + Microsoft 365).',
    'careers.title': 'Work at Mirow',
    'careers.sub':
      'We offer accelerated growth opportunities in a gentle and entrepreneurial work environment',
    'careers.apply': 'Apply now',
    'form.cv': 'Attach your CV (PDF)',
    'careers.demo':
      'Prototype: in production this application goes by email to our HR team, with the CV attached.',
    'footer.offices': 'Rio de Janeiro · São Paulo',
    'footer.rights': 'All rights reserved',
  },
  pt: {
    'nav.practices': 'Práticas',
    'nav.insights': 'Insights',
    'nav.leaders': 'Líderes',
    'nav.careers': 'Carreiras',
    'nav.contact': 'Contato',
    'nav.sectors': 'Setores',
    'sectors.title': 'Perspectivas por setor',
    'sectors.sub': 'Nossos insights organizados pelos setores em que atuamos',
    'hero.kicker': 'Consultoria estratégica',
    'hero.title': 'Envolver para desenvolver',
    'hero.sub':
      'Somos uma consultoria estratégica que usa abordagens inovadoras e que trabalha lado a lado com nossos clientes para solucionar seus principais desafios e entregar resultados duradouros',
    'hero.lead':
      'Somos uma consultoria de estratégia. Trabalhamos lado a lado com a alta gestão em estratégia, pricing e compras — e ficamos até a decisão virar resultado',
    'hero.contact.label': 'Fale direto com a gente',
    'hero.contact.whatsapp': 'WhatsApp',
    'hero.contact.email': 'E-mail',
    'hero.contact.form': 'Formulário de contato',
    'home.clients.label': 'Empresas que confiam na Mirow & Co.',
    'home.clients.note':
      'Alguns dos clientes para os quais já entregamos projetos, listados com autorização dos nossos sócios',
    'home.cardinals': 'Estratégia, pricing e compras',
    'home.cardinals.sub':
      'Somos uma consultoria de estratégia — e pricing e compras são onde a estratégia vira dinheiro',
    'home.cardinals.more': 'Conheça a prática',
    'testimonial.label': 'O que dizem nossos clientes',
    'home.practices': 'Nossas áreas de atuação',
    'home.principle':
      'Para o cliente, importa mais ver com quem trabalhamos do que ver os prêmios que temos',
    'home.recognitions': 'Reconhecimentos',
    'rec.gptw.title': 'Great Place to Work — sete anos consecutivos',
    'rec.gptw.desc':
      'A Mirow & Co. recebeu o selo Great Place to Work todos os anos desde 2018: um ambiente colaborativo, construído com respeito e imparcialidade, do qual a nossa equipe sente orgulho de pertencer',
    'rec.seven.title': 'Seven to Watch — Consulting Magazine',
    'rec.seven.desc':
      'Em 2018 a Consulting Magazine elegeu a Mirow & Co. como uma das sete consultorias mais promissoras do mundo, e a única da América Latina no ranking',
    'rec.growth.title': 'Entre as consultorias que mais cresceram no mundo',
    'rec.growth.desc':
      'Em 2019 a Consulting Magazine selecionou a Mirow & Co. entre as vinte consultorias de crescimento mais rápido do mundo, após crescimento orgânico de receita superior a 200% em três anos',
    'rec.source': 'Fonte: página de Reconhecimentos, Mirow & Co.',
    'home.leaders': 'Nossos líderes',
    'home.leaders.all': 'Conheça toda a liderança',
    'home.figures': 'Mirow em números',
    'fig.source': 'Fonte: base de projetos da Mirow & Co.',
    'fig.clients': 'clientes atendidos',
    'fig.reengage': 'dos clientes nos contratam novamente',
    'fig.revenue': 'dos projetos em empresas com faturamento acima de R$ 1 bilhão',
    'fig.years': 'anos de mercado',
    'home.insights': 'Últimos insights',
    'home.insights.all': 'Ver todos os insights',
    'cta.contact': 'Como podemos ajudar?',
    'cta.careers': 'Transforme a sua carreira',
    'insights.title': 'Insights',
    'insights.sub': 'Estudos e perspectivas das nossas práticas',
    'insights.download': 'Leia o estudo completo',
    'leaders.title': 'Conheça a nossa liderança',
    'leaders.sub':
      'Nossa liderança reúne profissionais com longa experiência em consultoria estratégica e em posições executivas de diversos setores',
    'contact.title': 'Fale conosco',
    'contact.sub': 'Entre em contato com o nosso time — sua mensagem vai direto aos sócios',
    'form.name': 'Nome',
    'form.email': 'E-mail',
    'form.phone': 'Telefone',
    'form.company': 'Empresa',
    'form.message': 'Mensagem',
    'form.send': 'Enviar mensagem',
    'form.demo':
      'Protótipo: em produção este formulário dispara e-mail direto para os sócios (serverless + Microsoft 365).',
    'careers.title': 'Trabalhe na Mirow',
    'careers.sub':
      'Oferecemos oportunidades de crescimento acelerado em um ambiente de trabalho leve e empreendedor',
    'careers.apply': 'Candidate-se',
    'form.cv': 'Anexe seu CV (PDF)',
    'careers.demo':
      'Protótipo: em produção esta candidatura vai por e-mail para o RH, com o CV anexado.',
    'footer.offices': 'Rio de Janeiro · São Paulo',
    'footer.rights': 'Todos os direitos reservados',
  },
  de: {
    'nav.practices': 'Kompetenzen',
    'nav.insights': 'Insights',
    'nav.leaders': 'Führungskräfte',
    'nav.careers': 'Karriere',
    'nav.contact': 'Kontakt',
    'nav.sectors': 'Branchen',
    'sectors.title': 'Perspektiven nach Branche',
    'sectors.sub': 'Unsere Insights, geordnet nach den Branchen, in denen wir tätig sind',
    'hero.kicker': 'Strategieberatung',
    'hero.title': 'Einbinden, um zu entwickeln',
    'hero.sub':
      'Wir sind eine Strategieberatung, die mit innovativen Ansätzen und in enger Zusammenarbeit mit unseren Kunden deren wichtigste Herausforderungen löst und nachhaltige Ergebnisse liefert',
    'hero.lead':
      'Wir sind eine Strategieberatung. Wir arbeiten Seite an Seite mit dem Top-Management an Strategie, Pricing und Einkauf — und bleiben, bis die Entscheidung zum Ergebnis wird',
    'hero.contact.label': 'Sprechen Sie uns direkt an',
    'hero.contact.whatsapp': 'WhatsApp',
    'hero.contact.email': 'E-Mail',
    'hero.contact.form': 'Kontaktformular',
    'home.clients.label': 'Unternehmen, die auf Mirow & Co. vertrauen',
    'home.clients.note':
      'Einige der Kunden, für die wir Projekte umgesetzt haben — aufgeführt mit Zustimmung unserer Partner',
    'home.cardinals': 'Strategie, Pricing und Einkauf',
    'home.cardinals.sub':
      'Wir sind eine Strategieberatung — und Pricing und Einkauf sind die Stellen, an denen Strategie zu Geld wird',
    'home.cardinals.more': 'Kompetenzfeld entdecken',
    'testimonial.label': 'Was unsere Kunden sagen',
    'home.practices': 'Unsere Kompetenzfelder',
    'home.principle':
      'Für den Kunden zählt mehr, mit wem wir arbeiten, als die Auszeichnungen, die wir haben',
    'home.recognitions': 'Auszeichnungen',
    'rec.gptw.title': 'Great Place to Work — sieben Jahre in Folge',
    'rec.gptw.desc':
      'Mirow & Co. trägt das Siegel Great Place to Work seit 2018 in jedem Jahr: ein kollaboratives Umfeld, geprägt von Respekt und Fairness, auf das unser Team stolz ist',
    'rec.seven.title': 'Seven to Watch — Consulting Magazine',
    'rec.seven.desc':
      'Das Consulting Magazine wählte Mirow & Co. 2018 zu einer der sieben vielversprechendsten Beratungen der Welt — als einzige aus Lateinamerika',
    'rec.growth.title': 'Unter den am stärksten wachsenden Beratungen der Welt',
    'rec.growth.desc':
      'Das Consulting Magazine zählte Mirow & Co. 2019 zu den zwanzig am schnellsten wachsenden Beratungen weltweit, nach einem organischen Umsatzwachstum von mehr als 200% in drei Jahren',
    'rec.source': 'Quelle: Seite Auszeichnungen, Mirow & Co.',
    'home.leaders': 'Unsere Führungskräfte',
    'home.leaders.all': 'Das gesamte Führungsteam kennenlernen',
    'home.figures': 'Mirow in Zahlen',
    'fig.source': 'Quelle: Projektbasis von Mirow & Co.',
    'fig.clients': 'betreute Kunden',
    'fig.reengage': 'unserer Kunden beauftragen uns erneut',
    'fig.revenue':
      'der Projekte für Kunden mit einem Jahresumsatz von über 1 Mrd. R$',
    'fig.years': 'Jahre am Markt',
    'home.insights': 'Neueste Insights',
    'home.insights.all': 'Alle Insights ansehen',
    'cta.contact': 'Wie können wir Ihnen helfen?',
    'cta.careers': 'Verändern Sie Ihre Karriere',
    'insights.title': 'Insights',
    'insights.sub': 'Studien und Perspektiven aus unseren Kompetenzfeldern',
    'insights.download': 'Die vollständige Studie lesen',
    'leaders.title': 'Unser Führungsteam',
    'leaders.sub':
      'Unser Führungsteam vereint Fachleute mit langjähriger Erfahrung in der Strategieberatung und in Führungspositionen verschiedener Branchen',
    'contact.title': 'Kontaktieren Sie uns',
    'contact.sub':
      'Nehmen Sie Kontakt mit unserem Team auf — Ihre Nachricht geht direkt an unsere Partner',
    'form.name': 'Name',
    'form.email': 'E-Mail',
    'form.phone': 'Telefon',
    'form.company': 'Unternehmen',
    'form.message': 'Nachricht',
    'form.send': 'Nachricht senden',
    'form.demo':
      'Prototyp: In der Produktion sendet dieses Formular eine E-Mail direkt an die Partner (serverless + Microsoft 365).',
    'careers.title': 'Arbeiten bei Mirow',
    'careers.sub':
      'Wir bieten Möglichkeiten für schnelles Wachstum in einem angenehmen und unternehmerischen Arbeitsumfeld',
    'careers.apply': 'Jetzt bewerben',
    'form.cv': 'Laden Sie Ihren Lebenslauf hoch (PDF)',
    'careers.demo':
      'Prototyp: In der Produktion wird diese Bewerbung mit dem angehängten Lebenslauf per E-Mail an unser HR-Team gesendet.',
    'footer.offices': 'Rio de Janeiro · São Paulo',
    'footer.rights': 'Alle Rechte vorbehalten',
  },
};

export function other(lang: Lang): Lang {
  return lang === 'en' ? 'pt' : 'en';
}
