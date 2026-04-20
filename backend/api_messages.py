from fastapi import APIRouter, HTTPException, Depends, Query, Request
from datetime import datetime, timezone
import uuid

from api_shared import vtstorage, vtlog, get_current_user, \
    MESSAGES_COLLECTION, CONVERSATIONS_COLLECTION, CONTACTS_COLLECTION
from data_models import MessageSend
import whatsapp_api

router = APIRouter(tags=["messages"])


def _serialize(doc: dict) -> dict:
    doc["id"] = doc.pop("_id")
    return doc


@router.get("/conversations/{conv_id}/messages")
async def list_messages(
    conv_id: str,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    query = {"conversationId": conv_id}
    docs = vtstorage.get_many(collection=MESSAGES_COLLECTION, query=query,
                              sort=[("timestamp", 1)], limit=limit, start=skip)
    total = vtstorage.count(collection=MESSAGES_COLLECTION, query=query)
    return {"messages": [_serialize(d) for d in docs], "total": total}


@router.post("/messages/send")
async def send_message(data: MessageSend, user: dict = Depends(get_current_user)):
    conv = vtstorage.get_one(collection=CONVERSATIONS_COLLECTION, query={"_id": data.conversationId})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    now = datetime.now(timezone.utc).isoformat()

    # Call WhatsApp API (mock)
    if data.type == "template" and data.templateName:
        wa_result = whatsapp_api.send_template_message(data.contactPhone, data.templateName)
    elif data.type == "media" and data.mediaUrl:
        wa_result = whatsapp_api.send_media_message(data.contactPhone, "image", data.mediaUrl)
    else:
        wa_result = whatsapp_api.send_text_message(data.contactPhone, data.text)

    wa_message_id = wa_result.get("messages", [{}])[0].get("id", "")

    msg_doc = {
        "_id": str(uuid.uuid4()),
        "conversationId": data.conversationId,
        "waMessageId": wa_message_id,
        "direction": "outbound",
        "senderType": "human",
        "senderId": user["_id"],
        "senderName": user.get("name", user.get("email", "")),
        "type": data.type,
        "text": data.text,
        "templateName": data.templateName,
        "mediaUrl": data.mediaUrl,
        "status": "sent",
        "timestamp": now,
        "metadata": {},
    }
    vtstorage.insert_one(collection=MESSAGES_COLLECTION, set_object=msg_doc)

    # Update conversation
    vtstorage.update_one(
        collection=CONVERSATIONS_COLLECTION,
        query={"_id": data.conversationId},
        update={"$set": {
            "lastMessageAt": now,
            "lastMessagePreview": data.text[:100] if data.text else f"[{data.type}]",
            "lastSenderType": "human",
            "updatedAt": now,
            "status": "open" if conv.get("status") == "new" else conv.get("status"),
        }, "$inc": {"messageCount": 1}}
    )

    vtlog.info("message_sent", conv_id=data.conversationId, type=data.type)
    return _serialize(msg_doc)


# ── Webhook for incoming WhatsApp messages ──
@router.get("/webhook")
async def webhook_verify(request: Request):
    """Meta webhook verification endpoint."""
    params = request.query_params
    mode = params.get("hub.mode", "")
    token = params.get("hub.verify_token", "")
    challenge = params.get("hub.challenge", "")
    result = whatsapp_api.verify_webhook(mode, token, challenge)
    if result is not None:
        return int(result)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def webhook_receive(request: Request):
    """Receive incoming WhatsApp messages from Meta webhook."""
    body = await request.json()
    parsed = whatsapp_api.parse_webhook_payload(body)

    for msg in parsed:
        if msg.get("type") == "_status_update":
            # Update message delivery status
            if msg.get("waMessageId"):
                vtstorage.update_one(
                    collection=MESSAGES_COLLECTION,
                    query={"waMessageId": msg["waMessageId"]},
                    update={"$set": {"status": msg.get("status", "sent")}}
                )
            continue

        # Find or create contact
        phone = msg.get("from", "")
        contact = vtstorage.get_one(collection=CONTACTS_COLLECTION, query={"phone": phone})
        now = datetime.now(timezone.utc).isoformat()

        if not contact:
            contact = {
                "_id": str(uuid.uuid4()),
                "fullName": msg.get("fromName", phone),
                "phone": phone,
                "tags": [],
                "status": "new_lead",
                "owner": None,
                "stage": "new_lead",
                "source": "whatsapp",
                "notes": "",
                "customFields": {},
                "optIn": True,
                "createdAt": now,
                "updatedAt": now,
                "createdBy": "system",
                "lastInteraction": now,
                "conversationCount": 1,
                "externalIds": {},
                "activityTimeline": [],
            }
            vtstorage.insert_one(collection=CONTACTS_COLLECTION, set_object=contact)
            vtlog.info("contact_auto_created", phone=phone)

        # Find or create conversation
        conv = vtstorage.get_one(
            collection=CONVERSATIONS_COLLECTION,
            query={"contactId": contact["_id"], "status": {"$nin": ["archived"]}}
        )
        if not conv:
            conv = {
                "_id": str(uuid.uuid4()),
                "contactId": contact["_id"],
                "status": "new",
                "assignedTo": None,
                "tags": [],
                "automationState": "enabled",
                "aiMode": "off",
                "createdAt": now,
                "updatedAt": now,
                "lastMessageAt": now,
                "lastMessagePreview": msg.get("text", "")[:100],
                "lastSenderType": "customer",
                "unreadCount": 1,
                "messageCount": 1,
                "internalNotes": "",
                "slaState": "waiting",
            }
            vtstorage.insert_one(collection=CONVERSATIONS_COLLECTION, set_object=conv)
            vtlog.info("conversation_auto_created", conv_id=conv["_id"])
        else:
            vtstorage.update_one(
                collection=CONVERSATIONS_COLLECTION,
                query={"_id": conv["_id"]},
                update={"$set": {
                    "lastMessageAt": now,
                    "lastMessagePreview": msg.get("text", "")[:100],
                    "lastSenderType": "customer",
                    "updatedAt": now,
                    "slaState": "waiting",
                }, "$inc": {"unreadCount": 1, "messageCount": 1}}
            )

        # Store message
        msg_doc = {
            "_id": str(uuid.uuid4()),
            "conversationId": conv["_id"],
            "waMessageId": msg.get("waMessageId", ""),
            "direction": "inbound",
            "senderType": "customer",
            "senderId": contact["_id"],
            "senderName": contact.get("fullName", phone),
            "type": msg.get("type", "text"),
            "text": msg.get("text", ""),
            "status": "received",
            "timestamp": now,
            "metadata": msg.get("metadata", {}),
        }
        vtstorage.insert_one(collection=MESSAGES_COLLECTION, set_object=msg_doc)

        # Update contact last interaction
        vtstorage.update_one(
            collection=CONTACTS_COLLECTION,
            query={"_id": contact["_id"]},
            update={"$set": {"lastInteraction": now, "updatedAt": now}}
        )

    return {"status": "ok"}
