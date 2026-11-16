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

    <div className="mx-auto mt-10 max-w-5xl text-left">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <h2 className="text-base font-semibold text-slate-900">What NutriLens checks</h2>
        <p className="text-xs text-slate-500">
          Results outside the healthy range get a food plan where diet helps, or a clear note to see your doctor.
        </p>
      </div>
      <ul className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {PANELS.map(({ name, tests, guidance }) => (
          <li key={name} className="rounded-xl border border-slate-200 bg-white p-4 shadow-card">
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-semibold text-slate-900">{name}</p>
              <span
                className={
                  guidance === 'Doctor review'
                    ? 'shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600'
                    : 'shrink-0 rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-medium text-brand-700 ring-1 ring-inset ring-brand-100'
                }
              >
                {guidance}
              </span>
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-slate-500">{tests}</p>
          </li>
        ))}
      </ul>
    </div>
  </section>
);
