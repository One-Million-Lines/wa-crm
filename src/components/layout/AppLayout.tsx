import { NavLink, Outlet } from 'react-router-dom';
import {
  MessageSquare, Users, CheckSquare, Zap, FileText, BarChart3,
  Puzzle, Settings, LogOut, ChevronLeft, ChevronRight,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useState } from 'react';
import { cn } from '@/lib/utils';

const navItems = [
  { to: '/', icon: MessageSquare, label: 'Inbox' },
  { to: '/contacts', icon: Users, label: 'Contacts' },
  { to: '/tasks', icon: CheckSquare, label: 'Tasks' },
  { to: '/automations', icon: Zap, label: 'Automations' },
  { to: '/templates', icon: FileText, label: 'Templates' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/modules', icon: Puzzle, label: 'Modules' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function AppLayout() {
  const { logout, name, email, role } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className={cn(
        "flex flex-col border-r transition-all duration-200",
        "bg-sidebar text-sidebar-foreground",
        collapsed ? "w-16" : "w-56"
      )}>
        {/* Logo */}
        <div className="flex items-center gap-2 px-4 h-14 border-b border-white/10">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-bold text-sm shrink-0">
            W
          </div>
          {!collapsed && <span className="font-semibold text-sm tracking-tight">WaCRM</span>}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-2 space-y-0.5 px-2 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                isActive
                  ? "bg-sidebar-accent text-white font-medium"
                  : "text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-white/5"
              )}
            >
              <Icon className="w-4.5 h-4.5 shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* User section */}
        <div className="border-t border-white/10 p-2">
          {!collapsed && (
            <div className="px-3 py-2 mb-1">
              <div className="text-xs font-medium truncate">{name || email}</div>
              <div className="text-[10px] text-sidebar-foreground/50 capitalize">{role}</div>
            </div>
          )}
          <button
            onClick={logout}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm w-full text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-white/5 transition-colors"
          >
            <LogOut className="w-4 h-4 shrink-0" />
            {!collapsed && <span>Sign out</span>}
          </button>
        </div>

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center h-10 border-t border-white/10 text-sidebar-foreground/50 hover:text-sidebar-foreground transition-colors"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
