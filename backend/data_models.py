from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Auth ──
class EmailRequest(BaseModel):
    email: str

class ChallengeResponse(BaseModel):
    challengeId: str

class LoginRequest(BaseModel):
    challengeId: str
    password: str

class TokenResponse(BaseModel):
    token: str
    email: str
    userId: str


# ── Contact ──
class ContactCreate(BaseModel):
    fullName: str
    phone: str
    tags: list[str] = []
    status: str = "new_lead"
    owner: Optional[str] = None
    stage: str = "new_lead"
    source: str = "whatsapp"
    notes: str = ""
    customFields: dict = {}
    optIn: bool = True

class ContactUpdate(BaseModel):
    fullName: Optional[str] = None
    phone: Optional[str] = None
    tags: Optional[list[str]] = None
    status: Optional[str] = None
    owner: Optional[str] = None
    stage: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    customFields: Optional[dict] = None
    optIn: Optional[bool] = None


# ── Conversation ──
class ConversationCreate(BaseModel):
    contactId: str
    status: str = "new"
    assignedTo: Optional[str] = None
    tags: list[str] = []
    automationState: str = "enabled"
    aiMode: str = "off"

class ConversationUpdate(BaseModel):
    status: Optional[str] = None
    assignedTo: Optional[str] = None
    tags: Optional[list[str]] = None
    automationState: Optional[str] = None
    aiMode: Optional[str] = None
    internalNotes: Optional[str] = None


# ── Message ──
class MessageSend(BaseModel):
    conversationId: str
    contactPhone: str
    type: str = "text"
    text: str = ""
    templateName: Optional[str] = None
    mediaUrl: Optional[str] = None

class MessageInbound(BaseModel):
    # Used by webhook
    from_phone: str = Field(..., alias="from")
    text: str = ""
    type: str = "text"
    timestamp: Optional[str] = None


# ── Task ──
class TaskCreate(BaseModel):
    title: str
    description: str = ""
    assignee: Optional[str] = None
    dueDate: Optional[str] = None
    priority: str = "medium"
    contactId: Optional[str] = None
    conversationId: Optional[str] = None
    status: str = "todo"

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee: Optional[str] = None
    dueDate: Optional[str] = None
    priority: Optional[str] = None
    contactId: Optional[str] = None
    conversationId: Optional[str] = None
    status: Optional[str] = None


# ── Automation ──
class AutomationCreate(BaseModel):
    name: str
    description: str = ""
    trigger: str
    conditions: list[dict] = []
    actions: list[dict] = []
    isActive: bool = True
    requiresApproval: bool = False

class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger: Optional[str] = None
    conditions: Optional[list[dict]] = None
    actions: Optional[list[dict]] = None
    isActive: Optional[bool] = None
    requiresApproval: Optional[bool] = None


# ── Template ──
class TemplateCreate(BaseModel):
    name: str
    category: str = "general"
    body: str
    variables: list[str] = []
    isQuickReply: bool = False

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    body: Optional[str] = None
    variables: Optional[list[str]] = None
    isQuickReply: Optional[bool] = None


# ── Settings ──
class BusinessSettingsUpdate(BaseModel):
    companyName: Optional[str] = None
    timezone: Optional[str] = None
    businessHours: Optional[dict] = None
    defaultQueue: Optional[str] = None

class WhatsAppSettingsUpdate(BaseModel):
    phoneNumberId: Optional[str] = None
    businessAccountId: Optional[str] = None
    accessToken: Optional[str] = None
    verifyToken: Optional[str] = None
    autoReplyEnabled: Optional[bool] = None
    offHoursMessage: Optional[str] = None
