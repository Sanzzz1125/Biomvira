import React, { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { ChevronDown, History, LayoutDashboard, LogOut, ScanLine, Settings, ShieldCheck } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { Avatar, Logo, RoleBadge, Skeleton } from './brand';
import { useToast } from './Toast';
import { cx } from './ui';

interface NavbarProps {
  onOpenDisclaimer: () => void;
}

const navClass = ({ isActive }: { isActive: boolean }) =>
  cx(
    'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
    isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
  );

const iconNavClass = ({ isActive }: { isActive: boolean }) =>
  cx(
    'flex h-9 w-9 items-center justify-center rounded-lg transition-colors',
    isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100'
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
        <span className="hidden max-w-[140px] truncate text-sm font-medium text-slate-800 md:inline">
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

export const Navbar: React.FC<NavbarProps> = ({ onOpenDisclaimer }) => {
  const { user, ready, isStaff } = useAuth();
  const links = [
    { to: '/', label: 'Analyze', icon: ScanLine, end: true },
    { to: '/history', label: 'History', icon: History, end: false },
    ...(isStaff ? [{ to: '/admin', label: 'Admin', icon: LayoutDashboard, end: false }] : []),
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Logo />
          <nav aria-label="Primary" className="hidden items-center gap-1 sm:flex">
            {links.map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end} className={navClass}>
                <Icon className="h-4 w-4" aria-hidden />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2">
          <nav aria-label="Primary mobile" className="flex items-center gap-1 sm:hidden">
            {links.map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end} aria-label={label} className={iconNavClass}>
                <Icon className="h-[18px] w-[18px]" aria-hidden />
              </NavLink>
            ))}
          </nav>

          <button
            type="button"
            onClick={onOpenDisclaimer}
            className="flex h-9 items-center gap-2 rounded-lg px-2.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
          >
            <ShieldCheck className="h-4 w-4 text-brand-600" aria-hidden />
            <span className="hidden lg:inline">Safety &amp; privacy</span>
            <span className="sr-only lg:hidden">Safety and privacy</span>
          </button>

          <span className="mx-1 hidden h-6 w-px bg-slate-200 sm:block" aria-hidden />

          {!ready ? (
            <Skeleton className="h-8 w-8 rounded-full" />
          ) : user ? (
            <UserMenu />
          ) : (
            <div className="flex items-center gap-1.5">
              <Link
                to="/login"
                className="hidden h-9 items-center rounded-lg px-3 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 sm:flex"
              >
                Log in
              </Link>
              <Link
                to="/register"
                className="hidden h-9 items-center rounded-lg bg-brand-600 px-3.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700 sm:flex"
              >
                Get started
              </Link>
              <Link
                to="/login"
                className="flex h-9 items-center rounded-lg bg-brand-600 px-3.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700 sm:hidden"
              >
                Log in
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
