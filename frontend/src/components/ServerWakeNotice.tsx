import { useEffect } from 'react';

/**
 * The free API server can be asleep when the site opens. Request its health endpoint straight away so that it is
 * already waking while the visitor reads the page. Nothing is shown to the visitor; requests made in the meantime
 * simply wait (see services/http.ts).
 */
export const ServerWakeNotice: React.FC = () => {
  useEffect(() => {
    fetch('/api/health', { cache: 'no-store' }).catch(() => undefined);
  }, []);
  return null;
};
