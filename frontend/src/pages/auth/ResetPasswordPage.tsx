import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AlertTriangle, KeyRound, Mail } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { PasswordField, PasswordStrength, isPasswordValid } from '../../components/forms';
import { useToast } from '../../components/Toast';
import { Alert, Button } from '../../components/ui';
import { authApi } from '../../services/accounts';
import { LinkInfo } from '../../types';
import { AuthLayout } from './AuthLayout';
import { LinkLoading, LinkProblem } from './InvitePage';

export const ResetPasswordPage: React.FC = () => {
  const { token = '' } = useParams();
  const { setUser } = useAuth();
  const { notify } = useToast();
  const navigate = useNavigate();

  const [info, setInfo] = useState<LinkInfo | null>(null);
  const [linkError, setLinkError] = useState<string | null>(null);
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    authApi.resetInfo(token).then(setInfo).catch((err: Error) => setLinkError(err.message));
  }, [token]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isPasswordValid(password)) {
      setError('Use at least 8 characters, including a letter and a number.');
      return;
    }
    setError(null);
    setFormError(null);
    setBusy(true);
    try {
      const me = await authApi.resetPassword(token, password);
      setUser(me);
      notify('success', 'Password updated', 'You are now logged in. Other devices were signed out.');
      navigate('/', { replace: true });
    } catch (err) {
      setFormError((err as Error).message);
      setBusy(false);
    }
  };

  return (
    <AuthLayout title="Choose a new password" subtitle="Pick something you haven't used before.">
      {linkError ? (
        <LinkProblem message={linkError} />
      ) : !info ? (
        <LinkLoading />
      ) : (
        <form onSubmit={submit} noValidate className="space-y-5">
          {formError && (
            <Alert tone="error" icon={<AlertTriangle className="h-4 w-4" aria-hidden />}>
              {formError}
            </Alert>
          )}
          <div className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
            <Mail className="h-4 w-4 shrink-0 text-slate-400" aria-hidden />
            <span className="truncate text-sm font-medium text-slate-900">{info.email}</span>
          </div>
          <div>
            <PasswordField
              label="New password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={error}
              maxLength={128}
              autoFocus
            />
            {password && <PasswordStrength password={password} />}
          </div>
          <Button type="submit" size="lg" loading={busy} className="w-full" icon={<KeyRound className="h-4 w-4" aria-hidden />}>
            Set new password
          </Button>
        </form>
      )}
    </AuthLayout>
  );
};
