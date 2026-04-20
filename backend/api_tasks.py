from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone
import uuid

from api_shared import vtstorage, vtlog, get_current_user, TASKS_COLLECTION
from data_models import TaskCreate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _serialize(doc: dict) -> dict:
    doc["id"] = doc.pop("_id")
    return doc


@router.get("")
async def list_tasks(
    status: str = Query("", description="Filter by status"),
    assignee: str = Query("", description="Filter by assignee"),
    priority: str = Query("", description="Filter by priority"),
    contactId: str = Query("", description="Filter by contact"),
    conversationId: str = Query("", description="Filter by conversation"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    query = {}
    if status:
        query["status"] = status
    if assignee:
        query["assignee"] = assignee
    if priority:
        query["priority"] = priority
    if contactId:
        query["contactId"] = contactId
    if conversationId:
        query["conversationId"] = conversationId

    docs = vtstorage.get_many(collection=TASKS_COLLECTION, query=query,
                              sort=[("dueDate", 1), ("priority", -1)], limit=limit, start=skip)
    total = vtstorage.count(collection=TASKS_COLLECTION, query=query)
    return {"tasks": [_serialize(d) for d in docs], "total": total}


@router.get("/{task_id}")
async def get_task(task_id: str, user: dict = Depends(get_current_user)):
    doc = vtstorage.get_one(collection=TASKS_COLLECTION, query={"_id": task_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found")
    return _serialize(doc)


@router.post("")
async def create_task(data: TaskCreate, user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "_id": str(uuid.uuid4()),
        **data.model_dump(),
        "createdAt": now,
        "updatedAt": now,
        "createdBy": user["_id"],
        "comments": [],
    }
    vtstorage.insert_one(collection=TASKS_COLLECTION, set_object=doc)
    vtlog.info("task_created", task_id=doc["_id"])
    return _serialize(doc)


@router.put("/{task_id}")
async def update_task(task_id: str, data: TaskUpdate, user: dict = Depends(get_current_user)):
    existing = vtstorage.get_one(collection=TASKS_COLLECTION, query={"_id": task_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

    vtstorage.update_one(collection=TASKS_COLLECTION, query={"_id": task_id}, set_object={"$set": updates})
    updated = vtstorage.get_one(collection=TASKS_COLLECTION, query={"_id": task_id})
    vtlog.info("task_updated", task_id=task_id)
    return _serialize(updated)


@router.delete("/{task_id}")
async def delete_task(task_id: str, user: dict = Depends(get_current_user)):
    existing = vtstorage.get_one(collection=TASKS_COLLECTION, query={"_id": task_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")
    vtstorage.delete_one(collection=TASKS_COLLECTION, query={"_id": task_id})
    vtlog.info("task_deleted", task_id=task_id)
    return {"deleted": True}
