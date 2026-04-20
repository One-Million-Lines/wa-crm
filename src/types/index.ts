// ── Contact ──
export interface Contact {
  id: string;
  fullName: string;
  phone: string;
  tags: string[];
  status: string;
  owner: string | null;
  stage: string;
  source: string;
  notes: string;
  customFields: Record<string, any>;
  optIn: boolean;
  createdAt: string;
  updatedAt: string;
  lastInteraction: string | null;
  conversationCount: number;
  externalIds: Record<string, string>;
  activityTimeline: any[];
}

// ── Conversation ──
export interface Conversation {
  id: string;
  contactId: string;
  status: ConversationStatus;
  assignedTo: string | null;
  tags: string[];
  automationState: string;
  aiMode: string;
  createdAt: string;
  updatedAt: string;
  lastMessageAt: string;
  lastMessagePreview: string;
  lastSenderType: string;
  unreadCount: number;
  messageCount: number;
  internalNotes: string;
  slaState: string;
  contact?: {
    fullName: string;
    phone: string;
    tags: string[];
    stage: string;
  } | Contact;
}

export type ConversationStatus =
  | 'new' | 'open' | 'assigned' | 'waiting_on_customer'
  | 'waiting_on_team' | 'automated' | 'paused' | 'resolved' | 'archived';

// ── Message ──
export interface Message {
  id: string;
  conversationId: string;
  waMessageId: string;
  direction: 'inbound' | 'outbound';
  senderType: 'customer' | 'human' | 'automation' | 'system';
  senderId: string;
  senderName: string;
  type: string;
  text: string;
  templateName?: string;
  mediaUrl?: string;
  status: string;
  timestamp: string;
  metadata: Record<string, any>;
}

// ── Task ──
export interface Task {
  id: string;
  title: string;
  description: string;
  assignee: string | null;
  dueDate: string | null;
  priority: TaskPriority;
  contactId: string | null;
  conversationId: string | null;
  status: TaskStatus;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  comments: any[];
}

export type TaskStatus = 'todo' | 'in_progress' | 'waiting' | 'done' | 'canceled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

// ── Automation ──
export interface Automation {
  id: string;
  name: string;
  description: string;
  trigger: string;
  conditions: AutomationCondition[];
  actions: AutomationAction[];
  isActive: boolean;
  requiresApproval: boolean;
  createdAt: string;
  updatedAt: string;
  executionCount: number;
  lastExecutedAt: string | null;
}

export interface AutomationCondition {
  type: string;
  [key: string]: any;
}

export interface AutomationAction {
  type: string;
  [key: string]: any;
}

// ── Template ──
export interface Template {
  id: string;
  name: string;
  category: string;
  body: string;
  variables: string[];
  isQuickReply: boolean;
  createdAt: string;
  updatedAt: string;
  usageCount: number;
}

// ── Analytics ──
export interface AnalyticsOverview {
  totalContacts: number;
  totalConversations: number;
  activeConversations: number;
  totalMessages: number;
  messagesSent: number;
  messagesReceived: number;
  totalTasks: number;
  openTasks: number;
  totalAutomations: number;
  activeAutomations: number;
  contactStages: Record<string, number>;
  conversationStatuses: Record<string, number>;
}

export interface TeamMember {
  userId: string;
  name: string;
  email: string;
  role: string;
  assignedConversations: number;
  assignedTasks: number;
  messagesSent: number;
}

// ── Module ──
export interface Module {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  installed: boolean;
  installedAt?: string;
  status?: string;
  config?: Record<string, any>;
}

// ── Settings ──
export interface BusinessSettings {
  id: string;
  companyName: string;
  timezone: string;
  businessHours: Record<string, { start: string; end: string; enabled: boolean }>;
  defaultQueue: string;
}

export interface WhatsAppSettings {
  id: string;
  phoneNumberId: string;
  businessAccountId: string;
  accessToken: string;
  verifyToken: string;
  connected: boolean;
  autoReplyEnabled: boolean;
  offHoursMessage: string;
}

export interface TeamUser {
  id: string;
  name: string;
  email: string;
  role: string;
  createdAt: string;
}
