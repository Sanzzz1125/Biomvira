import React from 'react';
import { Apple, FileSearch, ShieldCheck } from 'lucide-react';

const FEATURES = [
  {
    icon: FileSearch,
    title: 'Reads 60+ common tests',
    text: 'Upload a PDF or photo from any Indian lab. Results, units and ranges are read automatically.',
  },
  {
    icon: Apple,
    title: 'Indian food plans',
    text: '180+ Indian foods from ICMR-NIN tables, matched to your diet and allergies, for results that need it.',
  },
  {
    icon: ShieldCheck,
    title: 'Private by default',
    text: 'Personal details are removed from your report before it is analysed.',
  },
];

// What each panel gets when a result is outside the healthy range (kept in step with biomarkers.json).
const PANELS = [
  { name: 'Blood count (CBC)', tests: 'Haemoglobin, RBC, PCV, MCV, MCH, MCHC, WBC, platelets, differential count, ESR', guidance: 'Food plan' },
  { name: 'Iron studies', tests: 'Ferritin, serum iron, TIBC, transferrin saturation', guidance: 'Food plan' },
  { name: 'Vitamins & minerals', tests: 'Vitamin D, vitamin B12, folate, calcium', guidance: 'Food plan' },
  { name: 'Blood sugar', tests: 'HbA1c, fasting and post-meal glucose', guidance: 'Food plan' },
  { name: 'Cholesterol (lipid profile)', tests: 'Total cholesterol, LDL, HDL, triglycerides', guidance: 'Food plan' },
  { name: 'Liver function', tests: 'SGPT, SGOT, GGT, ALP, bilirubin, total protein, albumin, globulin', guidance: 'Food plan + doctor' },
  { name: 'Kidney function', tests: 'Creatinine, urea, BUN, uric acid, eGFR, phosphorus', guidance: 'Food plan + doctor' },
  { name: 'Thyroid', tests: 'TSH, T3, T4, free T3, free T4', guidance: 'Doctor review' },
  { name: 'Electrolytes & inflammation', tests: 'Sodium, potassium, chloride, CRP', guidance: 'Doctor review' },
];

export const Hero: React.FC = () => (
  <section className="text-center">
    <p className="eyebrow">Precision nutrition</p>
    <h1 className="mx-auto mt-3 max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl sm:leading-[1.1]">
      Turn your blood report into a{' '}
      <span className="text-brand-600">personalised diet plan</span>
    </h1>
    <p className="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-slate-600">
      Upload your blood report from any Indian lab. NutriLens reads common tests such as blood count, sugar,
      cholesterol, liver, kidney, thyroid, iron and vitamins, gives you an Indian food plan for the results that need
      it, and foods to keep the rest healthy.
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

    <SupportedTests />
  </section>
);

/** Compact overview of the supported panels: one chip per panel, coloured by the kind of guidance it gets. */
const GUIDANCE_STYLE: Record<string, string> = {
  'Food plan': 'bg-brand-500',
  'Food plan + doctor': 'bg-amber-500',
  'Doctor review': 'bg-slate-400',
};

const SupportedTests: React.FC = () => (
  <div className="mx-auto mt-6 max-w-5xl rounded-xl border border-slate-200 bg-white px-5 py-4 text-left shadow-card">
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm font-semibold text-slate-900">What NutriLens checks</p>
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500" aria-label="Legend">
        {Object.entries(GUIDANCE_STYLE).map(([label, dot]) => (
          <li key={label} className="flex items-center gap-1.5">
            <span className={`h-2 w-2 rounded-full ${dot}`} aria-hidden />
            {label}
          </li>
        ))}
      </ul>
    </div>
    <ul className="mt-3 flex flex-wrap gap-2">
      {PANELS.map(({ name, tests, guidance }) => (
        <li
          key={name}
          title={tests}
          className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700"
        >
          <span className={`h-2 w-2 rounded-full ${GUIDANCE_STYLE[guidance]}`} aria-hidden />
          {name}
          <span className="sr-only">: {tests} ({guidance})</span>
        </li>
      ))}
    </ul>
  </div>
);
