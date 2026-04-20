import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/apiClient';
import type { Task } from '@/types';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  CheckSquare, Plus, Clock, AlertTriangle, MoreVertical, Trash2, Calendar,
  CircleDot, Circle, CheckCircle2, XCircle, Loader2,
} from 'lucide-react';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { format, formatDistanceToNow, isPast } from 'date-fns';
import { useAuth } from '@/contexts/AuthContext';

const statusConfig: Record<string, { label: string; icon: typeof Circle; color: string }> = {
  todo: { label: 'To Do', icon: Circle, color: 'text-blue-500' },
  in_progress: { label: 'In Progress', icon: Loader2, color: 'text-amber-500' },
  waiting: { label: 'Waiting', icon: Clock, color: 'text-orange-500' },
  done: { label: 'Done', icon: CheckCircle2, color: 'text-green-500' },
  canceled: { label: 'Canceled', icon: XCircle, color: 'text-gray-400' },
};

const priorityConfig: Record<string, { label: string; color: string; bgColor: string }> = {
  low: { label: 'Low', color: 'text-slate-500', bgColor: 'bg-slate-100' },
  medium: { label: 'Medium', color: 'text-blue-600', bgColor: 'bg-blue-50' },
  high: { label: 'High', color: 'text-orange-600', bgColor: 'bg-orange-50' },
  urgent: { label: 'Urgent', color: 'text-red-600', bgColor: 'bg-red-50' },
};

export default function Tasks() {
  const { userId } = useAuth();
  const queryClient = useQueryClient();
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [view, setView] = useState<'list' | 'board'>('list');
  const [form, setForm] = useState({ title: '', description: '', priority: 'medium', status: 'todo', dueDate: '' });

  const { data, isLoading } = useQuery({
    queryKey: ['tasks', filterStatus, filterPriority],
    queryFn: () => api.getTasks({ status: filterStatus, priority: filterPriority }),
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => api.createTask(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      setShowCreate(false);
      setForm({ title: '', description: '', priority: 'medium', status: 'todo', dueDate: '' });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => api.updateTask(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteTask(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const tasks = data?.tasks || [];
  const total = data?.total || 0;

  const boardStatuses = ['todo', 'in_progress', 'waiting', 'done'];

  const TaskCard = ({ task }: { task: Task }) => {
    const st = statusConfig[task.status] || statusConfig.todo;
    const pr = priorityConfig[task.priority] || priorityConfig.medium;
    const StatusIcon = st.icon;
    const overdue = task.dueDate && isPast(new Date(task.dueDate)) && !['done', 'canceled'].includes(task.status);

    return (
      <Card className="group">
        <CardContent className="p-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-2 flex-1 min-w-0">
              <button
                className="mt-0.5 shrink-0"
                onClick={() => updateMutation.mutate({
                  id: task.id,
                  data: { status: task.status === 'done' ? 'todo' : 'done' }
                })}
              >
                <StatusIcon className={cn("w-4 h-4", st.color)} />
              </button>
              <div className="min-w-0">
                <p className={cn("text-sm font-medium", task.status === 'done' && 'line-through text-muted-foreground')}>{task.title}</p>
                {task.description && <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{task.description}</p>}
                <div className="flex items-center gap-2 mt-2">
                  <Badge className={cn("text-[10px] h-4", pr.bgColor, pr.color)} variant="outline">{pr.label}</Badge>
                  {task.dueDate && (
                    <span className={cn("text-[10px] flex items-center gap-0.5", overdue ? "text-destructive" : "text-muted-foreground")}>
                      <Calendar className="w-3 h-3" />
                      {format(new Date(task.dueDate), 'MMM d')}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-6 w-6 opacity-0 group-hover:opacity-100">
                  <MoreVertical className="w-3.5 h-3.5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {Object.entries(statusConfig).map(([key, conf]) => (
                  <DropdownMenuItem key={key} onClick={() => updateMutation.mutate({ id: task.id, data: { status: key } })}>
                    <conf.icon className={cn("w-4 h-4 mr-2", conf.color)} /> {conf.label}
                  </DropdownMenuItem>
                ))}
                <DropdownMenuItem className="text-destructive" onClick={() => deleteMutation.mutate(task.id)}>
                  <Trash2 className="w-4 h-4 mr-2" /> Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-14 border-b flex items-center justify-between px-6 bg-card shrink-0">
        <div className="flex items-center gap-3">
          <CheckSquare className="w-5 h-5 text-primary" />
          <h1 className="font-semibold">Tasks</h1>
          <Badge variant="secondary" className="text-xs">{total}</Badge>
        </div>
        <div className="flex items-center gap-2">
          <Tabs value={view} onValueChange={(v: any) => setView(v)}>
            <TabsList className="h-8">
              <TabsTrigger value="list" className="text-xs px-3 h-6">List</TabsTrigger>
              <TabsTrigger value="board" className="text-xs px-3 h-6">Board</TabsTrigger>
            </TabsList>
          </Tabs>
          <Select value={filterPriority} onValueChange={setFilterPriority}>
            <SelectTrigger className="h-9 w-28">
              <SelectValue placeholder="Priority" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              {Object.entries(priorityConfig).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}
            </SelectContent>
          </Select>
          <Dialog open={showCreate} onOpenChange={setShowCreate}>
            <DialogTrigger asChild>
              <Button size="sm" className="gap-1"><Plus className="w-4 h-4" /> New Task</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Create Task</DialogTitle></DialogHeader>
              <div className="space-y-3 mt-2">
                <div><Label>Title</Label><Input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} /></div>
                <div><Label>Description</Label><Textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Priority</Label>
                    <Select value={form.priority} onValueChange={v => setForm({ ...form, priority: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>{Object.entries(priorityConfig).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div><Label>Due Date</Label><Input type="date" value={form.dueDate} onChange={e => setForm({ ...form, dueDate: e.target.value })} /></div>
                </div>
                <Button className="w-full" onClick={() => createMutation.mutate({
                  ...form,
                  assignee: userId,
                  dueDate: form.dueDate ? new Date(form.dueDate).toISOString() : undefined,
                })} disabled={!form.title || createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Task'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1 p-6">
        {isLoading ? (
          <div className="text-center text-muted-foreground py-12">Loading tasks...</div>
        ) : view === 'list' ? (
          <div className="max-w-3xl mx-auto space-y-2">
            {tasks.length === 0 ? (
              <div className="text-center py-12">
                <CheckSquare className="w-10 h-10 mx-auto text-muted-foreground/40 mb-2" />
                <p className="text-muted-foreground">No tasks yet</p>
              </div>
            ) : tasks.map(task => <TaskCard key={task.id} task={task} />)}
          </div>
        ) : (
          <div className="grid grid-cols-4 gap-4 min-w-[800px]">
            {boardStatuses.map(status => {
              const conf = statusConfig[status];
              const StatusIcon = conf.icon;
              const filtered = tasks.filter(t => t.status === status);
              return (
                <div key={status} className="space-y-2">
                  <div className="flex items-center gap-2 px-1 mb-2">
                    <StatusIcon className={cn("w-4 h-4", conf.color)} />
                    <span className="text-sm font-medium">{conf.label}</span>
                    <Badge variant="outline" className="text-[10px] ml-auto">{filtered.length}</Badge>
                  </div>
                  <div className="space-y-2">
                    {filtered.map(task => <TaskCard key={task.id} task={task} />)}
                    {filtered.length === 0 && (
                      <div className="text-xs text-muted-foreground text-center py-4 border border-dashed rounded-lg">
                        No tasks
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
