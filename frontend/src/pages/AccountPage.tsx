import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CalendarDays, Clock, KeyRound, Mail, Trash2, User as UserIcon } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { Avatar, RoleBadge } from '../components/brand';
import { PasswordField, PasswordStrength, TextField, isPasswordValid } from '../components/forms';
import { ConfirmDialog } from '../components/Modal';
import { useToast } from '../components/Toast';
import { Alert, Button, Card, PageHeader } from '../components/ui';
import { formatDate, relativeTime } from '../lib/format';
import { authApi } from '../services/accounts';

const Section: React.FC<{ title: string; description: string; children: React.ReactNode; danger?: boolean }> = ({
  title,
  description,
  children,
  danger,
}) => (
  <Card className={danger ? 'border-red-200' : undefined}>
    <div className="border-b border-slate-100 px-6 py-5">
      <h3 className={danger ? 'text-base font-semibold text-red-700' : 'text-base font-semibold'}>{title}</h3>
      <p className="mt-0.5 text-sm text-slate-500">{description}</p>
    </div>
    <div className="px-6 py-5">{children}</div>
  </Card>
);

export const AccountPage: React.FC = () => {
  const { user, setUser } = useAuth();
  const { notify } = useToast();
  const navigate = useNavigate();

  const [name, setName] = useState(user?.name ?? '');
  const [savingName, setSavingName] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);

  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [pwErrors, setPwErrors] = useState<{ current?: string; next?: string }>({});
  const [pwError, setPwError] = useState<string | null>(null);
  const [savingPw, setSavingPw] = useState(false);

  const [confirmDelete, setConfirmDelete] = useState(false);

  if (!user) return null;
  const isOwner = user.role === 'owner';

  const saveName = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setNameError('Enter your name.');
      return;
    }
    setNameError(null);
    setSavingName(true);
    try {
      const updated = await authApi.updateProfile(name.trim());
      setUser(updated);
      setName(updated.name);
      notify('success', 'Profile updated');
    } catch (err) {
      setNameError((err as Error).message);
    } finally {
      setSavingName(false);
    }
  };

  const savePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    const errors: typeof pwErrors = {};
    if (!current) errors.current = 'Enter your current password.';
    if (!isPasswordValid(next)) errors.next = 'Use at least 8 characters, including a letter and a number.';
    setPwErrors(errors);
    setPwError(null);
    if (Object.keys(errors).length) return;
    setSavingPw(true);
    try {
      const updated = await authApi.changePassword(current, next);
      setUser(updated);
      setCurrent('');
      setNext('');
      notify('success', 'Password updated', 'Your other devices have been signed out.');
    } catch (err) {
      setPwError((err as Error).message);
    } finally {
      setSavingPw(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <PageHeader eyebrow="Account" title="Account settings" description="Manage your profile, password and data." />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="h-fit p-6">
          <div className="flex flex-col items-center text-center">
            <Avatar name={user.name} size="lg" />
            <p className="mt-3 text-base font-semibold text-slate-900">{user.name}</p>
            <p className="text-sm text-slate-500">{user.email}</p>
            {user.role !== 'user' && (
              <div className="mt-2.5">
                <RoleBadge role={user.role} />
              </div>
            )}
          </div>
          <dl className="mt-6 space-y-3 border-t border-slate-100 pt-5 text-sm">
            <div className="flex items-center justify-between gap-3">
              <dt className="flex items-center gap-2 text-slate-500">
                <CalendarDays className="h-4 w-4" aria-hidden /> Member since
              </dt>
              <dd className="font-medium text-slate-800">{formatDate(user.created_at)}</dd>
            </div>
            <div className="flex items-center justify-between gap-3">
              <dt className="flex items-center gap-2 text-slate-500">
                <Clock className="h-4 w-4" aria-hidden /> Last login
              </dt>
              <dd className="font-medium text-slate-800">{relativeTime(user.last_login_at)}</dd>
            </div>
          </dl>
        </Card>

        <div className="space-y-6 lg:col-span-2">
          <Section title="Profile" description="Your name appears in the navigation bar and on invitations you send.">
            <form onSubmit={saveName} className="space-y-4">
              <TextField
                label="Full name"
                icon={UserIcon}
                value={name}
                onChange={(e) => setName(e.target.value)}
                error={nameError}
                maxLength={80}
                autoComplete="name"
              />
              <TextField
                label="Email"
                icon={Mail}
                value={user.email}
                readOnly
                disabled
                hint="To change your email, ask an administrator."
              />
              <div className="flex justify-end">
                <Button type="submit" loading={savingName} disabled={name.trim() === user.name}>
                  Save changes
                </Button>
              </div>
            </form>
          </Section>

          <Section title="Password" description="Changing your password signs you out on every other device.">
            <form onSubmit={savePassword} className="space-y-4">
              {pwError && <Alert tone="error">{pwError}</Alert>}
              <PasswordField
                label="Current password"
                autoComplete="current-password"
                value={current}
                onChange={(e) => setCurrent(e.target.value)}
                error={pwErrors.current}
              />
              <div>
                <PasswordField
                  label="New password"
                  autoComplete="new-password"
                  value={next}
                  onChange={(e) => setNext(e.target.value)}
                  error={pwErrors.next}
                  maxLength={128}
                />
                {next && <PasswordStrength password={next} />}
              </div>
              <div className="flex justify-end">
                <Button type="submit" loading={savingPw} icon={<KeyRound className="h-4 w-4" aria-hidden />}>
                  Update password
                </Button>
              </div>
            </form>
          </Section>

          <Section
            danger
            title="Delete account"
            description="Permanently delete your account and every saved report. This can't be undone."
          >
            {isOwner ? (
              <Alert tone="warning">
                The owner account can't be deleted. Transfer ownership to an admin from the Admin portal first.
              </Alert>
            ) : (
              <Button variant="danger" icon={<Trash2 className="h-4 w-4" aria-hidden />} onClick={() => setConfirmDelete(true)}>
                Delete my account
              </Button>
            )}
          </Section>
        </div>
      </div>

      <ConfirmDialog
        open={confirmDelete}
        onClose={() => setConfirmDelete(false)}
        tone="danger"
        requirePassword
        title="Delete your account?"
        message="Your account and all saved reports will be permanently deleted. Enter your password to confirm."
        confirmLabel="Delete account"
        onConfirm={async (password) => {
          await authApi.deleteAccount(password);
          setUser(null);
          notify('info', 'Your account has been deleted');
          navigate('/', { replace: true });
        }}
      />
    </div>
  );
};
