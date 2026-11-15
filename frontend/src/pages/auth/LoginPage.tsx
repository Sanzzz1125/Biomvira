import React, { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { AlertTriangle, ArrowRight, Info, Mail } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { PasswordField, TextField } from '../../components/forms';
import { useToast } from '../../components/Toast';
import { Alert, Button } from '../../components/ui';
import { AuthLayout, AuthLink } from './AuthLayout';

export const LoginPage: React.FC = () => {
  const { user, ready, login } = useAuth();
  const { notify } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from || '/';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  if (ready && user) return <Navigate to={from} replace />;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const next: typeof errors = {};
    if (!email.trim()) next.email = 'Enter your email address.';
    if (!password) next.password = 'Enter your password.';
    setErrors(next);
    setFormError(null);
    if (Object.keys(next).length) return;

    setBusy(true);
    try {
      const me = await login(email.trim(), password);
      notify('success', `Welcome back, ${me.name.split(' ')[0]}`);
      navigate(from, { replace: true });
    } catch (err) {
      setFormError((err as Error).message);
      setBusy(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Log in to see your saved reports and manage your account."
      footer={
        <>
          New to NutriLens? <AuthLink to="/register">Create a free account</AuthLink>
        </>
      }
    >
      <form onSubmit={submit} noValidate className="space-y-5">
        {formError && (
          <Alert tone="error" icon={<AlertTriangle className="h-4 w-4" aria-hidden />}>
            {formError}
          </Alert>
        )}
        <TextField
          label="Email"
          type="email"
          icon={Mail}
          autoComplete="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
          autoFocus
        />
        <PasswordField
          label="Password"
          autoComplete="current-password"
          placeholder="Your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.password}
          labelAction={
            <button
              type="button"
              onClick={() => setShowHelp((v) => !v)}
              className="text-[13px] font-medium text-brand-700 hover:underline"
              aria-expanded={showHelp}
            >
              Forgot password?
            </button>
          }
        />
        {showHelp && (
          <Alert tone="info" icon={<Info className="h-4 w-4" aria-hidden />}>
            Ask a NutriLens administrator to send you a password reset link. It lets you choose a new
            password in one step.
          </Alert>
        )}
        <Button type="submit" size="lg" loading={busy} className="w-full" iconRight={<ArrowRight className="h-4 w-4" aria-hidden />}>
          Log in
        </Button>
      </form>

      <div className="mt-6 border-t border-slate-100 pt-5 text-center">
        <AuthLink to="/">Continue as guest</AuthLink>
        <p className="mt-1 text-xs text-slate-500">Guests can analyze reports, but results aren't saved.</p>
      </div>
    </AuthLayout>
  );
};
