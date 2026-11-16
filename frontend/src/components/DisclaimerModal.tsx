import React, { useEffect, useRef } from 'react';
import { AlertTriangle, FileCheck2, Lock, ShieldCheck, X } from 'lucide-react';
import { Button } from './ui';

interface DisclaimerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const POINTS = [
  {
    icon: FileCheck2,
    title: 'Food plans only where diet helps',
    text: 'Results such as iron, vitamins, sugar, cholesterol, protein and uric acid get Indian food plans based on ICMR-NIN data. Thyroid, electrolytes and results that point to kidney disease are referred to a doctor instead. NutriLens never changes medical treatment.',
  },
  {
    icon: AlertTriangle,
    title: 'Safety alerts',
    text: 'Dangerous values (for example haemoglobin below 8 g/dL, very low platelets, high potassium or liver enzymes above three times normal) are clearly marked with advice to see a doctor.',
  },
  {
    icon: Lock,
    title: 'Privacy by design',
    text: 'Names, phone numbers and patient IDs are removed from your report before any analysis takes place.',
  },
];

export const DisclaimerModal: React.FC<DisclaimerModalProps> = ({ isOpen, onClose }) => {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeRef.current?.focus();

    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener('keydown', onKey);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/50 p-4 backdrop-blur-sm animate-fade-in sm:items-center"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="disclaimer-title"
        className="w-full max-w-lg overflow-hidden rounded-2xl bg-white shadow-card-lg animate-fade-up"
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 p-6">
          <div className="flex items-start gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-100">
              <ShieldCheck className="h-5 w-5" aria-hidden />
            </span>
            <div>
              <h2 id="disclaimer-title" className="text-lg font-semibold">
                Safety &amp; privacy
              </h2>
              <p className="text-sm text-slate-500">How NutriLens keeps your data and guidance safe</p>
            </div>
          </div>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="-m-1 rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
          >
            <X className="h-5 w-5" aria-hidden />
          </button>
        </div>

        <div className="space-y-5 p-6">
          <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" aria-hidden />
            <p className="leading-relaxed">
              NutriLens is an <strong>educational nutrition tool</strong>. It does not diagnose
              conditions, prescribe medication or replace medical advice.
            </p>
          </div>

          <ul className="space-y-4">
            {POINTS.map(({ icon: Icon, title, text }) => (
              <li key={title} className="flex items-start gap-3">
                <Icon className="mt-0.5 h-5 w-5 shrink-0 text-brand-600" aria-hidden />
                <div>
                  <p className="text-sm font-semibold text-slate-900">{title}</p>
                  <p className="mt-0.5 text-sm leading-relaxed text-slate-600">{text}</p>
                </div>
              </li>
            ))}
          </ul>

          <p className="border-t border-slate-200 pt-4 text-xs leading-relaxed text-slate-500">
            Always consult a certified medical practitioner before changing your diet,
            supplements or prescribed treatment.
          </p>
        </div>

        <div className="flex justify-end border-t border-slate-200 bg-slate-50 px-6 py-4">
          <Button onClick={onClose}>I understand</Button>
        </div>
      </div>
    </div>
  );
};
