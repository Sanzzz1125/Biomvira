import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AlertTriangle, ArrowRight, Link2Off, Mail, User as UserIcon } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { RoleBadge, Skeleton } from '../../components/brand';
import { PasswordField, PasswordStrength, TextField, isPasswordValid } from '../../components/forms';
import { useToast } from '../../components/Toast';
import { Alert, Button } from '../../components/ui';
import { authApi } from '../../services/accounts';
import { formatDateTime } from '../../lib/format';
import { LinkInfo } from '../../types';
import { AuthLayout, AuthLink } from './AuthLayout';

export const LinkProblem: React.FC<{ message: string }> = ({ message }) => (
  <div className="text-center">
    <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200">
      <Link2Off className="h-6 w-6" aria-hidden />
    </span>
    <p className="mt-4 text-[15px] font-semibold text-slate-900">This link can't be used</p>
    <p className="mt-1 text-sm leading-relaxed text-slate-500">{message}</p>
    <div className="mt-6">
      <AuthLink to="/login">Go to log in</AuthLink>
    </div>
  </div>
);

export const LinkLoading: React.FC = () => (
  <div className="space-y-4" role="status" aria-label="Checking link">
    <Skeleton className="h-5 w-2/3" />
    <Skeleton className="h-11 w-full" />
    <Skeleton className="h-11 w-full" />
    <Skeleton className="h-12 w-full" />
  </div>
);

export const InvitePage: React.FC = () => {
  const { token = '' } = useParams();
  const { user, setUser, logout } = useAuth();
  const { notify } = useToast();
  const navigate = useNavigate();

  const [info, setInfo] = useState<LinkInfo | null>(null);
  const [linkError, setLinkError] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    authApi.inviteInfo(token).then(setInfo).catch((err: Error) => setLinkError(err.message));
  }, [token]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const next: Record<string, string> = {};
    if (!name.trim()) next.name = 'Enter your name.';
    if (!isPasswordValid(password)) next.password = 'Use at least 8 characters, including a letter and a number.';
    setErrors(next);
    setFormError(null);
    if (Object.keys(next).length) return;
    setBusy(true);
    try {
      const me = await authApi.acceptInvite(token, name.trim(), password);
      setUser(me);
      notify('success', 'Your account is ready', me.role === 'admin' ? 'You now have admin access.' : undefined);
      navigate(me.role === 'admin' ? '/admin' : '/', { replace: true });
    } catch (err) {
      setFormError((err as Error).message);
      setBusy(false);
    }
  };

  const roleText = info?.role === 'admin' ? 'an admin' : 'a member';

  return (
    <AuthLayout
      title="Accept your invitation"
      subtitle={
        info
          ? `${info.invited_by ? `${info.invited_by} invited you` : "You've been invited"} to join Biomvira as ${roleText}.`
          : 'Set up your Biomvira account.'
      }
    >
      {linkError ? (
        <LinkProblem message={linkError} />
      ) : !info ? (
        <LinkLoading />
      ) : user ? (
        <div className="space-y-4">
          <Alert tone="warning" icon={<AlertTriangle className="h-4 w-4" aria-hidden />} title="You're already logged in">
            You're signed in as {user.email}. Log out first to accept this invitation for {info.email}.
          </Alert>
          <Button variant="secondary" className="w-full" onClick={() => logout()}>
            Log out
          </Button>
        </div>
      ) : (
        <form onSubmit={submit} noValidate className="space-y-5">
          {formError && (
            <Alert tone="error" icon={<AlertTriangle className="h-4 w-4" aria-hidden />}>
              {formError}
            </Alert>
          )}
          <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
            <div className="flex min-w-0 items-center gap-2.5">
              <Mail className="h-4 w-4 shrink-0 text-slate-400" aria-hidden />
              <span className="truncate text-sm font-medium text-slate-900">{info.email}</span>
            </div>
            {info.role && <RoleBadge role={info.role} />}
          </div>
          <TextField
            label="Full name"
            icon={UserIcon}
            autoComplete="name"
            placeholder="e.g. Priya Sharma"
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={errors.name}
            maxLength={80}
            autoFocus
          />
          <div>
            <PasswordField
              label="Create a password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={errors.password}
              maxLength={128}
            />
            {password && <PasswordStrength password={password} />}
          </div>
          <Button type="submit" size="lg" loading={busy} className="w-full" iconRight={<ArrowRight className="h-4 w-4" aria-hidden />}>
            Accept & create account
          </Button>
          <p className="text-center text-xs text-slate-500">This invitation expires {formatDateTime(info.expires_at)}.</p>
        </form>
      )}
    </AuthLayout>
  );
};
