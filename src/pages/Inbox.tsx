import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/apiClient';
import { useAuth } from '@/contexts/AuthContext';
import type { Conversation, Message } from '@/types';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  Search, Send, Filter, User, Phone, Tag, Clock, Bot, UserCheck,
  PauseCircle, MoreVertical, StickyNote, CheckSquare, Zap, X,
  MessageSquare, ChevronRight,
} from 'lucide-react';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { format, formatDistanceToNow } from 'date-fns';

const statusColors: Record<string, string> = {
  new: 'bg-blue-500',
  open: 'bg-emerald-500',
  assigned: 'bg-violet-500',
  waiting_on_customer: 'bg-amber-500',
  waiting_on_team: 'bg-orange-500',
  automated: 'bg-cyan-500',
  paused: 'bg-gray-400',
  resolved: 'bg-green-600',
  archived: 'bg-gray-300',
};

const statusLabels: Record<string, string> = {
  new: 'New',
  open: 'Open',
  assigned: 'Assigned',
  waiting_on_customer: 'Waiting on Customer',
  waiting_on_team: 'Waiting on Team',
  automated: 'Automated',
  paused: 'Paused',
  resolved: 'Resolved',
  archived: 'Archived',
};

const senderTypeIcon: Record<string, typeof Bot> = {
  customer: User,
  human: UserCheck,
  automation: Bot,
  system: Zap,
};

export default function Inbox() {
  const { userId } = useAuth();
  const queryClient = useQueryClient();
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [messageText, setMessageText] = useState('');
  const [showProfile, setShowProfile] = useState(false);
  const [noteText, setNoteText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: convsData, isLoading: convsLoading } = useQuery({
    queryKey: ['conversations', filterStatus, searchQuery],
    queryFn: () => api.getConversations({ status: filterStatus, search: searchQuery }),
    refetchInterval: 5000,
  });

  const selectedConv = convsData?.conversations.find(c => c.id === selectedConvId);

  const { data: convDetail } = useQuery({
    queryKey: ['conversation', selectedConvId],
    queryFn: () => api.getConversation(selectedConvId!),
    enabled: !!selectedConvId,
  });

  const { data: messagesData } = useQuery({
    queryKey: ['messages', selectedConvId],
    queryFn: () => api.getMessages(selectedConvId!, { limit: 100 }),
    enabled: !!selectedConvId,
    refetchInterval: 3000,
  });

  const sendMutation = useMutation({
    mutationFn: (text: string) => {
      const phone = (convDetail?.contact as any)?.phone || '';
      return api.sendMessage({
        conversationId: selectedConvId!,
        contactPhone: phone,
        text,
      });
    },
    onSuccess: () => {
      setMessageText('');
      queryClient.invalidateQueries({ queryKey: ['messages', selectedConvId] });
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });

  const updateConvMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => api.updateConversation(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
      queryClient.invalidateQueries({ queryKey: ['conversation', selectedConvId] });
    },
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messagesData?.messages.length]);

  const handleSend = () => {
    if (!messageText.trim() || !selectedConvId) return;
    sendMutation.mutate(messageText.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const conversations = convsData?.conversations || [];
  const messages = messagesData?.messages || [];
  const contact = convDetail?.contact as any;

  const initials = (name: string) => name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '?';

  return (
    <div className="flex h-full">
      {/* Conversation List */}
      <div className="w-80 border-r flex flex-col bg-card shrink-0">
        <div className="p-3 border-b space-y-2">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search conversations..."
                className="pl-8 h-9"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-9 h-9 p-0 justify-center">
                <Filter className="w-4 h-4" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {Object.entries(statusLabels).map(([key, label]) => (
                  <SelectItem key={key} value={key}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <ScrollArea className="flex-1">
          {convsLoading ? (
            <div className="p-4 text-sm text-muted-foreground text-center">Loading...</div>
          ) : conversations.length === 0 ? (
            <div className="p-8 text-center">
              <MessageSquare className="w-10 h-10 mx-auto text-muted-foreground/40 mb-2" />
              <p className="text-sm text-muted-foreground">No conversations found</p>
            </div>
          ) : (
            conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => { setSelectedConvId(conv.id); setShowProfile(false); }}
                className={cn(
                  "w-full text-left px-3 py-3 border-b hover:bg-muted/50 transition-colors",
                  selectedConvId === conv.id && "bg-primary/5 border-l-2 border-l-primary"
                )}
              >
                <div className="flex items-start gap-2.5">
                  <Avatar className="w-9 h-9 shrink-0 mt-0.5">
                    <AvatarFallback className="text-xs bg-primary/10 text-primary">
                      {initials(conv.contact?.fullName || '')}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span className="font-medium text-sm truncate">{conv.contact?.fullName || 'Unknown'}</span>
                      <span className="text-[10px] text-muted-foreground shrink-0">
                        {conv.lastMessageAt ? formatDistanceToNow(new Date(conv.lastMessageAt), { addSuffix: false }) : ''}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground truncate mt-0.5">{conv.lastMessagePreview || 'No messages'}</p>
                    <div className="flex items-center gap-1.5 mt-1">
                      <span className={cn("w-1.5 h-1.5 rounded-full", statusColors[conv.status] || 'bg-gray-400')} />
                      <span className="text-[10px] text-muted-foreground">{statusLabels[conv.status] || conv.status}</span>
                      {conv.unreadCount > 0 && (
                        <Badge variant="default" className="h-4 min-w-4 text-[10px] px-1 ml-auto">
                          {conv.unreadCount}
                        </Badge>
                      )}
                      {conv.lastSenderType === 'automation' && (
                        <Bot className="w-3 h-3 text-cyan-500 ml-auto" />
                      )}
                    </div>
                  </div>
                </div>
              </button>
            ))
          )}
        </ScrollArea>
      </div>

      {/* Conversation Panel */}
      {selectedConvId && convDetail ? (
        <div className="flex-1 flex flex-col min-w-0">
          {/* Header */}
          <div className="h-14 border-b flex items-center justify-between px-4 bg-card shrink-0">
            <div className="flex items-center gap-3">
              <Avatar className="w-8 h-8">
                <AvatarFallback className="text-xs bg-primary/10 text-primary">
                  {initials(contact?.fullName || '')}
                </AvatarFallback>
              </Avatar>
              <div>
                <h3 className="text-sm font-medium">{contact?.fullName || 'Unknown'}</h3>
                <div className="flex items-center gap-2">
                  <span className={cn("w-1.5 h-1.5 rounded-full", statusColors[convDetail.status])} />
                  <span className="text-xs text-muted-foreground">{statusLabels[convDetail.status]}</span>
                  {convDetail.automationState === 'paused' && (
                    <Badge variant="outline" className="text-[10px] h-4 gap-0.5">
                      <PauseCircle className="w-2.5 h-2.5" /> Automation paused
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Select
                value={convDetail.status}
                onValueChange={(v) => updateConvMutation.mutate({ id: selectedConvId, data: { status: v } })}
              >
                <SelectTrigger className="h-8 text-xs w-auto gap-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(statusLabels).map(([key, label]) => (
                    <SelectItem key={key} value={key}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setShowProfile(!showProfile)}
              >
                <User className="w-4 h-4" />
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => updateConvMutation.mutate({
                    id: selectedConvId,
                    data: { assignedTo: userId }
                  })}>
                    <UserCheck className="w-4 h-4 mr-2" /> Assign to me
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => updateConvMutation.mutate({
                    id: selectedConvId,
                    data: { automationState: convDetail.automationState === 'paused' ? 'enabled' : 'paused' }
                  })}>
                    <Zap className="w-4 h-4 mr-2" />
                    {convDetail.automationState === 'paused' ? 'Enable automation' : 'Pause automation'}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => updateConvMutation.mutate({
                    id: selectedConvId,
                    data: { status: 'resolved' }
                  })}>
                    <CheckSquare className="w-4 h-4 mr-2" /> Mark resolved
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => updateConvMutation.mutate({
                    id: selectedConvId,
                    data: { status: 'archived' }
                  })}>
                    <X className="w-4 h-4 mr-2" /> Archive
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {/* Messages */}
          <ScrollArea className="flex-1 p-4">
            <div className="max-w-2xl mx-auto space-y-3">
              {messages.map((msg) => {
                const isInbound = msg.direction === 'inbound';
                const SenderIcon = senderTypeIcon[msg.senderType] || User;
                return (
                  <div key={msg.id} className={cn("flex gap-2", isInbound ? "justify-start" : "justify-end")}>
                    {isInbound && (
                      <Avatar className="w-7 h-7 shrink-0 mt-1">
                        <AvatarFallback className="text-[10px] bg-muted"><SenderIcon className="w-3.5 h-3.5" /></AvatarFallback>
                      </Avatar>
                    )}
                    <div className={cn(
                      "max-w-[70%] rounded-2xl px-3.5 py-2 text-sm",
                      isInbound
                        ? "bg-muted text-foreground rounded-bl-md"
                        : msg.senderType === 'automation'
                          ? "bg-cyan-500/10 text-foreground border border-cyan-500/20 rounded-br-md"
                          : "bg-primary text-primary-foreground rounded-br-md"
                    )}>
                      {msg.senderType !== 'customer' && (
                        <div className="flex items-center gap-1 mb-0.5">
                          <SenderIcon className="w-3 h-3 opacity-60" />
                          <span className="text-[10px] opacity-60">{msg.senderName}</span>
                        </div>
                      )}
                      <p className="whitespace-pre-wrap">{msg.text}</p>
                      <div className={cn(
                        "text-[10px] mt-1 flex items-center gap-1",
                        isInbound ? "text-muted-foreground" : "opacity-70"
                      )}>
                        {format(new Date(msg.timestamp), 'HH:mm')}
                        {!isInbound && msg.status && (
                          <span className="capitalize">· {msg.status}</span>
                        )}
                      </div>
                    </div>
                    {!isInbound && (
                      <Avatar className="w-7 h-7 shrink-0 mt-1">
                        <AvatarFallback className="text-[10px] bg-primary/10 text-primary">
                          <SenderIcon className="w-3.5 h-3.5" />
                        </AvatarFallback>
                      </Avatar>
                    )}
                  </div>
                );
              })}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="border-t p-3 bg-card shrink-0">
            <div className="max-w-2xl mx-auto flex gap-2">
              <Textarea
                placeholder="Type a message..."
                className="min-h-[40px] max-h-32 resize-none text-sm"
                rows={1}
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                onKeyDown={handleKeyDown}
              />
              <Button
                size="icon"
                className="shrink-0"
                onClick={handleSend}
                disabled={!messageText.trim() || sendMutation.isPending}
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center bg-muted/20">
          <div className="text-center">
            <MessageSquare className="w-12 h-12 mx-auto text-muted-foreground/30 mb-3" />
            <h3 className="font-medium text-muted-foreground">Select a conversation</h3>
            <p className="text-sm text-muted-foreground/60 mt-1">Choose from the left panel to start</p>
          </div>
        </div>
      )}

      {/* Contact Profile Sidebar */}
      {showProfile && contact && (
        <div className="w-72 border-l bg-card flex flex-col shrink-0">
          <div className="p-4 border-b flex items-center justify-between">
            <h3 className="text-sm font-medium">Contact Details</h3>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setShowProfile(false)}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          <ScrollArea className="flex-1 p-4 space-y-4">
            <div className="text-center mb-4">
              <Avatar className="w-16 h-16 mx-auto mb-2">
                <AvatarFallback className="text-lg bg-primary/10 text-primary">
                  {initials(contact.fullName)}
                </AvatarFallback>
              </Avatar>
              <h4 className="font-medium">{contact.fullName}</h4>
              <p className="text-sm text-muted-foreground">{contact.phone}</p>
            </div>

            <Separator />

            <div className="space-y-3 mt-4">
              <div className="flex items-center gap-2 text-sm">
                <Tag className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="text-muted-foreground">Stage:</span>
                <Badge variant="outline" className="text-xs capitalize">{contact.stage?.replace(/_/g, ' ')}</Badge>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Phone className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="text-muted-foreground">Source:</span>
                <span className="capitalize">{contact.source}</span>
              </div>
              {contact.tags?.length > 0 && (
                <div className="flex items-start gap-2 text-sm">
                  <Tag className="w-3.5 h-3.5 text-muted-foreground mt-0.5" />
                  <div className="flex flex-wrap gap-1">
                    {contact.tags.map((t: string) => (
                      <Badge key={t} variant="secondary" className="text-[10px]">{t}</Badge>
                    ))}
                  </div>
                </div>
              )}
              {contact.lastInteraction && (
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="w-3.5 h-3.5 text-muted-foreground" />
                  <span className="text-muted-foreground">Last active:</span>
                  <span>{formatDistanceToNow(new Date(contact.lastInteraction), { addSuffix: true })}</span>
                </div>
              )}
              {contact.notes && (
                <div className="mt-3">
                  <div className="flex items-center gap-1.5 text-sm text-muted-foreground mb-1">
                    <StickyNote className="w-3.5 h-3.5" /> Notes
                  </div>
                  <p className="text-sm bg-muted/50 rounded-lg p-2">{contact.notes}</p>
                </div>
              )}
            </div>

            {/* Internal Notes */}
            <Separator className="my-4" />
            <div>
              <div className="flex items-center gap-1.5 text-sm text-muted-foreground mb-2">
                <StickyNote className="w-3.5 h-3.5" /> Internal Notes
              </div>
              <Textarea
                placeholder="Add internal note..."
                className="text-sm min-h-[60px]"
                value={noteText || convDetail?.internalNotes || ''}
                onChange={(e) => setNoteText(e.target.value)}
              />
              <Button
                size="sm"
                variant="outline"
                className="mt-2 w-full text-xs"
                onClick={() => {
                  if (selectedConvId) {
                    updateConvMutation.mutate({ id: selectedConvId, data: { internalNotes: noteText } });
                  }
                }}
              >
                Save Note
              </Button>
            </div>
          </ScrollArea>
        </div>
      )}
    </div>
  );
}
