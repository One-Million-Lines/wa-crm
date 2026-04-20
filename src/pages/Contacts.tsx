import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/apiClient';
import type { Contact } from '@/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  Search, Plus, Phone, Tag, Clock, Users, MoreVertical, Edit, Trash2, Eye,
} from 'lucide-react';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatDistanceToNow } from 'date-fns';

const stages = [
  { value: 'new_lead', label: 'New Lead', color: 'bg-blue-500' },
  { value: 'active_lead', label: 'Active Lead', color: 'bg-violet-500' },
  { value: 'customer', label: 'Customer', color: 'bg-emerald-500' },
  { value: 'repeat_customer', label: 'Repeat Customer', color: 'bg-green-600' },
  { value: 'support_case', label: 'Support Case', color: 'bg-orange-500' },
  { value: 'inactive', label: 'Inactive', color: 'bg-gray-400' },
  { value: 'blocked', label: 'Blocked', color: 'bg-red-500' },
];

const stageColor = (stage: string) => stages.find(s => s.value === stage)?.color || 'bg-gray-400';

export default function Contacts() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [filterStage, setFilterStage] = useState('');
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ fullName: '', phone: '', tags: '', stage: 'new_lead', source: 'whatsapp', notes: '' });

  const { data, isLoading } = useQuery({
    queryKey: ['contacts', search, filterStage],
    queryFn: () => api.getContacts({ search, stage: filterStage }),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.createContact(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      setShowCreate(false);
      setForm({ fullName: '', phone: '', tags: '', stage: 'new_lead', source: 'whatsapp', notes: '' });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteContact(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      setSelectedContact(null);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => api.updateContact(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
    },
  });

  const contacts = data?.contacts || [];
  const total = data?.total || 0;

  const initials = (name: string) => name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '?';

  return (
    <div className="flex h-full">
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="h-14 border-b flex items-center justify-between px-6 bg-card shrink-0">
          <div className="flex items-center gap-3">
            <Users className="w-5 h-5 text-primary" />
            <h1 className="font-semibold">Contacts</h1>
            <Badge variant="secondary" className="text-xs">{total}</Badge>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 w-4 h-4 text-muted-foreground" />
              <Input placeholder="Search..." className="pl-8 h-9 w-56" value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            <Select value={filterStage} onValueChange={setFilterStage}>
              <SelectTrigger className="h-9 w-36">
                <SelectValue placeholder="All stages" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All stages</SelectItem>
                {stages.map(s => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}
              </SelectContent>
            </Select>
            <Dialog open={showCreate} onOpenChange={setShowCreate}>
              <DialogTrigger asChild>
                <Button size="sm" className="gap-1"><Plus className="w-4 h-4" /> Add Contact</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader><DialogTitle>New Contact</DialogTitle></DialogHeader>
                <div className="space-y-3 mt-2">
                  <div className="grid grid-cols-2 gap-3">
                    <div><Label>Full Name</Label><Input value={form.fullName} onChange={e => setForm({ ...form, fullName: e.target.value })} /></div>
                    <div><Label>Phone</Label><Input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="+41..." /></div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label>Stage</Label>
                      <Select value={form.stage} onValueChange={v => setForm({ ...form, stage: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>{stages.map(s => <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Source</Label>
                      <Select value={form.source} onValueChange={v => setForm({ ...form, source: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="whatsapp">WhatsApp</SelectItem>
                          <SelectItem value="website">Website</SelectItem>
                          <SelectItem value="referral">Referral</SelectItem>
                          <SelectItem value="ads">Ads</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div><Label>Tags (comma separated)</Label><Input value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })} placeholder="vip, lead" /></div>
                  <div><Label>Notes</Label><Textarea value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} /></div>
                  <Button className="w-full" onClick={() => createMutation.mutate({ ...form, tags: form.tags.split(',').map(t => t.trim()).filter(Boolean) })} disabled={createMutation.isPending}>
                    {createMutation.isPending ? 'Creating...' : 'Create Contact'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Table */}
        <ScrollArea className="flex-1">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Contact</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Stage</TableHead>
                <TableHead>Tags</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Last Active</TableHead>
                <TableHead className="w-10"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground">Loading...</TableCell></TableRow>
              ) : contacts.length === 0 ? (
                <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground py-8">No contacts found</TableCell></TableRow>
              ) : contacts.map((c) => (
                <TableRow key={c.id} className="cursor-pointer" onClick={() => setSelectedContact(c)}>
                  <TableCell>
                    <div className="flex items-center gap-2.5">
                      <Avatar className="w-8 h-8">
                        <AvatarFallback className="text-xs bg-primary/10 text-primary">{initials(c.fullName)}</AvatarFallback>
                      </Avatar>
                      <span className="font-medium text-sm">{c.fullName}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{c.phone}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1.5">
                      <span className={`w-2 h-2 rounded-full ${stageColor(c.stage)}`} />
                      <span className="text-xs capitalize">{c.stage?.replace(/_/g, ' ')}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1 flex-wrap">{c.tags?.slice(0, 3).map(t => <Badge key={t} variant="secondary" className="text-[10px]">{t}</Badge>)}</div>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground capitalize">{c.source}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {c.lastInteraction ? formatDistanceToNow(new Date(c.lastInteraction), { addSuffix: true }) : '—'}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild onClick={e => e.stopPropagation()}>
                        <Button variant="ghost" size="icon" className="h-7 w-7"><MoreVertical className="w-3.5 h-3.5" /></Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); setSelectedContact(c); }}><Eye className="w-4 h-4 mr-2" /> View</DropdownMenuItem>
                        <DropdownMenuItem className="text-destructive" onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(c.id); }}><Trash2 className="w-4 h-4 mr-2" /> Delete</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ScrollArea>
      </div>

      {/* Contact Detail Sidebar */}
      {selectedContact && (
        <div className="w-80 border-l bg-card flex flex-col shrink-0">
          <div className="p-4 border-b flex items-center justify-between">
            <h3 className="text-sm font-medium">Contact Profile</h3>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setSelectedContact(null)}>
              <span className="text-lg leading-none">&times;</span>
            </Button>
          </div>
          <ScrollArea className="flex-1 p-4">
            <div className="text-center mb-4">
              <Avatar className="w-16 h-16 mx-auto mb-2">
                <AvatarFallback className="text-lg bg-primary/10 text-primary">{initials(selectedContact.fullName)}</AvatarFallback>
              </Avatar>
              <h4 className="font-medium">{selectedContact.fullName}</h4>
              <p className="text-sm text-muted-foreground">{selectedContact.phone}</p>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Stage</span>
                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${stageColor(selectedContact.stage)}`} />
                  <span className="capitalize">{selectedContact.stage?.replace(/_/g, ' ')}</span>
                </div>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Source</span>
                <span className="capitalize">{selectedContact.source}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Opt-in</span>
                <Badge variant={selectedContact.optIn ? 'default' : 'destructive'} className="text-[10px]">
                  {selectedContact.optIn ? 'Yes' : 'No'}
                </Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Conversations</span>
                <span>{selectedContact.conversationCount}</span>
              </div>
              {selectedContact.tags?.length > 0 && (
                <div>
                  <span className="text-sm text-muted-foreground">Tags</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedContact.tags.map(t => <Badge key={t} variant="secondary" className="text-xs">{t}</Badge>)}
                  </div>
                </div>
              )}
              {selectedContact.notes && (
                <div>
                  <span className="text-sm text-muted-foreground">Notes</span>
                  <p className="text-sm bg-muted/50 rounded-lg p-2 mt-1">{selectedContact.notes}</p>
                </div>
              )}
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Created</span>
                <span className="text-xs">{selectedContact.createdAt ? formatDistanceToNow(new Date(selectedContact.createdAt), { addSuffix: true }) : '—'}</span>
              </div>
            </div>
          </ScrollArea>
        </div>
      )}
    </div>
  );
}
