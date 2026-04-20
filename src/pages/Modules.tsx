import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/apiClient';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Switch } from '@/components/ui/switch';
import {
  Blocks, Check, ShoppingCart, Bot, Calendar, Headphones, CreditCard, HelpCircle, Heart,
} from 'lucide-react';

const moduleIcons: Record<string, any> = {
  crm_sync: ShoppingCart,
  ecommerce: ShoppingCart,
  ai_assistant: Bot,
  booking: Calendar,
  helpdesk: Headphones,
  payments: CreditCard,
  faq_bot: HelpCircle,
  loyalty: Heart,
};

export default function Modules() {
  const queryClient = useQueryClient();

  const { data: settingsData } = useQuery({
    queryKey: ['settings', 'modules'],
    queryFn: () => api.getModules(),
  });

  const installMutation = useMutation({
    mutationFn: (id: string) => api.installModule(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings', 'modules'] }),
  });

  const uninstallMutation = useMutation({
    mutationFn: (id: string) => api.uninstallModule(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['settings', 'modules'] }),
  });

  const modules = settingsData?.installed || [];
  const marketplace = settingsData?.available || [];

  const installed = modules;
  const available = marketplace;

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 border-b flex items-center px-6 bg-card shrink-0">
        <Blocks className="w-5 h-5 text-primary mr-3" />
        <h1 className="font-semibold">Modules & Integrations</h1>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-6 space-y-6 max-w-4xl mx-auto">
          {/* Installed */}
          <div>
            <h2 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">Installed ({installed.length})</h2>
            {installed.length === 0 ? (
              <p className="text-sm text-muted-foreground">No modules installed yet.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {installed.map((mod: any) => {
                  const Icon = moduleIcons[mod.moduleId] || Blocks;
                  return (
                    <Card key={mod.moduleId} className="border-primary/20">
                      <CardContent className="p-4 flex items-start gap-3">
                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                          <Icon className="w-5 h-5 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <h3 className="font-medium text-sm">{mod.name || mod.moduleId}</h3>
                            <Switch
                              checked={true}
                              onCheckedChange={() => uninstallMutation.mutate(mod.moduleId || mod.id)}
                            />
                          </div>
                          <p className="text-xs text-muted-foreground mt-0.5">{mod.description || 'Installed module'}</p>
                          <Badge variant="outline" className="text-[10px] mt-1.5">
                            <Check className="w-2.5 h-2.5 mr-0.5" /> Active
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>

          {/* Marketplace */}
          <div>
            <h2 className="text-sm font-semibold mb-3 text-muted-foreground uppercase tracking-wide">Marketplace</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {marketplace.map((mp: any) => {
                const Icon = moduleIcons[mp.id] || Blocks;
                const isInstalled = modules.find((m: any) => m.moduleId === mp.id && m.enabled);
                return (
                  <Card key={mp.id} className={isInstalled ? 'opacity-60' : ''}>
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center shrink-0">
                          <Icon className="w-5 h-5 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-sm">{mp.name}</h3>
                          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{mp.description}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="secondary" className="text-[10px] capitalize">{mp.category}</Badge>
                            {mp.price === 'free' ? (
                              <Badge variant="outline" className="text-[10px] text-green-600">Free</Badge>
                            ) : (
                              <Badge variant="outline" className="text-[10px]">{mp.price}</Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <Button
                        variant={isInstalled ? 'outline' : 'default'}
                        size="sm"
                        className="w-full mt-3"
                        disabled={!!isInstalled}
                        onClick={() => installMutation.mutate(mp.id)}
                      >
                        {isInstalled ? 'Installed' : 'Install'}
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
