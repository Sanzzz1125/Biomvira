import React, { useId, useState } from 'react';
import { Check, Eye, EyeOff, Lock } from 'lucide-react';
import { cx } from './ui';

/* ------------------------------------------------------------------ TextField */

interface TextFieldProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label: string;
  icon?: React.ElementType;
  error?: string | null;
  hint?: React.ReactNode;
  trailing?: React.ReactNode;
  labelAction?: React.ReactNode;
}

export const TextField = React.forwardRef<HTMLInputElement, TextFieldProps>(
  ({ label, icon: Icon, error, hint, trailing, labelAction, id, className, ...rest }, ref) => {
    const autoId = useId();
    const inputId = id || autoId;
    const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined;
    return (
      <div className={className}>
        <div className="mb-1.5 flex items-center justify-between gap-2">
          <label htmlFor={inputId} className="text-sm font-medium text-slate-700">
            {label}
          </label>
          {labelAction}
        </div>
        <div className="relative">
          {Icon && (
            <Icon
              className="pointer-events-none absolute left-3 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400"
              aria-hidden
            />
          )}
          <input
            ref={ref}
            id={inputId}
            aria-invalid={error ? true : undefined}
            aria-describedby={describedBy}
            className={cx(
              'field h-11',
              Icon && 'pl-10',
              trailing ? 'pr-11' : null,
              error && 'border-red-400 hover:border-red-400 focus:border-red-500 focus:ring-red-500/20'
            )}
            {...rest}
          />
          {trailing && <div className="absolute inset-y-0 right-1 flex items-center">{trailing}</div>}
        </div>
        {error ? (
          <p id={`${inputId}-error`} role="alert" className="mt-1.5 text-[13px] text-red-600">
            {error}
          </p>
        ) : (
          hint && (
            <p id={`${inputId}-hint`} className="mt-1.5 text-[13px] text-slate-500">
              {hint}
            </p>
          )
        )}
      </div>
    );
  }
);
TextField.displayName = 'TextField';

/* ------------------------------------------------------------------ PasswordField */

type PasswordFieldProps = Omit<TextFieldProps, 'type' | 'icon' | 'trailing'>;

export const PasswordField: React.FC<PasswordFieldProps> = ({ hint, ...props }) => {
  const [visible, setVisible] = useState(false);
  const [capsLock, setCapsLock] = useState(false);
  const onKey = (e: React.KeyboardEvent<HTMLInputElement>) =>
    setCapsLock(e.getModifierState?.('CapsLock') ?? false);
  return (
    <TextField
      {...props}
      type={visible ? 'text' : 'password'}
      icon={Lock}
      onKeyUp={onKey}
      onKeyDown={onKey}
      hint={capsLock ? 'Caps Lock is on.' : hint}
      trailing={
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          className="flex h-9 w-9 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
          aria-label={visible ? 'Hide password' : 'Show password'}
          aria-pressed={visible}
        >
          {visible ? <EyeOff className="h-[18px] w-[18px]" aria-hidden /> : <Eye className="h-[18px] w-[18px]" aria-hidden />}
        </button>
      }
    />
  );
};

/* ------------------------------------------------------------------ password rules */

export const passwordChecks = (password: string) => [
  { label: 'At least 8 characters', ok: password.length >= 8 },
  { label: 'A letter and a number', ok: /[A-Za-z]/.test(password) && /\d/.test(password) },
];

export const isPasswordValid = (password: string) =>
  password.length <= 128 && passwordChecks(password).every((c) => c.ok);

function strength(password: string): number {
  if (!password) return 0;
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Za-z]/.test(password) && /\d/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password) || (/[a-z]/.test(password) && /[A-Z]/.test(password))) score++;
  return Math.max(1, score);
}

const STRENGTH = [
  { label: '', bar: 'bg-slate-200', text: 'text-slate-500' },
  { label: 'Weak', bar: 'bg-red-500', text: 'text-red-600' },
  { label: 'Fair', bar: 'bg-amber-500', text: 'text-amber-700' },
  { label: 'Good', bar: 'bg-brand-400', text: 'text-brand-700' },
  { label: 'Strong', bar: 'bg-brand-600', text: 'text-brand-700' },
];

export const PasswordStrength: React.FC<{ password: string }> = ({ password }) => {
  const score = strength(password);
  const meta = STRENGTH[score];
  return (
    <div className="mt-2.5 space-y-2" aria-live="polite">
      <div className="flex items-center gap-3">
        <div className="grid flex-1 grid-cols-4 gap-1.5">
          {[1, 2, 3, 4].map((i) => (
            <span
              key={i}
              className={cx('h-1.5 rounded-full transition-colors', i <= score ? meta.bar : 'bg-slate-200')}
            />
          ))}
        </div>
        <span className={cx('w-12 text-right text-xs font-semibold', meta.text)}>{meta.label}</span>
      </div>
      <ul className="flex flex-wrap gap-x-4 gap-y-1">
        {passwordChecks(password).map((check) => (
          <li
            key={check.label}
            className={cx('flex items-center gap-1.5 text-xs', check.ok ? 'text-brand-700' : 'text-slate-500')}
          >
            <span
              className={cx(
                'flex h-3.5 w-3.5 items-center justify-center rounded-full',
                check.ok ? 'bg-brand-600 text-white' : 'border border-slate-300'
              )}
            >
              {check.ok && <Check className="h-2.5 w-2.5" strokeWidth={3} aria-hidden />}
            </span>
            {check.label}
          </li>
        ))}
      </ul>
    </div>
  );
};

/* ------------------------------------------------------------------ Select */

export const SelectField: React.FC<
  React.SelectHTMLAttributes<HTMLSelectElement> & { label: string; hideLabel?: boolean }
> = ({ label, hideLabel, className, children, id, ...rest }) => {
  const autoId = useId();
  const selectId = id || autoId;
  return (
    <div className={className}>
      <label htmlFor={selectId} className={cx('mb-1.5 block text-sm font-medium text-slate-700', hideLabel && 'sr-only')}>
        {label}
      </label>
      <select id={selectId} className="field h-10 pr-8" {...rest}>
        {children}
      </select>
    </div>
  );
};
