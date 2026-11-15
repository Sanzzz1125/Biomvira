import React from 'react';
import { Check } from 'lucide-react';
import { cx } from './ui';

export interface StepItem {
  id: string;
  label: string;
}

interface StepperProps {
  steps: StepItem[];
  currentIndex: number;
}

export const Stepper: React.FC<StepperProps> = ({ steps, currentIndex }) => (
  <nav aria-label="Progress">
    <ol className="flex items-center">
      {steps.map((step, idx) => {
        const done = idx < currentIndex;
        const active = idx === currentIndex;
        const last = idx === steps.length - 1;

        return (
          <li key={step.id} className={cx('flex items-center', !last && 'flex-1')}>
            <div className="flex items-center gap-2.5" aria-current={active ? 'step' : undefined}>
              <span
                className={cx(
                  'flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold transition-colors',
                  done && 'bg-brand-600 text-white',
                  active && 'bg-white text-brand-700 ring-2 ring-brand-600',
                  !done && !active && 'bg-white text-slate-400 ring-1 ring-slate-300'
                )}
              >
                {done ? <Check className="h-4 w-4" strokeWidth={3} aria-hidden /> : idx + 1}
              </span>
              <span
                className={cx(
                  'text-sm font-medium',
                  active ? 'inline text-slate-900' : 'hidden text-slate-500 md:inline'
                )}
              >
                {step.label}
              </span>
            </div>
            {!last && (
              <div
                aria-hidden
                className={cx(
                  'mx-3 h-px flex-1 transition-colors sm:mx-4',
                  done ? 'bg-brand-600' : 'bg-slate-300'
                )}
              />
            )}
          </li>
        );
      })}
    </ol>
  </nav>
);
