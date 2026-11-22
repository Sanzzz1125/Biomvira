import React, { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { AlertTriangle, ArrowRight, Mail, User as UserIcon } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { PasswordField, PasswordStrength, TextField, isPasswordValid } from '../../components/forms';
import { useToast } from '../../components/Toast';
import { Alert, Button, cx } from '../../components/ui';
import { AuthLayout, AuthLink } from './AuthLayout';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const RegisterPage: React.FC = () => {
  const { user, ready, register } = useAuth();
  const { notify } = useToast();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [consent, setConsent] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (ready && user) return <Navigate to="/" replace />;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const next: Record<string, string> = {};
    if (!name.trim()) next.name = 'Enter your name.';
    if (!EMAIL_RE.test(email.trim())) next.email = 'Enter a valid email address.';
    if (!isPasswordValid(password)) next.password = 'Use at least 8 characters, including a letter and a number.';
    if (!consent) next.consent = 'Please agree so we can save your reports.';
    setErrors(next);
    setFormError(null);
    if (Object.keys(next).length) return;

    setBusy(true);
    try {
      const me = await register(name.trim(), email.trim(), password);
      notify('success', `Welcome to Biomvira, ${me.name.split(' ')[0]}`, 'Your analyses will now be saved to your history.');
      navigate('/', { replace: true });
    } catch (err) {
      setFormError((err as Error).message);
      setBusy(false);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Save every analysis and track your levels over time. It's free."
      footer={
        <>
          Already have an account? <AuthLink to="/login">Log in</AuthLink>
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
        <TextField
          label="Email"
          type="email"
          icon={Mail}
          autoComplete="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
        />
        <div>
          <PasswordField
            label="Password"
            autoComplete="new-password"
            placeholder="Create a password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
            maxLength={128}
          />
          {password && <PasswordStrength password={password} />}
        </div>

        <div>
          <label className="flex cursor-pointer items-start gap-3 text-sm leading-relaxed text-slate-600">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              className={cx('mt-0.5 h-4 w-4 shrink-0 cursor-pointer rounded accent-brand-600')}
              aria-invalid={errors.consent ? true : undefined}
            />
            <span>
              I agree that Biomvira stores my analyses in my private account. I can delete them, or my
              whole account, at any time.
            </span>
          </label>
          {errors.consent && (
            <p role="alert" className="mt-1.5 text-[13px] text-red-600">
              {errors.consent}
            </p>
          )}
        </div>

        <Button type="submit" size="lg" loading={busy} className="w-full" iconRight={<ArrowRight className="h-4 w-4" aria-hidden />}>
          Create account
        </Button>
      </form>
    </AuthLayout>
  );
};
