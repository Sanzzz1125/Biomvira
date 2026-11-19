import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { ARTICLES } from '../pages/LearnPages';
import { cx } from './ui';

/* ------------------------------------------------------------------ hero */

const SAMPLE = [
  { name: 'Haemoglobin', value: '10.4 g/dL' },
  { name: 'Vitamin D', value: '11.2 ng/mL' },
];
const SAMPLE_MEALS = ['Sajja rotte with tomato pachadi', 'Rice, palakura pappu, gongura pachadi, curd', 'Jonna rotte, pachi pulusu, mushroom curry'];

export const HomeHero: React.FC = () => (
  <section className="mx-[calc(50%-50vw)] w-screen -mt-10 bg-gradient-to-b from-brand-50/70 to-transparent px-4 pb-6 pt-14 sm:-mt-14 sm:px-6 sm:pt-20 lg:px-8">
    <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-12">
      <div className="flex min-w-0 flex-[1_1_520px] flex-col gap-6">
        <p className="eyebrow">Blood report to Indian meals</p>
        <h1 className="text-4xl font-bold leading-[1.08] tracking-tight text-slate-900 sm:text-5xl">
          Your blood report, turned into meals you will actually eat.
        </h1>
        <p className="max-w-xl text-lg leading-relaxed text-slate-600">
          Upload a report from any Indian lab. NutriLens explains each result, then builds diet plans from your region's dishes, your diet type and your allergies.
        </p>
        <div className="flex flex-wrap gap-3">
          <a href="#analyze"
            className="flex h-[52px] items-center rounded-xl bg-brand-600 px-6 text-base font-semibold text-white hover:bg-brand-700">
            Analyse my report
          </a>
          <a href="#how" className="flex h-[52px] items-center rounded-xl border border-slate-300 bg-white px-5 text-base font-semibold text-slate-900 hover:bg-slate-50">
            See how it works
          </a>
        </div>
        <p className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-700">
          <span><strong className="font-semibold">61</strong> common blood tests</span>
          <span><strong className="font-semibold">542</strong> Indian foods from ICMR-NIN tables</span>
          <span translate="no">English · हिन्दी · తెలుగు</span>
        </p>
      </div>
      <div className="flex min-w-0 max-w-[480px] flex-[1_1_420px] flex-col gap-3.5 rounded-[20px] border border-slate-200 bg-white p-5 shadow-[0_24px_48px_-20px_rgba(15,23,42,0.25)]">
        <div className="flex items-center justify-between">
          <span className="text-[13px] font-semibold text-slate-600">Your results</span>
          <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-semibold text-brand-700">2 need attention</span>
        </div>
        {SAMPLE.map((s) => (
          <div key={s.name} className="flex items-center justify-between rounded-xl border border-slate-100 px-3 py-2.5">
            <span className="flex flex-col">
              <span className="text-[14.5px] font-semibold text-slate-900">{s.name}</span>
              <span className="text-[12.5px] text-slate-500">{s.value}</span>
            </span>
            <span className="rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-700">Low</span>
          </div>
        ))}
        <div className="flex flex-col gap-1.5 rounded-2xl border border-brand-100 bg-brand-50/60 p-3.5">
          <span className="text-xs font-semibold uppercase tracking-wider text-brand-700">Today · Telangana style</span>
          {SAMPLE_MEALS.map((m) => <span key={m} className="text-sm text-slate-900">{m}</span>)}
        </div>
      </div>
    </div>
  </section>
);

/* ------------------------------------------------------------------ how it works */

const STEPS = [
  { title: 'Upload your report', text: 'A PDF or a phone photo from any Indian lab. Your name and phone number are removed first.' },
  { title: 'See what each result means', text: "Every test is checked against your lab's range, in plain language, with clear notes on when to see a doctor." },
  { title: 'Pick foods you like', text: 'Choose from the Indian foods that help your results. Tell us your region and what you already eat.' },
  { title: 'Get your diet plans', text: 'Three plan options and a 7-day menu with a shopping list, all within your daily targets.' },
];

export const HowItWorksSection: React.FC = () => (
  <section id="how" className="mx-auto flex max-w-6xl scroll-mt-20 flex-col gap-8">
    <div className="max-w-2xl">
      <p className="eyebrow">How it works</p>
      <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">From a lab report to a week of meals in four steps</h2>
    </div>
    <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {STEPS.map((s, i) => (
        <li key={s.title} className="flex flex-col gap-2.5 rounded-2xl border border-slate-200 bg-white p-5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-50 font-bold text-brand-700">{i + 1}</span>
          <h3 className="text-[17px] font-semibold text-slate-900">{s.title}</h3>
          <p className="text-[14.5px] leading-relaxed text-slate-600">{s.text}</p>
        </li>
      ))}
    </ol>
  </section>
);

/* ------------------------------------------------------------------ science band */

const SCIENCE = [
  { title: 'Indian Food Composition Tables', text: 'Lab-measured nutrients for 542 foods from ICMR-NIN, Hyderabad, linked to everyday dishes from each region.' },
  { title: 'Clinical reference ranges', text: "Your lab's own range first, then published guidelines, with separate ranges for men and women where needed." },
  { title: 'Plans that meet your targets', text: 'An optimisation engine picks dishes and portions that meet your calories, protein and nutrient targets, never breaking your diet or allergies.' },
  { title: 'Recipes checked against real food', text: 'Every dish is checked against lab-measured values of home-cooked Indian food, and a typical day against the salt Indians actually eat.' },
];

export const ScienceBand: React.FC = () => (
  <section id="science" className="mx-[calc(50%-50vw)] w-screen scroll-mt-16 bg-[#0f2a24] px-4 py-16 text-[#e7f5ef] sm:px-6 lg:px-8">
    <div className="mx-auto flex max-w-6xl flex-wrap gap-10">
      <div className="flex min-w-0 flex-[1_1_360px] flex-col gap-3.5">
        <p className="text-[13px] font-semibold uppercase tracking-[0.08em] text-[#7dd1b7]">Our science</p>
        <h2 className="text-3xl font-bold tracking-tight text-white">Measured Indian food data. Plans you can check.</h2>
        <p className="text-base leading-relaxed text-[#c7e8dc]">
          We do not guess. Every number on your plan comes from official Indian food tables and published clinical ranges, and every plan is checked against your targets before you see it.
        </p>
        <Link to="/science" className="inline-flex items-center gap-1 text-[15px] font-semibold text-[#7dd1b7] hover:text-white">
          Read how NutriLens works <ArrowRight className="h-4 w-4" aria-hidden />
        </Link>
      </div>
      <div className="grid min-w-0 flex-[2_1_560px] gap-3.5 sm:grid-cols-2">
        {SCIENCE.map((c) => (
          <div key={c.title} className="flex flex-col gap-2 rounded-2xl border border-[#24564a] p-5">
            <h3 className="text-base font-semibold text-white">{c.title}</h3>
            <p className="text-sm leading-relaxed text-[#c7e8dc]">{c.text}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

/* ------------------------------------------------------------------ articles */

const TOPICS = ['All', 'Diet', 'Nutrition', 'Weight loss', 'Health'];
const TOPIC_STYLE: Record<string, [string, string]> = {
  Nutrition: ['bg-[#e7f5ef]', 'text-brand-700'], Diet: ['bg-[#fdf3e3]', 'text-amber-800'],
  Health: ['bg-[#eaf0fb]', 'text-blue-900'], 'Weight loss': ['bg-[#f3eefb]', 'text-violet-800'],
};

export const ArticlesSection: React.FC = () => {
  const [topic, setTopic] = React.useState('All');
  const shown = ARTICLES.filter((a) => topic === 'All' || a.category === topic).slice(0, 3);
  return (
    <section id="articles" className="mx-auto flex max-w-6xl scroll-mt-20 flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Articles</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Read before your next meal</h2>
        </div>
        <div role="tablist" aria-label="Article topics" className="flex flex-wrap gap-2">
          {TOPICS.map((t) => (
            <button key={t} type="button" role="tab" aria-selected={topic === t} onClick={() => setTopic(t)}
              className={cx('h-[38px] rounded-full px-4 text-sm font-semibold transition-colors',
                topic === t ? 'bg-slate-900 text-white' : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50')}>
              {t}
            </button>
          ))}
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {shown.map((a) => {
          const [bg, fg] = TOPIC_STYLE[a.category] ?? TOPIC_STYLE.Nutrition;
          return (
            <Link key={a.slug} to={`/articles/${a.slug}`} className="flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white hover:border-brand-300">
              <span className={cx('flex h-36 items-end p-4', bg)}>
                <span className={cx('rounded-full bg-white px-2.5 py-1 text-xs font-semibold', fg)}>{a.category}</span>
              </span>
              <span className="flex flex-col gap-2 p-4">
                <span className="text-lg font-semibold leading-snug text-slate-900">{a.title}</span>
                <span className="text-sm text-slate-600">{a.minutes} min read</span>
              </span>
            </Link>
          );
        })}
      </div>
    </section>
  );
};

/* ------------------------------------------------------------------ FAQ */

const HOME_FAQ = [
  ['Is my report stored?', 'The file you upload is never stored. Your name and phone number are removed before anything else. Results are saved only if you are signed in, and only you can see them.'],
  ['Which labs and tests are supported?', 'Printed reports from any Indian lab, as a PDF or a clear photo. NutriLens reads 61 common tests: blood count, sugar, cholesterol, liver, kidney, thyroid, iron and vitamins.'],
  ['How are the diet plans made?', 'Your calories and protein come from your age, sex, height, weight and activity. An optimisation engine then picks dishes and portions from 270+ Indian home recipes so each day meets your targets and the nutrients your report shows as low, within your diet, region and allergies.'],
  ['Is this a medical diagnosis?', 'No. NutriLens gives general nutrition guidance. Results that need medical care are clearly marked, and you should always talk to your doctor before changing treatment.'],
  ['Is NutriLens free?', 'Yes. Analysing reports, diet plans and saving them to your account are free.'],
];

export const FaqSection: React.FC = () => (
  <section id="faq" className="mx-[calc(50%-50vw)] w-screen -mb-10 scroll-mt-16 bg-slate-50 px-4 py-16 sm:-mb-14 sm:px-6 lg:px-8">
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <div className="text-center">
        <p className="eyebrow">FAQ</p>
        <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Questions people ask us</h2>
      </div>
      <div className="flex flex-col gap-2.5">
        {HOME_FAQ.map(([q, a], i) => (
          <details key={q} open={i === 0} className="rounded-2xl border border-slate-200 bg-white px-5 py-4">
            <summary className="cursor-pointer text-base font-semibold text-slate-900">{q}</summary>
            <p className="mt-2.5 text-[15px] leading-relaxed text-slate-600">{a}</p>
          </details>
        ))}
      </div>
      <p className="text-center text-sm">
        <Link to="/faq" className="font-semibold text-brand-700 hover:underline">More questions</Link>
      </p>
    </div>
  </section>
);
