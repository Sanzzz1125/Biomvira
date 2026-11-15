import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import {
  Ban, CheckCircle2, ChevronLeft, ChevronRight, Crown, KeyRound, Link2, LogOut, Mail, MoreHorizontal,
  Pencil, RefreshCw, ShieldOff, Trash2, Unlock, User as UserIcon, UserPlus, XCircle,
} from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { CopyLinkBox, RoleBadge } from '../../components/brand';
import { SelectField, TextField } from '../../components/forms';
import { ConfirmDialog, Modal } from '../../components/Modal';
import { useToast } from '../../components/Toast';
import { Alert, Badge, Button, Card, Tone, cx } from '../../components/ui';
import { formatDateTime } from '../../lib/format';
import { adminApi } from '../../services/accounts';
import { AdminUser, Invite, LinkCreated } from '../../types';

/* ------------------------------------------------------------------ audit actions */

export const ACTION_META: Record<string, { label: string; tone: Tone }> = {
  'auth.register': { label: 'Signed up', tone: 'brand' },
  'auth.login': { label: 'Logged in', tone: 'neutral' },
  'auth.logout': { label: 'Logged out', tone: 'neutral' },
  'auth.login_failed': { label: 'Failed login', tone: 'amber' },
  'auth.locked': { label: 'Account locked', tone: 'red' },
  'auth.password_changed': { label: 'Changed password', tone: 'neutral' },
  'account.updated': { label: 'Updated profile', tone: 'neutral' },
  'account.deleted': { label: 'Deleted own account', tone: 'red' },
  'invite.created': { label: 'Created invite', tone: 'indigo' },
  'invite.renewed': { label: 'Renewed invite', tone: 'indigo' },
  'invite.revoked': { label: 'Revoked invite', tone: 'amber' },
  'invite.accepted': { label: 'Accepted invite', tone: 'brand' },
  'reset.created': { label: 'Created reset link', tone: 'indigo' },
  'reset.completed': { label: 'Reset password', tone: 'neutral' },
  'user.updated': { label: 'Edited user', tone: 'neutral' },
  'user.disabled': { label: 'Disabled user', tone: 'red' },
  'user.enabled': { label: 'Enabled user', tone: 'brand' },
  'user.unlocked': { label: 'Unlocked user', tone: 'brand' },
  'user.signed_out': { label: 'Signed user out', tone: 'amber' },
  'user.deleted': { label: 'Deleted user', tone: 'red' },
  'role.promoted': { label: 'Granted admin', tone: 'indigo' },
  'role.demoted': { label: 'Removed admin', tone: 'amber' },
  'owner.transferred': { label: 'Transferred ownership', tone: 'indigo' },
  'owner.created': { label: 'Owner created', tone: 'indigo' },
};

export const ActionBadge: React.FC<{ action: string }> = ({ action }) => {
  const meta = ACTION_META[action] ?? { label: action, tone: 'neutral' as Tone };
  return <Badge tone={meta.tone}>{meta.label}</Badge>;
};

export const AccountStatus: React.FC<{ user: Pick<AdminUser, 'status' | 'locked'> }> = ({ user }) => {
  if (user.status === 'disabled') return <Badge tone="red">Disabled</Badge>;
  if (user.locked) return <Badge tone="amber">Locked</Badge>;
  return <Badge tone="brand">Active</Badge>;
};

/* ------------------------------------------------------------------ row action menu */

export interface MenuItem {
  label: string;
  icon: React.ElementType;
  onSelect: () => void;
  danger?: boolean;
  hidden?: boolean;
}

export const ActionMenu: React.FC<{ items: MenuItem[]; label: string }> = ({ items, label }) => {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<{ top: number; right: number } | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (!open || !buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    const menuHeight = menuRef.current?.offsetHeight ?? 260;
    const below = rect.bottom + 6 + menuHeight < window.innerHeight;
    setPos({ top: below ? rect.bottom + 6 : rect.top - menuHeight - 6, right: window.innerWidth - rect.right });
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const close = (e: Event) => {
      if (e.type === 'mousedown' && (menuRef.current?.contains(e.target as Node) || buttonRef.current?.contains(e.target as Node))) return;
      setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('mousedown', close);
    window.addEventListener('scroll', close, true);
    window.addEventListener('resize', close);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', close);
      window.removeEventListener('scroll', close, true);
      window.removeEventListener('resize', close);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const visible = items.filter((i) => !i.hidden);

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={label}
        className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800"
      >
        <MoreHorizontal className="h-4 w-4" aria-hidden />
      </button>
      {open &&
        createPortal(
          <div
            ref={menuRef}
            role="menu"
            style={{ position: 'fixed', top: pos?.top ?? -9999, right: pos?.right ?? 0 }}
            className="z-50 w-60 rounded-xl border border-slate-200 bg-white p-1.5 shadow-card-lg animate-fade-in"
          >
            {visible.map(({ label: itemLabel, icon: Icon, onSelect, danger }, i) => (
              <React.Fragment key={itemLabel}>
                {danger && i > 0 && <div className="my-1 h-px bg-slate-100" />}
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setOpen(false);
                    onSelect();
                  }}
                  className={cx(
                    'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition-colors',
                    danger ? 'text-red-600 hover:bg-red-50' : 'text-slate-700 hover:bg-slate-100'
                  )}
                >
                  <Icon className={cx('h-4 w-4', danger ? 'text-red-500' : 'text-slate-500')} aria-hidden />
                  {itemLabel}
                </button>
              </React.Fragment>
            ))}
          </div>,
          document.body
        )}
    </>
  );
};

/* ------------------------------------------------------------------ dialogs */

export const LinkDialog: React.FC<{
  link: (LinkCreated & { title: string; description: React.ReactNode }) | null;
  onClose: () => void;
}> = ({ link, onClose }) => (
  <Modal
    open={!!link}
    onClose={onClose}
    size="md"
    title={link?.title ?? ''}
    description={link?.description}
    icon={
      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-50 text-brand-700">
        <Link2 className="h-[18px] w-[18px]" aria-hidden />
      </span>
    }
    footer={
      <Button onClick={onClose} data-autofocus>
        Done
      </Button>
    }
  >
    {link && <CopyLinkBox path={link.path} expiresAt={link.expires_at} />}
  </Modal>
);

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const EditUserDialog: React.FC<{
  user: AdminUser | null;
  onClose: () => void;
  onSaved: (user: AdminUser) => void;
}> = ({ user, onClose, onSaved }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (user) {
      setName(user.name);
      setEmail(user.email);
      setError(null);
      setBusy(false);
    }
  }, [user]);

  const save = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!user) return;
    if (!name.trim()) return setError('Enter a name.');
    if (!EMAIL_RE.test(email.trim())) return setError('Enter a valid email address.');
    setBusy(true);
    setError(null);
    try {
      const updated = await adminApi.updateUser(user.id, { name: name.trim(), email: email.trim() });
      onSaved(updated);
      onClose();
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  };

  return (
    <Modal
      open={!!user}
      onClose={onClose}
      title="Edit details"
      description={user ? `Update the name or login email for ${user.name}.` : undefined}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button loading={busy} onClick={() => save()}>
            Save changes
          </Button>
        </>
      }
    >
      <form onSubmit={save} className="space-y-4">
        {error && <Alert tone="error">{error}</Alert>}
        <TextField label="Full name" icon={UserIcon} value={name} onChange={(e) => setName(e.target.value)} maxLength={80} />
        <TextField
          label="Login email"
          type="email"
          icon={Mail}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          hint="They'll use this email to log in from now on."
        />
        <button type="submit" hidden />
      </form>
    </Modal>
  );
};

export const InviteDialog: React.FC<{
  open: boolean;
  onClose: () => void;
  allowAdminRole: boolean;
  onCreated: () => void;
}> = ({ open, onClose, allowAdminRole, onCreated }) => {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'user' | 'admin'>('user');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [link, setLink] = useState<LinkCreated | null>(null);

  useEffect(() => {
    if (open) {
      setEmail('');
      setRole('user');
      setError(null);
      setBusy(false);
      setLink(null);
    }
  }, [open]);

  const create = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!EMAIL_RE.test(email.trim())) return setError('Enter a valid email address.');
    setBusy(true);
    setError(null);
    try {
      const created = await adminApi.createInvite(email.trim(), role);
      setLink({ path: created.path, expires_at: created.invite.expires_at });
      onCreated();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="md"
      title={link ? 'Invitation link ready' : 'Invite someone'}
      description={
        link
          ? `Send this link to ${email.trim()}. They'll set their own name and password.`
          : 'Create a one-time sign-up link. No email is sent, so you share the link yourself.'
      }
      icon={
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-50 text-brand-700">
          <UserPlus className="h-[18px] w-[18px]" aria-hidden />
        </span>
      }
      footer={
        link ? (
          <Button onClick={onClose}>Done</Button>
        ) : (
          <>
            <Button variant="secondary" onClick={onClose} disabled={busy}>
              Cancel
            </Button>
            <Button loading={busy} onClick={() => create()}>
              Create invite link
            </Button>
          </>
        )
      }
    >
      {link ? (
        <CopyLinkBox path={link.path} expiresAt={link.expires_at} />
      ) : (
        <form onSubmit={create} className="space-y-4">
          {error && <Alert tone="error">{error}</Alert>}
          <TextField
            label="Email address"
            type="email"
            icon={Mail}
            placeholder="name@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          {allowAdminRole && (
            <SelectField label="Role" value={role} onChange={(e) => setRole(e.target.value as 'user' | 'admin')}>
              <option value="user">User: analyze and keep their own reports</option>
              <option value="admin">Admin: also manage users</option>
            </SelectField>
          )}
          <button type="submit" hidden />
        </form>
      )}
    </Modal>
  );
};

/* ------------------------------------------------------------------ per-user actions */

type Pending = 'disable' | 'enable' | 'signout' | 'delete' | 'remove-admin' | 'transfer' | null;

export const UserActions: React.FC<{
  user: AdminUser;
  onChanged: (user: AdminUser) => void;
  onRemoved: (id: string) => void;
}> = ({ user, onChanged, onRemoved }) => {
  const { user: viewer, refresh } = useAuth();
  const { notify } = useToast();
  const navigate = useNavigate();
  const [editing, setEditing] = useState<AdminUser | null>(null);
  const [pending, setPending] = useState<Pending>(null);
  const [link, setLink] = useState<React.ComponentProps<typeof LinkDialog>['link']>(null);

  if (!user.can_manage) return null;
  const ownerViewingAdmin = viewer?.role === 'owner' && user.role === 'admin';

  const run = async (action: () => Promise<AdminUser>, message: string) => {
    const updated = await action();
    onChanged(updated);
    notify('success', message);
  };

  const confirmCopy: Record<Exclude<Pending, null>, { title: string; message: React.ReactNode; label: string; danger?: boolean; password?: boolean; go: (pw: string) => Promise<void> }> = {
    disable: {
      title: `Disable ${user.name}?`,
      message: "They'll be signed out everywhere and won't be able to log in until you enable the account again. Their reports are kept.",
      label: 'Disable account',
      danger: true,
      go: () => run(() => adminApi.updateUser(user.id, { status: 'disabled' }), 'Account disabled'),
    },
    enable: {
      title: `Enable ${user.name}?`,
      message: 'They will be able to log in again.',
      label: 'Enable account',
      go: () => run(() => adminApi.updateUser(user.id, { status: 'active' }), 'Account enabled'),
    },
    signout: {
      title: 'Sign out everywhere?',
      message: `${user.name} will be logged out on every device and must log in again.`,
      label: 'Sign out',
      go: () => run(() => adminApi.signOut(user.id), 'Signed out of all devices'),
    },
    delete: {
      title: `Delete ${user.name}?`,
      message: 'The account and every saved report will be permanently deleted. This cannot be undone.',
      label: 'Delete permanently',
      danger: true,
      go: async () => {
        await adminApi.deleteUser(user.id);
        onRemoved(user.id);
        notify('success', 'Account deleted');
      },
    },
    'remove-admin': {
      title: `Remove admin access from ${user.name}?`,
      message: 'They become a regular user immediately and lose access to the admin portal.',
      label: 'Remove admin access',
      danger: true,
      go: () => run(() => adminApi.removeAdmin(user.id), 'Admin access removed'),
    },
    transfer: {
      title: `Make ${user.name} the owner?`,
      message: (
        <>
          There is only ever one owner. <strong>{user.name}</strong> becomes the owner and you become an admin. You
          won't be able to undo this yourself.
        </>
      ),
      label: 'Transfer ownership',
      danger: true,
      password: true,
      go: async (password) => {
        await adminApi.transferOwnership(user.id, password);
        notify('success', 'Ownership transferred', `${user.name} is now the owner. You are an admin.`);
        await refresh();
        navigate('/admin', { replace: true });
      },
    },
  };

  const items: MenuItem[] = [
    { label: 'Edit details', icon: Pencil, onSelect: () => setEditing(user) },
    {
      label: 'Create password reset link',
      icon: KeyRound,
      onSelect: async () => {
        try {
          const created = await adminApi.resetLink(user.id);
          setLink({
            ...created,
            title: 'Password reset link',
            description: `Send this to ${user.name} (${user.email}) so they can choose a new password.`,
          });
        } catch (err) {
          notify('error', 'Could not create link', (err as Error).message);
        }
      },
    },
    {
      label: 'Unlock account',
      icon: Unlock,
      hidden: !user.locked,
      onSelect: () => run(() => adminApi.unlock(user.id), 'Account unlocked').catch((err) => notify('error', 'Could not unlock', err.message)),
    },
    { label: 'Sign out everywhere', icon: LogOut, onSelect: () => setPending('signout') },
    user.status === 'active'
      ? { label: 'Disable account', icon: Ban, onSelect: () => setPending('disable') }
      : { label: 'Enable account', icon: CheckCircle2, onSelect: () => setPending('enable') },
    { label: 'Make owner', icon: Crown, hidden: !ownerViewingAdmin || user.status !== 'active', onSelect: () => setPending('transfer') },
    { label: 'Remove admin access', icon: ShieldOff, hidden: !ownerViewingAdmin, danger: true, onSelect: () => setPending('remove-admin') },
    { label: 'Delete account', icon: Trash2, danger: true, onSelect: () => setPending('delete') },
  ];

  const current = pending ? confirmCopy[pending] : null;

  return (
    <>
      <ActionMenu items={items} label={`Actions for ${user.name}`} />
      <EditUserDialog
        user={editing}
        onClose={() => setEditing(null)}
        onSaved={(u) => {
          onChanged(u);
          notify('success', 'Details updated');
        }}
      />
      <LinkDialog link={link} onClose={() => setLink(null)} />
      <ConfirmDialog
        open={!!current}
        onClose={() => setPending(null)}
        title={current?.title ?? ''}
        message={current?.message}
        confirmLabel={current?.label ?? ''}
        tone={current?.danger ? 'danger' : 'primary'}
        requirePassword={current?.password}
        onConfirm={(pw) => current!.go(pw)}
      />
    </>
  );
};

/* ------------------------------------------------------------------ pending invites */

export const PendingInvites: React.FC<{ role?: 'user' | 'admin'; refreshKey: number; title?: string }> = ({
  role,
  refreshKey,
  title = 'Pending invitations',
}) => {
  const { notify } = useToast();
  const [invites, setInvites] = useState<Invite[] | null>(null);
  const [link, setLink] = useState<React.ComponentProps<typeof LinkDialog>['link']>(null);
  const [revoking, setRevoking] = useState<Invite | null>(null);

  const load = useCallback(() => {
    adminApi.invites(role).then(setInvites).catch(() => setInvites([]));
  }, [role]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  if (!invites || invites.length === 0) return null;

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-slate-100 px-5 py-4">
        <h3 className="text-base font-semibold">{title}</h3>
        <p className="mt-0.5 text-sm text-slate-500">Links that haven't been used yet. Expired links can be renewed.</p>
      </div>
      <ul className="divide-y divide-slate-100">
        {invites.map((invite) => (
          <li key={invite.id} className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="truncate text-sm font-medium text-slate-900">{invite.email}</span>
                {invite.role && <RoleBadge role={invite.role} />}
                <Badge tone={invite.status === 'pending' ? 'amber' : 'neutral'}>
                  {invite.status === 'pending' ? 'Pending' : 'Expired'}
                </Badge>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                {invite.status === 'pending' ? 'Expires' : 'Expired'} {formatDateTime(invite.expires_at)}
                {invite.created_by && <> · invited by {invite.created_by}</>}
              </p>
            </div>
            <div className="flex shrink-0 gap-2">
              <Button
                size="sm"
                variant="secondary"
                icon={<RefreshCw className="h-3.5 w-3.5" aria-hidden />}
                onClick={async () => {
                  try {
                    const renewed = await adminApi.renewInvite(invite.id);
                    setLink({
                      path: renewed.path,
                      expires_at: renewed.invite.expires_at,
                      title: 'New invitation link',
                      description: `The old link for ${invite.email} no longer works. Share this one instead.`,
                    });
                    load();
                  } catch (err) {
                    notify('error', 'Could not renew invite', (err as Error).message);
                  }
                }}
              >
                New link
              </Button>
              <Button size="sm" variant="ghost" icon={<XCircle className="h-3.5 w-3.5" aria-hidden />} onClick={() => setRevoking(invite)}>
                Revoke
              </Button>
            </div>
          </li>
        ))}
      </ul>
      <LinkDialog link={link} onClose={() => setLink(null)} />
      <ConfirmDialog
        open={!!revoking}
        onClose={() => setRevoking(null)}
        title="Revoke this invitation?"
        message={revoking ? `The link sent to ${revoking.email} will stop working immediately.` : ''}
        confirmLabel="Revoke invite"
        tone="danger"
        onConfirm={async () => {
          await adminApi.revokeInvite(revoking!.id);
          notify('success', 'Invitation revoked');
          load();
        }}
      />
    </Card>
  );
};

/* ------------------------------------------------------------------ pagination */

export const Pagination: React.FC<{ page: number; pageSize: number; total: number; onPage: (page: number) => void }> = ({
  page,
  pageSize,
  total,
  onPage,
}) => {
  if (total <= pageSize) return null;
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(total, page * pageSize);
  return (
    <div className="flex items-center justify-between gap-3 border-t border-slate-100 px-5 py-3 text-sm text-slate-500">
      <span>
        Showing <span className="font-medium text-slate-700">{from}–{to}</span> of{' '}
        <span className="font-medium text-slate-700">{total}</span>
      </span>
      <div className="flex gap-2">
        <Button size="sm" variant="secondary" disabled={page <= 1} onClick={() => onPage(page - 1)} icon={<ChevronLeft className="h-4 w-4" aria-hidden />}>
          Previous
        </Button>
        <Button size="sm" variant="secondary" disabled={to >= total} onClick={() => onPage(page + 1)} iconRight={<ChevronRight className="h-4 w-4" aria-hidden />}>
          Next
        </Button>
      </div>
    </div>
  );
};

