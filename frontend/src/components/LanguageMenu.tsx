import React from 'react';
import { Check, ChevronDown, Languages } from 'lucide-react';
import { LANGUAGES, Language, setLanguage, useLanguage } from '../lib/i18n';
import { cx } from './ui';

/** The site language: a small menu showing each language in its own script, with the current one ticked. */
export const LanguageMenu: React.FC = () => {
  const language = useLanguage();
  const [open, setOpen] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);
  const current = LANGUAGES.find((l) => l.id === language) ?? LANGUAGES[0];

  React.useEffect(() => {
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

  const choose = (id: Language) => {
    setLanguage(id);
    setOpen(false);
  };

  return (
    <div ref={ref} className="relative" translate="no">
      <button type="button" onClick={() => setOpen((o) => !o)} aria-haspopup="menu" aria-expanded={open}
        aria-label={`Language: ${current.label}`}
        className="flex h-9 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 group-data-[floating=true]/header:border-slate-300/70 group-data-[floating=true]/header:bg-white/60 group-data-[floating=true]/header:text-black">
        <Languages className="h-4 w-4 text-brand-600" aria-hidden />
        <span className="hidden sm:inline">{current.native}</span>
        <span className="sm:hidden">{{ en: 'EN', hi: 'हि', te: 'తె' }[current.id]}</span>
        <ChevronDown className={cx('h-3.5 w-3.5 text-slate-400 transition-transform', open && 'rotate-180')} aria-hidden />
      </button>
      {open && (
        <div role="menu" className="absolute right-0 top-11 z-50 w-48 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-card-lg">
          {LANGUAGES.map((l) => (
            <button key={l.id} type="button" role="menuitemradio" aria-checked={l.id === language} onClick={() => choose(l.id)}
              className={cx('flex w-full items-center justify-between gap-3 px-3.5 py-2.5 text-left text-sm transition-colors hover:bg-slate-50',
                l.id === language ? 'font-semibold text-brand-700' : 'text-slate-700')}>
              <span className="flex flex-col">
                <span>{l.native}</span>
                {l.native !== l.label && <span className="text-xs font-normal text-slate-500">{l.label}</span>}
              </span>
              {l.id === language && <Check className="h-4 w-4" aria-hidden />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
