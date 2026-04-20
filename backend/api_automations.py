from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone
import uuid

from api_shared import vtstorage, vtlog, get_current_user, AUTOMATIONS_COLLECTION
from data_models import AutomationCreate, AutomationUpdate

router = APIRouter(prefix="/automations", tags=["automations"])


def _serialize(doc: dict) -> dict:
    doc["id"] = doc.pop("_id")
    return doc


@router.get("")
async def list_automations(
    isActive: str = Query("", description="Filter by active state"),
    trigger: str = Query("", description="Filter by trigger type"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    query = {}
    if isActive == "true":
        query["isActive"] = True
    elif isActive == "false":
        query["isActive"] = False
    if trigger:
        query["trigger"] = trigger

    docs = vtstorage.get_many(collection=AUTOMATIONS_COLLECTION, query=query,
                              sort=[("updatedAt", -1)], limit=limit, start=skip)
    total = vtstorage.count(collection=AUTOMATIONS_COLLECTION, query=query)
    return {"automations": [_serialize(d) for d in docs], "total": total}


@router.get("/{auto_id}")
async def get_automation(auto_id: str, user: dict = Depends(get_current_user)):
    doc = vtstorage.get_one(collection=AUTOMATIONS_COLLECTION, query={"_id": auto_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Automation not found")
    return _serialize(doc)


@router.post("")
async def create_automation(data: AutomationCreate, user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "_id": str(uuid.uuid4()),
        **data.model_dump(),
        "createdAt": now,
        "updatedAt": now,
        "createdBy": user["_id"],
        "executionCount": 0,
        "lastExecutedAt": None,
        "executionLog": [],
    }
    vtstorage.insert_one(collection=AUTOMATIONS_COLLECTION, set_object=doc)
    vtlog.info("automation_created", auto_id=doc["_id"])
    return _serialize(doc)


@router.put("/{auto_id}")
async def update_automation(auto_id: str, data: AutomationUpdate, user: dict = Depends(get_current_user)):
    existing = vtstorage.get_one(collection=AUTOMATIONS_COLLECTION, query={"_id": auto_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Automation not found")

    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

    vtstorage.update_one(collection=AUTOMATIONS_COLLECTION, query={"_id": auto_id}, set_object={"$set": updates})
    updated = vtstorage.get_one(collection=AUTOMATIONS_COLLECTION, query={"_id": auto_id})
    vtlog.info("automation_updated", auto_id=auto_id)
    return _serialize(updated)


@router.delete("/{auto_id}")
async def delete_automation(auto_id: str, user: dict = Depends(get_current_user)):
    existing = vtstorage.get_one(collection=AUTOMATIONS_COLLECTION, query={"_id": auto_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Automation not found")
    vtstorage.delete_one(collection=AUTOMATIONS_COLLECTION, query={"_id": auto_id})
    vtlog.info("automation_deleted", auto_id=auto_id)
    return {"deleted": True}
