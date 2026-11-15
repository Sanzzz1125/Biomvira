import React from 'react';
import { Link } from 'react-router-dom';
import { Apple, ArrowLeft, FileSearch, ShieldCheck } from 'lucide-react';
import { Logo } from '../../components/brand';
import { Card } from '../../components/ui';

const POINTS = [
  {
    icon: FileSearch,
    title: 'Reads your lab report',
    text: 'PDFs and photos from major Indian labs, checked by you before analysis.',
  },
  {
    icon: Apple,
    title: 'Indian food-first plans',
    text: 'Matched to your diet and allergies from 65 ICMR-NIN foods.',
  },
  {
    icon: ShieldCheck,
    title: 'Private by design',
    text: 'Personal details are stripped, and only you can see your saved reports.',
  },
];

interface AuthLayoutProps {
  title: string;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ title, subtitle, children, footer }) => (
  <div className="grid min-h-screen bg-white lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
    {/* Brand panel */}
    <aside className="relative hidden overflow-hidden bg-brand-800 text-white lg:flex lg:flex-col lg:justify-between lg:p-12 xl:p-16">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            'radial-gradient(600px 400px at 0% 0%, rgba(70,182,151,0.35), transparent 60%),' +
            'radial-gradient(500px 380px at 100% 100%, rgba(99,102,241,0.25), transparent 60%),' +
            'linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),' +
            'linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)',
          backgroundSize: 'auto, auto, 32px 32px, 32px 32px',
        }}
      />
      <Logo inverted className="relative" />

      <div className="relative max-w-md">
        <p className="text-xs font-semibold uppercase tracking-wider text-brand-200">Precision nutrition</p>
        <h1 className="mt-3 text-[34px] font-bold leading-[1.15] tracking-tight text-white">
          From blood report to a diet plan you can actually follow.
        </h1>
        <ul className="mt-10 space-y-6">
          {POINTS.map(({ icon: Icon, title, text }) => (
            <li key={title} className="flex gap-4">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/10 ring-1 ring-inset ring-white/15">
                <Icon className="h-5 w-5 text-brand-100" aria-hidden />
              </span>
              <div>
                <p className="text-[15px] font-semibold text-white">{title}</p>
                <p className="mt-0.5 text-sm leading-relaxed text-brand-100/80">{text}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <p className="relative max-w-md text-xs leading-relaxed text-brand-100/70">
        NutriLens is an educational nutrition tool and does not replace medical advice.
      </p>
    </aside>

    {/* Form panel */}
    <main className="page-backdrop flex min-h-screen flex-col">
      <div className="flex items-center justify-between px-4 py-5 sm:px-8">
        <Logo className="lg:invisible" />
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-sm font-medium text-slate-600 transition-colors hover:text-slate-900"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden />
          Back to NutriLens
        </Link>
      </div>

      <div className="flex flex-1 items-center justify-center px-4 pb-16 pt-4 sm:px-8">
        <div className="w-full max-w-[420px] animate-fade-up">
          <div className="mb-7">
            <h2 className="text-[28px] font-bold leading-tight tracking-tight">{title}</h2>
            {subtitle && <p className="mt-2 text-[15px] leading-relaxed text-slate-600">{subtitle}</p>}
          </div>
          <Card className="p-6 shadow-card-lg sm:p-8">{children}</Card>
          {footer && <div className="mt-6 text-center text-sm text-slate-600">{footer}</div>}
        </div>
      </div>
    </main>
  </div>
);

export const AuthLink: React.FC<{ to: string; children: React.ReactNode }> = ({ to, children }) => (
  <Link to={to} className="font-semibold text-brand-700 underline-offset-2 hover:underline">
    {children}
  </Link>
);
