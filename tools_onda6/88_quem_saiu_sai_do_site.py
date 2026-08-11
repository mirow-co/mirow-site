# -*- coding: utf-8 -*-
"""88 — onda 33, S-118 (#66 e #81): quem saiu sai do site.

Uso:
    python tools_onda6/88_quem_saiu_sai_do_site.py <raiz-que-contem-public> [--dry-run]

Mandato do Andreas (jul/2026): "tirar quem saiu". A asserção L01 já garantia que os
ex-líderes não apareciam nas homes nem no quadro de líderes — mas eles continuavam
no site de quatro outras formas, todas acessíveis por URL direta e indexáveis:

  1. 12 páginas de PERFIL próprias (pt/lider, en/leader, de/lider × Giulia Turcato,
     Lucas Duarte, Mariana Nakagawa, Matheus Strapasson), com foto, cargo e bio.
  2. 16 stubs de redirect apontando para essas 12 (herança da S-107).
  3. 4 MODAIS completos na en/homepage (Marcelo Soares, Marcelo Massarente,
     Lucas Santiago, Fernando Fabbris) — órfãos: medido, 0 referência ao id de
     cada modal fora dele mesmo. HTML morto que só o robô lê.
  4. AUTORIA: 8 artigos em PT com Giulia Turcato como autora em `<meta name=author>`,
     em `twitter:data1` e no JSON-LD do Yoast (nó Article + nó Person com Gravatar),
     mais uma bio na página da transição climática afirmando, no PRESENTE, que
     Fernando Fabbris "é sócio-associado e líder da prática".

Decisão do Mario (04/08), quando perguntado se a autoria estava no escopo:
"para que precisamos dos perfis dessas outras pessoas? eu já decidi que eles
sairam. pode mudar autor para andreas e felipe em todos."

O que faz, na ordem:
  1. Reaponta os 16 stubs direto para a página de líderes do idioma — sem isso o
     visitante daria dois saltos (stub -> perfil, que agora também é stub), o que a
     asserção S107 proíbe.
  2. Grava stub de redirect nas 12 páginas de perfil, destino = página de líderes.
  3. Remove os 4 modais da en/homepage por varredura de `<div>` balanceada.
  4. Troca a autoria dos 8 artigos para Andreas Mirow e Felipe Diniz (os dois, como
     o Mario pediu) e reescreve a linha da bio do Fernando no passado.

NÃO toca: `administrador.mirow` (22 páginas), `Elpidio Lomeu` (6) e `João Ramos` (1)
como autores. São conta de CMS e o dev externo — mesma classe de defeito, mas ninguém
que "saiu": decisão editorial própria, registrada como achado no fim da onda.

Idempotente: no segundo run os stubs já batem, os modais já não existem e a autoria
já é a nova — reporta 0 mudança em tudo.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

MARK = "onda33:quem-saiu"

# Os que saíram e têm página de perfil própria no espelho.
SLUGS = ["giulia-turcato", "lucas-duarte", "mariana-nakagawa", "matheus-strapasson"]

# Os 4 modais órfãos da en/homepage (#81).
MODAIS = ["Marcelo Soares", "Marcelo Massarente", "Lucas Santiago", "Fernando Fabbris"]

# Página de líderes por idioma — destino de todo redirect desta onda.
LIDERES = {
    "pt": "/mirow-site/pt/sobre-nos/lideres/",
    "en": "/mirow-site/en/about-us/leaders/",
    "de": "/mirow-site/de/ueber-uns/fuehrungskraefte/",
}

TEXTO = {
    "pt": (u"Esta pessoa não faz mais parte da equipe.", u"Ver os líderes da Mirow &amp; Co."),
    "en": (u"This person is no longer part of the team.", u"See the leaders of Mirow &amp; Co."),
    "de": (u"Diese Person gehört nicht mehr zum Team.", u"Die Führungskräfte von Mirow &amp; Co."),
}

# Autoria nova (decisão do Mario). Os @id apontam para as páginas de líder reais.
AUTORES = [
    (u"Andreas Mirow", "/mirow-site/pt/lider/andreas-mirow/"),
    (u"Felipe Diniz", "/mirow-site/pt/lider/felipe-diniz/"),
]
AUTOR_META = u" e ".join(n for n, _u in AUTORES)

EX_AUTOR = u"Giulia Turcato"


def idioma_do_caminho(rel):
    """Idioma pelo primeiro segmento; sem prefixo de idioma o espelho serve PT."""
    seg = rel.split("/")[0]
    return seg if seg in ("pt", "en", "de") else "pt"


# Bloco de medicao que os stubs da S-107 já carregam (PR #12, do Marcell). Os 28
# stubs desta onda o carregam igual, para a assercao M01 seguir cobrando as 285
# paginas em vez de abrir excecao.
# ATENCAO: nos 125 stubs da S-107 este src saiu como "/wp-content/..." — SEM o
# prefixo /mirow-site/ — porque o `base_prefix` do helper deduz o prefixo de uma
# referencia a wp-content que o stub minimo nao tem. Lá o asset 404a e a M01 passa
# do mesmo jeito (ela procura o nome do arquivo, nao o caminho). Aqui vai com o
# prefixo certo; o bug dos outros 125 esta registrado como achado da onda 33.
MEDICAO = (
    u'  <!-- Medicao Mirow (GA4) - issue mirow-marketing#3. Config e eventos em '
    u'wp-content/uploads/2026/07/onda6/onda31-medicao.js -->\n'
    u'  <script src="/mirow-site/wp-content/uploads/2026/07/onda6/'
    u'onda31-medicao.js"></script>\n'
    u'  <script async src="https://www.googletagmanager.com/gtag/js?'
    u'id=G-5VTS0MZK79"></script>\n')


def stub(lang):
    destino = LIDERES[lang]
    frase, botao = TEXTO[lang]
    return (u'<!DOCTYPE html><html lang="%s"><head><meta charset="utf-8">\n'
            u'%s'
            u'<!-- %s: pagina de quem saiu da firma — redireciona para os lideres -->\n'
            u'<meta http-equiv="refresh" content="0;url=%s">\n'
            u'<link rel="canonical" href="%s">\n'
            u'<meta name="robots" content="noindex,follow">\n'
            u'<title>Mirow &amp; Co.</title></head>\n'
            u'<body><p>%s <a href="%s">%s</a>.</p></body></html>\n'
            % (lang, MEDICAO, MARK, destino, destino, frase, destino, botao))


def eh_stub(rel, html):
    if rel == "index.html":
        return True
    return 'http-equiv="refresh"' in html and '<footer class="footer">' not in html


def paginas_index(pub):
    """[(rel, path, html)] de todo index.html sob public/."""
    out = []
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            p = os.path.join(dirpath, nome)
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            out.append((rel, p, ler(p)))
    out.sort()
    return out


def remove_div_balanceada(html, inicio):
    """Remove o <div> que começa em `inicio` junto com tudo até o </div> que o fecha.

    Varredura de profundidade sobre `<div` / `</div>`: o modal tem 6 níveis de div
    aninhada, então cortar no primeiro `</div>` deixaria lixo desbalanceado na
    página. Devolve o html novo, ou None se não fechar (aí é melhor não mexer).
    """
    prof = 0
    i = inicio
    for m in re.finditer(r'<div\b|</div>', html[inicio:]):
        if m.group(0) == "</div>":
            prof -= 1
            if prof == 0:
                fim = inicio + m.end()
                return html[:inicio] + html[fim:]
        else:
            prof += 1
        i = inicio + m.end()
    return None


def troca_autoria(html):
    """Autoria de Giulia -> Andreas e Felipe, nas 4 formas em que o Yoast a escreve."""
    novo = html

    # 1. <meta name="author"> e o "Written by" do Twitter
    novo = novo.replace(u'<meta name="author" content="%s" />' % EX_AUTOR,
                        u'<meta name="author" content="%s" />' % AUTOR_META)
    novo = novo.replace(u'<meta name="twitter:data1" content="%s" />' % EX_AUTOR,
                        u'<meta name="twitter:data1" content="%s" />' % AUTOR_META)

    # 2. JSON-LD, nó Article: "author":{"name":"...","@id":"...person/<hash>"}
    #    vira um array com os dois autores. O @id de cada um passa a ser a página
    #    de líder — que existe de verdade, ao contrário do hash do Gravatar.
    autores_json = u",".join(
        u'{"name":"%s","@id":"%s"}' % (n, u) for n, u in AUTORES)
    novo = re.sub(
        r'"author":\{"name":"%s","@id":"[^"]*"\}' % re.escape(EX_AUTOR),
        u'"author":[%s]' % autores_json,
        novo)

    # 3. JSON-LD, nó Person da Giulia (com Gravatar e url /author/giulia-turcato/,
    #    que nem existe no espelho) -> um nó Person por autor novo, sem imagem.
    pessoas_json = u",".join(
        u'{"@type":"Person","@id":"%s","name":"%s","url":"%s"}' % (u, n, u)
        for n, u in AUTORES)
    novo = re.sub(
        r'\{"@type":"Person","@id":"[^"]*","name":"%s".*?"url":"[^"]*"\}'
        % re.escape(EX_AUTOR),
        pessoas_json,
        novo, flags=re.S)

    return novo


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    dry = "--dry-run" in sys.argv

    todas = paginas_index(pub)

    # ---- passos 1 e 2: as 28 páginas de quem saiu viram redirect para os líderes.
    # Não há distinção a fazer entre "perfil" e "stub que aponta para o perfil":
    # as duas viram o MESMO stub, e o visitante chega aos líderes num salto.
    n_stub = 0
    alvos = []
    for rel, p, h in todas:
        low = rel.lower()
        if not any(sl in low for sl in SLUGS):
            continue
        lang = idioma_do_caminho(rel)
        conteudo = stub(lang)
        alvos.append((rel, "stub" if eh_stub(rel, h) else "CONTEUDO"))
        if h == conteudo:
            continue
        n_stub += 1
        if not dry:
            with io.open(p, "w", encoding="utf-8", newline="") as f:
                f.write(conteudo)
    print("paginas de quem saiu -> redirect para os lideres: %d de %d%s"
          % (n_stub, len(alvos), " (dry-run)" if dry else ""))
    for rel, tipo in alvos:
        print("    %-8s %s" % (tipo, rel))

    # ---- passo 3: os 4 modais orfaos da en/homepage
    rel_home = "en/homepage/index.html"
    p_home = os.path.join(pub, rel_home.replace("/", os.sep))
    h = ler(p_home)
    novo = h
    removidos = []
    for nome in MODAIS:
        while True:
            i = novo.find(nome)
            if i < 0:
                break
            j = novo.rfind('<div class="modal fade" id="', 0, i)
            if j < 0:
                print("  AVISO: %r na en/homepage fora de modal — nao removido" % nome)
                break
            cortado = remove_div_balanceada(novo, j)
            if cortado is None:
                print("  AVISO: modal de %r nao fecha — nao removido" % nome)
                break
            novo = cortado
            removidos.append(nome)
    print("modais de ex-lider removidos da en/homepage: %d%s"
          % (len(removidos), " (dry-run)" if dry else ""))
    if novo != h and not dry:
        gravar(p_home, novo)

    # ---- passo 4: autoria dos artigos
    n_autor = 0
    for rel, p, h in todas:
        if EX_AUTOR not in h:
            continue
        if any(sl in rel.lower() for sl in SLUGS):
            continue          # a propria pagina de perfil, ja virou stub
        novo = troca_autoria(h)
        if novo == h:
            continue
        n_autor += 1
        print("    autoria -> %s: %s" % (AUTOR_META, rel))
        if not dry:
            gravar(p, novo)
    print("artigos com autoria trocada: %d%s" % (n_autor, " (dry-run)" if dry else ""))

    # ---- passo 4b: a bio do Fernando Fabbris no PRESENTE
    # "Fernando Fabbris e socio-associado e lider da pratica de Adaptacao Climatica"
    # num site no ar afirma que ele lidera a pratica hoje. Vira passado.
    n_bio = 0
    for rel, p, h in todas:
        if u"Fernando Fabbris" not in h or rel == rel_home:
            continue
        novo = re.sub(
            u'(<strong><mark[^>]*>Fernando Fabbris</mark></strong>)\\s*é\\s*'
            u'sócio-associado e líder da prática de Adaptação Climática',
            u'\\1 foi sócio-associado e líder da prática de Adaptação Climática',
            h)
        if novo == h:
            continue
        n_bio += 1
        print("    bio no passado: %s" % rel)
        if not dry:
            gravar(p, novo)
    print("bios corrigidas para o passado: %d%s" % (n_bio, " (dry-run)" if dry else ""))


if __name__ == "__main__":
    main()
