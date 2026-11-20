import { LanguageMenu } from './LanguageMenu';
import React, { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { LANGUAGES, setLanguage, useLanguage } from '../lib/i18n';
import { House, BookOpen, ChevronDown, CircleHelp, FlaskConical, History, LayoutDashboard, LogOut, Menu, ScanLine, Settings, ShieldCheck, X } from 'lucide-react';
import { useAuth, wasSignedIn } from '../auth/AuthContext';
import { Avatar, Logo, RoleBadge, Skeleton, toTopIfHere } from './brand';
import { useToast } from './Toast';
import { cx } from './ui';

interface NavbarProps {
  onOpenDisclaimer: () => void;
}

// Floating header looks. 'plain' was the approved one; 'tinted' is the current trial. Switch here.
const FLOATING = {
  plain: 'h-14 rounded-2xl border border-slate-200/70 bg-white/85 shadow-[0_10px_30px_-12px_rgba(15,23,42,0.28)] backdrop-blur-xl backdrop-saturate-150',
  glossy: 'h-14 rounded-2xl border border-white/70 bg-gradient-to-b from-white/90 via-white/75 to-brand-50/70 '
    + 'shadow-[inset_0_1px_0_rgba(255,255,255,0.9),inset_0_-1px_0_rgba(22,124,100,0.08),0_12px_32px_-12px_rgba(15,23,42,0.30)] '
    + 'ring-1 ring-brand-600/10 backdrop-blur-2xl backdrop-saturate-[1.8]',
  // white only, a little see-through, no colour, gradient or shine
  tinted: 'h-14 rounded-2xl border border-slate-200/60 bg-white/70 shadow-[0_10px_30px_-14px_rgba(15,23,42,0.25)] backdrop-blur-md',
} as const;
const FLOATING_STYLE: keyof typeof FLOATING = 'tinted';

const navClass = ({ isActive }: { isActive: boolean }) =>
  cx(
    'flex items-center gap-2 whitespace-nowrap rounded-lg px-2.5 py-2 text-sm font-medium transition-colors xl:px-3',
    isActive ? 'bg-brand-50 text-brand-700 group-data-[floating=true]/header:bg-brand-600/10 group-data-[floating=true]/header:text-brand-900'
      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 group-data-[floating=true]/header:text-black group-data-[floating=true]/header:hover:bg-white/70'
  );

const iconNavClass = ({ isActive }: { isActive: boolean }) =>
  cx(
    'flex h-9 w-9 items-center justify-center rounded-lg transition-colors',
    isActive ? 'bg-brand-50 text-brand-700 group-data-[floating=true]/header:bg-brand-600/10' : 'text-slate-600 hover:bg-slate-100 group-data-[floating=true]/header:text-black'
  );

const UserMenu: React.FC = () => {
  const { user, isStaff, logout } = useAuth();
  const { notify } = useToast();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => setOpen(false), [location.pathname]);
  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('mousedown', onClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  if (!user) return null;

  const item = 'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-100';

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex items-center gap-2 rounded-full py-1 pl-1 pr-2 transition-colors hover:bg-slate-100"
      >
        <Avatar name={user.name} />
        <span className="hidden max-w-[140px] truncate text-sm font-medium text-slate-800 xl:inline">
          {user.name.split(' ')[0]}
        </span>
        <ChevronDown className={cx('h-4 w-4 text-slate-500 transition-transform', open && 'rotate-180')} aria-hidden />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-50 mt-2 w-72 origin-top-right rounded-xl border border-slate-200 bg-white p-1.5 shadow-card-lg animate-fade-in"
        >
          <div className="flex items-center gap-3 px-3 pb-3 pt-2.5">
            <Avatar name={user.name} size="lg" />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-900">{user.name}</p>
              <p className="truncate text-xs text-slate-500">{user.email}</p>
              {user.role !== 'user' && (
                <div className="mt-1.5">
                  <RoleBadge role={user.role} />
                </div>
              )}
            </div>
          </div>
          <div className="my-1 h-px bg-slate-100" />
          <Link to="/history" role="menuitem" className={item}>
            <History className="h-4 w-4 text-slate-500" aria-hidden /> My reports
          </Link>
          <Link to="/account" role="menuitem" className={item}>
            <Settings className="h-4 w-4 text-slate-500" aria-hidden /> Account settings
          </Link>
          {isStaff && (
            <Link to="/admin" role="menuitem" className={item}>
              <LayoutDashboard className="h-4 w-4 text-slate-500" aria-hidden /> Admin portal
            </Link>
          )}
          <div className="my-1 h-px bg-slate-100" />
          <button
            type="button"
            role="menuitem"
            className={cx(item, 'text-red-600 hover:bg-red-50')}
            onClick={async () => {
              setOpen(false);
              navigate('/', { replace: true });
              await logout();
              notify('info', 'You have been logged out');
            }}
          >
            <LogOut className="h-4 w-4" aria-hidden /> Log out
          </button>
        </div>
      )}
    </div>
  );
};

/** Phones and tablets: every link, the language, safety and the account in one panel under the header. */
const MobileMenu: React.FC<{ links: { to: string; label: string; icon: React.ElementType; end: boolean }[];
  onOpenDisclaimer: () => void }> = ({ links, onOpenDisclaimer }) => {
  const { user, isStaff, logout } = useAuth();
  const { notify } = useToast();
  const language = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => setOpen(false), [location.pathname]);
  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent | KeyboardEvent) => {
      if (e instanceof KeyboardEvent ? e.key === 'Escape' : !ref.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', close);
    document.addEventListener('keydown', close);
    return () => {
      document.removeEventListener('mousedown', close);
      document.removeEventListener('keydown', close);
    };
  }, [open]);
  const row = 'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-[15px] font-medium text-slate-700 transition-colors hover:bg-slate-100';
  const all = [...links, { to: '/science', label: 'Science', icon: FlaskConical, end: false },
    { to: '/articles', label: 'Articles', icon: BookOpen, end: false }, { to: '/faq', label: 'FAQ', icon: CircleHelp, end: false }];
  return (
    <div ref={ref} className="lg:hidden">
      <button type="button" onClick={() => setOpen((o) => !o)} aria-expanded={open} aria-controls="site-menu"
        aria-label={open ? 'Close menu' : 'Open menu'}
        className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-700 transition-colors hover:bg-slate-100 group-data-[floating=true]/header:text-black">
        {open ? <X className="h-5 w-5" aria-hidden /> : <Menu className="h-5 w-5" aria-hidden />}
      </button>
      {open && (
        <div id="site-menu" className="absolute inset-x-0 top-full z-50 mt-2 max-h-[calc(100dvh-5.5rem)] overflow-y-auto rounded-2xl border border-slate-200 bg-white p-2 shadow-card-lg animate-fade-in">
          {user && (
            <div className="flex items-center gap-3 px-3 pb-3 pt-2">
              <Avatar name={user.name} size="lg" />
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-900">{user.name}</p>
                <p className="truncate text-xs text-slate-500">{user.email}</p>
              </div>
            </div>
          )}
          <nav aria-label="Menu" className="grid gap-0.5">
            {all.map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end} onClick={toTopIfHere(to)}
                className={({ isActive }) => cx(row, isActive && 'bg-brand-50 text-brand-700')}>
                <Icon className="h-[18px] w-[18px]" aria-hidden /> {label}
              </NavLink>
            ))}
            <button type="button" className={row} onClick={() => { setOpen(false); onOpenDisclaimer(); }}>
              <ShieldCheck className="h-[18px] w-[18px] text-brand-600" aria-hidden /> Safety &amp; privacy
            </button>
          </nav>
          <div className="my-2 h-px bg-slate-100" />
          <div className="grid grid-cols-3 gap-1.5 px-1" role="radiogroup" aria-label="Language" translate="no">
            {LANGUAGES.map((l) => (
              <button key={l.id} type="button" role="radio" aria-checked={l.id === language} onClick={() => setLanguage(l.id)}
                className={cx('rounded-lg border px-2 py-2 text-sm font-medium transition-colors',
                  l.id === language ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-slate-200 text-slate-700 hover:bg-slate-50')}>
                {l.native}
              </button>
            ))}
          </div>
          <div className="my-2 h-px bg-slate-100" />
          {user ? (
            <div className="grid gap-0.5">
              <Link to="/account" className={row}><Settings className="h-[18px] w-[18px] text-slate-500" aria-hidden /> Account settings</Link>
              {isStaff && <Link to="/admin" className={row}><LayoutDashboard className="h-[18px] w-[18px] text-slate-500" aria-hidden /> Admin portal</Link>}
              <button type="button" className={cx(row, 'text-red-600 hover:bg-red-50')}
                onClick={async () => { setOpen(false); navigate('/', { replace: true }); await logout(); notify('info', 'You have been logged out'); }}>
                <LogOut className="h-[18px] w-[18px]" aria-hidden /> Log out
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2 p-1">
              <Link to="/login" className="flex h-10 items-center justify-center rounded-lg border border-slate-300 text-sm font-semibold text-slate-800 hover:bg-slate-50">Log in</Link>
              <Link to="/register" className="flex h-10 items-center justify-center rounded-lg bg-brand-600 text-sm font-semibold text-white hover:bg-brand-700">Get started</Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const Navbar: React.FC<NavbarProps> = ({ onOpenDisclaimer }) => {
  const { user, ready } = useAuth();
  const [scrolled, setScrolled] = React.useState(false);
  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);
  const links = [
    { to: '/', label: 'Home', icon: House, end: true },
    { to: '/analyze', label: 'Analyze', icon: ScanLine, end: false },
    // History exists in the page only for signed-in users (not hidden: never rendered for guests).
    ...(user ? [{ to: '/history', label: 'History', icon: History, end: false }] : []),
  ];

  return (
    <header data-floating={scrolled} className={cx('group/header sticky top-0 z-50 transition-[padding,background-color,border-color] duration-300',
      scrolled ? 'border-b border-transparent px-2 pt-2 sm:px-4 sm:pt-3 lg:px-6' : 'border-b border-slate-200/80 bg-white/85 backdrop-blur-md')}>
      <div className={cx('relative mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 transition-[height,border-radius,box-shadow,background-color] duration-300 sm:px-6 lg:px-8',
        scrolled ? FLOATING[FLOATING_STYLE] : 'h-16')}>
        <div className="flex min-w-0 items-center gap-6 xl:gap-8">
          <Logo />
          {/* Laptops and desktops: the links in the bar (icons and the learn pages from 1280 px, where they fit). */}
          <nav aria-label="Primary" className="hidden items-center gap-0.5 lg:flex">
            {links.map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end} className={navClass} onClick={toTopIfHere(to)}>
                <Icon className="hidden h-4 w-4 xl:block" aria-hidden />
                {label}
              </NavLink>
            ))}
            {[{ to: '/science', label: 'Science', icon: FlaskConical }, { to: '/articles', label: 'Articles', icon: BookOpen }].map(
              ({ to, label, icon: Icon }) => (
                <NavLink key={to} to={to} className={navClass}>
                  <Icon className="hidden h-4 w-4 xl:block" aria-hidden />
                  {label}
                </NavLink>
              )
            )}
          </nav>
        </div>

        <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
          <button
            type="button"
            onClick={onOpenDisclaimer}
            className="hidden h-9 items-center gap-2 rounded-lg px-2.5 lg:flex text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900 group-data-[floating=true]/header:text-black group-data-[floating=true]/header:hover:bg-white/70"
          >
            <ShieldCheck className="h-4 w-4 text-brand-600" aria-hidden />
            <span className="hidden whitespace-nowrap xl:inline">Safety &amp; privacy</span>
            <span className="sr-only xl:hidden">Safety and privacy</span>
          </button>

          <div className="hidden sm:block"><LanguageMenu /></div>

          <span className="mx-1 hidden h-6 w-px bg-slate-200 lg:block" aria-hidden />

          {!ready && wasSignedIn() ? (
            <Skeleton className="h-8 w-8 rounded-full" />
          ) : user ? (
            <div className="hidden lg:block"><UserMenu /></div>
          ) : (
            <div className="flex items-center gap-1.5">
              <Link
                to="/login"
                className="flex h-9 items-center whitespace-nowrap rounded-lg bg-brand-600 px-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700 lg:bg-transparent lg:text-slate-700 lg:shadow-none lg:hover:bg-slate-100 lg:group-data-[floating=true]/header:text-black lg:group-data-[floating=true]/header:hover:bg-white/70"
              >
                Log in
              </Link>
              <Link
                to="/register"
                className="hidden h-9 items-center whitespace-nowrap rounded-lg bg-brand-600 px-3.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700 lg:flex"
              >
                Get started
              </Link>
            </div>
          )}
          <MobileMenu links={links} onOpenDisclaimer={onOpenDisclaimer} />
        </div>
      </div>
    </header>
  );
};
