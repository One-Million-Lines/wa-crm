"""Mock Meta WhatsApp Business API client.

All methods return mock/simulated responses matching the Meta Graph API structure.
Replace with real HTTP calls to graph.facebook.com when ready for production.
"""

import uuid
from datetime import datetime, timezone
from api_shared import vtlog, config


GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

PHONE_NUMBER_ID = config.get("META_WHATSAPP_PHONE_ID", "mock-phone-id")
BUSINESS_ACCOUNT_ID = config.get("META_WHATSAPP_BUSINESS_ID", "mock-business-id")
ACCESS_TOKEN = config.get("META_WHATSAPP_TOKEN", "mock-token")
VERIFY_TOKEN = config.get("META_WHATSAPP_VERIFY_TOKEN", "mock-verify-token")


def verify_webhook(mode: str, token: str, challenge: str) -> str | None:
    """Verify webhook subscription from Meta."""
    if mode == "subscribe" and token == VERIFY_TOKEN:
        vtlog.info("webhook_verified")
        return challenge
    vtlog.warning("webhook_verification_failed", mode=mode)
    return None


def parse_webhook_payload(body: dict) -> list[dict]:
    """Parse incoming webhook payload from Meta into normalized messages."""
    messages = []
    if body.get("object") != "whatsapp_business_account":
        return messages
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            if "messages" in value:
                for msg in value["messages"]:
                    contact = next(
                        (c for c in value.get("contacts", []) if c.get("wa_id") == msg.get("from")),
                        {}
                    )
                    messages.append({
                        "waMessageId": msg.get("id", str(uuid.uuid4())),
                        "from": msg.get("from", ""),
                        "fromName": contact.get("profile", {}).get("name", ""),
                        "type": msg.get("type", "text"),
                        "text": msg.get("text", {}).get("body", "") if msg.get("type") == "text" else "",
                        "timestamp": msg.get("timestamp", str(int(datetime.now(timezone.utc).timestamp()))),
                        "metadata": msg,
                    })
            # Status updates
            if "statuses" in value:
                for status in value["statuses"]:
                    messages.append({
                        "type": "_status_update",
                        "waMessageId": status.get("id"),
                        "status": status.get("status"),  # sent, delivered, read, failed
                        "recipientId": status.get("recipient_id"),
                        "timestamp": status.get("timestamp"),
                        "errors": status.get("errors", []),
                    })
    return messages


def send_text_message(to: str, text: str) -> dict:
    """Send a text message via WhatsApp Business API (MOCK)."""
    mock_id = f"wamid.{uuid.uuid4().hex[:24]}"
    vtlog.info("wa_send_text_mock", to=to, text_preview=text[:50])
    # Real implementation:
    # POST {GRAPH_API_BASE}/{PHONE_NUMBER_ID}/messages
    # Authorization: Bearer {ACCESS_TOKEN}
    # Body: { messaging_product: "whatsapp", to, type: "text", text: { body: text } }
    return {
        "messaging_product": "whatsapp",
        "contacts": [{"input": to, "wa_id": to}],
        "messages": [{"id": mock_id}],
        "_mock": True,
    }


def send_template_message(to: str, template_name: str, language: str = "en_US", components: list = None) -> dict:
    """Send a template message via WhatsApp Business API (MOCK)."""
    mock_id = f"wamid.{uuid.uuid4().hex[:24]}"
    vtlog.info("wa_send_template_mock", to=to, template=template_name)
    # Real implementation:
    # POST {GRAPH_API_BASE}/{PHONE_NUMBER_ID}/messages
    # Body: { messaging_product: "whatsapp", to, type: "template",
    #         template: { name, language: { code }, components } }
    return {
        "messaging_product": "whatsapp",
        "contacts": [{"input": to, "wa_id": to}],
        "messages": [{"id": mock_id}],
        "_mock": True,
    }


def send_media_message(to: str, media_type: str, media_url: str, caption: str = "") -> dict:
    """Send image/video/document via WhatsApp Business API (MOCK)."""
    mock_id = f"wamid.{uuid.uuid4().hex[:24]}"
    vtlog.info("wa_send_media_mock", to=to, media_type=media_type)
    return {
        "messaging_product": "whatsapp",
        "contacts": [{"input": to, "wa_id": to}],
        "messages": [{"id": mock_id}],
        "_mock": True,
    }


def mark_as_read(message_id: str) -> dict:
    """Mark a message as read (MOCK)."""
    vtlog.info("wa_mark_read_mock", message_id=message_id)
    # Real: POST {GRAPH_API_BASE}/{PHONE_NUMBER_ID}/messages
    # Body: { messaging_product: "whatsapp", status: "read", message_id }
    return {"success": True, "_mock": True}


def get_business_profile() -> dict:
    """Get WhatsApp Business profile info (MOCK)."""
    return {
        "data": [{
            "about": "WaCRM Demo Business",
            "address": "123 Business St",
            "description": "Demo WhatsApp Business for WaCRM",
            "email": "demo@wacrm.example",
            "messaging_product": "whatsapp",
            "profile_picture_url": "",
            "websites": ["https://wacrm.example"],
            "vertical": "OTHER",
        }],
        "_mock": True,
    }


def get_phone_numbers() -> dict:
    """List phone numbers on the business account (MOCK)."""
    return {
        "data": [{
            "id": PHONE_NUMBER_ID,
            "display_phone_number": "+1 555-0100",
            "verified_name": "WaCRM Demo",
            "quality_rating": "GREEN",
            "platform_type": "CLOUD_API",
            "code_verification_status": "VERIFIED",
        }],
        "_mock": True,
    }


def get_message_templates() -> dict:
    """List approved message templates (MOCK)."""
    return {
        "data": [
            {
                "name": "hello_world",
                "status": "APPROVED",
                "category": "UTILITY",
                "language": "en_US",
                "components": [{"type": "BODY", "text": "Hello {{1}}, welcome to our service!"}],
            },
            {
                "name": "order_confirmation",
                "status": "APPROVED",
                "category": "UTILITY",
                "language": "en_US",
                "components": [{"type": "BODY", "text": "Hi {{1}}, your order #{{2}} has been confirmed."}],
            },
        ],
        "_mock": True,
    }
