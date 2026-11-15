import React, { useEffect, useState } from 'react';
import { BrowserRouter, Link, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import { Compass } from 'lucide-react';
import { AuthProvider } from './auth/AuthContext';
import { RequireAuth } from './auth/RequireAuth';
import { EmptyState } from './components/brand';
import { DisclaimerModal } from './components/DisclaimerModal';
import { Footer } from './components/Footer';
import { Navbar } from './components/Navbar';
import { ServerWakeNotice } from './components/ServerWakeNotice';
import { ToastProvider } from './components/Toast';
import { Card, buttonClasses } from './components/ui';
import { useAnalyzer } from './hooks/useAnalyzer';
import { AccountPage } from './pages/AccountPage';
import { AnalyzerPage } from './pages/AnalyzerPage';
import { HistoryDetailPage } from './pages/HistoryDetailPage';
import { HistoryPage } from './pages/HistoryPage';
import { AdminAccess } from './pages/admin/AdminAccess';
import { AdminAudit } from './pages/admin/AdminAudit';
import { AdminDashboard } from './pages/admin/AdminDashboard';
import { AdminLayout } from './pages/admin/AdminLayout';
import { AdminUsers } from './pages/admin/AdminUsers';
import { InvitePage } from './pages/auth/InvitePage';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage';

const ScrollToTop: React.FC = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo?.({ top: 0 });
  }, [pathname]);
  return null;
};

const SiteLayout: React.FC = () => {
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  return (
    <div className="page-backdrop flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:shadow-card-lg"
      >
        Skip to content
      </a>
      <Navbar onOpenDisclaimer={() => setShowDisclaimer(true)} />
      <main id="main" className="mx-auto w-full max-w-7xl flex-1 px-4 py-10 sm:px-6 sm:py-14 lg:px-8">
        <Outlet />
      </main>
      <Footer onOpenDisclaimer={() => setShowDisclaimer(true)} />
      <DisclaimerModal isOpen={showDisclaimer} onClose={() => setShowDisclaimer(false)} />
    </div>
  );
};

const NotFound: React.FC = () => (
  <Card className="mx-auto max-w-2xl">
    <EmptyState
      icon={Compass}
      title="Page not found"
      description="The page you're looking for doesn't exist or has moved."
      action={
        <Link to="/" className={buttonClasses('primary')}>
          Go to the analyzer
        </Link>
      }
    />
  </Card>
);

export const App: React.FC = () => {
  const analyzer = useAnalyzer();
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider onSignedOut={analyzer.reset}>
          <ScrollToTop />
          <Routes>
            <Route element={<SiteLayout />}>
              <Route index element={<AnalyzerPage analyzer={analyzer} />} />
              <Route path="history" element={<HistoryPage />} />
              <Route path="history/:id" element={<RequireAuth><HistoryDetailPage /></RequireAuth>} />
              <Route path="account" element={<RequireAuth><AccountPage /></RequireAuth>} />
              <Route path="admin" element={<RequireAuth roles={['admin', 'owner']}><AdminLayout /></RequireAuth>}>
                <Route index element={<AdminDashboard />} />
                <Route path="users" element={<AdminUsers />} />
                <Route path="access" element={<RequireAuth roles={['owner']}><AdminAccess /></RequireAuth>} />
                <Route path="audit" element={<AdminAudit />} />
              </Route>
              <Route path="*" element={<NotFound />} />
            </Route>
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />
            <Route path="invite/:token" element={<InvitePage />} />
            <Route path="reset-password/:token" element={<ResetPasswordPage />} />
          </Routes>
          <ServerWakeNotice />
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
};

export default App;
