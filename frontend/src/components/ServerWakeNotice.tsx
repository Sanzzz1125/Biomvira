import React, { useEffect, useState } from 'react';
import { WifiOff } from 'lucide-react';

/**
 * The free API server sleeps when idle and takes up to a minute to wake. Ping it as soon as the
 * site opens, and explain the wait instead of leaving people staring at a spinner.
 */
export const ServerWakeNotice: React.FC = () => {
  const [state, setState] = useState<'ok' | 'waking' | 'down'>('ok');

  useEffect(() => {
    let cancelled = false;
    const slow = window.setTimeout(() => !cancelled && setState('waking'), 2500);

    const ping = async (attempt: number) => {
      try {
        const response = await fetch('/api/health', { cache: 'no-store' });
        if (!response.ok) throw new Error(String(response.status));
        if (!cancelled) {
          window.clearTimeout(slow);
          setState('ok');
        }
      } catch {
        if (cancelled) return;
        if (attempt >= 10) {
          window.clearTimeout(slow);
          setState('down');
          return;
        }
        window.setTimeout(() => ping(attempt + 1), 6000);
      }
    };
    ping(0);
    return () => {
      cancelled = true;
      window.clearTimeout(slow);
    };
  }, []);

  if (state === 'ok') return null;

  return (
    <div
      role="status"
      className="fixed bottom-4 left-1/2 z-[60] flex w-[calc(100vw-2rem)] max-w-md -translate-x-1/2 items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-card-lg animate-fade-up"
    >
      {state === 'waking' ? (
        <span className="mt-0.5 h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-brand-200 border-t-brand-600" />
      ) : (
        <WifiOff className="mt-0.5 h-5 w-5 shrink-0 text-red-600" aria-hidden />
      )}
      <div>
        <p className="text-sm font-semibold text-slate-900">
          {state === 'waking' ? 'Waking up the server…' : "Can't reach the server"}
        </p>
        <p className="mt-0.5 text-sm leading-relaxed text-slate-600">
          {state === 'waking'
            ? 'After a quiet period this can take up to a minute. You can keep browsing.'
            : 'Please check your connection and refresh the page in a moment.'}
        </p>
      </div>
    </div>
  );
};
