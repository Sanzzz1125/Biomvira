import React from 'react';

/* A real example: day 1 of the plan the engine builds for a vegetarian woman in Telangana (30 years, 160 cm, 57 kg)
   whose report shows low iron (haemoglobin, ferritin). Dishes, iron foods and day totals are taken from that plan. */
const STEPS = ['Reading your report', 'Understanding your results', 'Choosing foods for you', 'Planning your week'];
const CHIPS = [
  { label: 'Hb 10.4 ↓', x: 0, y: -84, low: true }, { label: 'Ferritin 9 ↓', x: 80, y: -26, low: true },
  { label: '+ Gongura', x: 49, y: 68 }, { label: '+ Horse gram', x: -49, y: 68 }, { label: '+ Bajra', x: -80, y: -26 },
];
const MEALS = [['B', 'Pesarattu'], ['L', 'Sajja rotte'], ['S', 'Roasted corn'], ['D', 'Mudda pappu']];
const LEAVES = [{ x: 70, d: 0, s: 1 }, { x: 150, d: 1.6, s: 0.8 }, { x: 300, d: 0.8, s: 1.1 }, { x: 390, d: 2.4, s: 0.9 }, { x: 230, d: 3.2, s: 0.7 }];

/** Hero animation: a report flows in, results and foods circle the Biomvira leaf, a day of meals comes out. */
export const HeroVisual: React.FC = () => {
  const still = typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const [step, setStep] = React.useState(still ? 3 : 0);
  React.useEffect(() => {
    if (still) return;
    const id = window.setInterval(() => setStep((s) => (s + 1) % STEPS.length), 1800);
    return () => window.clearInterval(id);
  }, [still]);

  return (
    <div className="relative w-full min-w-0 max-w-[480px] flex-[1_1_400px] overflow-hidden rounded-[24px] border border-brand-100 bg-gradient-to-br from-white via-brand-50/60 to-emerald-50 p-5 shadow-[0_24px_48px_-20px_rgba(15,23,42,0.25)]">
      <svg viewBox="0 88 460 220" className="h-auto w-full" aria-hidden>
        <defs>
          <linearGradient id="nl-flow" x1="0" x2="1">
            <stop offset="0" stopColor="#34d399" stopOpacity="0.2" />
            <stop offset="1" stopColor="#167c64" />
          </linearGradient>
          <path id="nl-leaf" d="M0 0 C 6 -10 18 -10 22 0 C 18 10 6 10 0 0 Z" />
        </defs>
        {LEAVES.map((l, i) => (
          <g key={i} transform={`translate(${l.x} 320) scale(${l.s})`} opacity="0">
            <use href="#nl-leaf" fill="#86efac" />
            {!still && (
              <>
                <animateTransform attributeName="transform" type="translate" additive="sum" values="0 0; 18 -110; -10 -230"
                  dur="7s" begin={`${l.d}s`} repeatCount="indefinite" />
                <animate attributeName="opacity" values="0;0.8;0" dur="7s" begin={`${l.d}s`} repeatCount="indefinite" />
              </>
            )}
          </g>
        ))}

        <g transform="translate(14 132)">
          <rect width="84" height="108" rx="12" fill="#fff" stroke="#cbd5e1" />
          <text x="14" y="20" fontSize="9" fontWeight="700" fill="#64748b">CBC · IRON</text>
          {[34, 50, 66, 82].map((y, i) => (
            <rect key={y} x="14" y={y} width={i % 2 ? 40 : 56} height="6" rx="3" fill={i < 2 ? '#fca5a5' : '#e2e8f0'}>
              {!still && <animate attributeName="fill" values={`${i < 2 ? '#fca5a5' : '#e2e8f0'};#a7f3d0;${i < 2 ? '#fca5a5' : '#e2e8f0'}`}
                dur="3.6s" begin={`${i * 0.3}s`} repeatCount="indefinite" />}
            </rect>
          ))}
          <text x="42" y="126" textAnchor="middle" fontSize="11" fill="#475569" fontWeight="600">Lab report</text>
        </g>

        {['M100 186 C 136 186, 150 190, 174 190', 'M286 190 C 310 190, 318 186, 346 186'].map((d) => (
          <path key={d} d={d} fill="none" stroke="url(#nl-flow)" strokeWidth="3" strokeLinecap="round" strokeDasharray="6 8">
            {!still && <animate attributeName="stroke-dashoffset" values="28;0" dur="1s" repeatCount="indefinite" />}
          </path>
        ))}

        <g transform="translate(230 190)">
          <circle r="84" fill="none" stroke="#bbf7d0" strokeDasharray="2 7">
            {!still && <animateTransform attributeName="transform" type="rotate" values="0;360" dur="40s" repeatCount="indefinite" />}
          </circle>
          <g>
            {!still && <animateTransform attributeName="transform" type="rotate" values="0;360" dur="24s" repeatCount="indefinite" />}
            {CHIPS.map((c) => (
              <g key={c.label} transform={`translate(${c.x} ${c.y})`}>
                <g>
                  {!still && <animateTransform attributeName="transform" type="rotate" values="0;-360" dur="24s" repeatCount="indefinite" />}
                  <rect x="-34" y="-11" width="68" height="22" rx="11" fill="#fff" stroke={c.low ? '#fecaca' : '#86efac'} />
                  <text textAnchor="middle" y="4" fontSize="9.5" fontWeight="600" fill={c.low ? '#b91c1c' : '#136352'}>{c.label}</text>
                </g>
              </g>
            ))}
          </g>
          <circle r="54" fill="#167c64" opacity="0.12">
            {!still && <animate attributeName="r" values="48;58;48" dur="2.4s" repeatCount="indefinite" />}
          </circle>
          <image href="/biomvira-mark.svg" x="-36" y="-36" width="72" height="72" />
        </g>

        <g transform="translate(348 132)">
          <rect width="100" height="108" rx="12" fill="#fff" stroke="#cbd5e1" />
          <text x="12" y="20" fontSize="9" fontWeight="700" fill="#64748b">DAY 1</text>
          {MEALS.map(([slot, dish], i) => (
            <g key={slot} transform={`translate(12 ${36 + i * 19})`} opacity={still ? 1 : 0}>
              {!still && <animate attributeName="opacity" values="0;0;1;1;0" keyTimes={`0;${0.12 + i * 0.12};${0.2 + i * 0.12};0.92;1`}
                dur="7.2s" repeatCount="indefinite" />}
              <rect x="-2" y="-9" width="14" height="13" rx="3" fill="#d7f3e8" />
              <text x="5" y="1" textAnchor="middle" fontSize="8" fontWeight="700" fill="#136352">{slot}</text>
              <text x="18" y="1" fontSize="9.5" fill="#0f172a" fontWeight="600">{dish}</text>
            </g>
          ))}
          <text x="50" y="126" textAnchor="middle" fontSize="11" fill="#475569" fontWeight="600">7-day plan</text>
        </g>
      </svg>

      <p className="mt-2 flex items-center justify-center gap-2 text-sm font-medium text-slate-700" aria-live="polite">
        <span className="h-2 w-2 animate-pulse rounded-full bg-brand-600" aria-hidden />
        <span key={step} className="animate-fade-in">{STEPS[step]}…</span>
      </p>
    </div>
  );
};
