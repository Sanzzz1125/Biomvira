import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { KeyRound, LayoutDashboard, ScrollText, Users } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { Avatar, RoleBadge } from '../../components/brand';
import { cx } from '../../components/ui';

export const AdminLayout: React.FC = () => {
  const { user } = useAuth();
  const items = [
    { to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true },
    { to: '/admin/users', label: 'Users', icon: Users, end: false },
    ...(user?.role === 'owner' ? [{ to: '/admin/access', label: 'Admins & access', icon: KeyRound, end: false }] : []),
    { to: '/admin/audit', label: 'Audit log', icon: ScrollText, end: false },
  ];

  return (
    <div className="mx-auto grid max-w-7xl grid-cols-[minmax(0,1fr)] gap-8 lg:grid-cols-[232px_minmax(0,1fr)]">
      <aside className="min-w-0 lg:sticky lg:top-24 lg:self-start">
        <nav aria-label="Admin" className="-mx-4 flex gap-1 overflow-x-auto px-4 pb-1 lg:mx-0 lg:flex-col lg:px-0">
          {items.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cx(
                  'flex shrink-0 items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive ? 'bg-white text-brand-700 shadow-card ring-1 ring-slate-200' : 'text-slate-600 hover:bg-white/70 hover:text-slate-900'
                )
              }
            >
              <Icon className="h-4 w-4" aria-hidden />
              {label}
            </NavLink>
          ))}
        </nav>
        {user && (
          <div className="mt-6 hidden items-center gap-3 rounded-xl border border-slate-200 bg-white p-3 lg:flex">
            <Avatar name={user.name} />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-900">{user.name}</p>
              <div className="mt-1">
                <RoleBadge role={user.role} />
              </div>
            </div>
          </div>
        )}
      </aside>
      <section className="min-w-0 animate-fade-up">
        <Outlet />
      </section>
    </div>
  );
};
