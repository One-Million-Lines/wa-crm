from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone
import uuid

from api_shared import vtstorage, vtlog, get_current_user, CONVERSATIONS_COLLECTION, CONTACTS_COLLECTION
from data_models import ConversationCreate, ConversationUpdate

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _serialize(doc: dict) -> dict:
    doc["id"] = doc.pop("_id")
    return doc


@router.get("")
async def list_conversations(
    status: str = Query("", description="Filter by status"),
    assignedTo: str = Query("", description="Filter by assignee"),
    tag: str = Query("", description="Filter by tag"),
    search: str = Query("", description="Search contacts"),
    unreadOnly: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    query = {}
    if status:
        query["status"] = status
    if assignedTo:
        query["assignedTo"] = assignedTo
    if tag:
        query["tags"] = tag
    if unreadOnly:
        query["unreadCount"] = {"$gt": 0}

    docs = vtstorage.get_many(collection=CONVERSATIONS_COLLECTION, query=query,
                              sort=[("lastMessageAt", -1)], limit=limit, start=skip)
    total = vtstorage.count(collection=CONVERSATIONS_COLLECTION, query=query)

    # Enrich with contact info
    results = []
    for d in docs:
        contact = vtstorage.get_one(collection=CONTACTS_COLLECTION, query={"_id": d.get("contactId")})
        d["contact"] = {
            "fullName": contact.get("fullName", "Unknown") if contact else "Unknown",
            "phone": contact.get("phone", "") if contact else "",
            "tags": contact.get("tags", []) if contact else [],
            "stage": contact.get("stage", "") if contact else "",
        } if contact else None
        results.append(_serialize(d))

    return {"conversations": results, "total": total}


@router.get("/{conv_id}")
async def get_conversation(conv_id: str, user: dict = Depends(get_current_user)):
    doc = vtstorage.get_one(collection=CONVERSATIONS_COLLECTION, query={"_id": conv_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Conversation not found")
    contact = vtstorage.get_one(collection=CONTACTS_COLLECTION, query={"_id": doc.get("contactId")})
    if contact:
        contact["id"] = contact.pop("_id")
        doc["contact"] = contact
    return _serialize(doc)


@router.post("")
async def create_conversation(data: ConversationCreate, user: dict = Depends(get_current_user)):
    contact = vtstorage.get_one(collection=CONTACTS_COLLECTION, query={"_id": data.contactId})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "_id": str(uuid.uuid4()),
        **data.model_dump(),
        "createdAt": now,
        "updatedAt": now,
        "lastMessageAt": now,
        "lastMessagePreview": "",
        "lastSenderType": "",
        "unreadCount": 0,
        "messageCount": 0,
        "internalNotes": "",
        "slaState": "ok",
    }
    vtstorage.insert_one(collection=CONVERSATIONS_COLLECTION, set_object=doc)
    vtlog.info("conversation_created", conv_id=doc["_id"])
    return _serialize(doc)


@router.put("/{conv_id}")
async def update_conversation(conv_id: str, data: ConversationUpdate, user: dict = Depends(get_current_user)):
    existing = vtstorage.get_one(collection=CONVERSATIONS_COLLECTION, query={"_id": conv_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Conversation not found")

    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

    vtstorage.update_one(collection=CONVERSATIONS_COLLECTION, query={"_id": conv_id}, set_object={"$set": updates})
    updated = vtstorage.get_one(collection=CONVERSATIONS_COLLECTION, query={"_id": conv_id})
    vtlog.info("conversation_updated", conv_id=conv_id)
    return _serialize(updated)
