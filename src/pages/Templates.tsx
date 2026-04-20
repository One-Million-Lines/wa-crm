import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/apiClient';
import type { Template } from '@/types';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  FileText, Plus, Search, Copy, MoreVertical, Trash2, MessageSquare, Zap,
} from 'lucide-react';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const categories = [
  { value: 'general', label: 'General' },
  { value: 'onboarding', label: 'Onboarding' },
  { value: 'sales', label: 'Sales' },
  { value: 'support', label: 'Support' },
  { value: 'commerce', label: 'Commerce' },
  { value: 'scheduling', label: 'Scheduling' },
];

export default function Templates() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [tab, setTab] = useState('all');
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', category: 'general', body: '', variables: '', isQuickReply: false });

  const { data, isLoading } = useQuery({
    queryKey: ['templates', search, filterCategory, tab],
    queryFn: () => api.getTemplates({
      search,
      category: filterCategory,
      isQuickReply: tab === 'quick' ? 'true' : tab === 'templates' ? 'false' : '',
    }),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.createTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setShowCreate(false);
      setForm({ name: '', category: 'general', body: '', variables: '', isQuickReply: false });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteTemplate(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['templates'] }),
  });

  const templates = data?.templates || [];

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 border-b flex items-center justify-between px-6 bg-card shrink-0">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-primary" />
          <h1 className="font-semibold">Templates</h1>
          <Badge variant="secondary" className="text-xs">{templates.length}</Badge>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 w-4 h-4 text-muted-foreground" />
            <Input placeholder="Search..." className="pl-8 h-9 w-48" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="h-8">
              <TabsTrigger value="all" className="text-xs px-3 h-6">All</TabsTrigger>
              <TabsTrigger value="templates" className="text-xs px-3 h-6">Templates</TabsTrigger>
              <TabsTrigger value="quick" className="text-xs px-3 h-6">Quick Replies</TabsTrigger>
            </TabsList>
          </Tabs>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button size="sm" className="gap-1"><Plus className="w-4 h-4" /> New Template</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Create Template</DialogTitle></DialogHeader>
              <div className="space-y-3 mt-2">
                <div><Label>Name</Label><Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Category</Label>
                    <Select value={form.category} onValueChange={v => setForm({ ...form, category: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>{categories.map(c => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-end gap-2 pb-1">
                    <Switch checked={form.isQuickReply} onCheckedChange={v => setForm({ ...form, isQuickReply: v })} />
                    <Label className="text-sm">Quick Reply</Label>
                  </div>
                </div>
                <div>
                  <Label>Body</Label>
                  <Textarea value={form.body} onChange={e => setForm({ ...form, body: e.target.value })} rows={4}
                    placeholder="Use {{variable}} for dynamic content" />
                </div>
                <div><Label>Variables (comma separated)</Label><Input value={form.variables} onChange={e => setForm({ ...form, variables: e.target.value })} placeholder="name, company, date" /></div>
                <Button className="w-full" onClick={() => createMutation.mutate({
                  ...form,
                  variables: form.variables.split(',').map(v => v.trim()).filter(Boolean),
                })} disabled={!form.name || !form.body || createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Template'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <ScrollArea className="flex-1 p-6">
        {isLoading ? (
          <div className="text-center text-muted-foreground py-12">Loading templates...</div>
        ) : templates.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-10 h-10 mx-auto text-muted-foreground/40 mb-2" />
            <p className="text-muted-foreground">No templates found</p>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto grid gap-3 grid-cols-1 md:grid-cols-2">
            {templates.map((tpl) => (
              <Card key={tpl.id} className="group">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-sm">{tpl.name}</h3>
                        {tpl.isQuickReply && (
                          <Badge variant="outline" className="text-[10px] h-4 gap-0.5">
                            <Zap className="w-2.5 h-2.5" /> Quick
                          </Badge>
                        )}
                      </div>
                      <Badge variant="secondary" className="text-[10px] mt-1 capitalize">{tpl.category}</Badge>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-7 w-7 opacity-0 group-hover:opacity-100">
                          <MoreVertical className="w-3.5 h-3.5" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => navigator.clipboard.writeText(tpl.body)}>
                          <Copy className="w-4 h-4 mr-2" /> Copy body
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-destructive" onClick={() => deleteMutation.mutate(tpl.id)}>
                          <Trash2 className="w-4 h-4 mr-2" /> Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                  <div className="bg-muted/50 rounded-lg p-2.5 text-sm whitespace-pre-wrap">{tpl.body}</div>
                  {tpl.variables.length > 0 && (
                    <div className="flex items-center gap-1 mt-2 flex-wrap">
                      <span className="text-[10px] text-muted-foreground">Variables:</span>
                      {tpl.variables.map(v => (
                        <Badge key={v} variant="outline" className="text-[10px] font-mono">{`{{${v}}}`}</Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
