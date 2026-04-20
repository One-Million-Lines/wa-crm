import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/apiClient';
import type { Automation } from '@/types';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Zap, Plus, Play, Pause, MoreVertical, Trash2, ArrowRight,
  MessageSquare, Tag, UserCheck, Bell, Clock, Shield, Edit,
} from 'lucide-react';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatDistanceToNow } from 'date-fns';

const triggerLabels: Record<string, { label: string; icon: typeof MessageSquare }> = {
  new_inbound_message: { label: 'New Inbound Message', icon: MessageSquare },
  first_message_new_contact: { label: 'First Message from New Contact', icon: MessageSquare },
  no_team_reply_timeout: { label: 'No Team Reply Timeout', icon: Clock },
  no_customer_reply_timeout: { label: 'No Customer Reply Timeout', icon: Clock },
  conversation_tagged: { label: 'Conversation Tagged', icon: Tag },
  conversation_assigned: { label: 'Conversation Assigned', icon: UserCheck },
  contact_created: { label: 'Contact Created', icon: UserCheck },
  task_completed: { label: 'Task Completed', icon: Zap },
  keyword_detected: { label: 'Keyword Detected', icon: MessageSquare },
  business_hours_event: { label: 'Business Hours Event', icon: Clock },
};

const actionLabels: Record<string, string> = {
  send_message: 'Send Message',
  send_template: 'Send Template',
  assign_conversation: 'Assign Conversation',
  create_task: 'Create Task',
  add_tag: 'Add Tag',
  change_status: 'Change Status',
  notify_team: 'Notify Team',
  pause_automation: 'Pause Automation',
  escalate_to_human: 'Escalate to Human',
  add_note: 'Add Internal Note',
  update_contact_field: 'Update Contact Field',
};

export default function Automations() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: '', description: '', trigger: 'new_inbound_message',
    actionType: 'send_message', actionValue: '', requiresApproval: false,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['automations'],
    queryFn: () => api.getAutomations(),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.createAutomation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['automations'] });
      setShowCreate(false);
      setForm({ name: '', description: '', trigger: 'new_inbound_message', actionType: 'send_message', actionValue: '', requiresApproval: false });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => api.updateAutomation(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['automations'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteAutomation(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['automations'] }),
  });

  const automations = data?.automations || [];

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 border-b flex items-center justify-between px-6 bg-card shrink-0">
        <div className="flex items-center gap-3">
          <Zap className="w-5 h-5 text-primary" />
          <h1 className="font-semibold">Automations</h1>
          <Badge variant="secondary" className="text-xs">{automations.length}</Badge>
        </div>
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogTrigger asChild>
            <Button size="sm" className="gap-1"><Plus className="w-4 h-4" /> New Rule</Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader><DialogTitle>Create Automation Rule</DialogTitle></DialogHeader>
            <div className="space-y-3 mt-2">
              <div><Label>Name</Label><Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g. Welcome new contacts" /></div>
              <div><Label>Description</Label><Textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={2} /></div>
              <div>
                <Label>Trigger</Label>
                <Select value={form.trigger} onValueChange={v => setForm({ ...form, trigger: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {Object.entries(triggerLabels).map(([k, v]) => (
                      <SelectItem key={k} value={k}>{v.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Action</Label>
                <Select value={form.actionType} onValueChange={v => setForm({ ...form, actionType: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {Object.entries(actionLabels).map(([k, v]) => (
                      <SelectItem key={k} value={k}>{v}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div><Label>Action Value</Label><Input value={form.actionValue} onChange={e => setForm({ ...form, actionValue: e.target.value })} placeholder="Message text, tag name, etc." /></div>
              <div className="flex items-center gap-2">
                <Switch checked={form.requiresApproval} onCheckedChange={v => setForm({ ...form, requiresApproval: v })} />
                <Label className="text-sm">Requires human approval before executing</Label>
              </div>
              <Button className="w-full" onClick={() => createMutation.mutate({
                name: form.name,
                description: form.description,
                trigger: form.trigger,
                conditions: [],
                actions: [{ type: form.actionType, value: form.actionValue }],
                requiresApproval: form.requiresApproval,
              })} disabled={!form.name || createMutation.isPending}>
                {createMutation.isPending ? 'Creating...' : 'Create Rule'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <ScrollArea className="flex-1 p-6">
        {isLoading ? (
          <div className="text-center text-muted-foreground py-12">Loading automations...</div>
        ) : automations.length === 0 ? (
          <div className="text-center py-12">
            <Zap className="w-10 h-10 mx-auto text-muted-foreground/40 mb-2" />
            <p className="text-muted-foreground">No automation rules yet</p>
            <p className="text-sm text-muted-foreground/60 mt-1">Create rules to automate repetitive tasks</p>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-3">
            {automations.map((auto) => {
              const trigger = triggerLabels[auto.trigger];
              const TriggerIcon = trigger?.icon || Zap;
              return (
                <Card key={auto.id} className={cn(!auto.isActive && "opacity-60")}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        <div className={cn(
                          "w-9 h-9 rounded-lg flex items-center justify-center shrink-0",
                          auto.isActive ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                        )}>
                          <TriggerIcon className="w-4.5 h-4.5" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium text-sm">{auto.name}</h3>
                            {auto.requiresApproval && (
                              <Badge variant="outline" className="text-[10px] gap-0.5 h-4">
                                <Shield className="w-2.5 h-2.5" /> Approval
                              </Badge>
                            )}
                          </div>
                          {auto.description && <p className="text-xs text-muted-foreground mt-0.5">{auto.description}</p>}
                          <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                            <Badge variant="secondary" className="text-[10px]">{trigger?.label || auto.trigger}</Badge>
                            <ArrowRight className="w-3 h-3" />
                            {auto.actions.map((a, i) => (
                              <Badge key={i} variant="outline" className="text-[10px]">{actionLabels[a.type] || a.type}</Badge>
                            ))}
                          </div>
                          {auto.executionCount > 0 && (
                            <p className="text-[10px] text-muted-foreground mt-1">
                              Executed {auto.executionCount} times
                              {auto.lastExecutedAt && ` · Last: ${formatDistanceToNow(new Date(auto.lastExecutedAt), { addSuffix: true })}`}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={auto.isActive}
                          onCheckedChange={(v) => updateMutation.mutate({ id: auto.id, data: { isActive: v } })}
                        />
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-7 w-7">
                              <MoreVertical className="w-3.5 h-3.5" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem className="text-destructive" onClick={() => deleteMutation.mutate(auto.id)}>
                              <Trash2 className="w-4 h-4 mr-2" /> Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
