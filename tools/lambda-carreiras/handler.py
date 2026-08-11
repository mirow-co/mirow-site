"""Assinador de candidaturas do site novo -> plataforma de recrutamento.

O site (GitHub Pages, estatico) nao pode guardar o segredo HMAC. Esta funcao:
  1. valida o token hCaptcha (header X-Captcha-Token) contra a hCaptcha siteverify;
  2. assina o corpo EXATO (multipart cru) com HMAC-SHA256;
  3. repassa ao endpoint /webhook/import/cadidates/start da plataforma de recrutamento.

Robustez: assina/repassa os BYTES CRUS do corpo, sem parsear multipart -- a assinatura
sempre casa com o que a plataforma recebe. O token do captcha viaja em HEADER, fora do
corpo, entao nao afeta a assinatura. Fail-closed em toda etapa.

Env vars:
  START_HMAC_SECRET  - segredo compartilhado com a view /start (obrigatorio)
  HCAPTCHA_SECRET    - segredo do hCaptcha p/ siteverify (obrigatorio; use a chave de teste
                       0x0000000000000000000000000000000000000000 enquanto nao houver conta)
  START_URL          - default https://recruiting-platform.mirow.com.br/webhook/import/cadidates/start
  ALLOW_ORIGIN       - CORS; default *
"""
import base64
import hashlib
import hmac
import json
import os
import urllib.parse
import urllib.request

START_URL = os.environ.get(
    "START_URL",
    "https://recruiting-platform.mirow.com.br/webhook/import/cadidates/start",
)
HCAPTCHA_VERIFY = "https://api.hcaptcha.com/siteverify"
# Lista de origens permitidas (CORS). Ecoa a origem do request se estiver na lista.
ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("ALLOW_ORIGINS", "*").split(",") if o.strip()
]


def _cors(origin):
    if "*" in ALLOWED_ORIGINS:
        allow = "*"
    elif origin and origin in ALLOWED_ORIGINS:
        allow = origin
    else:
        allow = ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else "null"
    return {
        "Access-Control-Allow-Origin": allow,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Captcha-Token",
        "Vary": "Origin",
    }


def _resp(status, body, origin=None, extra=None):
    h = {"Content-Type": "application/json"}
    h.update(_cors(origin))
    if extra:
        h.update(extra)
    return {"statusCode": status, "headers": h, "body": json.dumps(body)}


def _verify_captcha(token, remoteip=None):
    secret = os.environ.get("HCAPTCHA_SECRET")
    if not secret:
        return False, "captcha_not_configured"
    if not token:
        return False, "captcha_missing"
    data = urllib.parse.urlencode(
        {"secret": secret, "response": token, **({"remoteip": remoteip} if remoteip else {})}
    ).encode()
    try:
        with urllib.request.urlopen(HCAPTCHA_VERIFY, data=data, timeout=10) as r:
            res = json.loads(r.read().decode("utf-8"))
        return bool(res.get("success")), ("ok" if res.get("success") else "captcha_rejected")
    except Exception as e:  # noqa: BLE001
        return False, "captcha_unreachable:" + str(e)[:60]


def handler(event, context):
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    origin = headers.get("origin")
    method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or "POST"
    )
    if method == "OPTIONS":
        return _resp(204, {}, origin)
    if method != "POST":
        return _resp(405, {"error": "method_not_allowed"}, origin)

    secret = os.environ.get("START_HMAC_SECRET")
    if not secret:
        return _resp(500, {"error": "server_misconfigured"}, origin)

    remoteip = event.get("requestContext", {}).get("http", {}).get("sourceIp")
    ok, why = _verify_captcha(headers.get("x-captcha-token"), remoteip)
    if not ok:
        return _resp(403, {"error": "captcha_failed", "detail": why}, origin)

    body = event.get("body") or ""
    raw = base64.b64decode(body) if event.get("isBase64Encoded") else body.encode("utf-8")
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
            upstream_status, upstream_body = r.status, r.read(500).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        upstream_status, upstream_body = e.code, e.read(500).decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        return _resp(502, {"error": "upstream_unreachable", "detail": str(e)[:120]}, origin)

    if upstream_status == 200:
        return _resp(200, {"ok": True}, origin)
    return _resp(
        502 if upstream_status >= 500 else 400,
        {"error": "upstream_rejected", "upstream_status": upstream_status,
         "upstream_body": upstream_body[:200]},
        origin,
    )
