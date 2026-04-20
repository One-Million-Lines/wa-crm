import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/apiClient';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Settings as SettingsIcon, Building2, MessageSquare, Users, Zap } from 'lucide-react';

export default function Settings() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState('business');

  const { data: businessSettings } = useQuery({
    queryKey: ['settings', 'business'],
    queryFn: () => api.getBusinessSettings(),
  });

  const { data: whatsappSettings } = useQuery({
    queryKey: ['settings', 'whatsapp'],
    queryFn: () => api.getWhatsAppSettings(),
  });

  const { data: teamData } = useQuery({
    queryKey: ['settings', 'team'],
    queryFn: () => api.getTeam(),
  });

  const [businessForm, setBusinessForm] = useState<any>(null);
  const [waForm, setWaForm] = useState<any>(null);

  const biz = businessForm || businessSettings?.settings || {};
  const wa = waForm || whatsappSettings?.settings || {};
  const team = teamData?.users || [];

  const saveBizMutation = useMutation({
    mutationFn: (data: any) => api.updateBusinessSettings(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings', 'business'] }),
  });

  const saveWaMutation = useMutation({
    mutationFn: (data: any) => api.updateWhatsAppSettings(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings', 'whatsapp'] }),
  });

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 border-b flex items-center px-6 bg-card shrink-0">
        <SettingsIcon className="w-5 h-5 text-primary mr-3" />
        <h1 className="font-semibold">Settings</h1>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <Tabs value={tab} onValueChange={setTab} className="flex flex-1 overflow-hidden" orientation="vertical">
          <div className="w-48 border-r bg-muted/30 p-3 space-y-1 shrink-0">
            <TabsList className="flex flex-col h-auto bg-transparent gap-1 w-full">
              <TabsTrigger value="business" className="w-full justify-start gap-2 text-xs data-[state=active]:bg-primary/10">
                <Building2 className="w-3.5 h-3.5" /> Business
              </TabsTrigger>
              <TabsTrigger value="whatsapp" className="w-full justify-start gap-2 text-xs data-[state=active]:bg-primary/10">
                <MessageSquare className="w-3.5 h-3.5" /> WhatsApp
              </TabsTrigger>
              <TabsTrigger value="team" className="w-full justify-start gap-2 text-xs data-[state=active]:bg-primary/10">
                <Users className="w-3.5 h-3.5" /> Team
              </TabsTrigger>
              <TabsTrigger value="automations" className="w-full justify-start gap-2 text-xs data-[state=active]:bg-primary/10">
                <Zap className="w-3.5 h-3.5" /> Automations
              </TabsTrigger>
            </TabsList>
          </div>

          <ScrollArea className="flex-1 p-6">
            <div className="max-w-lg">
              <TabsContent value="business" className="mt-0 space-y-4">
                <Card>
                  <CardHeader><CardTitle className="text-sm">Business Information</CardTitle></CardHeader>
                  <CardContent className="space-y-3">
                    <div><Label>Business Name</Label><Input value={biz.businessName || ''} onChange={e => setBusinessForm({ ...biz, businessName: e.target.value })} /></div>
                    <div><Label>Email</Label><Input value={biz.email || ''} onChange={e => setBusinessForm({ ...biz, email: e.target.value })} /></div>
                    <div><Label>Phone</Label><Input value={biz.phone || ''} onChange={e => setBusinessForm({ ...biz, phone: e.target.value })} /></div>
                    <div><Label>Address</Label><Input value={biz.address || ''} onChange={e => setBusinessForm({ ...biz, address: e.target.value })} /></div>
                    <div><Label>Website</Label><Input value={biz.website || ''} onChange={e => setBusinessForm({ ...biz, website: e.target.value })} /></div>
                    <div><Label>Timezone</Label><Input value={biz.timezone || ''} onChange={e => setBusinessForm({ ...biz, timezone: e.target.value })} /></div>
                    <Button onClick={() => saveBizMutation.mutate(biz)} disabled={saveBizMutation.isPending}>
                      {saveBizMutation.isPending ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="whatsapp" className="mt-0 space-y-4">
                <Card>
                  <CardHeader><CardTitle className="text-sm">WhatsApp Business API</CardTitle></CardHeader>
                  <CardContent className="space-y-3">
                    <div><Label>Phone Number ID</Label><Input value={wa.phoneNumberId || ''} onChange={e => setWaForm({ ...wa, phoneNumberId: e.target.value })} /></div>
                    <div><Label>Business Account ID</Label><Input value={wa.businessAccountId || ''} onChange={e => setWaForm({ ...wa, businessAccountId: e.target.value })} /></div>
                    <div><Label>Access Token</Label><Input type="password" value={wa.accessToken || ''} onChange={e => setWaForm({ ...wa, accessToken: e.target.value })} /></div>
                    <div><Label>Webhook Verify Token</Label><Input value={wa.webhookVerifyToken || ''} onChange={e => setWaForm({ ...wa, webhookVerifyToken: e.target.value })} /></div>
                    <Separator />
                    <div className="flex items-center justify-between">
                      <Label>Read Receipts</Label>
                      <Switch checked={wa.readReceipts ?? true} onCheckedChange={v => setWaForm({ ...wa, readReceipts: v })} />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label>Auto-Reply (Off Hours)</Label>
                      <Switch checked={wa.autoReplyOffHours ?? false} onCheckedChange={v => setWaForm({ ...wa, autoReplyOffHours: v })} />
                    </div>
                    <Button onClick={() => saveWaMutation.mutate(wa)} disabled={saveWaMutation.isPending}>
                      {saveWaMutation.isPending ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="team" className="mt-0 space-y-4">
                <Card>
                  <CardHeader><CardTitle className="text-sm">Team Members</CardTitle></CardHeader>
                  <CardContent>
                    {team.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No team members found.</p>
                    ) : (
                      <div className="space-y-3">
                        {team.map((u: any) => (
                          <div key={u.id} className="flex items-center justify-between p-3 border rounded-lg">
                            <div>
                              <p className="text-sm font-medium">{u.name}</p>
                              <p className="text-xs text-muted-foreground">{u.email}</p>
                            </div>
                            <Badge variant="secondary" className="capitalize">{u.role}</Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="automations" className="mt-0 space-y-4">
                <Card>
                  <CardHeader><CardTitle className="text-sm">Automation Settings</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">Global Automations</p>
                        <p className="text-xs text-muted-foreground">Enable/disable all automations</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <Separator />
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">Require Approval</p>
                        <p className="text-xs text-muted-foreground">Sensitive automations need manager approval</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <Separator />
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">Rate Limiting</p>
                        <p className="text-xs text-muted-foreground">Limit to 100 automated messages/hour</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </div>
          </ScrollArea>
        </Tabs>
      </div>
    </div>
  );
}
