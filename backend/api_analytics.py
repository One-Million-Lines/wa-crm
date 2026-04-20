from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta

from api_shared import vtstorage, get_current_user, \
    CONTACTS_COLLECTION, CONVERSATIONS_COLLECTION, MESSAGES_COLLECTION, \
    TASKS_COLLECTION, AUTOMATIONS_COLLECTION

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(user: dict = Depends(get_current_user)):
    total_contacts = vtstorage.count(collection=CONTACTS_COLLECTION, query={})
    total_conversations = vtstorage.count(collection=CONVERSATIONS_COLLECTION, query={})
    active_conversations = vtstorage.count(collection=CONVERSATIONS_COLLECTION,
                                           query={"status": {"$in": ["new", "open", "assigned", "waiting_on_team"]}})
    total_messages = vtstorage.count(collection=MESSAGES_COLLECTION, query={})
    total_tasks = vtstorage.count(collection=TASKS_COLLECTION, query={})
    open_tasks = vtstorage.count(collection=TASKS_COLLECTION,
                                 query={"status": {"$in": ["todo", "in_progress", "waiting"]}})
    total_automations = vtstorage.count(collection=AUTOMATIONS_COLLECTION, query={})
    active_automations = vtstorage.count(collection=AUTOMATIONS_COLLECTION, query={"isActive": True})

    # Stage breakdown
    stages = ["new_lead", "active_lead", "customer", "repeat_customer", "support_case", "inactive"]
    stage_counts = {}
    for s in stages:
        stage_counts[s] = vtstorage.count(collection=CONTACTS_COLLECTION, query={"stage": s})

    # Conversation status breakdown
    conv_statuses = ["new", "open", "assigned", "waiting_on_customer", "waiting_on_team",
                     "automated", "paused", "resolved", "archived"]
    conv_status_counts = {}
    for s in conv_statuses:
        conv_status_counts[s] = vtstorage.count(collection=CONVERSATIONS_COLLECTION, query={"status": s})

    # Messages sent/received
    msgs_sent = vtstorage.count(collection=MESSAGES_COLLECTION, query={"direction": "outbound"})
    msgs_received = vtstorage.count(collection=MESSAGES_COLLECTION, query={"direction": "inbound"})

    return {
        "totalContacts": total_contacts,
        "totalConversations": total_conversations,
        "activeConversations": active_conversations,
        "totalMessages": total_messages,
        "messagesSent": msgs_sent,
        "messagesReceived": msgs_received,
        "totalTasks": total_tasks,
        "openTasks": open_tasks,
        "totalAutomations": total_automations,
        "activeAutomations": active_automations,
        "contactStages": stage_counts,
        "conversationStatuses": conv_status_counts,
    }


@router.get("/team")
async def team_stats(user: dict = Depends(get_current_user)):
    # Get all team members
    from api_shared import USERS_COLLECTION
    users = vtstorage.get_many(collection=USERS_COLLECTION, query={}, limit=100)

    team = []
    for u in users:
        uid = u["_id"]
        assigned_convs = vtstorage.count(collection=CONVERSATIONS_COLLECTION, query={"assignedTo": uid})
        assigned_tasks = vtstorage.count(collection=TASKS_COLLECTION, query={"assignee": uid})
        msgs_sent = vtstorage.count(collection=MESSAGES_COLLECTION,
                                     query={"senderId": uid, "direction": "outbound"})
        team.append({
            "userId": uid,
            "name": u.get("name", u.get("email", "")),
            "email": u.get("email", ""),
            "role": u.get("role", "agent"),
            "assignedConversations": assigned_convs,
            "assignedTasks": assigned_tasks,
            "messagesSent": msgs_sent,
        })

    return {"team": team}
