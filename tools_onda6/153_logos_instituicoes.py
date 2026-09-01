# -*- coding: utf-8 -*-
"""Onda 79: baixa e normaliza os logotipos das instituicoes dos lideres.

    python tools_onda6/153_logos_instituicoes.py .            # baixa o que falta
    python tools_onda6/153_logos_instituicoes.py . --rebaixar  # baixa tudo de novo

Pedido do Mario em 31/08/2026: "o logo que quero e o da universidade, da empresa"
-- nao um desenho generico de predio ou birrete, que foi o que eu entendi errado
na primeira tentativa.

MESTRE (P3). A tabela LOGOS abaixo e a fonte: nome curto do chip -> URL de origem,
tipo de fonte e nota de licenca. Cada URL foi conferida por mim com curl (200 +
content-type de imagem), nao aceita de relatorio de agente.

TRES REGRAS QUE MOLDARAM A TABELA
---------------------------------
1. **Baixar, nunca linkar.** Logo servido do CDN alheio some quando eles mexem no
   site, e entrega o IP de quem visita a mirow.com.br para um terceiro.
2. **Fair use nao entra.** PUC-Rio e Chicago Booth tem logo na Wikipedia como
   "uso nao-livre" -- e permissao daquele contexto editorial, nao licenca para
   copiar para site comercial. A PUC-Rio foi resolvida indo ao site oficial, que
   serve o brasao em SVG proprio. A Booth ficou SEM logo, de proposito.
3. **User-Agent descritivo.** O Wikimedia devolve 429 para agente generico. Com
   `MirowSiteLogos/1.0 (contato)` as mesmas nove URLs que falhavam responderam
   200. "429 do Wikimedia" quase nunca e bloqueio de IP -- e falta de identificacao.

O QUE FICOU SEM LOGO, e por que isso e resposta e nao falha
-----------------------------------------------------------
Cam, Arcoplan, RC Alvarenga e Chicago Booth. As tres primeiras nao tem arquivo
verificavel (CNPJ ativo, zero presenca digital; e ha homonimos que seriam faceis
de confundir). Chip sem logo cai no icone generico da onda 78 -- o card continua
completo, so nao tem marca. Logo de homonimo seria pior que ausencia.
"""
import io
import os
import subprocess
import sys

UA = "MirowSiteLogos/1.0 (https://mirow.com.br; mario.guazzelli@mirow.com.br)"
DESTINO = os.path.join("wp-content", "uploads", "2026", "08", "onda79", "logos")

# chip -> (url, fonte, nota)
LOGOS = {
    # --- faculdades ---
    u"TU Berlin": ("https://upload.wikimedia.org/wikipedia/commons/3/30/TU-Berlin-Logo.svg",
                   "Wikimedia Commons", u"logo oficial, vermelho da marca"),
    u"Stevens Tech": ("https://upload.wikimedia.org/wikipedia/commons/5/5c/Stevens_inst_tech_textlogo.png",
                      "Wikimedia Commons", u"wordmark oficial; nao ha SVG livre"),
    u"Univ. of Chicago": ("https://upload.wikimedia.org/wikipedia/commons/0/05/University_of_Chicago_wordmark.svg",
                          "Wikimedia Commons", u"wordmark oficial"),
    u"FGV EPGE": ("https://upload.wikimedia.org/wikipedia/commons/c/cf/Logo_FGV_-_Funda%C3%A7%C3%A3o_Getulio_Vargas.png",
                  "Wikimedia Commons", u"logo institucional da FGV (CC-BY-SA-4.0); a EPGE nao tem marca propria livre"),
    u"PUC-Rio": ("https://www.puc-rio.br/imagens/brasao_preto_horizontal.svg",
                 u"site oficial puc-rio.br", u"brasao horizontal servido pela home; evita o arquivo fair-use da Wikipedia"),
    u"IME": ("https://www.ime.eb.mil.br/images/logo.png",
             u"site oficial ime.eb.mil.br", u"logo do cabecalho do site"),
    u"Univ. de Barcelona": ("https://upload.wikimedia.org/wikipedia/commons/6/60/Universit%C3%A4t_Barcelona.svg",
                            "Wikimedia Commons", u"brasao institucional; licenca a conferir na pagina do arquivo"),
    u"UFRJ": ("https://ufrj.br/wp-content/themes/arion-new-home/assets/images/ufrj-horizontal-negativa.png",
              u"site oficial ufrj.br", u"versao NEGATIVA (branca) -- cai bem no card escuro"),
    u"Univ. Karlsruhe": ("https://upload.wikimedia.org/wikipedia/commons/3/3a/Logo_KIT.svg",
                         "Wikimedia Commons", u"o KIT e o sucessor da Universitat Karlsruhe (fusao de 2009)"),
    u"Univ. Mannheim": ("https://upload.wikimedia.org/wikipedia/commons/4/48/Uni-mannheim.svg",
                        "Wikimedia Commons", u"selo oficial, azul escuro"),
    u"Carnegie Mellon (Tepper)": ("https://upload.wikimedia.org/wikipedia/commons/f/f3/Carnegie_Mellon_University_wordmark.svg",
                                  "Wikimedia Commons", u"wordmark da CMU; a Tepper nao tem marca propria livre"),
    u"UnB": ("https://upload.wikimedia.org/wikipedia/commons/9/9e/Webysther_20160322_-_Logo_UnB.svg",
             "Wikimedia Commons", u"marca institucional"),
    u"Univ. Bremen": ("https://www.uni-bremen.de/_assets/8ec6f74154680cbbd6366024eea31e0b/Images/logo_ub_2021.png",
                      u"site oficial uni-bremen.de", u"logo institucional 2021"),
    # --- empresas ---
    u"McKinsey": ("https://upload.wikimedia.org/wikipedia/commons/e/e2/McKinsey_and_Company_Logo_1.svg",
                  "Wikimedia Commons", u"wordmark oficial"),
    u"Booz Allen": ("https://upload.wikimedia.org/wikipedia/commons/8/83/Booz_Allen_Hamilton_logo.svg",
                    "Wikimedia Commons", u"wordmark oficial"),
    u"Monitor Deloitte": ("https://upload.wikimedia.org/wikipedia/commons/7/73/Monitor_Deloitte_logo.png",
                          "Wikimedia Commons", u"logo da propria unidade Monitor Deloitte"),
    u"Arthur D. Little": ("https://upload.wikimedia.org/wikipedia/commons/b/b2/Arthur-D.-Little-Logo.svg",
                          "Wikimedia Commons", u"wordmark oficial"),
    u"Schlumberger": ("https://upload.wikimedia.org/wikipedia/commons/d/d6/SLB_Logo_2022.svg",
                      "Wikimedia Commons", u"marca ATUAL (SLB, 2022); o Raoni trabalhou la quando era Schlumberger"),
    u"Enel Chile": ("https://upload.wikimedia.org/wikipedia/commons/2/22/Enel_Group_logo.svg",
                    "Wikimedia Commons", u"marca do grupo Enel; a Chilectra virou Enel Distribucion Chile"),
    u"Aracruz Celulose": ("https://upload.wikimedia.org/wikipedia/commons/4/47/Aracruz-Logo.svg",
                          "Wikimedia Commons", u"logo historico: a empresa foi incorporada pela Suzano em 2009"),
    u"IMP": ("https://cdn.prod.website-files.com/616aa47666f45f24279a2ff9/61a8a11654d4502af7ebbba3_imp-logo-mag-nosignet.svg",
             u"site oficial impconsulting.com", u"logo atual"),
    u"Malik": ("https://www.malik-management.com/wp-content/uploads/2018/09/Logo_malik_weiss-klein3.png",
               u"site oficial malik-management.com", u"variante BRANCA -- cai bem no card escuro"),
    # o arquivo se chama .png na origem mas o otimizador do site entrega WEBP --
    # conferido pelos bytes iniciais (RIFF/WEBP), nao pela extensao. Salvo como
    # .webp: arquivo que mente sobre o proprio tipo e defeito esperando acontecer.
    u"Catavento": ("https://catavento.biz/wp-content/themes/catavento/images/logo.png",
                   u"site oficial catavento.biz", u"servido como WebP pelo otimizador do site"),
    u"Consórcio Rio (CIRJ)": ("https://upload.wikimedia.org/wikipedia/commons/a/a1/Ch2m_logo.png",
                              "Wikimedia Commons", u"o consorcio nao tem marca propria; usado o da CH2M Hill, que o formou"),
    # --- onda 79b: instituicoes do Elmar Gans e do Joao Daniel Ramos, que o Mario
    # pediu depois ("cade???"). Os dois nao estao no cadastro de lideres (PAGINAS),
    # entao o dado deles NAO alimenta o JSON-LD -- so o chip do card.
    u"WHU": ("https://upload.wikimedia.org/wikipedia/commons/f/f0/WHU_Logo.svg",
             "Wikimedia Commons", u"WHU - Otto Beisheim School of Management"),
    u"UMass Amherst": ("https://upload.wikimedia.org/wikipedia/commons/3/32/University_of_Massachusetts_Amherst_wordmark.svg",
                       "Wikimedia Commons", u"wordmark oficial"),
    u"LMU München": ("https://upload.wikimedia.org/wikipedia/commons/0/06/LMU_Muenchen_Logo.svg",
                     "Wikimedia Commons", u"Ludwig-Maximilians-Universitat Munchen"),
    u"FECAP": ("https://upload.wikimedia.org/wikipedia/commons/6/69/FECAP_logo.jpg",
               "Wikimedia Commons", u"unico arquivo disponivel e JPG (com fundo), nao PNG transparente"),
    u"UFPR": ("https://upload.wikimedia.org/wikipedia/commons/b/bc/Logo_oficial_da_UFPR_%28fundo_branco%29.svg",
              "Wikimedia Commons", u"versao oficial com fundo branco"),
    u"Kumon": ("https://upload.wikimedia.org/wikipedia/commons/8/82/Kumon_Method_Logo.svg",
               "Wikimedia Commons", u"marca do metodo Kumon"),
    u"Dexco": ("https://upload.wikimedia.org/wikipedia/commons/c/c4/Logotipo_da_Dexco.svg",
               "Wikimedia Commons", u"marca atual (a Duratex virou Dexco em 2021)"),
}

# Sem arquivo, de proposito. Cada um cai no icone generico da onda 78.
SEM_LOGO = {
    u"Chicago Booth": u"so existe como fair use na Wikipedia; o site oficial nao expoe URL direta",
    u"Cam": u"nome generico demais; nenhum site oficial ou marca verificavel -- risco de homonimo",
    u"Arcoplan": u"CNPJ ativo em Brasilia, sem presenca digital; o homonimo de moveis planejados foi descartado",
    u"RC Alvarenga": u"nao localizada com esse nome; os 'RC Engenharia' encontrados sao outras empresas",
    u"Ampla": u"virou Enel Distribuicao Rio em 2016; nao ha arquivo do logo historico verificavel",
}


def slug(nome):
    # o "ü" de "LMU Munchen" escapou da primeira versao desta tabela e gerou
    # `lmu-munchen.svg` com o trema no NOME DO ARQUIVO -- R5 do CLAUDE.md: nome de
    # arquivo e ASCII, sempre. Agora a normalizacao e por unicodedata, que cobre
    # qualquer acento, e nao por lista escrita a mao.
    fora = u"ÁÀÃÂÉÊÍÓÔÕÚÇáàãâéêíóôõúç"
    dentro = u"AAAAEEIOOOUCaaaaeeiooouc"
    import unicodedata
    s = unicodedata.normalize("NFKD", nome)
    s = u"".join(c for c in s if not unicodedata.combining(c))
    s = u"".join(dentro[fora.index(c)] if c in fora else c for c in s)
    s = u"".join(c if c.isalnum() else "-" for c in s.lower())
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


def extensao_real(path):
    """O que o arquivo E, pelos bytes -- nao pelo que a URL prometeu.

    As assinaturas sao montadas com bytes([...]) de proposito: este arquivo ja
    foi escrito uma vez por heredoc e o 0x89 do PNG entrou CRU no meio da string,
    quebrando o parser. E o erro 13 do CLAUDE.md (familia backslash) aparecendo
    em bytes em vez de regex.
    """
    b = io.open(path, "rb").read(16)
    PNG = bytes([0x89]) + b"PNG" + bytes([0x0D, 0x0A, 0x1A, 0x0A])
    JPG = bytes([0xFF, 0xD8])
    if b[:8] == PNG:
        return ".png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return ".webp"
    if b[:2] == JPG:
        return ".jpg"
    if b.lstrip()[:5] in (b"<?xml", b"<svg ") or b"<svg" in b:
        return ".svg"
    return None


def baixar(url, destino):
    r = subprocess.run(["curl", "-sSL", "--max-time", "40", "-A", UA, "-o", destino,
                        "-w", "%{http_code} %{content_type}"], capture_output=True)
    # curl com -o precisa da URL no fim
    r = subprocess.run(["curl", "-sSL", "--max-time", "40", "-A", UA, "-o", destino,
                        "-w", "%{http_code}|%{content_type}", url], capture_output=True)
    saida = r.stdout.decode("utf-8", "replace").strip()
    code, _, ctype = saida.partition("|")
    return code, ctype


def main(raiz, rebaixar=False):
    pub = os.path.join(os.path.abspath(raiz), "public")
    pasta = os.path.join(pub, DESTINO)
    if not os.path.isdir(pasta):
        os.makedirs(pasta)
    novos, ja, falhas = 0, 0, []
    for nome, (url, _fonte, _nota) in sorted(LOGOS.items()):
        # extensao provisoria pela URL; corrigida abaixo pelos BYTES do arquivo
        ext = ".svg" if ".svg" in url.lower() else (".png" if ".png" in url.lower() else ".img")
        alvo = os.path.join(pasta, slug(nome) + ext)
        if os.path.exists(alvo) and not rebaixar:
            ja += 1
            continue
        code, ctype = baixar(url, alvo)
        if code != "200" or "image" not in ctype:
            falhas.append((nome, code, ctype))
            if os.path.exists(alvo):
                os.remove(alvo)
            continue
        real = extensao_real(alvo)
        if real and not alvo.endswith(real):
            certo = os.path.splitext(alvo)[0] + real
            os.replace(alvo, certo)
            alvo = certo
        novos += 1
        print(u"  %-26s %s  %s" % (nome, code, os.path.basename(alvo)))
    print(u"153: %d baixado(s), %d ja existia(m), %d falha(s); %d sem logo por decisao"
          % (novos, ja, len(falhas), len(SEM_LOGO)))
    for nome, code, ctype in falhas:
        print(u"   FALHOU %-24s %s %s" % (nome, code, ctype))
    return len(falhas)


if __name__ == "__main__":
    args = sys.argv[1:]
    raiz = args[0] if args and not args[0].startswith("--") else "."
    sys.exit(main(raiz, "--rebaixar" in args))
