# -*- coding: utf-8 -*-
"""70 — onda 18, S-57 (issue #115): pagina de imprensa como lista com fundo branco.

Uso:
    python tools_onda6/70_imprensa_lista.py <raiz-que-contem-public>
    python tools_onda6/70_imprensa_lista.py <raiz> --sem-download   (nao busca icone)

Pedido do Mario: "colocar os icones do veiculo de comunicacao no qual o nosso
material foi impresso. lista com fundo branco mostrando o logo do veiculo, o nome
do veiculo, a data, o link para o material (como esta, no titulo, funciona bem)."

Hoje a pagina e uma sequencia de blocos Gutenberg: um <h6> com o badge
"DD/MM/AAAA | VEICULO" e um <h5> com o titulo linkado. O script LE esses pares
(nao reescreve o conteudo a mao) e emite uma <ul> semantica com 4 colunas:
icone | nome do veiculo | data | titulo linkado — sobre fundo branco.

ICONE: nao existe arquivo de logo dos veiculos no repo. O script baixa UMA VEZ o
favicon 64px de cada dominio e grava em
public/wp-content/uploads/2026/08/imprensa/<dominio>.png — a pagina publicada nao
faz nenhuma chamada externa. Favicon e um proxy do logo; wordmark de verdade
exigiria curadoria manual por veiculo (fica como PENDENTE na issue #115).

NOME DO VEICULO: o badge esta todo em CAPS; a lista usa a grafia correta
(R4 — nunca CAPS no corpo), via tabela VEICULOS abaixo.

Idempotente: bloco entre marcadores; download so se o arquivo ainda nao existe.
"""
import io
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

ICONES_REL = "wp-content/uploads/2026/08/imprensa"
MARK_INI = "<!-- onda18:imprensa-lista -->"
MARK_FIM = "<!-- /onda18:imprensa-lista -->"

REX_LISTA = re.compile(
    r'<li class="onda18-imprensa__item">.*?__veiculo">(?P<veiculo>[^<]+)</span>'
    r'<time[^>]*>(?P<data>[^<]+)</time>'
    r'<a class="onda18-imprensa__titulo" href="(?P<url>[^"]+)"[^>]*>(?P<titulo>[^<]+)', re.S)

REX_PAR = re.compile(
    r'<strong>(?P<data>\d{2}/\d{2}/\d{4})\s*\|\s*(?P<veiculo>[^<]+?)\s*</strong>.*?'
    r'<h5 class="wp-block-heading"><a href="(?P<url>[^"]+)"[^>]*>(?:<mark[^>]*>)?'
    r'(?P<titulo>[^<]+)', re.S)

# grafia correta do nome do veiculo + o dominio CANONICO dele (de onde sai o
# icone). O dominio vem do veiculo, nunca do link do material: dois itens tem
# link divergente do veiculo desde antes da onda 18 (ver DIVERGENTES no fim da
# execucao) e seguiam com o logo de outro jornal.
DOMINIO = {
    u"Empresas & Negócios": "jornalempresasenegocios.com.br",
    u"Reuters": "www.reuters.com",
    u"Technibus": "technibus.com.br",
    u"Move News": "www.movenews.com.br",
    u"Estadão": "www.estadao.com.br",
    u"iG": "www.ig.com.br",
    u"The Economist": "www.economist.com",
    u"Público": "www.publico.pt",
    u"Valor Econômico": "valor.globo.com",
    u"CZ Insights": "www.czapp.com",
    u"Gazeta do Povo": "www.gazetadopovo.com.br",
    u"UOL": "www.uol.com.br",
    u"Money Times": "www.moneytimes.com.br",
    u"epbr": "epbr.com.br",
    u"O Globo": "oglobo.globo.com",
    u"BNews": "www.bnews.com.br",
    u"Folha de S.Paulo": "www1.folha.uol.com.br",
    u"IstoÉ Dinheiro": "istoedinheiro.com.br",
}

# grafia correta do nome do veiculo (o badge original esta em CAPS)
VEICULOS = {
    u"EMPRESAS & NEGÓCIOS": u"Empresas & Negócios",
    u"REUTERS": u"Reuters",
    u"TECHNIBUS": u"Technibus",
    u"MOVE NEWS": u"Move News",
    u"ESTADÃO": u"Estadão",
    u"IG": u"iG",
    u"THE ECONOMIST": u"The Economist",
    u"PÚBLICO": u"Público",
    u"VALOR ECONÔMICO": u"Valor Econômico",
    u"CZ INSIGHTS": u"CZ Insights",
    u"GAZETA DO POVO": u"Gazeta do Povo",
    u"UOL": u"UOL",
    u"MONEY TIMES": u"Money Times",
    u"EPBR": u"epbr",
    u"O GLOBO": u"O Globo",
    u"BNEWS": u"BNews",
    u"FOLHA DE SÃO PAULO": u"Folha de S.Paulo",
    u"ISTO É DINHEIRO": u"IstoÉ Dinheiro",
}

CSS = """/* S-57: imprensa como lista sobre fundo branco — icone do veiculo, nome,
   data e o titulo como link (o titulo linkado ja funcionava bem). */
.onda18-imprensa{list-style:none;margin:0 0 60px;padding:0;background:#fff}
.onda18-imprensa__item{display:grid;
  grid-template-columns:34px minmax(150px,190px) 108px 1fr;
  align-items:center;gap:0 18px;padding:16px 22px;
  border-bottom:1px solid rgba(2,14,102,.12)}
.onda18-imprensa__item:last-child{border-bottom:0}
.onda18-imprensa__item:hover{background:#F4F8FC}
.onda18-imprensa__logo{width:28px;height:28px;object-fit:contain;display:block;
  background:#F0F4F8;border-radius:4px;padding:2px;box-sizing:border-box}
.onda18-imprensa__logo--vazio{display:flex;align-items:center;justify-content:center;
  width:28px;height:28px;background:#AAD5E8;color:#020E66;font-weight:700;
  font-size:13px;border-radius:3px}
.onda18-imprensa__veiculo{color:#020E66;font-weight:700;font-size:15px;
  line-height:1.25}
.onda18-imprensa__data{color:#7F7F7F;font-size:14px;white-space:nowrap}
.onda18-imprensa__titulo{color:#071C25;font-size:16px;line-height:1.35;
  text-decoration:none;border-bottom:1px solid transparent;transition:all 200ms ease}
.onda18-imprensa__titulo:hover,.onda18-imprensa__titulo:focus-visible{
  color:#00ADEC;border-bottom-color:#00ADEC}
@media only screen and (max-width: 991px){
  .onda18-imprensa__item{grid-template-columns:28px 1fr;gap:6px 14px;
    padding:14px 16px}
  .onda18-imprensa__veiculo{font-size:14px}
  .onda18-imprensa__data{grid-column:2;font-size:13px}
  .onda18-imprensa__titulo{grid-column:1 / -1;font-size:15px}
}"""


def dominio(url):
    m = re.match(r'https?://([^/]+)/?', url)
    return m.group(1).lower() if m else ""


def baixar_icone(pub, dom, baixar=True):
    """Devolve o nome do arquivo local do icone, ou None se nao houver."""
    destino_dir = os.path.join(pub, ICONES_REL.replace("/", os.sep))
    nome = dom.replace(":", "_") + ".png"
    p = os.path.join(destino_dir, nome)
    if os.path.exists(p) and os.path.getsize(p) > 200:
        return nome
    if not baixar:
        return None
    os.makedirs(destino_dir, exist_ok=True)
    url = "https://www.google.com/s2/favicons?domain=%s&sz=64" % dom
    try:
        r = subprocess.run(["curl", "-sSL", "--max-time", "20", "-o", p, url],
                           capture_output=True, text=True)
    except Exception as e:
        print("    erro no curl de %s: %s" % (dom, e))
        return None
    if r.returncode != 0 or not os.path.exists(p) or os.path.getsize(p) < 200:
        if os.path.exists(p):
            os.unlink(p)
        print("    sem icone para %s" % dom)
        return None
    print("    icone baixado: %s" % nome)
    return nome


def nome_veiculo(bruto):
    limpo = bruto.replace("&amp;", "&").strip()
    return VEICULOS.get(limpo, limpo)


def iso(data):
    d, m, a = data.split("/")
    return "%s-%s-%s" % (a, m, d)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    baixar = "--sem-download" not in sys.argv

    mudou = escrever_bloco_css(pub, "imprensa", CSS, onda="onda18")
    print("bloco onda18:imprensa %s" % ("gravado" if mudou else "ja estava igual"))

    paginas = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if n != "index.html":
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if "onda12:imprensa-formatacao" not in h:
                continue
            rel = os.path.relpath(p, pub).replace(os.sep, "/")

            if MARK_INI in h:
                itens = [m.groupdict() for m in REX_LISTA.finditer(h)]
            else:
                itens = [m.groupdict() for m in REX_PAR.finditer(h)]
            if not itens:
                print("  %s: nao achei os pares data|veiculo — NAO alterada" % rel)
                continue
            print("  %s: %d item(ns)" % (rel, len(itens)))

            lis = []
            divergentes = []
            for it in itens:
                veic = nome_veiculo(it["veiculo"])
                dom_link = dominio(it["url"])
                dom = DOMINIO.get(veic, dom_link)
                if dom_link and dom_link.replace("www.", "") not in dom.replace("www.", "")                         and dom.replace("www.", "") not in dom_link.replace("www.", ""):
                    divergentes.append(u"%s %s: veiculo %s, link em %s"
                                       % (it["data"], veic, veic, dom_link))
                arq = baixar_icone(pub, dom, baixar)
                if arq:
                    logo = ('<img class="onda18-imprensa__logo" src="/mirow-site/%s/%s" '
                            'alt="%s" width="28" height="28" loading="lazy">'
                            % (ICONES_REL, arq, veic))
                else:
                    logo = ('<span class="onda18-imprensa__logo--vazio" aria-hidden="true">%s'
                            '</span>' % veic[:1].upper())
                lis.append(
                    '<li class="onda18-imprensa__item">%s'
                    '<span class="onda18-imprensa__veiculo">%s</span>'
                    '<time class="onda18-imprensa__data" datetime="%s">%s</time>'
                    '<a class="onda18-imprensa__titulo" href="%s" target="_blank" '
                    'rel="noopener noreferrer">%s</a></li>'
                    % (logo, veic, iso(it["data"]), it["data"], it["url"], it["titulo"]))

            bloco = '%s<ul class="onda18-imprensa">%s</ul>%s' % (
                MARK_INI, "".join(lis), MARK_FIM)

            # troca da 1a badge ate o ultimo separador pela lista;
            # o rodape editorial ("solicitacoes de imprensa") continua depois
            if MARK_INI in h:
                ini = h.index(MARK_INI)
                fim = h.index(MARK_FIM) + len(MARK_FIM)
            else:
                ini = h.find('<!-- wp:heading {"level":6} -->')
                fim = h.rfind('<!-- /wp:separator -->')
                if ini < 0 or fim < 0 or fim < ini:
                    print("  %s: nao achei os limites do trecho — NAO alterada" % rel)
                    continue
                fim += len('<!-- /wp:separator -->')
            novo = h[:ini] + bloco + h[fim:]
            gravar(p, novo)
            paginas += 1
            for d in divergentes:
                print(u"    DIVERGENTE (dado antigo, logo agora segue o veiculo): %s" % d)

    print("resumo: %d pagina(s) de imprensa convertida(s) em lista" % paginas)


if __name__ == "__main__":
    main()
