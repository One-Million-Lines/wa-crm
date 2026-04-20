from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone
import uuid

from api_shared import vtstorage, vtlog, get_current_user, TEMPLATES_COLLECTION
from data_models import TemplateCreate, TemplateUpdate

router = APIRouter(prefix="/templates", tags=["templates"])


def _serialize(doc: dict) -> dict:
    doc["id"] = doc.pop("_id")
    return doc


@router.get("")
async def list_templates(
    category: str = Query("", description="Filter by category"),
    isQuickReply: str = Query("", description="Filter quick replies"),
    search: str = Query("", description="Search by name"),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    query = {}
    if category:
        query["category"] = category
    if isQuickReply == "true":
        query["isQuickReply"] = True
    elif isQuickReply == "false":
        query["isQuickReply"] = False
    if search:
        query["name"] = {"$regex": search, "$options": "i"}

    docs = vtstorage.get_many(collection=TEMPLATES_COLLECTION, query=query,
                              sort=[("name", 1)], limit=limit, start=skip)
    total = vtstorage.count(collection=TEMPLATES_COLLECTION, query=query)
    return {"templates": [_serialize(d) for d in docs], "total": total}


@router.get("/{tpl_id}")
async def get_template(tpl_id: str, user: dict = Depends(get_current_user)):
    doc = vtstorage.get_one(collection=TEMPLATES_COLLECTION, query={"_id": tpl_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Template not found")
    return _serialize(doc)


@router.post("")
async def create_template(data: TemplateCreate, user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "_id": str(uuid.uuid4()),
        **data.model_dump(),
        "createdAt": now,
        "updatedAt": now,
        "createdBy": user["_id"],
        "usageCount": 0,
    }
    vtstorage.insert_one(collection=TEMPLATES_COLLECTION, set_object=doc)
    vtlog.info("template_created", tpl_id=doc["_id"])
    return _serialize(doc)


@router.put("/{tpl_id}")
async def update_template(tpl_id: str, data: TemplateUpdate, user: dict = Depends(get_current_user)):
    existing = vtstorage.get_one(collection=TEMPLATES_COLLECTION, query={"_id": tpl_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")

    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

    vtstorage.update_one(collection=TEMPLATES_COLLECTION, query={"_id": tpl_id}, set_object={"$set": updates})
    updated = vtstorage.get_one(collection=TEMPLATES_COLLECTION, query={"_id": tpl_id})
    return _serialize(updated)


@router.delete("/{tpl_id}")
async def delete_template(tpl_id: str, user: dict = Depends(get_current_user)):
    existing = vtstorage.get_one(collection=TEMPLATES_COLLECTION, query={"_id": tpl_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")
    vtstorage.delete_one(collection=TEMPLATES_COLLECTION, query={"_id": tpl_id})
    return {"deleted": True}
