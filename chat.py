"""Sends a direct (1 to 1) Discuss chat message in Odoo 17 through JSON-RPC (discuss.channel)."""
"""
Datos de usuario secundario
coordinacioncx@heyvet.pe
123456
"""


import os
import requests

# Configuration
URL = "https://heyvet-staging-39706532.dev.odoo.com"
DB = "heyvet-staging-39706532"
USERNAME = "steve@logicpool.ai"  # User who sends the message
# user_passwird = 123456
PASSWORD = "0fc8379fda8e51ded0039e89ea564b2a7465f17c"  # API key recommended (Preferences > Account Security > New API Key)

RECIPIENT_LOGIN = "coordinacioncx@heyvet.pe"  # Login of the user who receives the message
MESSAGE = "Hello from JSON-RPC"  # HTML allowed


def jsonrpc(service, method, *args, timeout=60):
    """Calls an Odoo service through JSON-RPC and returns its result; raises Odoo errors."""
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {"service": service, "method": method, "args": args},
        "id": 1,
    }
    response = requests.post(f"{URL}/jsonrpc", json=payload, timeout=timeout)
    response.raise_for_status()
    body = response.json()
    if body.get("error"):
        error = body["error"]
        raise RuntimeError(error.get("data", {}).get("message") or error.get("message"))
    return body["result"]


def execute(uid, model, method, *args, **kwargs):
    """Runs a model method (execute_kw) as the authenticated user."""
    return jsonrpc("object", "execute_kw", DB, uid, PASSWORD, model, method, list(args), kwargs)


def send_direct_message(uid, recipient_login, message):
    """Gets (or creates) the 1 to 1 chat with the recipient and posts the message as the authenticated user."""
    recipients = execute(uid, "res.users", "search_read", [("login", "=", recipient_login)],
                         fields=["partner_id"], limit=1)
    if not recipients:
        raise RuntimeError(f"User not found: {recipient_login}")
    partner_id = recipients[0]["partner_id"][0]

    channel = execute(uid, "discuss.channel", "channel_get", partners_to=[partner_id])
    return execute(uid, "discuss.channel", "message_post", [channel["id"]],
                   body=message, message_type="comment", subtype_xmlid="mail.mt_comment")


def main():
    if not PASSWORD:
        raise SystemExit("Set the ODOO_API_KEY environment variable (or PASSWORD in the configuration)")

    uid = jsonrpc("common", "login", DB, USERNAME, PASSWORD)
    if not uid:
        raise SystemExit("Invalid credentials")

    message = send_direct_message(uid, RECIPIENT_LOGIN, MESSAGE)
    print(f"Message {message.get('id') if isinstance(message, dict) else message} sent to {RECIPIENT_LOGIN}")


if __name__ == "__main__":
    main()
