# -*- coding: utf-8 -*-
"""Lambda que transforma o formulario de contato do site em e-mail (issue #226).

Rota: POST /contato na API mirow-carreiras-api (hp813geae7, sa-east-1).
Runtime: python3.12. Sem dependencia externa — boto3 ja vem no runtime.

Por que existe
--------------
O formulario de contato do espelho postava em admin-ajax.php, endpoint do
WordPress que NAO existe no site estatico: media 404 ao vivo em 14/08/2026. A
pagina recebia ~195 views/mes e nao entregava nada.

Por que na AWS e nao num servico de forms
-----------------------------------------
A Mirow ja tem esta API em Sao Paulo, recebendo curriculos — dado mais sensivel
que uma mensagem de contato. Reusar significa: dado nao sai do Brasil, nenhum
operador novo, e nada a acrescentar na politica de privacidade (#225). A
alternativa (Web3Forms) poria um terceiro nos EUA no meio do funil de contato.

Anti-spam
---------
O proprio formulario ja trazia um honeypot do Formidable (item_meta[228],
"If you are human, leave this field blank"). Se vier preenchido, respondemos 200
e descartamos em silencio — bot que recebe erro tenta de novo; bot que recebe
sucesso vai embora. Sem captcha novo, sem segredo novo para guardar.

Variaveis de ambiente
---------------------
  DESTINATARIOS  e-mails separados por virgula (ex.: andreas...,felipe...)
  REMETENTE      endereco verificado no SES (ex.: site@mirow.com.br)
  ALLOW_ORIGINS  origens permitidas no CORS, separadas por virgula

NENHUM segredo aqui: sao todos valores publicos ou de configuracao (R11).
"""
import json
import os
import re

import boto3

ses = boto3.client("ses")

LIMITE = {"nome": 120, "email": 160, "telefone": 40, "empresa": 160, "mensagem": 5000}
RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


def _cors(origem):
    permitidas = [o.strip() for o in os.environ.get("ALLOW_ORIGINS", "").split(",") if o.strip()]
    escolhida = origem if origem in permitidas else (permitidas[0] if permitidas else "")
    return {
        "Access-Control-Allow-Origin": escolhida,
        "Access-Control-Allow-Headers": "content-type",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
        "Content-Type": "application/json; charset=utf-8",
    }


def _resposta(codigo, corpo, origem):
    return {"statusCode": codigo, "headers": _cors(origem),
            "body": json.dumps(corpo, ensure_ascii=False)}


def handler(evento, _contexto):
    cab = {k.lower(): v for k, v in (evento.get("headers") or {}).items()}
    origem = cab.get("origin", "")
    metodo = (evento.get("requestContext", {}).get("http", {}).get("method")
              or evento.get("httpMethod") or "")

    if metodo == "OPTIONS":
        return {"statusCode": 204, "headers": _cors(origem), "body": ""}
    if metodo != "POST":
        return _resposta(405, {"erro": "metodo nao permitido"}, origem)

    try:
        dados = json.loads(evento.get("body") or "{}")
    except ValueError:
        return _resposta(400, {"erro": "corpo invalido"}, origem)

    # Honeypot: bot preencheu o campo que humano nao ve. 200 de proposito —
    # erro ensina o bot a tentar de novo.
    if (dados.get("armadilha") or "").strip():
        return _resposta(200, {"ok": True}, origem)

    campos = {k: (dados.get(k) or "").strip()[:LIMITE[k]] for k in LIMITE}

    faltando = [k for k in ("nome", "email", "mensagem") if not campos[k]]
    if faltando:
        return _resposta(400, {"erro": "campos obrigatorios", "campos": faltando}, origem)
    if not RE_EMAIL.match(campos["email"]):
        return _resposta(400, {"erro": "e-mail invalido"}, origem)

    destinatarios = [e.strip() for e in os.environ["DESTINATARIOS"].split(",") if e.strip()]
    remetente = os.environ["REMETENTE"]

    corpo = (
        u"Nova mensagem pelo formulario de contato do site.\n\n"
        u"Nome:      %(nome)s\n"
        u"E-mail:    %(email)s\n"
        u"Telefone:  %(telefone)s\n"
        u"Empresa:   %(empresa)s\n\n"
        u"Mensagem:\n%(mensagem)s\n"
    ) % campos

    ses.send_email(
        Source=remetente,
        Destination={"ToAddresses": destinatarios},
        # Responder vai direto para quem escreveu, sem passar pelo site.
        ReplyToAddresses=[campos["email"]],
        Message={
            "Subject": {"Data": u"[Site] Contato de %s" % campos["nome"], "Charset": "UTF-8"},
            "Body": {"Text": {"Data": corpo, "Charset": "UTF-8"}},
        },
    )
    return _resposta(200, {"ok": True}, origem)
