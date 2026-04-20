import type {
  Contact, Conversation, Message, Task, Automation, Template,
  AnalyticsOverview, TeamMember, Module, BusinessSettings,
  WhatsAppSettings, TeamUser,
} from '@/types';

const API_BASE = import.meta.env.VITE_API_BASE;
const STORAGE_KEY = 'wacrm_auth';

function getToken(): string | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw).token ?? null;
  } catch { /* ignore */ }
  return null;
}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(opts.body ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers: { ...headers, ...(opts.headers as Record<string, string> || {}) } });
  if (res.status === 401) {
    localStorage.removeItem(STORAGE_KEY);
    window.location.reload();
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  // Contacts
  getContacts: (params?: { search?: string; status?: string; tag?: string; owner?: string; stage?: string; limit?: number; skip?: number }) => {
    const q = new URLSearchParams();
    if (params?.search) q.set('search', params.search);
    if (params?.status) q.set('status', params.status);
    if (params?.tag) q.set('tag', params.tag);
    if (params?.owner) q.set('owner', params.owner);
    if (params?.stage) q.set('stage', params.stage);
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.skip) q.set('skip', String(params.skip));
    return req<{ contacts: Contact[]; total: number }>(`/contacts?${q}`);
  },
  getContact: (id: string) => req<Contact>(`/contacts/${id}`),
  createContact: (data: Partial<Contact>) => req<Contact>('/contacts', { method: 'POST', body: JSON.stringify(data) }),
  updateContact: (id: string, data: Partial<Contact>) => req<Contact>(`/contacts/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteContact: (id: string) => req<{ deleted: boolean }>(`/contacts/${id}`, { method: 'DELETE' }),

  // Conversations
  getConversations: (params?: { status?: string; assignedTo?: string; tag?: string; search?: string; unreadOnly?: boolean; limit?: number; skip?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set('status', params.status);
    if (params?.assignedTo) q.set('assignedTo', params.assignedTo);
    if (params?.tag) q.set('tag', params.tag);
    if (params?.search) q.set('search', params.search);
    if (params?.unreadOnly) q.set('unreadOnly', 'true');
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.skip) q.set('skip', String(params.skip));
    return req<{ conversations: Conversation[]; total: number }>(`/conversations?${q}`);
  },
  getConversation: (id: string) => req<Conversation>(`/conversations/${id}`),
  createConversation: (data: Partial<Conversation>) => req<Conversation>('/conversations', { method: 'POST', body: JSON.stringify(data) }),
  updateConversation: (id: string, data: Partial<Conversation>) => req<Conversation>(`/conversations/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  // Messages
  getMessages: (convId: string, params?: { limit?: number; skip?: number }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.skip) q.set('skip', String(params.skip));
    return req<{ messages: Message[]; total: number }>(`/conversations/${convId}/messages?${q}`);
  },
  sendMessage: (data: { conversationId: string; contactPhone: string; type?: string; text: string; templateName?: string; mediaUrl?: string }) =>
    req<Message>('/messages/send', { method: 'POST', body: JSON.stringify(data) }),

  // Tasks
  getTasks: (params?: { status?: string; assignee?: string; priority?: string; contactId?: string; conversationId?: string; limit?: number; skip?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set('status', params.status);
    if (params?.assignee) q.set('assignee', params.assignee);
    if (params?.priority) q.set('priority', params.priority);
    if (params?.contactId) q.set('contactId', params.contactId);
    if (params?.conversationId) q.set('conversationId', params.conversationId);
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.skip) q.set('skip', String(params.skip));
    return req<{ tasks: Task[]; total: number }>(`/tasks?${q}`);
  },
  getTask: (id: string) => req<Task>(`/tasks/${id}`),
  createTask: (data: Partial<Task>) => req<Task>('/tasks', { method: 'POST', body: JSON.stringify(data) }),
  updateTask: (id: string, data: Partial<Task>) => req<Task>(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteTask: (id: string) => req<{ deleted: boolean }>(`/tasks/${id}`, { method: 'DELETE' }),

  // Automations
  getAutomations: (params?: { isActive?: string; trigger?: string }) => {
    const q = new URLSearchParams();
    if (params?.isActive) q.set('isActive', params.isActive);
    if (params?.trigger) q.set('trigger', params.trigger);
    return req<{ automations: Automation[]; total: number }>(`/automations?${q}`);
  },
  getAutomation: (id: string) => req<Automation>(`/automations/${id}`),
  createAutomation: (data: Partial<Automation>) => req<Automation>('/automations', { method: 'POST', body: JSON.stringify(data) }),
  updateAutomation: (id: string, data: Partial<Automation>) => req<Automation>(`/automations/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteAutomation: (id: string) => req<{ deleted: boolean }>(`/automations/${id}`, { method: 'DELETE' }),

  // Templates
  getTemplates: (params?: { category?: string; isQuickReply?: string; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.category) q.set('category', params.category);
    if (params?.isQuickReply) q.set('isQuickReply', params.isQuickReply);
    if (params?.search) q.set('search', params.search);
    return req<{ templates: Template[]; total: number }>(`/templates?${q}`);
  },
  createTemplate: (data: Partial<Template>) => req<Template>('/templates', { method: 'POST', body: JSON.stringify(data) }),
  updateTemplate: (id: string, data: Partial<Template>) => req<Template>(`/templates/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteTemplate: (id: string) => req<{ deleted: boolean }>(`/templates/${id}`, { method: 'DELETE' }),

  // Analytics
  getAnalyticsOverview: () => req<AnalyticsOverview>('/analytics/overview'),
  getTeamStats: () => req<{ team: TeamMember[] }>('/analytics/team'),

  // Settings
  getBusinessSettings: () => req<BusinessSettings>('/settings/business'),
  updateBusinessSettings: (data: Partial<BusinessSettings>) => req<BusinessSettings>('/settings/business', { method: 'PUT', body: JSON.stringify(data) }),
  getWhatsAppSettings: () => req<WhatsAppSettings>('/settings/whatsapp'),
  updateWhatsAppSettings: (data: Partial<WhatsAppSettings>) => req<WhatsAppSettings>('/settings/whatsapp', { method: 'PUT', body: JSON.stringify(data) }),
  getTeam: () => req<{ team: TeamUser[] }>('/settings/team'),

  // Modules
  getModules: () => req<{ installed: Module[]; available: Module[] }>('/modules'),
  installModule: (id: string) => req<Module>(`/modules/${id}/install`, { method: 'POST' }),
  uninstallModule: (id: string) => req<{ deleted: boolean }>(`/modules/${id}`, { method: 'DELETE' }),
};
