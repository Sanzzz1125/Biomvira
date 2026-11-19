import React from 'react';
import { Languages } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { cx } from './ui';
import { Language, LANGUAGES, setLanguage, storedLanguage } from '../lib/i18n';

/** Asks a signed-in person once which language they want; the choice is kept on this device. */
export const LanguagePrompt: React.FC = () => {
  const { user } = useAuth();
  const [open, setOpen] = React.useState(false);
  const [choice, setChoice] = React.useState<Language>('en');
  React.useEffect(() => {
    const saved = storedLanguage();
    if (saved) document.documentElement.lang = saved;
    setOpen(!!user && !saved);
  }, [user]);
  if (!open) return null;
  const save = () => {
    setLanguage(choice);
    setOpen(false);
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" role="dialog" aria-modal="true" aria-labelledby="lang-title">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-card-lg">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
          <Languages className="h-5 w-5" aria-hidden />
        </span>
        <h2 id="lang-title" className="mt-4 text-lg font-semibold text-slate-900">Choose your language</h2>
        <p className="mt-1 text-sm text-slate-600">भाषा चुनें · భాష ఎంచుకోండి</p>
        <div role="radiogroup" aria-labelledby="lang-title" className="mt-5 grid gap-3">
          {LANGUAGES.map((l) => (
            <button key={l.id} type="button" role="radio" aria-checked={choice === l.id} onClick={() => setChoice(l.id)}
              className={cx('flex items-center justify-between rounded-xl border px-4 py-3 text-left transition-colors',
                choice === l.id ? 'border-brand-600 bg-brand-50 ring-1 ring-brand-600' : 'border-slate-300 hover:bg-slate-50')}>
              <span className="text-[15px] font-semibold text-slate-900">{l.native}</span>
              <span className="text-xs text-slate-500">{l.label}</span>
            </button>
          ))}
        </div>
        <button type="button" onClick={save}
          className="mt-6 h-11 w-full rounded-xl bg-brand-600 text-[15px] font-semibold text-white hover:bg-brand-700">
          Continue
        </button>
      </div>
    </div>
  );
};
