import { readDietFile } from '../services/api';
import React from 'react';
import { Bike, Footprints, Loader2, Plus, Sofa, Upload, X, Zap } from 'lucide-react';
import { Activity, UserProfile } from '../types';
import { cx } from './ui';
import { StringKey, useT } from '../lib/i18n';

export const REGIONS: { id: string; label: string }[] = [
  { id: 'telangana', label: 'Telangana' },
  { id: 'andhra', label: 'Andhra Pradesh' },
  { id: 'tamil_nadu', label: 'Tamil Nadu' },
  { id: 'kerala', label: 'Kerala' },
  { id: 'karnataka', label: 'Karnataka' },
  { id: 'punjab', label: 'Punjab' },
  { id: 'haryana', label: 'Haryana' },
  { id: 'delhi', label: 'Delhi' },
  { id: 'uttar_pradesh', label: 'Uttar Pradesh' },
  { id: 'uttarakhand', label: 'Uttarakhand' },
  { id: 'himachal_pradesh', label: 'Himachal Pradesh' },
  { id: 'jammu_kashmir', label: 'Jammu and Kashmir' },
  { id: 'ladakh', label: 'Ladakh' },
  { id: 'maharashtra', label: 'Maharashtra' },
  { id: 'gujarat', label: 'Gujarat' },
  { id: 'goa', label: 'Goa' },
  { id: 'rajasthan', label: 'Rajasthan' },
  { id: 'madhya_pradesh', label: 'Madhya Pradesh' },
  { id: 'chhattisgarh', label: 'Chhattisgarh' },
  { id: 'west_bengal', label: 'West Bengal' },
  { id: 'odisha', label: 'Odisha' },
  { id: 'bihar', label: 'Bihar' },
  { id: 'jharkhand', label: 'Jharkhand' },
  { id: 'assam', label: 'Assam' },
  { id: 'meghalaya', label: 'Meghalaya' },
  { id: 'manipur', label: 'Manipur' },
  { id: 'nagaland', label: 'Nagaland' },
  { id: 'mizoram', label: 'Mizoram' },
  { id: 'arunachal_pradesh', label: 'Arunachal Pradesh' },
  { id: 'sikkim', label: 'Sikkim' },
  { id: 'tripura', label: 'Tripura' },
];

const ACTIVITIES: { id: Activity; icon: React.ReactNode }[] = [
  { id: 'none', icon: <Sofa className="h-4 w-4" aria-hidden /> },
  { id: 'walking', icon: <Footprints className="h-4 w-4" aria-hidden /> },
  { id: 'cycling', icon: <Bike className="h-4 w-4" aria-hidden /> },
  { id: 'running', icon: <Zap className="h-4 w-4" aria-hidden /> },
];

const MEATS = ['chicken', 'mutton', 'fish', 'shellfish', 'egg', 'beef', 'pork'];

type Setter = React.Dispatch<React.SetStateAction<UserProfile>>;

const choice = (selected: boolean) =>
  cx(
    'rounded-xl border px-4 py-3 text-left transition-colors',
    selected ? 'border-brand-600 bg-brand-50 ring-1 ring-brand-600' : 'border-slate-300 bg-white hover:border-slate-400 hover:bg-slate-50'
  );

export const BodyFields: React.FC<{ profile: UserProfile; setProfile: Setter; errors: Record<string, string> }> = ({
  profile,
  setProfile,
  errors,
}) => {
  const t = useT();
  const number = (key: 'height_cm' | 'weight_kg') => (e: React.ChangeEvent<HTMLInputElement>) =>
    setProfile((p) => ({ ...p, [key]: e.target.value === '' ? null : Number(e.target.value) }));
  return (
    <>
      <div>
        <label htmlFor="height" className="mb-1.5 block text-sm font-medium text-slate-700">{t('height')}</label>
        <input id="height" type="number" min={120} max={220} value={profile.height_cm ?? ''} onChange={number('height_cm')}
          aria-invalid={!!errors.height} className="field tabular-nums" />
        {errors.height && <p role="alert" className="mt-1.5 text-xs text-red-700">{errors.height}</p>}
      </div>
      <div>
        <label htmlFor="weight" className="mb-1.5 block text-sm font-medium text-slate-700">{t('weight')}</label>
        <input id="weight" type="number" min={30} max={200} value={profile.weight_kg ?? ''} onChange={number('weight_kg')}
          aria-invalid={!!errors.weight} className="field tabular-nums" />
        {errors.weight && <p role="alert" className="mt-1.5 text-xs text-red-700">{errors.weight}</p>}
      </div>
      <div className="sm:col-span-2">
        <label htmlFor="region" className="mb-1.5 block text-sm font-medium text-slate-700">{t('region')}</label>
        <select id="region" className="field h-10 pr-8" value={profile.region ?? ''}
          onChange={(e) => setProfile((p) => ({ ...p, region: e.target.value }))}>
          <option value="">{t('chooseState')}</option>
          {REGIONS.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
          <option value="other">{t('otherState')}</option>
        </select>
        <p className="mt-1.5 text-xs text-slate-500">{t('regionHint')}</p>
      </div>
      <div className="sm:col-span-2">
        <span id="activity-label" className="mb-1.5 block text-sm font-medium text-slate-700">{t('activity')}</span>
        <div role="radiogroup" aria-labelledby="activity-label" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {ACTIVITIES.map((a) => {
            const selected = (profile.activity ?? 'none') === a.id;
            return (
              <button key={a.id} type="button" role="radio" aria-checked={selected} className={choice(selected)}
                onClick={() => setProfile((p) => ({ ...p, activity: a.id }))}>
                <span className="flex items-center gap-2 text-sm font-semibold text-slate-900">{a.icon}{t(`act_${a.id}` as StringKey)}</span>
                <span className="mt-0.5 block text-xs text-slate-500">{t(`act_${a.id}_hint` as StringKey)}</span>
              </button>
            );
          })}
        </div>
      </div>
    </>
  );
};

export const MeatFields: React.FC<{ profile: UserProfile; setProfile: Setter }> = ({ profile, setProfile }) => {
  const t = useT();
  if (profile.diet_type !== 'non_veg') return null;
  const meats = profile.meats ?? [];
  const toggle = (id: string) =>
    setProfile((p) => {
      const current = p.meats ?? [];
      return { ...p, meats: current.includes(id) ? current.filter((m) => m !== id) : [...current, id] };
    });
  return (
    <div className="space-y-2 pt-2">
      <p className="text-sm font-medium text-slate-700">{t('meatsQuestion')}</p>
      <p className="text-xs text-slate-500">{t('meatsHint')}</p>
      <div className="flex flex-wrap gap-2">
        {MEATS.map((m) => {
          const on = meats.includes(m);
          return (
            <button key={m} type="button" aria-pressed={on} onClick={() => toggle(m)}
              className={cx('rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors',
                on ? 'border-brand-600 bg-brand-600 text-white' : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50')}>
              {t(`meat_${m}` as StringKey)}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export const CustomAllergyField: React.FC<{ profile: UserProfile; setProfile: Setter }> = ({ profile, setProfile }) => {
  const t = useT();
  const [text, setText] = React.useState('');
  const items = profile.custom_allergies ?? [];
  const add = () => {
    const value = text.trim();
    if (!value || items.some((i) => i.toLowerCase() === value.toLowerCase())) return setText('');
    setProfile((p) => ({ ...p, custom_allergies: [...(p.custom_allergies ?? []), value].slice(0, 20) }));
    setText('');
  };
  return (
    <div className="rounded-xl border-2 border-dashed border-red-300 bg-red-50/50 p-4">
      <label htmlFor="custom-allergy" className="block text-sm font-semibold text-red-900">
        {t('customAllergy')}
      </label>
      <p className="mt-0.5 text-xs text-red-800/80">{t('customAllergyHint')}</p>
      <div className="mt-3 flex gap-2">
        <input id="custom-allergy" value={text} maxLength={40} placeholder={t('typeFood')} className="field flex-1"
          onChange={(e) => setText(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); add(); } }} />
        <button type="button" onClick={add}
          className="inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-4 text-sm font-semibold text-white hover:bg-red-700">
          <Plus className="h-4 w-4" aria-hidden /> {t('add')}
        </button>
      </div>
      {items.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-2">
          {items.map((item) => (
            <li key={item} className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1 text-sm font-medium text-red-900 ring-1 ring-red-300">
              {item}
              <button type="button" aria-label={`${t('remove')} ${item}`} className="rounded-full p-0.5 hover:bg-red-100"
                onClick={() => setProfile((p) => ({ ...p, custom_allergies: (p.custom_allergies ?? []).filter((i) => i !== item) }))}>
                <X className="h-3.5 w-3.5" aria-hidden />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export const ExistingDietField: React.FC<{ profile: UserProfile; setProfile: Setter }> = ({ profile, setProfile }) => {
  const t = useT();
  const [answer, setAnswer] = React.useState<'no' | 'yes' | null>(profile.existing_diet ? 'yes' : null);
  const [reading, setReading] = React.useState(false);
  const [readError, setReadError] = React.useState<string | null>(null);
  const readFile = async (file: File) => {
    setReadError(null);
    setReading(true);
    try {
      // Text files are read here; photos and PDFs are read on the server (Tesseract OCR, names and numbers removed).
      const text = file.type === 'text/plain' || file.name.endsWith('.txt') ? await file.text() : await readDietFile(file);
      setProfile((p) => ({ ...p, existing_diet: text.slice(0, 4000) }));
    } catch (e) {
      setReadError(e instanceof Error ? e.message : t('dietReadError'));
    } finally {
      setReading(false);
    }
  };
  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-slate-700">{t('dietNow')}</p>
      <div role="radiogroup" className="grid max-w-sm grid-cols-2 gap-3">
        {(['no', 'yes'] as const).map((id) => (
          <button key={id} type="button" role="radio" aria-checked={answer === id} className={choice(answer === id)}
            onClick={() => { setAnswer(id); if (id === 'no') setProfile((p) => ({ ...p, existing_diet: '' })); }}>
            <span className="text-sm font-semibold text-slate-900">{t(id)}</span>
          </button>
        ))}
      </div>
      {answer === 'yes' && (
        <div className="rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-5">
          <label htmlFor="existing-diet" className="flex items-center gap-2 text-sm font-semibold text-slate-800">
            <Upload className="h-4 w-4 text-brand-700" aria-hidden /> {t('dietUpload')}
          </label>
          <p className="mt-0.5 text-xs text-slate-500">{t('dietUploadHint')}</p>
          <textarea id="existing-diet" rows={4} maxLength={4000} className="field mt-3 h-auto py-2"
            placeholder={t('dietPlaceholder')}
            value={profile.existing_diet ?? ''} onChange={(e) => setProfile((p) => ({ ...p, existing_diet: e.target.value }))} />
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
              {reading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Upload className="h-4 w-4" aria-hidden />}
              {reading ? t('readingFile') : t('uploadText')}
              <input type="file" accept=".txt,.pdf,.jpg,.jpeg,.png,text/plain,application/pdf,image/jpeg,image/png" className="sr-only"
                disabled={reading}
                onChange={(e) => { const f = e.target.files?.[0]; if (f) void readFile(f); }} />
            </label>
            <button type="button" className="text-sm font-medium text-slate-500 underline-offset-2 hover:underline"
              onClick={() => { setAnswer('no'); setProfile((p) => ({ ...p, existing_diet: '' })); }}>
              {t('skip')}
            </button>
          </div>
          {readError && <p className="mt-2 text-sm text-red-700" role="alert">{readError}</p>}
        </div>
      )}
    </div>
  );
};
