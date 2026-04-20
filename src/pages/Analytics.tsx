import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/apiClient';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  BarChart3, Users, MessageSquare, CheckSquare, TrendingUp, ArrowUp, ArrowDown,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts';

const COLORS = ['hsl(162,72%,40%)', 'hsl(25,95%,53%)', 'hsl(220,70%,55%)', 'hsl(340,75%,55%)', 'hsl(45,90%,50%)', 'hsl(280,60%,55%)'];

export default function Analytics() {
  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: () => api.getAnalyticsOverview(),
  });

  const { data: team, isLoading: loadingTeam } = useQuery({
    queryKey: ['analytics', 'team'],
    queryFn: () => api.getTeamStats(),
  });

  const stageData = overview ? Object.entries(overview.stage_breakdown || {}).map(([name, value]) => ({
    name: name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    value: value as number,
  })) : [];

  const convData = overview ? Object.entries(overview.conversation_status_breakdown || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: value as number,
  })) : [];

  const msgData = overview ? [
    { name: 'Sent', value: overview.messages_sent },
    { name: 'Received', value: overview.messages_received },
  ] : [];

  const teamMembers = team?.team || [];

  if (loadingOverview) return <div className="flex items-center justify-center h-full text-muted-foreground">Loading analytics...</div>;

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 border-b flex items-center px-6 bg-card shrink-0">
        <BarChart3 className="w-5 h-5 text-primary mr-3" />
        <h1 className="font-semibold">Analytics</h1>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-6 space-y-6 max-w-6xl mx-auto">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard title="Total Contacts" value={overview?.total_contacts || 0} icon={<Users className="w-4 h-4" />} />
            <KpiCard title="Open Conversations" value={overview?.open_conversations || 0} icon={<MessageSquare className="w-4 h-4" />} />
            <KpiCard title="Messages Sent" value={overview?.messages_sent || 0} icon={<TrendingUp className="w-4 h-4" />} />
            <KpiCard title="Messages Received" value={overview?.messages_received || 0} icon={<ArrowDown className="w-4 h-4" />} />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Stage Funnel */}
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Contact Stages</CardTitle></CardHeader>
              <CardContent className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stageData} layout="vertical">
                    <XAxis type="number" fontSize={11} />
                    <YAxis type="category" dataKey="name" fontSize={11} width={80} />
                    <Tooltip />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {stageData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Conversation Status */}
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Conversation Status</CardTitle></CardHeader>
              <CardContent className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={convData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                      {convData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Legend fontSize={12} />
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Messages Sent vs Received */}
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Messages Overview</CardTitle></CardHeader>
            <CardContent className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={msgData}>
                  <XAxis dataKey="name" fontSize={12} />
                  <YAxis fontSize={11} />
                  <Tooltip />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {msgData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Team Performance */}
          {teamMembers.length > 0 && (
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Team Performance</CardTitle></CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 font-medium">Agent</th>
                        <th className="text-center py-2 font-medium">Assigned Convos</th>
                        <th className="text-center py-2 font-medium">Open Tasks</th>
                        <th className="text-center py-2 font-medium">Contacts Owned</th>
                      </tr>
                    </thead>
                    <tbody>
                      {teamMembers.map((m: any) => (
                        <tr key={m.userId} className="border-b last:border-0">
                          <td className="py-2 font-medium">{m.name}</td>
                          <td className="py-2 text-center">
                            <Badge variant="secondary">{m.assigned_conversations}</Badge>
                          </td>
                          <td className="py-2 text-center">
                            <Badge variant="outline">{m.open_tasks}</Badge>
                          </td>
                          <td className="py-2 text-center">{m.contacts_owned}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

function KpiCard({ title, value, icon }: { title: string; value: number; icon: React.ReactNode }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-muted-foreground">{title}</span>
          <span className="text-muted-foreground">{icon}</span>
        </div>
        <p className="text-2xl font-bold">{value.toLocaleString()}</p>
      </CardContent>
    </Card>
  );
}
