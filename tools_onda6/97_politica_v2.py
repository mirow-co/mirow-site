# -*- coding: utf-8 -*-
"""97_politica_v2.py — reescreve a politica de privacidade nas 3 linguas.

Issue mirow-marketing#225. Idempotente: rodar 2x reporta 0 mudancas.

    python tools_onda6/97_politica_v2.py <raiz-que-contem-public> [--check]

Por que
-------
A politica vigente e de antes da migracao e afirma coisas que deixaram de ser
verdade — a mais grave: "os Dados Pessoais serao armazenados exclusivamente nos
servidores da propria Mirow e/ou do provedor de cloud externo, localizados no
Brasil". Medido em 14/08/2026: o site e servido pelo GitHub Pages (Microsoft,
EUA), o GA4 e Google (EUA), o Leadfeeder e Dealfront (UE) e as fontes carregam do
Google a cada pagina. So o formulario de carreiras esta no Brasil (AWS sa-east-1).

A v2 tambem cobre o que faltava e a LGPD exige: base legal por finalidade
(art. 9), transferencia internacional (art. 33 + Resolucao CD/ANPD 19/2024),
prazos de retencao, tabela real de cookies, encarregado (art. 41) e o caminho de
oposicao — com botao de opt-out que chama window.mirowLeadfeederOptOut().

O que NAO entra, de proposito
-----------------------------
O formulario de contato: ele posta em admin-ajax.php, que responde 404 no site
estatico (medido). Enquanto nao funcionar, ele nao coleta nada, e a politica nao
pode dizer que coleta (mirow-marketing#64). O AddToAny saiu do site na #224,
entao tambem nao aparece como operador.
"""
from __future__ import unicode_literals

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public, ler, gravar, escrever_bloco_css  # noqa: E402

MARCA = "onda57:politica-v2"

PAGINAS = {
    "pt": "pt/politica-de-privacidade/index.html",
    "en": "en/privacy-policy/index.html",
    "de": "de/datenschutzrichtlinie/index.html",
}

# Cores medidas na propria pagina (14/08): o template da politica tem FUNDO
# ESCURO — nenhum elemento declara background, o navy vem do tema — e o corpo do
# texto e cinza #7F7F7F, com o h1 em branco. A primeira versao deste CSS usou
# #020E66 nos titulos, que e navy sobre navy: ilegivel. Titulo em branco e
# subtitulo em ciano seguem a hierarquia que a pagina ja tem.
CSS = """.pol-v2 h2{font-size:1.25rem;color:#fff;margin:2rem 0 .6rem}
.pol-v2 h3{font-size:1.05rem;color:#00ADEC;margin:1.4rem 0 .4rem}
.pol-v2 p,.pol-v2 li{line-height:1.6}
.pol-v2 strong{color:#fff}
.pol-v2 table{width:100%;border-collapse:collapse;margin:.8rem 0 1.4rem;font-size:.95rem}
.pol-v2 th,.pol-v2 td{border:1px solid #7F7F7F;padding:.5rem .7rem;text-align:left;
vertical-align:top}
.pol-v2 th{background:#AAD5E8;color:#071C25;font-weight:600}
.pol-v2 td{color:#D2D2D2}
.pol-v2 .pol-v2__data{color:#AAD5E8;font-size:.9rem;margin-bottom:1.5rem}
/* Os nomes de cookie usam <code> por semantica, mas o tema estiliza code com
 * pilha monospace — e o site inteiro roda em UMA fonte desde a onda 26. A V12
 * pegou os 4 elementos. Mantem-se a tag e herda-se a familia. */
.pol-v2 code{font-family:inherit;font-size:.95em;background:rgba(170,213,232,.18);
padding:.08em .35em;border-radius:3px}
.pol-v2 .pol-v2__optout{background:#020E66;color:#fff;border:0;border-radius:4px;
padding:.7rem 1.2rem;font:inherit;cursor:pointer}
.pol-v2 .pol-v2__optout:hover{background:#00ADEC}
.pol-v2 .pol-v2__status{margin-left:.8rem;color:#020E66;font-weight:600}
@media (max-width:600px){.pol-v2 table,.pol-v2 tbody,.pol-v2 tr,.pol-v2 td,.pol-v2 th{
display:block}.pol-v2 thead{display:none}.pol-v2 td{border-top:0}
.pol-v2 tr{border-top:1px solid #D2D2D2;margin-bottom:.8rem}}"""

# Botao de opt-out. Chama a funcao que o onda54-leadfeeder.js expoe; se o asset
# nao tiver carregado, avisa em vez de fingir que gravou.
JS_OPTOUT = """<script id="onda57-optout">
(function(){
  var b = document.getElementById('pol-optout');
  var s = document.getElementById('pol-optout-status');
  if (!b) return;
  var TXT = %s;
  function pinta(){
    var fora = false;
    try { fora = window.localStorage.getItem('mirow:leadfeeder:optout') === '1'; } catch(e){}
    s.textContent = fora ? TXT.fora : '';
    b.textContent = fora ? TXT.voltar : TXT.sair;
  }
  b.addEventListener('click', function(){
    if (typeof window.mirowLeadfeederOptOut !== 'function') { s.textContent = TXT.erro; return; }
    var fora = false;
    try { fora = window.localStorage.getItem('mirow:leadfeeder:optout') === '1'; } catch(e){}
    window.mirowLeadfeederOptOut(!fora);
    pinta();
  });
  pinta();
})();
</script>"""

TXT_BOTAO = {
    "pt": '{sair:"Não quero ser rastreado",voltar:"Voltar a permitir",'
          'fora:"Pronto: este navegador não será mais rastreado.",'
          'erro:"Não foi possível registrar agora. Tente recarregar a página."}',
    "en": '{sair:"Do not track me",voltar:"Allow again",'
          'fora:"Done: this browser will no longer be tracked.",'
          'erro:"Could not save right now. Please reload the page."}',
    "de": '{sair:"Nicht verfolgen",voltar:"Wieder erlauben",'
          'fora:"Fertig: Dieser Browser wird nicht mehr verfolgt.",'
          'erro:"Konnte nicht gespeichert werden. Bitte Seite neu laden."}',
}


def tabela(cabecalho, linhas):
    th = "".join("<th>%s</th>" % c for c in cabecalho)
    trs = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in l) for l in linhas)
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (th, trs)


def corpo_pt():
    return u"""
<p class="pol-v2__data">Versão 2 — vigente desde 16 de agosto de 2026. Substitui a versão anterior.</p>

<p>A <strong>Mirow &amp; Co. do Brasil Consultoria Ltda.</strong>, inscrita no CNPJ sob o nº
15.353.236/0001-89, com endereço na Rua Lauro Müller, 116, sala 1504, Rio de Janeiro/RJ
("Mirow"), é a <strong>controladora</strong> dos dados pessoais tratados por meio do site
https://mirow.com.br ("Site").</p>

<p>Esta política descreve, de forma específica, quais dados o Site coleta, para quê, com qual
base legal, com quem são compartilhados, por quanto tempo ficam guardados e como você pode se
opor ao tratamento.</p>

<h2>1. Dados que você nos fornece</h2>
<ul>
<li><strong>Candidaturas (página de Carreiras):</strong> nome, e-mail, telefone, formação,
experiência e o <strong>currículo que você anexa</strong>. O envio vai para infraestrutura da
Mirow na Amazon Web Services, região de São Paulo, no Brasil.</li>
<li><strong>Mirow CX Index:</strong> as respostas que você dá à ferramenta de avaliação de
maturidade em experiência do consumidor e os dados de identificação que optar por informar.</li>
<li><strong>Contato direto:</strong> o conteúdo do que você nos escreve por e-mail, WhatsApp ou
LinkedIn a partir dos links do Site. Esses canais são do próprio provedor que você usa; a
mensagem chega à nossa caixa de entrada.</li>
</ul>

<h2>2. Dados coletados automaticamente quando você navega</h2>
<ul>
<li><strong>Dados de navegação:</strong> endereço IP, tipo de navegador e dispositivo, idioma,
páginas visitadas, tempo de permanência e origem do acesso.</li>
<li><strong>Identificação da empresa do visitante.</strong> Usamos o serviço Leadfeeder
(Dealfront) para comparar o seu endereço IP com bases de faixas de IP corporativas e inferir
<strong>de qual empresa</strong> partiu o acesso. O serviço <strong>não identifica você como
pessoa</strong> — identifica, quando consegue, a organização. O IP <strong>não é
anonimizado</strong>, porque é justamente o dado necessário a essa inferência. O serviço também
recebe o identificador do Google Analytics do seu navegador.</li>
<li><strong>Medição de audiência.</strong> Usamos o Google Analytics 4 com Consent Mode v2. O
eixo de publicidade está <strong>desativado</strong>: a Mirow não veicula anúncios e nenhum dado
do Site alimenta personalização publicitária.</li>
</ul>

<h2>3. Para que usamos, e com qual base legal</h2>
""" + tabela(
        [u"Finalidade", u"Dados", u"Base legal (LGPD)"],
        [[u"Avaliar candidaturas a vagas", u"Item 1", u"Procedimentos preliminares de contrato — art. 7º, V"],
         [u"Responder ao seu contato", u"Item 1", u"Procedimentos preliminares — art. 7º, V"],
         [u"Fornecer o Mirow CX Index", u"Respostas e identificação", u"Execução de serviço solicitado — art. 7º, V"],
         [u"Medir audiência e melhorar o Site", u"Item 2", u"Legítimo interesse — art. 7º, IX"],
         [u"Identificar a empresa do visitante, para fins comerciais", u"IP e navegação", u"Legítimo interesse — art. 7º, IX"],
         [u"Cumprir obrigação legal ou ordem de autoridade", u"Conforme exigido", u"Art. 7º, II"]]) + u"""
<p>Nas duas finalidades apoiadas em <strong>legítimo interesse</strong>, você pode se opor a
qualquer momento, sem precisar justificar, pelo botão da seção 7.</p>

<h2>4. Com quem compartilhamos, e em que país</h2>
<p>Para operar o Site, os dados são tratados pelos operadores abaixo. Alguns estão fora do
Brasil, e por isso há transferência internacional.</p>
""" + tabela(
        [u"Operador", u"Para quê", u"País"],
        [[u"GitHub, Inc. (Microsoft)", u"Hospedagem do Site", u"Estados Unidos"],
         [u"Google LLC", u"Medição de audiência (GA4)", u"Estados Unidos"],
         [u"Dealfront Group GmbH", u"Identificação da empresa do visitante", u"União Europeia"],
         [u"Amazon Web Services", u"Recebimento de candidaturas e currículos", u"Brasil"]]) + u"""
<p>As transferências internacionais observam o art. 33 da LGPD e as cláusulas-padrão contratuais
da Resolução CD/ANPD nº 19/2024.</p>
<p>A Mirow <strong>não vende dados pessoais</strong> e não os compartilha para publicidade de
terceiros.</p>

<h2>5. Cookies</h2>
""" + tabela(
        [u"Cookie", u"Origem", u"Para quê", u"Duração"],
        [[u"<code>_ga</code>, <code>_ga_*</code>", u"Google Analytics", u"Distinguir visitantes e sessões", u"até 2 anos"],
         [u"<code>lfClientId</code>", u"Leadfeeder", u"Reconhecer o mesmo navegador entre páginas", u"até 2 anos"],
         [u"<code>pll_language</code>", u"Site", u"Lembrar o idioma escolhido", u"1 ano"]]) + u"""
<p>Você pode bloquear cookies nas configurações do navegador. O bloqueio não impede a leitura do
Site, mas pode fazer com que ele esqueça o idioma escolhido.</p>

<h2>6. Por quanto tempo guardamos</h2>
""" + tabela(
        [u"Dado", u"Prazo"],
        [[u"Currículos e candidaturas", u"6 meses após o encerramento do processo seletivo, salvo se você autorizar a manutenção para vagas futuras"],
         [u"Dados de navegação no Google Analytics", u"<strong>14 meses</strong> para os dados individuais. Os relatórios agregados, que não identificam ninguém, permanecem enquanto a propriedade existir"],
         [u"Dados no Leadfeeder", u"7 dias (limite do plano contratado)"],
         [u"Mensagens que você nos envia", u"Enquanto durar o relacionamento e, depois, pelos prazos legais aplicáveis"]]) + u"""

<h2>7. Como se opor ao rastreamento</h2>
<p><strong>Identificação de empresa (Leadfeeder).</strong> Clique no botão abaixo. A escolha fica
gravada neste navegador e passa a valer imediatamente, em todas as páginas do Site.</p>
<p><button type="button" id="pol-optout" class="pol-v2__optout">Não quero ser rastreado</button>
<span id="pol-optout-status" class="pol-v2__status"></span></p>
<p><strong>Sinal Global Privacy Control.</strong> Se o seu navegador ou uma extensão envia o
sinal GPC, nós o respeitamos automaticamente e o serviço de identificação não é carregado — você
não precisa fazer nada.</p>
<p><strong>Medição de audiência.</strong> Você pode instalar o complemento de desativação do
Google Analytics ou bloquear cookies no navegador.</p>

<h2>8. Seus direitos</h2>
<p>Nos termos do art. 18 da LGPD, você pode pedir: confirmação de que tratamos seus dados;
acesso a eles; correção de dados incompletos, inexatos ou desatualizados; anonimização, bloqueio
ou eliminação de dados desnecessários, excessivos ou tratados fora da lei; portabilidade;
informação sobre com quem compartilhamos; informação sobre a possibilidade de não consentir e as
consequências disso; revogação do consentimento; e <strong>oposição</strong> a tratamento
fundado em legítimo interesse.</p>
<p>Para exercer qualquer um deles, escreva para
<a href="mailto:contato@mirow.com.br">contato@mirow.com.br</a>. Responderemos nos prazos da
legislação aplicável.</p>
<p><strong>Encarregado pelo tratamento de dados pessoais (art. 41 da LGPD):</strong> contato pelo
mesmo endereço, <a href="mailto:contato@mirow.com.br">contato@mirow.com.br</a>.</p>

<h2>9. Segurança</h2>
<p>Adotamos medidas técnicas e administrativas para proteger os dados, e o acesso é restrito a
pessoas autorizadas que precisem conhecê-los. Nenhum sistema é infalível; havendo incidente de
segurança com risco relevante, comunicaremos você e a Autoridade Nacional de Proteção de Dados,
nos termos do art. 48 da LGPD.</p>

<h2>10. Links para outros sites</h2>
<p>O Site tem links para páginas de terceiros — veículos de imprensa, redes sociais e parceiros.
Esta política não se aplica a eles. Ao seguir um link externo, vale a política do site de
destino.</p>

<h2>11. Alterações desta política</h2>
<p>Esta política pode ser atualizada. A versão vigente e a data de vigência estarão sempre no
topo desta página, e alterações relevantes serão sinalizadas no Site.</p>

<h2>12. Contato</h2>
<p><a href="mailto:contato@mirow.com.br">contato@mirow.com.br</a> · Rua Lauro Müller, 116,
sala 1504, Rio de Janeiro/RJ.</p>
"""


def corpo_en():
    return u"""
<p class="pol-v2__data">Version 2 — effective 16 August 2026. Replaces the previous version.</p>

<p><strong>Mirow &amp; Co. do Brasil Consultoria Ltda.</strong>, registered under CNPJ
15.353.236/0001-89, at Rua Lauro Müller, 116, suite 1504, Rio de Janeiro, Brazil ("Mirow"), is
the <strong>controller</strong> of personal data processed through https://mirow.com.br (the
"Site").</p>

<p>This policy sets out specifically what the Site collects, why, on what legal basis, who it is
shared with, how long it is kept and how you can object.</p>

<h2>1. Data you give us</h2>
<ul>
<li><strong>Job applications (Careers page):</strong> name, e-mail, phone, education, experience
and the <strong>CV you attach</strong>. Submissions go to Mirow infrastructure on Amazon Web
Services, São Paulo region, in Brazil.</li>
<li><strong>Mirow CX Index:</strong> the answers you give the customer-experience maturity tool
and any identifying details you choose to provide.</li>
<li><strong>Direct contact:</strong> whatever you write to us by e-mail, WhatsApp or LinkedIn
from the links on the Site.</li>
</ul>

<h2>2. Data collected automatically as you browse</h2>
<ul>
<li><strong>Browsing data:</strong> IP address, browser and device type, language, pages viewed,
time on page and traffic source.</li>
<li><strong>Visitor company identification.</strong> We use Leadfeeder (Dealfront) to match your
IP address against corporate IP range databases and infer <strong>which company</strong> the
visit came from. The service <strong>does not identify you as an individual</strong> — where it
succeeds, it identifies the organisation. The IP is <strong>not anonymised</strong>, because it
is precisely the data that inference needs. The service also receives your browser's Google
Analytics identifier.</li>
<li><strong>Audience measurement.</strong> We use Google Analytics 4 with Consent Mode v2. The
advertising axis is <strong>switched off</strong>: Mirow runs no ads and no Site data feeds ad
personalisation.</li>
</ul>

<h2>3. Purposes and legal bases</h2>
""" + tabela(
        [u"Purpose", u"Data", u"Legal basis (LGPD)"],
        [[u"Assessing job applications", u"Section 1", u"Pre-contractual procedures — art. 7, V"],
         [u"Replying to your enquiry", u"Section 1", u"Pre-contractual procedures — art. 7, V"],
         [u"Providing the Mirow CX Index", u"Answers and identification", u"Performance of a requested service — art. 7, V"],
         [u"Measuring audience and improving the Site", u"Section 2", u"Legitimate interests — art. 7, IX"],
         [u"Identifying the visitor's company for business purposes", u"IP and browsing", u"Legitimate interests — art. 7, IX"],
         [u"Complying with legal obligations or orders", u"As required", u"Art. 7, II"]]) + u"""
<p>For the two purposes based on <strong>legitimate interests</strong>, you may object at any
time, without giving reasons, using the button in section 7.</p>

<h2>4. Who we share with, and in which country</h2>
""" + tabela(
        [u"Processor", u"Purpose", u"Country"],
        [[u"GitHub, Inc. (Microsoft)", u"Site hosting", u"United States"],
         [u"Google LLC", u"Audience measurement (GA4)", u"United States"],
         [u"Dealfront Group GmbH", u"Visitor company identification", u"European Union"],
         [u"Amazon Web Services", u"Receiving applications and CVs", u"Brazil"]]) + u"""
<p>International transfers follow art. 33 of the LGPD and the standard contractual clauses of
ANPD Resolution 19/2024.</p>
<p>Mirow <strong>does not sell personal data</strong> and does not share it for third-party
advertising.</p>

<h2>5. Cookies</h2>
""" + tabela(
        [u"Cookie", u"Source", u"Purpose", u"Lifetime"],
        [[u"<code>_ga</code>, <code>_ga_*</code>", u"Google Analytics", u"Distinguish visitors and sessions", u"up to 2 years"],
         [u"<code>lfClientId</code>", u"Leadfeeder", u"Recognise the same browser across pages", u"up to 2 years"],
         [u"<code>pll_language</code>", u"Site", u"Remember your language choice", u"1 year"]]) + u"""
<p>You can block cookies in your browser settings. Blocking does not stop you reading the Site,
but it may make it forget your language choice.</p>

<h2>6. How long we keep it</h2>
""" + tabela(
        [u"Data", u"Retention"],
        [[u"CVs and applications", u"6 months after the selection process ends, unless you allow us to keep them for future openings"],
         [u"Google Analytics browsing data", u"<strong>14 months</strong> for individual-level data. Aggregated reports, which identify no one, remain for as long as the property exists"],
         [u"Leadfeeder data", u"7 days (limit of the plan in use)"],
         [u"Messages you send us", u"For as long as the relationship lasts and thereafter for applicable legal periods"]]) + u"""

<h2>7. How to object to tracking</h2>
<p><strong>Company identification (Leadfeeder).</strong> Click the button below. The choice is
stored in this browser and takes effect immediately across the whole Site.</p>
<p><button type="button" id="pol-optout" class="pol-v2__optout">Do not track me</button>
<span id="pol-optout-status" class="pol-v2__status"></span></p>
<p><strong>Global Privacy Control.</strong> If your browser or an extension sends the GPC signal,
we honour it automatically and the identification service is not loaded — you need do nothing.</p>
<p><strong>Audience measurement.</strong> You can install the Google Analytics opt-out add-on or
block cookies in your browser.</p>

<h2>8. Your rights</h2>
<p>Under art. 18 of the LGPD you may request: confirmation that we process your data; access to
it; correction of incomplete, inaccurate or outdated data; anonymisation, blocking or deletion of
unnecessary or excessive data or data processed unlawfully; portability; information on who we
share with; information on the consequences of refusing consent; withdrawal of consent; and
<strong>objection</strong> to processing based on legitimate interests.</p>
<p>To exercise any of these, write to
<a href="mailto:contato@mirow.com.br">contato@mirow.com.br</a>.</p>
<p><strong>Data Protection Officer (art. 41 LGPD):</strong> reachable at the same address,
<a href="mailto:contato@mirow.com.br">contato@mirow.com.br</a>.</p>

<h2>9. Security</h2>
<p>We apply technical and administrative measures to protect the data, and access is restricted
to authorised people who need it. No system is infallible; in the event of a security incident
with relevant risk we will notify you and the Brazilian Data Protection Authority, under art. 48
of the LGPD.</p>

<h2>10. Links to other sites</h2>
<p>The Site links to third-party pages — press outlets, social networks and partners. This policy
does not apply to them.</p>

<h2>11. Changes to this policy</h2>
<p>This policy may be updated. The current version and its effective date always appear at the
top of this page.</p>

<h2>12. Contact</h2>
<p><a href="mailto:contato@mirow.com.br">contato@mirow.com.br</a> · Rua Lauro Müller, 116,
suite 1504, Rio de Janeiro, Brazil.</p>
"""


def corpo_de():
    return u"""
<p class="pol-v2__data">Version 2 — gültig ab 16. August 2026. Ersetzt die vorherige Fassung.</p>

<p>Die <strong>Mirow &amp; Co. do Brasil Consultoria Ltda.</strong>, eingetragen unter der CNPJ
15.353.236/0001-89, Rua Lauro Müller 116, Raum 1504, Rio de Janeiro, Brasilien ("Mirow"), ist
<strong>Verantwortliche</strong> für die über https://mirow.com.br ("Website") verarbeiteten
personenbezogenen Daten.</p>

<p>Diese Erklärung beschreibt konkret, welche Daten die Website erhebt, wozu, auf welcher
Rechtsgrundlage, mit wem sie geteilt werden, wie lange sie gespeichert bleiben und wie Sie
widersprechen können.</p>

<h2>1. Daten, die Sie uns geben</h2>
<ul>
<li><strong>Bewerbungen (Seite Karriere):</strong> Name, E-Mail, Telefon, Ausbildung, Erfahrung
und der <strong>angehängte Lebenslauf</strong>. Die Übermittlung erfolgt an Mirow-Infrastruktur
bei Amazon Web Services, Region São Paulo, Brasilien.</li>
<li><strong>Mirow CX Index:</strong> Ihre Antworten im Reifegrad-Tool zur Customer Experience
sowie die Angaben, die Sie freiwillig machen.</li>
<li><strong>Direkter Kontakt:</strong> der Inhalt dessen, was Sie uns per E-Mail, WhatsApp oder
LinkedIn über die Links der Website schreiben.</li>
</ul>

<h2>2. Daten, die beim Surfen automatisch erhoben werden</h2>
<ul>
<li><strong>Nutzungsdaten:</strong> IP-Adresse, Browser- und Gerätetyp, Sprache, aufgerufene
Seiten, Verweildauer und Herkunft des Zugriffs.</li>
<li><strong>Identifikation des Unternehmens des Besuchers.</strong> Wir nutzen Leadfeeder
(Dealfront), um Ihre IP-Adresse mit Datenbanken zu Unternehmens-IP-Bereichen abzugleichen und
abzuleiten, aus <strong>welchem Unternehmen</strong> der Zugriff kam. Der Dienst
<strong>identifiziert Sie nicht als Person</strong> — er identifiziert, soweit möglich, die
Organisation. Die IP wird <strong>nicht anonymisiert</strong>, da sie genau die für diese
Ableitung nötige Angabe ist. Der Dienst erhält zudem die Google-Analytics-Kennung Ihres
Browsers.</li>
<li><strong>Reichweitenmessung.</strong> Wir nutzen Google Analytics 4 mit Consent Mode v2. Die
Werbe-Achse ist <strong>deaktiviert</strong>: Mirow schaltet keine Werbung, und keine Daten der
Website fließen in Werbepersonalisierung.</li>
</ul>

<h2>3. Zwecke und Rechtsgrundlagen</h2>
""" + tabela(
        [u"Zweck", u"Daten", u"Rechtsgrundlage (LGPD)"],
        [[u"Bewerbungen prüfen", u"Ziffer 1", u"Vorvertragliche Maßnahmen — Art. 7 V"],
         [u"Auf Ihre Anfrage antworten", u"Ziffer 1", u"Vorvertragliche Maßnahmen — Art. 7 V"],
         [u"Mirow CX Index bereitstellen", u"Antworten und Angaben", u"Erbringung einer angefragten Leistung — Art. 7 V"],
         [u"Reichweite messen und Website verbessern", u"Ziffer 2", u"Berechtigtes Interesse — Art. 7 IX"],
         [u"Unternehmen des Besuchers zu Geschäftszwecken identifizieren", u"IP und Nutzung", u"Berechtigtes Interesse — Art. 7 IX"],
         [u"Gesetzliche Pflichten oder behördliche Anordnungen erfüllen", u"Wie gefordert", u"Art. 7 II"]]) + u"""
<p>Bei den beiden auf <strong>berechtigtem Interesse</strong> gestützten Zwecken können Sie
jederzeit und ohne Begründung widersprechen — über die Schaltfläche in Ziffer 7.</p>

<h2>4. Mit wem wir teilen, und in welchem Land</h2>
""" + tabela(
        [u"Auftragsverarbeiter", u"Zweck", u"Land"],
        [[u"GitHub, Inc. (Microsoft)", u"Hosting der Website", u"USA"],
         [u"Google LLC", u"Reichweitenmessung (GA4)", u"USA"],
         [u"Dealfront Group GmbH", u"Identifikation des Unternehmens", u"Europäische Union"],
         [u"Amazon Web Services", u"Empfang von Bewerbungen und Lebensläufen", u"Brasilien"]]) + u"""
<p>Internationale Übermittlungen richten sich nach Art. 33 LGPD und den Standardvertragsklauseln
der ANPD-Resolution 19/2024.</p>
<p>Mirow <strong>verkauft keine personenbezogenen Daten</strong> und teilt sie nicht für Werbung
Dritter.</p>

<h2>5. Cookies</h2>
""" + tabela(
        [u"Cookie", u"Herkunft", u"Zweck", u"Dauer"],
        [[u"<code>_ga</code>, <code>_ga_*</code>", u"Google Analytics", u"Besucher und Sitzungen unterscheiden", u"bis zu 2 Jahre"],
         [u"<code>lfClientId</code>", u"Leadfeeder", u"Denselben Browser seitenübergreifend erkennen", u"bis zu 2 Jahre"],
         [u"<code>pll_language</code>", u"Website", u"Sprachwahl merken", u"1 Jahr"]]) + u"""
<p>Sie können Cookies in den Browsereinstellungen blockieren. Das Lesen der Website bleibt
möglich; die Sprachwahl kann dann verloren gehen.</p>

<h2>6. Speicherdauer</h2>
""" + tabela(
        [u"Daten", u"Dauer"],
        [[u"Lebensläufe und Bewerbungen", u"6 Monate nach Abschluss des Auswahlverfahrens, sofern Sie einer längeren Speicherung für künftige Stellen nicht zustimmen"],
         [u"Nutzungsdaten in Google Analytics", u"<strong>14 Monate</strong> für Daten auf Einzelebene. Aggregierte Berichte, die niemanden identifizieren, bleiben, solange die Property besteht"],
         [u"Daten bei Leadfeeder", u"7 Tage (Grenze des genutzten Tarifs)"],
         [u"Nachrichten, die Sie uns senden", u"Für die Dauer der Beziehung und danach für die gesetzlichen Fristen"]]) + u"""

<h2>7. Wie Sie dem Tracking widersprechen</h2>
<p><strong>Unternehmensidentifikation (Leadfeeder).</strong> Klicken Sie auf die Schaltfläche
unten. Die Entscheidung wird in diesem Browser gespeichert und gilt sofort auf der ganzen
Website.</p>
<p><button type="button" id="pol-optout" class="pol-v2__optout">Nicht verfolgen</button>
<span id="pol-optout-status" class="pol-v2__status"></span></p>
<p><strong>Global Privacy Control.</strong> Sendet Ihr Browser oder eine Erweiterung das
GPC-Signal, beachten wir es automatisch und der Identifikationsdienst wird nicht geladen.</p>
<p><strong>Reichweitenmessung.</strong> Sie können das Google-Analytics-Deaktivierungs-Add-on
installieren oder Cookies blockieren.</p>

<h2>8. Ihre Rechte</h2>
<p>Nach Art. 18 LGPD können Sie verlangen: Bestätigung der Verarbeitung; Auskunft; Berichtigung
unvollständiger, unrichtiger oder veralteter Daten; Anonymisierung, Sperrung oder Löschung
unnötiger, übermäßiger oder rechtswidrig verarbeiteter Daten; Datenübertragbarkeit; Auskunft über
Empfänger; Auskunft über die Folgen einer Verweigerung der Einwilligung; Widerruf der
Einwilligung; sowie <strong>Widerspruch</strong> gegen eine auf berechtigtem Interesse gestützte
Verarbeitung.</p>
<p>Wenden Sie sich dazu an
<a href="mailto:contato@mirow.com.br">contato@mirow.com.br</a>.</p>
<p><strong>Datenschutzbeauftragter (Art. 41 LGPD):</strong> erreichbar unter derselben Adresse,
<a href="mailto:contato@mirow.com.br">contato@mirow.com.br</a>.</p>

<h2>9. Sicherheit</h2>
<p>Wir treffen technische und organisatorische Maßnahmen zum Schutz der Daten; der Zugriff ist
auf befugte Personen beschränkt. Kein System ist unfehlbar; bei einem Sicherheitsvorfall mit
relevantem Risiko informieren wir Sie und die brasilianische Datenschutzbehörde gemäß Art. 48
LGPD.</p>

<h2>10. Links zu anderen Websites</h2>
<p>Die Website verlinkt auf Seiten Dritter — Presse, soziale Netzwerke und Partner. Diese
Erklärung gilt dort nicht.</p>

<h2>11. Änderungen dieser Erklärung</h2>
<p>Diese Erklärung kann aktualisiert werden. Die geltende Fassung und ihr Datum stehen stets oben
auf dieser Seite.</p>

<h2>12. Kontakt</h2>
<p><a href="mailto:contato@mirow.com.br">contato@mirow.com.br</a> · Rua Lauro Müller 116,
Raum 1504, Rio de Janeiro, Brasilien.</p>
"""


CORPOS = {"pt": corpo_pt, "en": corpo_en, "de": corpo_de}

# O conteudo vive dentro de <div class="container page-default"><div class="row"><div class="col">
ALVO = re.compile(
    r'(<div class="container page-default"><div class="row"><div class="col">)'
    r'(.*?)'
    r'(</div></div></div></main>)', re.S)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    pub = resolve_public(args[0])

    trocadas = ja_ok = 0
    problemas = []

    for lang, rel in PAGINAS.items():
        caminho = os.path.join(pub, *rel.split("/"))
        if not os.path.exists(caminho):
            problemas.append(u"%s: pagina ausente (%s)" % (lang, rel))
            continue
        html = ler(caminho)
        m = ALVO.search(html)
        if not m:
            problemas.append(u"%s: nao achei o container de conteudo" % lang)
            continue

        novo_corpo = (u'<div class="pol-v2" data-bloco="%s">%s</div>\n%s'
                      % (MARCA, CORPOS[lang](), JS_OPTOUT % TXT_BOTAO[lang]))
        novo = html[:m.start(2)] + novo_corpo + html[m.end(2):]
        if novo == html:
            ja_ok += 1
            continue
        if not check:
            gravar(caminho, novo)
        trocadas += 1

    if not check:
        escrever_bloco_css(pub, "politica-v2", CSS, onda="onda57")

    print("paginas reescritas: %d" % trocadas)
    print("ja estavam na v2:   %d" % ja_ok)
    if problemas:
        print("problemas: %s" % "; ".join(problemas))
    print("mudancas: %d%s" % (trocadas, " (--check: nada escrito)" if check else ""))
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
