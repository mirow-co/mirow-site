# Medição de visibilidade nas IAs (GEO) — registro

> Protocolo do Felipe (e-mail de 24/08/2026): *"repetimos as mesmas perguntas, nos mesmos
> assistentes, deslogado, e comparamos palavra a palavra"*. Data marcada: **10/09/2026**,
> trinta dias depois de o site novo subir.

## Linha de base (18/08/2026, medição do Felipe)

- **Descoberta: 0/15** — em quinze perguntas do tipo "que consultoria eu contrato para X",
  a Mirow não apareceu nenhuma vez.
- **8 de 9 respostas sem citar o site próprio.**
- Confusão recorrente com a cidade alemã de Mirow, com o sobrenome e com o software Miro.

**As 8 perguntas do protocolo não estão neste repo** — vieram no handoff de 18/08, que é
material do Felipe. Sem elas, a comparação de 10/09 não é a mesma medição; **pedir a lista
antes.**

## Pré-medição de 31/08/2026 (D+0 do Wikidata) — instrumento diferente, e isso importa

Feita com **busca web ao vivo** (resultado sintetizado a partir da web indexada), **não** com
os mesmos assistentes do protocolo. Serve para uma coisa só: registrar o estado no dia em que
a ficha do Wikidata nasceu, para saber depois o que mudou por causa dela e o que já estava
mudado antes.

| Pergunta | Resultado |
|---|---|
| "Mirow & Co. consultoria estratégica quem é" (pt) | **Correto.** Consultoria estratégica **brasileira**, fundada em **12/04/2012**, sede no Rio, CNPJ certo. Cita o nosso site, o Sistema B e agregadores de CNPJ |
| "where is it headquartered, which country" (en) | **Correto.** *"Brazilian strategy consulting firm headquartered in Rio de Janeiro… Brazil"*, com Consulting Magazine e consultancy.lat entre as fontes |
| "Conte a história da Mirow & Co." | **Correto e detalhado.** Portas Consulting Brasil em 2012, os fundadores, a virada para papel e celulose, São Paulo, GPTW e Seven to Watch. Cita `mirow.com.br/en/about-us/our-history/` |
| "melhores consultorias estratégicas brasileiras" (**descoberta**) | **A Mirow não aparece.** A resposta lista Falconi, Dom Strategy Partners, EloGroup, Visagio e as internacionais |

**Leitura honesta dos quatro:** nenhuma confusão com a Alemanha ou com o Miro nas três de
identidade — mas isso mede o efeito das ondas de **site** (schema, sede, bios, `alumniOf`),
não do Wikidata, que tem horas de vida. E a quarta confirma exatamente o que o Felipe
escreveu no pacote: **o Wikidata conserta identidade, não descoberta.** A Mirow continua
fora da lista quando ninguém pergunta por ela pelo nome.

## Para a medição de 10/09 valer

1. **Pedir ao Felipe as 8 perguntas** e o registro literal das respostas de 18/08.
2. Rodar **nos mesmos assistentes**, deslogado, e comparar palavra a palavra — não com busca
   web, que é outro instrumento.
3. Registrar tudo aqui, com data, para a terceira medição ter duas para comparar.

## O que mudou entre as duas datas (para atribuir efeito)

| Data | Mudança |
|---|---|
| 18/08 | onda 59 (schema, frase de sede, llms.txt, sitemap) |
| 20/08 | onda 68 (14 superfícies de ícone, cartão de link, uma Organization só) |
| 25/08 | onda 72 (`alumniOf` dos 5, bio nova do Felipe, meta description dos líderes) |
| 25–26/08 | onda 73 (LinkedIn num mestre, experiência anterior no grafo) |
| **31/08** | **Wikidata**: firma + 5 pessoas criadas, com imprensa como referência; **onda 74** (`sameAs` ligando site ↔ Wikidata); onda 75 (link morto de imprensa arquivado) |

Como as ondas se acumulam, a medição de 10/09 mede **o conjunto**. Isolar o efeito do
Wikidata sozinho não é possível — e não vale a pena tentar.
