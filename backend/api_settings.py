from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from api_shared import vtstorage, vtlog, get_current_user, SETTINGS_COLLECTION, MODULES_COLLECTION
from data_models import BusinessSettingsUpdate, WhatsAppSettingsUpdate

router = APIRouter(tags=["settings"])


# ── Business Settings ──
@router.get("/settings/business")
async def get_business_settings(user: dict = Depends(get_current_user)):
    doc = vtstorage.get_one(collection=SETTINGS_COLLECTION, query={"_id": "business"})
    if not doc:
        doc = {
            "_id": "business",
            "companyName": "My Business",
            "timezone": "UTC",
            "businessHours": {
                "monday": {"start": "09:00", "end": "18:00", "enabled": True},
                "tuesday": {"start": "09:00", "end": "18:00", "enabled": True},
                "wednesday": {"start": "09:00", "end": "18:00", "enabled": True},
                "thursday": {"start": "09:00", "end": "18:00", "enabled": True},
                "friday": {"start": "09:00", "end": "18:00", "enabled": True},
                "saturday": {"start": "10:00", "end": "14:00", "enabled": False},
                "sunday": {"start": "10:00", "end": "14:00", "enabled": False},
            },
            "defaultQueue": "general",
        }
        vtstorage.insert_one(collection=SETTINGS_COLLECTION, set_object=doc)
    doc["id"] = doc.pop("_id")
    return doc


@router.put("/settings/business")
async def update_business_settings(data: BusinessSettingsUpdate, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()
    vtstorage.update_one(collection=SETTINGS_COLLECTION, query={"_id": "business"}, set_object={"$set": updates})
    doc = vtstorage.get_one(collection=SETTINGS_COLLECTION, query={"_id": "business"})
    doc["id"] = doc.pop("_id")
    return doc


# ── WhatsApp Settings ──
@router.get("/settings/whatsapp")
async def get_whatsapp_settings(user: dict = Depends(get_current_user)):
    doc = vtstorage.get_one(collection=SETTINGS_COLLECTION, query={"_id": "whatsapp"})
    if not doc:
        doc = {
            "_id": "whatsapp",
            "phoneNumberId": "",
            "businessAccountId": "",
            "accessToken": "",
            "verifyToken": "",
            "connected": False,
            "autoReplyEnabled": False,
            "offHoursMessage": "Thanks for reaching out! We'll get back to you during business hours.",
        }
        vtstorage.insert_one(collection=SETTINGS_COLLECTION, set_object=doc)
    doc["id"] = doc.pop("_id")
    # Mask sensitive token
    if doc.get("accessToken"):
        doc["accessToken"] = doc["accessToken"][:8] + "..." if len(doc["accessToken"]) > 8 else "***"
    return doc


@router.put("/settings/whatsapp")
async def update_whatsapp_settings(data: WhatsAppSettingsUpdate, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()
    if updates.get("accessToken") and updates["accessToken"].endswith("..."):
        del updates["accessToken"]  # Don't overwrite with masked value
    vtstorage.update_one(collection=SETTINGS_COLLECTION, query={"_id": "whatsapp"}, set_object={"$set": updates})
    doc = vtstorage.get_one(collection=SETTINGS_COLLECTION, query={"_id": "whatsapp"})
    doc["id"] = doc.pop("_id")
    return doc


# ── Team / Users ──
@router.get("/settings/team")
async def get_team(user: dict = Depends(get_current_user)):
    from api_shared import USERS_COLLECTION
    users = vtstorage.get_many(collection=USERS_COLLECTION, query={}, limit=100)
    result = []
    for u in users:
        result.append({
            "id": u["_id"],
            "name": u.get("name", ""),
            "email": u.get("email", ""),
            "role": u.get("role", "agent"),
            "createdAt": u.get("createdAt", ""),
        })
    return {"team": result}


# ── Modules / Integrations ──
@router.get("/modules")
async def list_modules(user: dict = Depends(get_current_user)):
    installed = vtstorage.get_many(collection=MODULES_COLLECTION, query={}, limit=100)
    installed_list = []
    for m in installed:
        m["id"] = m.pop("_id")
        installed_list.append(m)

    # Available modules catalog (hardcoded for now)
    available = [
        {
            "id": "crm-sync",
            "name": "CRM Sync",
            "description": "Sync contacts with HubSpot, Salesforce, or Pipedrive",
            "category": "crm",
            "icon": "database",
            "installed": any(m["id"] == "crm-sync" for m in installed_list),
        },
        {
            "id": "ecommerce",
            "name": "E-Commerce",
            "description": "Connect Shopify, WooCommerce for order lookups",
            "category": "commerce",
            "icon": "shopping-cart",
            "installed": any(m["id"] == "ecommerce" for m in installed_list),
        },
        {
            "id": "ai-assistant",
            "name": "AI Assistant",
            "description": "AI-powered reply suggestions and intent classification",
            "category": "ai",
            "icon": "brain",
            "installed": any(m["id"] == "ai-assistant" for m in installed_list),
        },
        {
            "id": "booking",
            "name": "Appointment Booking",
            "description": "Let customers book appointments via WhatsApp",
            "category": "scheduling",
            "icon": "calendar",
            "installed": any(m["id"] == "booking" for m in installed_list),
        },
        {
            "id": "helpdesk",
            "name": "Helpdesk Bridge",
            "description": "Connect Zendesk, Freshdesk, or Intercom",
            "category": "support",
            "icon": "headphones",
            "installed": any(m["id"] == "helpdesk" for m in installed_list),
        },
        {
            "id": "payments",
            "name": "Payment Tracker",
            "description": "Track and follow up on invoices and payments",
            "category": "finance",
            "icon": "credit-card",
            "installed": any(m["id"] == "payments" for m in installed_list),
        },
        {
            "id": "faq-bot",
            "name": "FAQ Bot",
            "description": "Automated FAQ responses from your knowledge base",
            "category": "ai",
            "icon": "message-circle",
            "installed": any(m["id"] == "faq-bot" for m in installed_list),
        },
        {
            "id": "loyalty",
            "name": "Loyalty Points",
            "description": "Manage customer loyalty programs and rewards",
            "category": "commerce",
            "icon": "award",
            "installed": any(m["id"] == "loyalty" for m in installed_list),
        },
    ]

    return {"installed": installed_list, "available": available}


@router.post("/modules/{module_id}/install")
async def install_module(module_id: str, user: dict = Depends(get_current_user)):
    existing = vtstorage.get_one(collection=MODULES_COLLECTION, query={"_id": module_id})
    if existing:
        raise HTTPException(status_code=400, detail="Module already installed")

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "_id": module_id,
        "installedAt": now,
        "installedBy": user["_id"],
        "status": "active",
        "config": {},
    }
    vtstorage.insert_one(collection=MODULES_COLLECTION, set_object=doc)
    vtlog.info("module_installed", module_id=module_id)
    doc["id"] = doc.pop("_id")
    return doc


@router.delete("/modules/{module_id}")
async def uninstall_module(module_id: str, user: dict = Depends(get_current_user)):
    existing = vtstorage.get_one(collection=MODULES_COLLECTION, query={"_id": module_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Module not installed")
    vtstorage.delete_one(collection=MODULES_COLLECTION, query={"_id": module_id})
    vtlog.info("module_uninstalled", module_id=module_id)
    return {"deleted": True}
