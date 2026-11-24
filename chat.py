"""Envía mensajes internos del chat de Odoo 17 (Conversaciones / Discuss) por JSON-RPC.

- Mensaje directo (chat 1 a 1) a uno o varios usuarios, por login.
- Mensaje a un canal existente, por nombre.

El mensaje sale como el usuario USERNAME. La contraseña (o API key, recomendado) se lee de la variable de entorno
ODOO_PASSWORD:
    export ODOO_PASSWORD='...'
    python chat.py
"""
import os

import requests

URL = "https://heyvet-staging-41803742.dev.odoo.com"
DB = "heyvet-staging-41803742"
USERNAME = "steve@logicpool.ai"                 # usuario que envía
PASSWORD = os.environ.get("ODOO_PASSWORD", "")  # contraseña o API key de USERNAME

RECIPIENT_LOGINS = ["abra@heyvet.pe"]  # chats directos: logins de los destinatarios ([] = ninguno)
CHANNEL_NAMES = []                               # canales: nombres exactos, p. ej. ["general"] ([] = ninguno)
MESSAGE = "Hola desde JSON-RPC"                  # texto plano (Odoo escapa el HTML que llega por RPC)


def jsonrpc(service, method, *args, timeout=60):
    """Llama a un servicio de Odoo por JSON-RPC y devuelve el resultado; levanta los errores de Odoo."""
    payload = {"jsonrpc": "2.0", "method": "call", "id": 1,
               "params": {"service": service, "method": method, "args": args}}
    response = requests.post(f"{URL}/jsonrpc", json=payload, timeout=timeout)
    response.raise_for_status()
    body = response.json()
    if body.get("error"):
        error = body["error"]
        raise RuntimeError(error.get("data", {}).get("message") or error.get("message"))
    return body["result"]


def execute(uid, model, method, *args, **kwargs):
    """Ejecuta un método de modelo (execute_kw) como el usuario autenticado."""
    return jsonrpc("object", "execute_kw", DB, uid, PASSWORD, model, method, list(args), kwargs)


def post(uid, channel_id, message):
    """Publica el mensaje en el canal o chat; devuelve el id del mail.message."""
    return execute(uid, "discuss.channel", "message_post", [channel_id],
                   body=message, message_type="comment", subtype_xmlid="mail.mt_comment")


def send_direct_message(uid, recipient_login, message):
    """Abre (o crea) el chat 1 a 1 con el destinatario y publica el mensaje."""
    users = execute(uid, "res.users", "search_read", [("login", "=", recipient_login)],
                    fields=["partner_id"], limit=1)
    if not users:
        raise RuntimeError(f"No existe el usuario {recipient_login}")
    channel = execute(uid, "discuss.channel", "channel_get", partners_to=[users[0]["partner_id"][0]])
    return post(uid, channel["id"], message)


def send_channel_message(uid, channel_name, message):
    """Publica el mensaje en un canal existente (el usuario que envía debe ser miembro o poder unirse)."""
    channels = execute(uid, "discuss.channel", "search_read",
                       [("name", "=", channel_name), ("channel_type", "=", "channel")], fields=["id"], limit=1)
    if not channels:
        raise RuntimeError(f"No existe el canal {channel_name}")
    return post(uid, channels[0]["id"], message)


def main():
    if not PASSWORD:
        raise SystemExit("Defina la variable de entorno ODOO_PASSWORD (contraseña o API key de %s)" % USERNAME)
    uid = jsonrpc("common", "login", DB, USERNAME, PASSWORD)
    if not uid:
        raise SystemExit("Credenciales inválidas")

    for login in RECIPIENT_LOGINS:
        print(f"Mensaje {send_direct_message(uid, login, MESSAGE)} enviado a {login}")
    for name in CHANNEL_NAMES:
        print(f"Mensaje {send_channel_message(uid, name, MESSAGE)} enviado al canal {name}")


if __name__ == "__main__":
    main()
