import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Check, Copy, Crown, ShieldCheck, User as UserIcon } from 'lucide-react';
import { ROLE_LABEL } from '../auth/AuthContext';
import { absoluteLink } from '../services/accounts';
import { formatDateTime, initials } from '../lib/format';
import { Role } from '../types';
import { Badge, Button, cx } from './ui';

/** A link to the page you are already on scrolls back to its top (the address does not change, so nothing else would). */
export const toTopIfHere = (to: string) => () => {
  if (window.location.pathname === to) window.scrollTo?.({ top: 0, behavior: 'smooth' });
};

export const Logo: React.FC<{ to?: string; inverted?: boolean; className?: string }> = ({
  to = '/',
  inverted = false,
  className,
}) => (
  <Link to={to} onClick={toTopIfHere(to)} className={cx('flex items-center gap-2.5 rounded-lg', className)} aria-label="Biomvira home">
    <img src="/biomvira-mark.svg" width={36} height={36} alt="" className="shrink-0" />
    <span className={cx('text-[17px] font-bold tracking-tight', inverted ? 'text-white' : 'text-slate-900')}>
      Biomvira
    </span>
  </Link>
);

export const Avatar: React.FC<{ name: string; size?: 'sm' | 'md' | 'lg' }> = ({ name, size = 'md' }) => (
  <span
    aria-hidden
    className={cx(
      'inline-flex shrink-0 select-none items-center justify-center rounded-full bg-brand-600 font-semibold text-white ring-2 ring-white',
      size === 'sm' && 'h-7 w-7 text-[11px]',
      size === 'md' && 'h-8 w-8 text-xs',
      size === 'lg' && 'h-12 w-12 text-base'
    )}
  >
    {initials(name)}
  </span>
);

export const RoleBadge: React.FC<{ role: Role }> = ({ role }) => {
  if (role === 'owner')
    return (
      <Badge tone="indigo" icon={<Crown className="h-3 w-3" aria-hidden />}>
        {ROLE_LABEL.owner}
      </Badge>
    );
  if (role === 'admin')
    return (
      <Badge tone="brand" icon={<ShieldCheck className="h-3 w-3" aria-hidden />}>
        {ROLE_LABEL.admin}
      </Badge>
    );
  return (
    <Badge tone="neutral" icon={<UserIcon className="h-3 w-3" aria-hidden />}>
      {ROLE_LABEL.user}
    </Badge>
  );
};

export const CopyLinkBox: React.FC<{ path: string; expiresAt?: string; note?: string }> = ({ path, expiresAt, note }) => {
  const [copied, setCopied] = useState(false);
  const url = absoluteLink(path);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      const input = document.getElementById('copy-link-input') as HTMLInputElement | null;
      input?.select();
      document.execCommand?.('copy');
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="rounded-xl border border-brand-200 bg-brand-50/60 p-4">
      <div className="flex gap-2">
        <input
          id="copy-link-input"
          readOnly
          value={url}
          onFocus={(e) => e.target.select()}
          className="field h-10 min-w-0 flex-1 font-mono text-xs"
          aria-label="One-time link"
        />
        <Button onClick={copy} icon={copied ? <Check className="h-4 w-4" aria-hidden /> : <Copy className="h-4 w-4" aria-hidden />}>
          {copied ? 'Copied' : 'Copy'}
        </Button>
      </div>
      <p className="mt-2.5 text-xs leading-relaxed text-slate-600">
        {note || 'Send this link privately.'} It works once
        {expiresAt ? ` and expires ${formatDateTime(expiresAt)}` : ''}.
      </p>
    </div>
  );
};

export const EmptyState: React.FC<{
  icon: React.ElementType;
  title: string;
  description: React.ReactNode;
  action?: React.ReactNode;
}> = ({ icon: Icon, title, description, action }) => (
  <div className="px-6 py-14 text-center">
    <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-100">
      <Icon className="h-6 w-6" aria-hidden />
    </span>
    <p className="mt-4 text-[15px] font-semibold text-slate-900">{title}</p>
    <div className="mx-auto mt-1 max-w-md text-sm leading-relaxed text-slate-500">{description}</div>
    {action && <div className="mt-6 flex flex-wrap justify-center gap-2">{action}</div>}
  </div>
);

export const Skeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cx('animate-pulse rounded-lg bg-slate-200/70', className)} />
);

export const PageSpinner: React.FC<{ label?: string }> = ({ label = 'Loading…' }) => (
  <div className="flex min-h-[40vh] items-center justify-center" role="status">
    <div className="flex items-center gap-3 text-sm text-slate-500">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-brand-200 border-t-brand-600" />
      {label}
    </div>
  </div>
);
