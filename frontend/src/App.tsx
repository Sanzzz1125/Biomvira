import { HomePage } from './pages/HomePage';
import React, { useEffect, useState } from 'react';
import { BrowserRouter, Link, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import { Compass } from 'lucide-react';
import { AuthProvider } from './auth/AuthContext';
import { RequireAuth } from './auth/RequireAuth';
import { EmptyState } from './components/brand';
import { ChatAssistant } from './components/ChatAssistant';
import { DisclaimerModal } from './components/DisclaimerModal';
import { Footer } from './components/Footer';
import { Navbar } from './components/Navbar';
import { ServerWakeNotice } from './components/ServerWakeNotice';
import { LanguagePrompt } from './components/LanguagePrompt';
import { ToastProvider } from './components/Toast';
import { Card, buttonClasses } from './components/ui';
import { PageSpinner } from './components/brand';
import { useAnalyzer } from './hooks/useAnalyzer';

// Pages other than the home page load when first opened, so the home page downloads only what it shows.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function page<M extends Record<string, any>, K extends keyof M>(load: () => Promise<M>, name: K) {
  return React.lazy(() => load().then((m) => ({ default: m[name] as React.ComponentType<any> })));
}
const AnalyzerPage = page(() => import('./pages/AnalyzerPage'), 'AnalyzerPage');
const SciencePage = page(() => import('./pages/LearnPages'), 'SciencePage');
const FaqPage = page(() => import('./pages/LearnPages'), 'FaqPage');
const ArticlesPage = page(() => import('./pages/LearnPages'), 'ArticlesPage');
const ArticlePage = page(() => import('./pages/LearnPages'), 'ArticlePage');
const AccountPage = page(() => import('./pages/AccountPage'), 'AccountPage');
const HistoryPage = page(() => import('./pages/HistoryPage'), 'HistoryPage');
const HistoryDetailPage = page(() => import('./pages/HistoryDetailPage'), 'HistoryDetailPage');
const AdminLayout = page(() => import('./pages/admin/AdminLayout'), 'AdminLayout');
const AdminDashboard = page(() => import('./pages/admin/AdminDashboard'), 'AdminDashboard');
const AdminUsers = page(() => import('./pages/admin/AdminUsers'), 'AdminUsers');
const AdminAccess = page(() => import('./pages/admin/AdminAccess'), 'AdminAccess');
const AdminAudit = page(() => import('./pages/admin/AdminAudit'), 'AdminAudit');
const LoginPage = page(() => import('./pages/auth/LoginPage'), 'LoginPage');
const RegisterPage = page(() => import('./pages/auth/RegisterPage'), 'RegisterPage');
const InvitePage = page(() => import('./pages/auth/InvitePage'), 'InvitePage');
const ResetPasswordPage = page(() => import('./pages/auth/ResetPasswordPage'), 'ResetPasswordPage');
const Loading = () => <PageSpinner label="Loading…" />;

const ScrollToTop: React.FC = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo?.({ top: 0 });
  }, [pathname]);
  return null;
};

// One official address per page for search engines, whichever domain served it. biomvira.live redirects to
// www.biomvira.live, so that is the canonical host; biomvira.vercel.app keeps working as a backup.
const SITE_URL = 'https://www.biomvira.live';
const CanonicalLink: React.FC = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    let link = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
    if (!link) {
      link = document.createElement('link');
      link.rel = 'canonical';
      document.head.appendChild(link);
    }
    link.href = SITE_URL + (pathname === '/' ? '/' : pathname.replace(/\/+$/, ''));
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
        <React.Suspense fallback={<Loading />}>
          <Outlet />
        </React.Suspense>
      </main>
      <Footer onOpenDisclaimer={() => setShowDisclaimer(true)} />
      <DisclaimerModal isOpen={showDisclaimer} onClose={() => setShowDisclaimer(false)} />
      <ChatAssistant />
      <LanguagePrompt />
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
          <CanonicalLink />
          <Routes>
            <Route element={<SiteLayout />}>
              <Route index element={<HomePage />} />
              <Route path="analyze" element={<AnalyzerPage analyzer={analyzer} />} />
              <Route path="history" element={<RequireAuth><HistoryPage /></RequireAuth>} />
              <Route path="science" element={<SciencePage />} />
              <Route path="faq" element={<FaqPage />} />
              <Route path="articles" element={<ArticlesPage />} />
              <Route path="articles/:slug" element={<ArticlePage />} />
              <Route path="history/:id" element={<RequireAuth><HistoryDetailPage /></RequireAuth>} />
              <Route path="account" element={<RequireAuth><AccountPage /></RequireAuth>} />
              <Route path="admin" element={<RequireAuth roles={['admin', 'owner']}><React.Suspense fallback={<Loading />}><AdminLayout /></React.Suspense></RequireAuth>}>
                <Route index element={<AdminDashboard />} />
                <Route path="users" element={<AdminUsers />} />
                <Route path="access" element={<RequireAuth roles={['owner']}><AdminAccess /></RequireAuth>} />
                <Route path="audit" element={<AdminAudit />} />
              </Route>
              <Route path="*" element={<NotFound />} />
            </Route>
            <Route path="login" element={<React.Suspense fallback={<Loading />}><LoginPage /></React.Suspense>} />
            <Route path="register" element={<React.Suspense fallback={<Loading />}><RegisterPage /></React.Suspense>} />
            <Route path="invite/:token" element={<React.Suspense fallback={<Loading />}><InvitePage /></React.Suspense>} />
            <Route path="reset-password/:token" element={<React.Suspense fallback={<Loading />}><ResetPasswordPage /></React.Suspense>} />
          </Routes>
          <ServerWakeNotice />
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
};

export default App;
