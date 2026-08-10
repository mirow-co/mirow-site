"""Assinador de candidaturas do site novo -> plataforma de recrutamento.

O site (GitHub Pages, estatico) nao pode guardar o segredo HMAC. Esta funcao recebe
o multipart do formulario /carreiras, assina o corpo EXATO com HMAC-SHA256 e repassa
ao endpoint /webhook/import/cadidates/start da plataforma de recrutamento.

Robustez: assina e repassa os BYTES CRUS do corpo, sem parsear multipart -- a assinatura
sempre casa com o que a plataforma recebe. Fail-closed: sem segredo configurado, 500.

Env vars:
  START_HMAC_SECRET  - segredo compartilhado com a view (obrigatorio)
  START_URL          - default https://recruiting-platform.mirow.com.br/webhook/import/cadidates/start
  ALLOW_ORIGIN       - CORS; default https://mirow.com.br
"""
import base64
import hashlib
import hmac
import json
import os
import urllib.request

START_URL = os.environ.get(
    "START_URL",
    "https://recruiting-platform.mirow.com.br/webhook/import/cadidates/start",
)
ALLOW_ORIGIN = os.environ.get("ALLOW_ORIGIN", "https://mirow.com.br")


def _cors():
    return {
        "Access-Control-Allow-Origin": ALLOW_ORIGIN,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Vary": "Origin",
    }


def _resp(status, body, extra=None):
    h = {"Content-Type": "application/json"}
    h.update(_cors())
    if extra:
        h.update(extra)
    return {"statusCode": status, "headers": h, "body": json.dumps(body)}


def handler(event, context):
    method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or "POST"
    )
    if method == "OPTIONS":
        return _resp(204, {})

    if method != "POST":
        return _resp(405, {"error": "method_not_allowed"})

    secret = os.environ.get("START_HMAC_SECRET")
    if not secret:
        return _resp(500, {"error": "server_misconfigured"})

    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(body)
    else:
        raw = body.encode("utf-8")

    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    content_type = headers.get("content-type", "application/octet-stream")

    signature = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()

    req = urllib.request.Request(
        START_URL,
        data=raw,
        method="POST",
        headers={"Content-Type": content_type, "X-Start-Signature": signature},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            upstream_status = r.status
            upstream_body = r.read(500).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        upstream_status = e.code
        upstream_body = e.read(500).decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return _resp(502, {"error": "upstream_unreachable", "detail": str(e)[:120]})

    if upstream_status == 200:
        return _resp(200, {"ok": True})
    return _resp(
        502 if upstream_status >= 500 else 400,
        {"error": "upstream_rejected", "upstream_status": upstream_status,
         "upstream_body": upstream_body[:200]},
    )
