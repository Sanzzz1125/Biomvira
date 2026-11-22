import React from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import { Lock } from 'lucide-react';
import { useAuth } from './AuthContext';
import { EmptyState, PageSpinner } from '../components/brand';
import { Card } from '../components/ui';
import { Role } from '../types';

/** Front-end route guard. The API enforces the same rules on every request. */
export const RequireAuth: React.FC<{ roles?: Role[]; children: React.ReactNode }> = ({ roles, children }) => {
  const { user, ready } = useAuth();
  const location = useLocation();

  if (!ready) return <PageSpinner />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (roles && !roles.includes(user.role)) return <Forbidden />;
  return <>{children}</>;
};

export const Forbidden: React.FC = () => (
  <Card className="mx-auto max-w-2xl">
    <EmptyState
      icon={Lock}
      title="You don't have access to this page"
      description="This area is limited to a different role. If you think this is a mistake, contact the Biomvira owner."
      action={
        <Link to="/" className="text-sm font-semibold text-brand-700 hover:underline">
          Go to the analyzer
        </Link>
      }
    />
  </Card>
);
