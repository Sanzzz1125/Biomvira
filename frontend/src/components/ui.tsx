import React from 'react';
import { Loader2 } from 'lucide-react';
import { MarkerStatus } from '../types';

export const cx = (...classes: (string | false | null | undefined)[]) =>
  classes.filter(Boolean).join(' ');

/* ---------------------------------------------------------------- Button */

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
}

const buttonVariants: Record<ButtonVariant, string> = {
  primary:
    'bg-brand-600 text-white shadow-sm hover:bg-brand-700 active:bg-brand-800 disabled:bg-slate-200 disabled:text-slate-400 disabled:shadow-none',
  secondary:
    'bg-white text-slate-700 border border-slate-300 shadow-sm hover:bg-slate-50 hover:border-slate-400 disabled:bg-slate-50 disabled:text-slate-400',
  ghost: 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 disabled:text-slate-400',
  danger:
    'bg-red-600 text-white shadow-sm hover:bg-red-700 active:bg-red-800 disabled:bg-slate-200 disabled:text-slate-400 disabled:shadow-none',
};

const buttonSizes: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-[13px] gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
  lg: 'h-12 px-6 text-sm gap-2',
};

/** Button styling for links (e.g. router <Link>s that should look like buttons). */
export const buttonClasses = (variant: ButtonVariant = 'primary', size: ButtonSize = 'md', className?: string) =>
  cx(
    'inline-flex items-center justify-center whitespace-nowrap rounded-lg font-semibold transition-colors',
    buttonVariants[variant],
    buttonSizes[size],
    className
  );

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  iconRight,
  className,
  children,
  disabled,
  type = 'button',
  ...rest
}) => (
  <button
    type={type}
    disabled={disabled || loading}
    className={cx(
      'inline-flex items-center justify-center whitespace-nowrap rounded-lg font-semibold transition-colors disabled:cursor-not-allowed',
      buttonVariants[variant],
      buttonSizes[size],
      className
    )}
    {...rest}
  >
    {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : icon}
    {children}
    {!loading && iconRight}
  </button>
);

/* ------------------------------------------------------------------ Card */

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...rest
}) => (
  <div
    className={cx('rounded-2xl border border-slate-200 bg-white shadow-card', className)}
    {...rest}
  >
    {children}
  </div>
);

/* ----------------------------------------------------------------- Badge */

export type Tone = 'neutral' | 'brand' | 'red' | 'amber' | 'indigo';

const toneClasses: Record<Tone, string> = {
  neutral: 'bg-slate-100 text-slate-700 ring-slate-200',
  brand: 'bg-brand-50 text-brand-700 ring-brand-200',
  red: 'bg-red-50 text-red-700 ring-red-200',
  amber: 'bg-amber-50 text-amber-800 ring-amber-200',
  indigo: 'bg-indigo-50 text-indigo-700 ring-indigo-200',
};

export const Badge: React.FC<{
  tone?: Tone;
  icon?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}> = ({ tone = 'neutral', icon, className, children }) => (
  <span
    className={cx(
      'inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
      toneClasses[tone],
      className
    )}
  >
    {icon}
    {children}
  </span>
);

/* --------------------------------------------------------- Section title */

export const PageHeader: React.FC<{
  eyebrow?: string;
  title: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
}> = ({ eyebrow, title, description, actions }) => (
  <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
    <div className="max-w-2xl">
      {eyebrow && <p className="eyebrow mb-1.5">{eyebrow}</p>}
      <h2 className="text-2xl font-semibold sm:text-[28px] sm:leading-9">{title}</h2>
      {description && <p className="mt-2 text-[15px] leading-relaxed text-slate-600">{description}</p>}
    </div>
    {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
  </div>
);

export const SectionTitle: React.FC<{
  icon?: React.ReactNode;
  title: string;
  description?: string;
  right?: React.ReactNode;
}> = ({ icon, title, description, right }) => (
  <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
    <div className="flex items-start gap-3">
      {icon && (
        <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-100">
          {icon}
        </span>
      )}
      <div>
        <h3 className="text-lg font-semibold">{title}</h3>
        {description && <p className="mt-0.5 text-sm text-slate-500">{description}</p>}
      </div>
    </div>
    {right}
  </div>
);

/* ----------------------------------------------------------- Status meta */

export interface StatusMeta {
  label: string;
  tone: Tone;
  text: string;
  dot: string;
  bar: string;
}

export const STATUS_META: Record<MarkerStatus, StatusMeta> = {
  low: { label: 'Low', tone: 'red', text: 'text-red-700', dot: 'bg-red-500', bar: 'bg-red-500' },
  borderline: {
    label: 'Borderline',
    tone: 'amber',
    text: 'text-amber-700',
    dot: 'bg-amber-500',
    bar: 'bg-amber-500',
  },
  normal: {
    label: 'Optimal',
    tone: 'brand',
    text: 'text-brand-700',
    dot: 'bg-brand-500',
    bar: 'bg-brand-500',
  },
  high: {
    label: 'Elevated',
    tone: 'indigo',
    text: 'text-indigo-700',
    dot: 'bg-indigo-500',
    bar: 'bg-indigo-500',
  },
};

/* ---------------------------------------------------------- Error banner */

export const Alert: React.FC<{
  tone?: 'error' | 'warning' | 'info';
  icon?: React.ReactNode;
  title?: string;
  children: React.ReactNode;
  className?: string;
}> = ({ tone = 'error', icon, title, children, className }) => {
  const styles = {
    error: 'border-red-200 bg-red-50 text-red-800',
    warning: 'border-amber-200 bg-amber-50 text-amber-900',
    info: 'border-brand-200 bg-brand-50 text-brand-900',
  }[tone];
  return (
    <div
      role={tone === 'error' ? 'alert' : undefined}
      className={cx('flex items-start gap-3 rounded-xl border p-4 text-sm', styles, className)}
    >
      {icon && <span className="mt-0.5 shrink-0">{icon}</span>}
      <div className="min-w-0">
        {title && <p className="font-semibold">{title}</p>}
        <div className={cx('leading-relaxed', title && 'mt-0.5')}>{children}</div>
      </div>
    </div>
  );
};
