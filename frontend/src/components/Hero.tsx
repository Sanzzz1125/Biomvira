import React from 'react';
import { Apple, FileSearch, ShieldCheck } from 'lucide-react';

const FEATURES = [
  {
    icon: FileSearch,
    title: 'Reads your lab report',
    text: 'Upload a PDF from any major Indian lab and key biomarkers are extracted automatically.',
  },
  {
    icon: Apple,
    title: 'Indian food-first plans',
    text: 'Recommendations come from 65 ICMR-NIN foods, matched to your diet and allergies.',
  },
  {
    icon: ShieldCheck,
    title: 'Private by default',
    text: 'Personal details are removed from your report before it is analysed.',
  },
];

export const Hero: React.FC = () => (
  <section className="text-center">
    <p className="eyebrow">Precision nutrition</p>
    <h1 className="mx-auto mt-3 max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl sm:leading-[1.1]">
      Turn your blood report into a{' '}
      <span className="text-brand-600">personalised diet plan</span>
    </h1>
    <p className="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-slate-600">
      Upload your lab results, tell us how you eat, and get evidence-based Indian food
      recommendations for Vitamin D, B12, iron, folate and more.
    </p>

    <ul className="mx-auto mt-10 grid max-w-5xl gap-4 text-left sm:grid-cols-3">
      {FEATURES.map(({ icon: Icon, title, text }) => (
        <li key={title} className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-card">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-100">
            <Icon className="h-[18px] w-[18px]" aria-hidden />
          </span>
          <div>
            <p className="text-sm font-semibold text-slate-900">{title}</p>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">{text}</p>
          </div>
        </li>
      ))}
    </ul>
  </section>
);
