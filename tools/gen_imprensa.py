# -*- coding: utf-8 -*-
u"""gen_imprensa.py — gera a lista da página Imprensa a partir dos arquivos mestre (P3).

Uso:
    python tools/gen_imprensa.py <raiz-que-contem-public>
        [--materias=<caminho.json>] [--veiculos=<caminho.json>] [--dry]

POR QUE ESTE ARQUIVO EXISTE
---------------------------
A lista de imprensa era HTML escrito à mão em três arquivos, e cada matéria nova
virou um script próprio: `45_imprensa-formatacao-pontos.py`, `70_imprensa_lista.py`,
`84_imprensa_en_de.py`, `98_imprensa_logos.py`, `106_imprensa_folha_vaivem_2026.py`,
`120_imprensa_descricao.py`. A onda 65 seria o **sétimo**.

O que esse modelo produziu está medido na issue #238: **três campos errados em dois
itens**, no ar por mais de doze meses.

  * 28/05/2024 "Armazenamento de energia trava aportes consistentes" saía rotulado
    **Estadão**, com o logo do Estadão — e o link é do **Valor** (Revista Energia),
    cujo `datePublished` é 2024-05-10. Veículo, logo E data errados no mesmo item.
  * 02/03/2024 "Descarbonização: onde investir…" saía como **Folha de S.Paulo** — e
    o link é do jornal **Empresas & Negócios**.

E existia asserção contra isso: a `S57b` cobra literalmente *"o logo segue o veículo,
não o link"*. Ela passava **verde** nos dois, porque o logo batia com o rótulo — e o
rótulo é que estava errado. Ela comparava dois campos NOSSOS entre si, e nunca
comparou nenhum deles com o **host do link**, que é o único dado que não escrevemos.
P2.1: medir o efeito, não a declaração.

A PARTIR DAQUI existe UMA fonte para a lista, no repo PRIVADO `mirow-co/mirow-marketing`:

    08_Site/2026-08-19_imprensa-materias-curadoria.json   (as matérias)
    08_Site/2026-08-06_imprensa-veiculos-curadoria.json   (o logo de cada veículo)

O HTML das três páginas é GERADO desses arquivos. **Editar a lista à mão é violação
de processo** — como já é na barra de clientes (`gen_clients.py`) e na Nossa Rede
(`gen_rede.py`).

O QUE ESTE SCRIPT NÃO FAZ DE PROPÓSITO
--------------------------------------
* Não silencia matéria cujo veículo não esteja no mestre de logos, nem logo declarado
  que não exista no disco: reporta e **sai com código 1**. Veículo sem entrada é
  exatamente o buraco por onde o rótulo errado entrou.
* Não chama a rede. Conferir se as URLs respondem 200 é trabalho do
  `tools_onda6/qa/checar_links_imprensa.py`, rodado por onda — rede externa dentro do
  gate o tornaria lento e não-determinístico, e um veículo fora do ar por cinco
  minutos bloquearia deploy.
* Não traduz título: o título fica no idioma em que a matéria foi publicada. As três
  páginas listam os mesmos itens, com o mesmo HTML (é assim desde a onda 29).

Também grava `tools/imprensa-publicada.json` (só o que a suíte precisa ler: data,
veículo, título, url, logo — nada de nota interna), para a asserção `S166` poder
RECALCULAR a lista e comparar, sem lista hardcoded que possa divergir.
"""
import io
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "tools_onda6"))

from _onda7_css import gravar, ler, resolve_public  # noqa: E402

BASE_MESTRE = os.path.join(
    os.path.expanduser("~"), "OneDrive - Mirow", "Mirow & Co", "05_Marketing",
    "05_NovoMarketing", "08_Site")
MESTRE_MATERIAS = os.path.join(BASE_MESTRE, "2026-08-19_imprensa-materias-curadoria.json")
MESTRE_VEICULOS = os.path.join(BASE_MESTRE, "2026-08-06_imprensa-veiculos-curadoria.json")

PAGINAS = ["pt/imprensa/index.html", "en/press/index.html", "de/presse/index.html"]

DIR_LOGOS = "wp-content/uploads/2026/08/imprensa-logos"

# Mesmo mecanismo dos logos de clientes: a query impede o plugin svgs-inline do
# tema de inlinar o SVG (ids/classes genéricas colidem entre logos).
QUERY_ANTI_INLINE = "?ver=1"

MESES = None  # a data no HTML é dd/mm/aaaa; não há nome de mês a localizar


def escapa(txt):
    return (txt.replace(u"&", u"&amp;").replace(u"<", u"&lt;")
               .replace(u">", u"&gt;").replace(u'"', u"&quot;"))


def data_br(iso):
    a, m, d = iso.split("-")
    return u"%s/%s/%s" % (d, m, a)


def carregar(caminho, chave):
    if not os.path.exists(caminho):
        raise SystemExit(
            u"arquivo mestre não encontrado: %s\n"
            u"ele mora no repo PRIVADO mirow-co/mirow-marketing, em 08_Site/.\n"
            u"passe o caminho com --%s=<...>" % (caminho, chave))
    with io.open(caminho, encoding="utf-8") as f:
        return json.load(f)


def montar_item(mat, logo_arq, prefixo):
    u"""Um <li> no markup canônico (onda 18 + S-102 + S-136)."""
    veic = escapa(mat["veiculo"])
    if logo_arq:
        query = QUERY_ANTI_INLINE if logo_arq.endswith(".svg") else u""
        marca = (u'<img class="onda41-imprensa__logo" src="%s%s/%s%s" alt="%s">'
                 % (prefixo, DIR_LOGOS, logo_arq, query, veic))
    else:
        # fallback de texto (wordmark tipográfico), já no ar para epbr,
        # CZ Insights e Money Times — veículo sem asset utilizável.
        marca = (u'<span class="onda41-imprensa__logo '
                 u'onda41-imprensa__logo--texto" aria-hidden="true">%s</span>' % veic)
    return (u'<li class="onda18-imprensa__item">'
            u'<a class="onda26-imprensa__link" href="%s" target="_blank" '
            u'rel="noopener noreferrer">'
            u'%s'
            u'<span class="onda18-imprensa__veiculo">%s</span>'
            u'<time class="onda18-imprensa__data" datetime="%s">%s</time>'
            u'<span class="onda18-imprensa__titulo">%s</span>'
            u'</a></li>'
            % (escapa(mat["url"]), marca, veic, mat["data"],
               data_br(mat["data"]), escapa(mat["titulo"])))


def prefixo_de(html):
    m = re.search(r'(?:src|href)="(/[^"]*?/)wp-content/', html)
    return m.group(1) if m else u"/"


REX_LISTA = re.compile(
    r'(<ul class="onda18-imprensa"[^>]*>)(.*?)(</ul>)', re.S)


def aplicar(pub, materias, logos, dry=False):
    mudou = []
    for rel in PAGINAS:
        p = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(p):
            raise SystemExit(u"falta a página %s" % rel)
        html = ler(p)
        m = REX_LISTA.search(html)
        if not m:
            raise SystemExit(
                u"%s: não achei <ul class=\"onda18-imprensa\">. O markup mudou?" % rel)
        prefixo = prefixo_de(html)
        corpo = u"".join(montar_item(mat, logos[mat["veiculo"]], prefixo)
                         for mat in materias)
        novo = html[:m.start(2)] + corpo + html[m.end(2):]
        if novo == html:
            continue
        if not dry:
            gravar(p, novo)
        mudou.append(rel)
    return mudou


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(argv[1])
    dry = "--dry" in argv
    p_mat, p_vei = MESTRE_MATERIAS, MESTRE_VEICULOS
    for a in argv[2:]:
        if a.startswith("--materias="):
            p_mat = a.split("=", 1)[1]
        elif a.startswith("--veiculos="):
            p_vei = a.split("=", 1)[1]

    materias = carregar(p_mat, "materias")["materias"]
    veiculos = carregar(p_vei, "veiculos")["veiculos"]
    logos = {v["nome"]: v["arquivo"] for v in veiculos}

    print(u"mestre de matérias: %s" % p_mat)
    print(u"mestre de veículos: %s" % p_vei)
    print(u"%d matéria(s) · %d veículo(s) no mestre de logos"
          % (len(materias), len(logos)))

    # --- travas que NÃO silenciam (a razão de o gerador existir) --------------
    problemas = []

    faltando = sorted(set(m["veiculo"] for m in materias) - set(logos))
    if faltando:
        problemas.append(u"veículo(s) de matéria fora do mestre de logos: %s"
                         % u", ".join(faltando))

    for nome, arq in sorted(logos.items()):
        if arq and not os.path.exists(
                os.path.join(pub, DIR_LOGOS.replace("/", os.sep), arq)):
            problemas.append(u"logo declarado e ausente do disco: %s (%s)"
                             % (arq, nome))

    urls = [m["url"] for m in materias]
    dup = sorted(set(u for u in urls if urls.count(u) > 1))
    if dup:
        problemas.append(u"URL duplicada: %s" % u", ".join(dup))

    for m in materias:
        for campo in ("data", "veiculo", "titulo", "url"):
            if not m.get(campo):
                problemas.append(u"matéria sem %s: %s" % (campo, m.get("url", "?")))
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", m.get("data", "")):
            problemas.append(u"data fora do formato aaaa-mm-dd: %s" % m.get("data"))
        if not m.get("url", "").startswith("http"):
            problemas.append(u"url não absoluta: %s" % m.get("url"))

    if problemas:
        for pr in problemas:
            print(u"  ERRO: %s" % pr)
        raise SystemExit(1)

    # ordem canônica: data decrescente, veículo como desempate estável
    materias = sorted(materias, key=lambda x: (x["data"], x["veiculo"]), reverse=True)

    sem_logo = sorted(set(m["veiculo"] for m in materias if not logos[m["veiculo"]]))
    if sem_logo:
        print(u"%d veículo(s) com wordmark de texto (sem asset no mestre): %s"
              % (len(sem_logo), u", ".join(sem_logo)))

    mudou = aplicar(pub, materias, logos, dry=dry)

    # lista pública que a suíte lê para RECALCULAR (nada interno)
    publicada = [{"data": m["data"], "veiculo": m["veiculo"],
                  "titulo": m["titulo"], "url": m["url"],
                  "logo": logos[m["veiculo"]]} for m in materias]
    saida = os.path.join(AQUI, "imprensa-publicada.json")
    if not dry:
        with io.open(saida, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(publicada, ensure_ascii=False, indent=1) + u"\n")

    print(u"%d item(ns) na lista%s" % (len(materias), u" (dry-run)" if dry else u""))
    print(u"páginas alteradas: %s"
          % (u", ".join(mudou) if mudou else u"nenhuma (já estava igual)"))
    if not dry:
        print(u"lista publicada em tools/imprensa-publicada.json")


if __name__ == "__main__":
    main(sys.argv)
