from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone
import uuid

from api_shared import vtstorage, vtlog, get_current_user, CONTACTS_COLLECTION
from data_models import ContactCreate, ContactUpdate

router = APIRouter(prefix="/contacts", tags=["contacts"])


def _serialize(doc: dict) -> dict:
    doc["id"] = doc.pop("_id")
    return doc


@router.get("")
async def list_contacts(
    search: str = Query("", description="Search by name, phone, tags"),
    status: str = Query("", description="Filter by status"),
    tag: str = Query("", description="Filter by tag"),
    owner: str = Query("", description="Filter by owner"),
    stage: str = Query("", description="Filter by stage"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    query = {}
    if search:
        query["$or"] = [
            {"fullName": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}},
        ]
    if status:
        query["status"] = status
    if tag:
        query["tags"] = tag
    if owner:
        query["owner"] = owner
    if stage:
        query["stage"] = stage

    docs = vtstorage.get_many(collection=CONTACTS_COLLECTION, query=query,
                              sort=[("updatedAt", -1)], limit=limit, start=skip)
    total = vtstorage.count(collection=CONTACTS_COLLECTION, query=query)
    return {"contacts": [_serialize(d) for d in docs], "total": total}


@router.get("/{contact_id}")
async def get_contact(contact_id: str, user: dict = Depends(get_current_user)):
    doc = vtstorage.get_one(collection=CONTACTS_COLLECTION, query={"_id": contact_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Contact not found")
    return _serialize(doc)


@router.post("")
async def create_contact(data: ContactCreate, user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "_id": str(uuid.uuid4()),
        **data.model_dump(),
        "createdAt": now,
        "updatedAt": now,
        "createdBy": user["_id"],
        "lastInteraction": None,
        "conversationCount": 0,
        "externalIds": {},
        "activityTimeline": [],
    }
    vtstorage.insert_one(collection=CONTACTS_COLLECTION, set_object=doc)
    vtlog.info("contact_created", contact_id=doc["_id"])
    return _serialize(doc)


@router.put("/{contact_id}")
async def update_contact(contact_id: str, data: ContactUpdate, user: dict = Depends(get_current_user)):
    existing = vtstorage.get_one(collection=CONTACTS_COLLECTION, query={"_id": contact_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Contact not found")

    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

    vtstorage.update_one(collection=CONTACTS_COLLECTION, query={"_id": contact_id}, set_object={"$set": updates})
    updated = vtstorage.get_one(collection=CONTACTS_COLLECTION, query={"_id": contact_id})
    return _serialize(updated)


@router.delete("/{contact_id}")
async def delete_contact(contact_id: str, user: dict = Depends(get_current_user)):
    existing = vtstorage.get_one(collection=CONTACTS_COLLECTION, query={"_id": contact_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Contact not found")
    vtstorage.delete_one(collection=CONTACTS_COLLECTION, query={"_id": contact_id})
    vtlog.info("contact_deleted", contact_id=contact_id)
    return {"deleted": True}
