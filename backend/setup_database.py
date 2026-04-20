"""Seed database with admin user and sample data."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from api_shared import vtstorage, vtlog, hash_password, \
    USERS_COLLECTION, CONTACTS_COLLECTION, CONVERSATIONS_COLLECTION, \
    MESSAGES_COLLECTION, TASKS_COLLECTION, AUTOMATIONS_COLLECTION, \
    TEMPLATES_COLLECTION, SETTINGS_COLLECTION
from datetime import datetime, timezone, timedelta
import uuid


def seed():
    # ── Admin user ──
    admin_email = "admin@wacrm.local"
    existing = vtstorage.get_one(collection=USERS_COLLECTION, query={"email": admin_email})
    if not existing:
        admin_id = str(uuid.uuid4())
        vtstorage.insert_one(collection=USERS_COLLECTION, set_object={
            "_id": admin_id,
            "email": admin_email,
            "password": hash_password("change-me-before-use"),
            "name": "Admin User",
            "role": "admin",
            "createdAt": datetime.now(timezone.utc).isoformat(),
        })
        vtlog.info("admin_seeded", email=admin_email)
    else:
        admin_id = existing["_id"]

    # Agent user
    agent_email = "admin@wacrm.local"
    existing_agent = vtstorage.get_one(collection=USERS_COLLECTION, query={"email": agent_email})
    if not existing_agent:
        agent_id = str(uuid.uuid4())
        vtstorage.insert_one(collection=USERS_COLLECTION, set_object={
            "_id": agent_id,
            "email": agent_email,
            "password": hash_password("change-agent-password"),
            "name": "Sarah Miller",
            "role": "agent",
            "createdAt": datetime.now(timezone.utc).isoformat(),
        })
    else:
        agent_id = existing_agent["_id"]

    # Skip if data already seeded
    if vtstorage.count(collection=CONTACTS_COLLECTION, query={}) > 0:
        vtlog.info("data_already_seeded")
        return

    now = datetime.now(timezone.utc)

    # ── Sample Contacts ──
    contacts = [
        {"fullName": "Marco Rossi", "phone": "+41791234567", "tags": ["vip", "repeat"], "status": "customer", "stage": "repeat_customer", "source": "whatsapp", "notes": "Regular buyer, prefers Italian"},
        {"fullName": "Anna Schmidt", "phone": "+41791234568", "tags": ["new"], "status": "new_lead", "stage": "new_lead", "source": "whatsapp", "notes": "Inquired about pricing"},
        {"fullName": "James Chen", "phone": "+41791234569", "tags": ["support"], "status": "customer", "stage": "support_case", "source": "website", "notes": "Issue with last order #1042"},
        {"fullName": "Sofia Martinez", "phone": "+41791234570", "tags": ["lead", "hot"], "status": "active_lead", "stage": "active_lead", "source": "referral", "notes": "Referred by Marco Rossi"},
        {"fullName": "Lena Weber", "phone": "+41791234571", "tags": ["inactive"], "status": "inactive", "stage": "inactive", "source": "whatsapp", "notes": "No response for 30 days"},
        {"fullName": "David Kim", "phone": "+41791234572", "tags": ["vip"], "status": "customer", "stage": "customer", "source": "whatsapp", "notes": "Enterprise client"},
        {"fullName": "Emma Brown", "phone": "+41791234573", "tags": ["new", "interested"], "status": "new_lead", "stage": "new_lead", "source": "whatsapp", "notes": "Asked about bulk discounts"},
        {"fullName": "Ali Hassan", "phone": "+41791234574", "tags": ["lead"], "status": "active_lead", "stage": "active_lead", "source": "ads", "notes": "Came from Facebook ad"},
        {"fullName": "Maria Garcia", "phone": "+41791234575", "tags": ["repeat", "loyalty"], "status": "customer", "stage": "repeat_customer", "source": "whatsapp", "notes": "Loyalty program member"},
        {"fullName": "Thomas Müller", "phone": "+41791234576", "tags": ["support", "urgent"], "status": "customer", "stage": "support_case", "source": "whatsapp", "notes": "Payment issue — escalated"},
    ]

    contact_ids = []
    for i, c in enumerate(contacts):
        cid = str(uuid.uuid4())
        contact_ids.append(cid)
        vtstorage.insert_one(collection=CONTACTS_COLLECTION, set_object={
            "_id": cid,
            **c,
            "customFields": {},
            "optIn": True,
            "createdAt": (now - timedelta(days=30 - i * 3)).isoformat(),
            "updatedAt": (now - timedelta(hours=i * 2)).isoformat(),
            "createdBy": admin_id,
            "lastInteraction": (now - timedelta(hours=i * 2)).isoformat(),
            "conversationCount": 1,
            "externalIds": {},
            "activityTimeline": [],
        })

    # ── Sample Conversations ──
    conv_statuses = ["open", "new", "assigned", "waiting_on_customer", "open", "assigned",
                     "new", "open", "resolved", "waiting_on_team"]
    conv_ids = []
    for i, cid in enumerate(contact_ids):
        conv_id = str(uuid.uuid4())
        conv_ids.append(conv_id)
        assigned = agent_id if i % 3 == 0 else (admin_id if i % 3 == 1 else None)
        vtstorage.insert_one(collection=CONVERSATIONS_COLLECTION, set_object={
            "_id": conv_id,
            "contactId": cid,
            "status": conv_statuses[i],
            "assignedTo": assigned,
            "tags": contacts[i]["tags"],
            "automationState": "enabled" if i < 7 else "paused",
            "aiMode": "off",
            "createdAt": (now - timedelta(days=20 - i * 2)).isoformat(),
            "updatedAt": (now - timedelta(minutes=i * 30)).isoformat(),
            "lastMessageAt": (now - timedelta(minutes=i * 30)).isoformat(),
            "lastMessagePreview": [
                "Hi, I'd like to reorder the same package as last time",
                "Hello, can you send me your price list?",
                "My order #1042 hasn't arrived yet, it's been 5 days",
                "Marco told me about your services, very interested!",
                "",
                "We need to discuss the Q2 contract renewal",
                "Do you offer bulk pricing for 500+ units?",
                "Saw your ad — what's the delivery time to Zurich?",
                "Thanks for the quick delivery! 5 stars ⭐",
                "I was charged twice for my last order, please fix ASAP",
            ][i],
            "lastSenderType": "customer" if i % 2 == 0 else "human",
            "unreadCount": [2, 1, 3, 1, 0, 0, 1, 2, 0, 1][i],
            "messageCount": [12, 3, 8, 5, 15, 22, 2, 4, 20, 6][i],
            "internalNotes": "" if i % 2 == 0 else "Follow up needed",
            "slaState": "ok" if i % 3 != 2 else "waiting",
        })

    # ── Sample Messages for first 3 conversations ──
    msg_sets = [
        # Marco Rossi conversation
        [
            {"dir": "inbound", "sType": "customer", "text": "Hey! I'd like to order again 👋", "mins": 120},
            {"dir": "outbound", "sType": "human", "text": "Hi Marco! Great to hear from you. Same package as last time?", "mins": 115},
            {"dir": "inbound", "sType": "customer", "text": "Yes please, the premium bundle", "mins": 110},
            {"dir": "outbound", "sType": "human", "text": "Perfect! I'll prepare that right away. Delivery to the usual address?", "mins": 105},
            {"dir": "inbound", "sType": "customer", "text": "Yes, same address. Can you do express?", "mins": 60},
            {"dir": "outbound", "sType": "automation", "text": "Express delivery is available for CHF 15 extra. Would you like to add it?", "mins": 59},
            {"dir": "inbound", "sType": "customer", "text": "Sure, add express please", "mins": 30},
            {"dir": "outbound", "sType": "human", "text": "Done! Your order has been placed with express delivery. You'll receive confirmation shortly.", "mins": 25},
            {"dir": "inbound", "sType": "customer", "text": "Perfect thanks! Also, do you have any new products coming?", "mins": 5},
            {"dir": "inbound", "sType": "customer", "text": "I'd like to reorder the same package as last time", "mins": 0},
        ],
        # Anna Schmidt conversation
        [
            {"dir": "inbound", "sType": "customer", "text": "Hello, can you send me your price list?", "mins": 60},
            {"dir": "outbound", "sType": "automation", "text": "Hi! Thanks for reaching out. I'll connect you with our team right away.", "mins": 59},
            {"dir": "inbound", "sType": "customer", "text": "Thank you!", "mins": 30},
        ],
        # James Chen conversation
        [
            {"dir": "inbound", "sType": "customer", "text": "Hi, I have an issue with my order", "mins": 480},
            {"dir": "outbound", "sType": "human", "text": "Hi James, sorry to hear that. What's your order number?", "mins": 470},
            {"dir": "inbound", "sType": "customer", "text": "Order #1042, placed last week", "mins": 460},
            {"dir": "outbound", "sType": "human", "text": "Let me check that for you...", "mins": 455},
            {"dir": "outbound", "sType": "human", "text": "I can see order #1042. It was shipped 3 days ago. The tracking shows it's in transit.", "mins": 450},
            {"dir": "inbound", "sType": "customer", "text": "But it says delivery was supposed to be yesterday", "mins": 300},
            {"dir": "outbound", "sType": "human", "text": "You're right, I see the delay. Let me escalate this with our shipping partner.", "mins": 290},
            {"dir": "inbound", "sType": "customer", "text": "My order #1042 hasn't arrived yet, it's been 5 days", "mins": 0},
        ],
    ]

    for conv_i, msgs in enumerate(msg_sets):
        for m in msgs:
            sender_id = contact_ids[conv_i] if m["dir"] == "inbound" else (admin_id if m["sType"] == "human" else "system")
            sender_name = contacts[conv_i]["fullName"] if m["dir"] == "inbound" else ("Admin User" if m["sType"] == "human" else "Automation")
            vtstorage.insert_one(collection=MESSAGES_COLLECTION, set_object={
                "_id": str(uuid.uuid4()),
                "conversationId": conv_ids[conv_i],
                "waMessageId": f"wamid.{uuid.uuid4().hex[:24]}",
                "direction": m["dir"],
                "senderType": m["sType"],
                "senderId": sender_id,
                "senderName": sender_name,
                "type": "text",
                "text": m["text"],
                "status": "read" if m["dir"] == "outbound" else "received",
                "timestamp": (now - timedelta(minutes=m["mins"])).isoformat(),
                "metadata": {},
            })

    # ── Sample Tasks ──
    tasks = [
        {"title": "Follow up with Anna on pricing", "description": "Send price list and schedule a call", "assignee": agent_id, "priority": "high", "status": "todo", "contactId": contact_ids[1], "conversationId": conv_ids[1]},
        {"title": "Resolve James order issue", "description": "Contact shipping partner about order #1042", "assignee": admin_id, "priority": "urgent", "status": "in_progress", "contactId": contact_ids[2], "conversationId": conv_ids[2]},
        {"title": "Send Sofia proposal", "description": "Prepare and send service proposal", "assignee": agent_id, "priority": "medium", "status": "todo", "contactId": contact_ids[3], "conversationId": conv_ids[3]},
        {"title": "Re-engage Lena", "description": "Send win-back message after 30 days of inactivity", "assignee": agent_id, "priority": "low", "status": "todo", "contactId": contact_ids[4], "conversationId": conv_ids[4]},
        {"title": "Prepare Q2 contract for David", "description": "Draft enterprise renewal contract", "assignee": admin_id, "priority": "high", "status": "in_progress", "contactId": contact_ids[5], "conversationId": conv_ids[5]},
        {"title": "Process Thomas refund", "description": "Issue refund for double charge", "assignee": admin_id, "priority": "urgent", "status": "todo", "contactId": contact_ids[9], "conversationId": conv_ids[9]},
    ]

    for i, t in enumerate(tasks):
        vtstorage.insert_one(collection=TASKS_COLLECTION, set_object={
            "_id": str(uuid.uuid4()),
            **t,
            "dueDate": (now + timedelta(days=i + 1)).isoformat(),
            "createdAt": (now - timedelta(days=2)).isoformat(),
            "updatedAt": now.isoformat(),
            "createdBy": admin_id,
            "comments": [],
        })

    # ── Sample Automations ──
    automations = [
        {
            "name": "Welcome New Contact",
            "description": "Send welcome message when a new contact messages for the first time",
            "trigger": "first_message_new_contact",
            "conditions": [],
            "actions": [{"type": "send_template", "templateName": "hello_world"}],
            "isActive": True,
            "requiresApproval": False,
        },
        {
            "name": "Tag Product Inquiry",
            "description": "Auto-tag when message contains price/cost/buy keywords",
            "trigger": "new_inbound_message",
            "conditions": [{"type": "keyword_match", "keywords": ["price", "cost", "buy", "purchase", "order"]}],
            "actions": [{"type": "add_tag", "tag": "product_inquiry"}],
            "isActive": True,
            "requiresApproval": False,
        },
        {
            "name": "Escalate No Reply",
            "description": "Notify team if no reply within 30 minutes during business hours",
            "trigger": "no_team_reply_timeout",
            "conditions": [{"type": "timeout_minutes", "value": 30}, {"type": "business_hours", "value": True}],
            "actions": [{"type": "notify_team", "message": "Customer waiting for reply > 30 min"}],
            "isActive": True,
            "requiresApproval": False,
        },
        {
            "name": "Off-hours Auto Reply",
            "description": "Send off-hours message outside business hours",
            "trigger": "new_inbound_message",
            "conditions": [{"type": "business_hours", "value": False}],
            "actions": [{"type": "send_message", "text": "Thanks for your message! Our team is currently offline and will respond during business hours."}],
            "isActive": False,
            "requiresApproval": False,
        },
        {
            "name": "Assign Support Cases",
            "description": "Route support-tagged conversations to support queue",
            "trigger": "conversation_tagged",
            "conditions": [{"type": "tag_match", "tag": "support"}],
            "actions": [{"type": "assign_conversation", "queue": "support"}],
            "isActive": True,
            "requiresApproval": False,
        },
    ]

    for a in automations:
        vtstorage.insert_one(collection=AUTOMATIONS_COLLECTION, set_object={
            "_id": str(uuid.uuid4()),
            **a,
            "createdAt": (now - timedelta(days=10)).isoformat(),
            "updatedAt": now.isoformat(),
            "createdBy": admin_id,
            "executionCount": 0,
            "lastExecutedAt": None,
            "executionLog": [],
        })

    # ── Sample Templates ──
    templates = [
        {"name": "Welcome Message", "category": "onboarding", "body": "Hi {{name}}! 👋 Welcome to {{company}}. How can we help you today?", "variables": ["name", "company"], "isQuickReply": False},
        {"name": "Out of Office", "category": "general", "body": "Thanks for reaching out! We're currently offline and will respond during business hours (Mon-Fri 9-18).", "variables": [], "isQuickReply": True},
        {"name": "Follow-Up Reminder", "category": "sales", "body": "Hi {{name}}, just following up on our earlier conversation. Do you have any questions about {{topic}}?", "variables": ["name", "topic"], "isQuickReply": False},
        {"name": "Order Confirmation", "category": "commerce", "body": "Hi {{name}}, your order #{{orderNumber}} has been confirmed! Expected delivery: {{deliveryDate}}.", "variables": ["name", "orderNumber", "deliveryDate"], "isQuickReply": False},
        {"name": "Quick Thanks", "category": "general", "body": "Thank you! Is there anything else I can help you with?", "variables": [], "isQuickReply": True},
        {"name": "Support Acknowledgment", "category": "support", "body": "Hi {{name}}, we've received your request and are looking into it. We'll get back to you shortly.", "variables": ["name"], "isQuickReply": True},
        {"name": "Product Inquiry Reply", "category": "sales", "body": "Hi {{name}}, thanks for your interest! Here's what we offer:\n\n{{productInfo}}\n\nWould you like more details?", "variables": ["name", "productInfo"], "isQuickReply": False},
        {"name": "Appointment Confirmation", "category": "scheduling", "body": "Hi {{name}}, your appointment is confirmed for {{date}} at {{time}}. See you then!", "variables": ["name", "date", "time"], "isQuickReply": False},
    ]

    for t in templates:
        vtstorage.insert_one(collection=TEMPLATES_COLLECTION, set_object={
            "_id": str(uuid.uuid4()),
            **t,
            "createdAt": (now - timedelta(days=15)).isoformat(),
            "updatedAt": now.isoformat(),
            "createdBy": admin_id,
            "usageCount": 0,
        })

    vtlog.info("seed_complete", contacts=len(contacts), conversations=len(conv_ids), tasks=len(tasks))


if __name__ == "__main__":
    seed()
    print("Seed complete!")
