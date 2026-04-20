import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import AppLayout from '@/components/layout/AppLayout';
import Login from '@/pages/Login';
import Inbox from '@/pages/Inbox';
import Contacts from '@/pages/Contacts';
import Tasks from '@/pages/Tasks';
import Automations from '@/pages/Automations';
import Templates from '@/pages/Templates';
import Analytics from '@/pages/Analytics';
import Modules from '@/pages/Modules';
import Settings from '@/pages/Settings';
import NotFound from '@/pages/NotFound';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 },
  },
});

function ProtectedRoutes() {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <AppLayout />;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
            <Route element={<ProtectedRoutes />}>
              <Route index element={<Inbox />} />
              <Route path="contacts" element={<Contacts />} />
              <Route path="tasks" element={<Tasks />} />
              <Route path="automations" element={<Automations />} />
              <Route path="templates" element={<Templates />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="modules" element={<Modules />} />
              <Route path="settings" element={<Settings />} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
