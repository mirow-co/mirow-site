export const LANGS = ['en', 'pt'] as const;
export type Lang = (typeof LANGS)[number];

export const t: Record<Lang, Record<string, string>> = {
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
    'home.practices': 'Our areas of expertise',
    'home.figures': 'Our figures',
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
    'home.practices': 'Nossas áreas de atuação',
    'home.figures': 'Mirow em números',
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
};

export function other(lang: Lang): Lang {
  return lang === 'en' ? 'pt' : 'en';
}
