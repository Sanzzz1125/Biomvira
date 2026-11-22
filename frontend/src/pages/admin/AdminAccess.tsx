import React, { useCallback, useEffect, useState } from 'react';
import { Crown, Mail, ShieldCheck, ShieldPlus } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { Avatar, EmptyState, RoleBadge, Skeleton } from '../../components/brand';
import { TextField } from '../../components/forms';
import { ConfirmDialog } from '../../components/Modal';
import { useToast } from '../../components/Toast';
import { Alert, Button, Card, PageHeader } from '../../components/ui';
import { relativeTime } from '../../lib/format';
import { adminApi } from '../../services/accounts';
import { AdminUser } from '../../types';
import { AccountStatus, LinkDialog, PendingInvites, UserActions } from './shared';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const AdminAccess: React.FC = () => {
  const { user: owner } = useAuth();
  const { notify } = useToast();
  const [admins, setAdmins] = useState<AdminUser[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [link, setLink] = useState<React.ComponentProps<typeof LinkDialog>['link']>(null);
  const [inviteKey, setInviteKey] = useState(0);

  const load = useCallback(() => {
    adminApi
      .users({ role: 'admin', page_size: 100 })
      .then((page) => setAdmins(page.items))
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const startAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!EMAIL_RE.test(email.trim())) {
      setEmailError('Enter a valid email address.');
      return;
    }
    setEmailError(null);
    setConfirming(true);
  };

  const addAdmin = async (password: string) => {
    const target = email.trim();
    const result = await adminApi.addAdmin(target, password);
    setEmail('');
    if (result.action === 'promoted') {
      notify('success', 'Admin access granted', `${result.user?.name ?? target} is now an admin.`);
      load();
    } else if (result.path && result.invite) {
      setLink({
        path: result.path,
        expires_at: result.invite.expires_at,
        title: 'Admin invitation link',
        description: `${target} doesn't have an account yet. Send them this link. They'll join as an admin.`,
      });
      setInviteKey((k) => k + 1);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin portal"
        title="Admins & access"
        description="Decide who can manage Biomvira. Only you, the owner, can add, edit or remove admins."
      />
      {error && <Alert tone="error">{error}</Alert>}

      <div className="grid items-start gap-6 xl:grid-cols-5">
        {/* Add admin */}
        <Card className="p-6 xl:col-span-3">
          <div className="flex items-start gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-100">
              <ShieldPlus className="h-5 w-5" aria-hidden />
            </span>
            <div>
              <h3 className="text-base font-semibold">Add an admin</h3>
              <p className="mt-0.5 text-sm leading-relaxed text-slate-500">
                If the email already has an account, they're promoted straight away. If not, you'll get a one-time
                invitation link to send them.
              </p>
            </div>
          </div>
          <form onSubmit={startAdd} noValidate className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-start">
            <TextField
              label="Email address"
              type="email"
              icon={Mail}
              placeholder="colleague@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={emailError}
              className="flex-1"
            />
            <Button type="submit" className="sm:mt-7" icon={<ShieldCheck className="h-4 w-4" aria-hidden />}>
              Give admin access
            </Button>
          </form>
        </Card>

        {/* Owner */}
        {owner && (
          <Card className="p-6 xl:col-span-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Owner</p>
            <div className="mt-3 flex items-center gap-3">
              <Avatar name={owner.name} size="lg" />
              <div className="min-w-0">
                <p className="truncate font-semibold text-slate-900">
                  {owner.name} <span className="text-xs font-normal text-slate-500">(you)</span>
                </p>
                <p className="truncate text-sm text-slate-500">{owner.email}</p>
                <div className="mt-1.5">
                  <RoleBadge role="owner" />
                </div>
              </div>
            </div>
            <p className="mt-4 flex gap-2 rounded-lg bg-indigo-50/70 p-3 text-xs leading-relaxed text-indigo-900">
              <Crown className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
              There is always exactly one owner. To hand over ownership, choose “Make owner” on an admin below.
            </p>
          </Card>
        )}
      </div>

      {/* Admin list */}
      <Card className="overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h3 className="text-base font-semibold">
            Admins {admins && <span className="font-normal text-slate-500">({admins.length})</span>}
          </h3>
        </div>
        {!admins ? (
          <div className="space-y-4 p-5">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-4/5" />
          </div>
        ) : admins.length === 0 ? (
          <EmptyState
            icon={ShieldCheck}
            title="No admins yet"
            description="Add someone above to help you manage users. Admins can't change other admins or you."
          />
        ) : (
          <ul className="divide-y divide-slate-100">
            {admins.map((admin) => (
              <li key={admin.id} className="flex items-center justify-between gap-3 px-5 py-3.5">
                <div className="flex min-w-0 items-center gap-3">
                  <Avatar name={admin.name} />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-900">{admin.name}</p>
                    <p className="truncate text-xs text-slate-500">{admin.email}</p>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-4">
                  <span className="hidden text-xs text-slate-500 sm:inline">Last login {relativeTime(admin.last_login_at).toLowerCase()}</span>
                  <AccountStatus user={admin} />
                  <UserActions
                    user={admin}
                    onChanged={(updated) =>
                      updated.role === 'admin'
                        ? setAdmins((list) => list && list.map((a) => (a.id === updated.id ? { ...a, ...updated } : a)))
                        : setAdmins((list) => list && list.filter((a) => a.id !== updated.id))
                    }
                    onRemoved={(id) => setAdmins((list) => list && list.filter((a) => a.id !== id))}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <PendingInvites role="admin" refreshKey={inviteKey} title="Pending admin invitations" />

      <ConfirmDialog
        open={confirming}
        onClose={() => setConfirming(false)}
        requirePassword
        title="Confirm admin access"
        message={
          <>
            <strong>{email.trim()}</strong> will be able to manage users, see account details and the audit log.
            Enter your password to confirm.
          </>
        }
        confirmLabel="Give admin access"
        onConfirm={addAdmin}
      />
      <LinkDialog link={link} onClose={() => setLink(null)} />
    </div>
  );
};
