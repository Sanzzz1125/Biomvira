import React from 'react';
import { ArrowLeft, Check, ShieldCheck, Sparkles } from 'lucide-react';
import { DietType, UserProfile } from '../types';
import { Button, Card, PageHeader, cx } from './ui';
import { BodyFields, CustomAllergyField, ExistingDietField, MeatFields } from './PlanProfileFields';
import { useT } from '../lib/i18n';

interface UserProfileFormProps {
  profile: UserProfile;
  setProfile: React.Dispatch<React.SetStateAction<UserProfile>>;
  onSubmit: (profile: UserProfile) => void;
  onBack: () => void;
  isLoading: boolean;
}

const DIET_OPTIONS: { id: DietType; label: string; tag: string; description: string }[] = [
  {
    id: 'veg',
    label: 'Vegetarian',
    tag: 'Dairy + plants',
    description: 'No meat, fish or eggs. Includes paneer, curd, milk, ghee, pulses and millets.',
  },
  {
    id: 'vegan',
    label: 'Vegan',
    tag: '100% plant-based',
    description: 'No animal products. Relies on fortified plant milks, tofu, pulses, nuts and seeds.',
  },
  {
    id: 'eggetarian',
    label: 'Eggetarian',
    tag: 'Vegetarian + eggs',
    description: 'Vegetarian diet with eggs, a useful source of choline and Vitamin D.',
  },
  {
    id: 'non_veg',
    label: 'Non-vegetarian',
    tag: 'All foods',
    description: 'Includes poultry, fish and meat for heme iron, marine Vitamin D3 and natural B12.',
  },
];

const ALLERGEN_OPTIONS = [
  { id: 'dairy', label: 'Dairy & lactose', items: 'Milk, paneer, curd, ghee' },
  { id: 'gluten', label: 'Gluten / wheat', items: 'Atta, maida, rava, barley' },
  { id: 'nuts', label: 'Tree nuts & peanuts', items: 'Almonds, cashews, peanuts' },
  { id: 'soy', label: 'Soy', items: 'Soybeans, tofu, soy milk' },
  { id: 'eggs', label: 'Eggs', items: 'Whole eggs, egg whites' },
  { id: 'seafood', label: 'Fish & shellfish', items: 'Fish, prawns, crab' },
];

const SEX_OPTIONS = [
  { id: 'female', label: 'Female', hint: 'Hb reference ≥ 12.0 g/dL' },
  { id: 'male', label: 'Male', hint: 'Hb reference ≥ 13.8 g/dL' },
];

export const UserProfileForm: React.FC<UserProfileFormProps> = ({
  profile,
  setProfile,
  onSubmit,
  onBack,
  isLoading,
}) => {
  // Keep the editable value separate from the numeric API profile.
  const [ageInput, setAgeInput] = React.useState(String(profile.age));
  const [ageError, setAgeError] = React.useState<string | null>(null);
  const t = useT();
  const [bodyErrors, setBodyErrors] = React.useState<Record<string, string>>({});

  const handleSubmit = () => {
    if (!ageInput.trim()) {
      setAgeError('Please enter your age.');
      return;
    }
    const age = Number(ageInput);
    if (!Number.isInteger(age) || age < 1 || age > 120) {
      setAgeError('Please enter a whole-number age between 1 and 120.');
      return;
    }
    setAgeError(null);
    const errors: Record<string, string> = {};
    const h = profile.height_cm, w = profile.weight_kg;
    if (h != null && (h < 120 || h > 220)) errors.height = t('heightError');
    if (w != null && (w < 30 || w > 200)) errors.weight = t('weightError');
    setBodyErrors(errors);
    if (Object.keys(errors).length) return;
    const validatedProfile = { ...profile, age };
    setProfile(validatedProfile);
    // Pass the validated value explicitly: React state updates are asynchronous.
    onSubmit(validatedProfile);
  };

  const toggleAllergen = (id: string) => {
    setProfile((prev) => {
      const exists = prev.allergens.includes(id);
      return {
        ...prev,
        allergens: exists ? prev.allergens.filter((a) => a !== id) : [...prev.allergens, id],
      };
    });
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        eyebrow="Your profile"
        title="Tell us about you"
        description="Your age, sex and food preferences help us pick the right reference ranges and only suggest foods you can eat."
        actions={
          <Button
            variant="secondary"
            size="sm"
            onClick={onBack}
            icon={<ArrowLeft className="h-4 w-4" aria-hidden />}
          >
            Review results
          </Button>
        }
      />

      <Card className="divide-y divide-slate-200">
        {/* About you */}
        <section className="grid gap-6 p-6 sm:grid-cols-2 sm:p-8" aria-labelledby="about-heading">
          <div className="sm:col-span-2">
            <h3 id="about-heading" className="text-base font-semibold">
              About you
            </h3>
          </div>

          <div>
            <label htmlFor="age" className="mb-1.5 block text-sm font-medium text-slate-700">
              Age
            </label>
            <input
              id="age"
              type="number"
              min={1}
              max={120}
              step={1}
              value={ageInput}
              onChange={(e) => {
                setAgeInput(e.target.value);
                setAgeError(null);
              }}
              aria-invalid={!!ageError}
              aria-describedby={ageError ? 'age-error' : 'age-hint'}
              className="field tabular-nums"
            />
            {ageError && <p id="age-error" role="alert" className="mt-1.5 text-xs text-red-700">{ageError}</p>}
            <p id="age-hint" className="mt-1.5 text-xs text-slate-500">Used to apply ICMR-NIN recommended daily allowances.</p>
          </div>

          <div>
            <span id="sex-label" className="mb-1.5 block text-sm font-medium text-slate-700">
              Sex
            </span>
            <div role="radiogroup" aria-labelledby="sex-label" className="grid grid-cols-2 gap-3">
              {SEX_OPTIONS.map((opt) => {
                const selected = profile.gender.toLowerCase() === opt.id;
                return (
                  <button
                    key={opt.id}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    onClick={() => setProfile((prev) => ({ ...prev, gender: opt.id }))}
                    className={cx(
                      'rounded-lg border px-4 py-2 text-left transition-colors',
                      selected
                        ? 'border-brand-600 bg-brand-50 ring-1 ring-brand-600'
                        : 'border-slate-300 bg-white hover:border-slate-400 hover:bg-slate-50'
                    )}
                  >
                    <span className={cx('block text-sm font-semibold', selected ? 'text-brand-800' : 'text-slate-900')}>
                      {opt.label}
                    </span>
                    <span className="block text-xs text-slate-500">{opt.hint}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        <section className="grid gap-6 p-6 sm:grid-cols-2 sm:p-8" aria-labelledby="body-heading">
          <div className="sm:col-span-2">
            <h3 id="body-heading" className="text-base font-semibold">{t('bodyHeading')}</h3>
            <p className="mt-0.5 text-sm text-slate-500">{t('bodyHint')}</p>
          </div>
          <BodyFields profile={profile} setProfile={setProfile} errors={bodyErrors} />
        </section>

        {/* Diet */}
        <section className="space-y-4 p-6 sm:p-8" aria-labelledby="diet-heading">
          <div>
            <h3 id="diet-heading" className="text-base font-semibold">
              Diet type
            </h3>
            <p className="mt-0.5 text-sm text-slate-500">
              Foods outside your diet are never recommended.
            </p>
          </div>

          <div role="radiogroup" aria-labelledby="diet-heading" className="grid gap-3 md:grid-cols-2">
            {DIET_OPTIONS.map((opt) => {
              const selected = profile.diet_type === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  onClick={() => setProfile((prev) => ({ ...prev, diet_type: opt.id }))}
                  className={cx(
                    'relative rounded-xl border p-4 text-left transition-colors',
                    selected
                      ? 'border-brand-600 bg-brand-50 ring-1 ring-brand-600'
                      : 'border-slate-300 bg-white hover:border-slate-400 hover:bg-slate-50'
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="block text-[15px] font-semibold text-slate-900">{opt.label}</span>
                      <span className={cx('block text-xs font-medium', selected ? 'text-brand-700' : 'text-slate-500')}>
                        {opt.tag}
                      </span>
                    </div>
                    <span
                      aria-hidden
                      className={cx(
                        'flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition-colors',
                        selected ? 'border-brand-600 bg-brand-600 text-white' : 'border-slate-300 bg-white'
                      )}
                    >
                      {selected && <Check className="h-3 w-3" strokeWidth={3} />}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-slate-600">{opt.description}</p>
                </button>
              );
            })}
          </div>
          <MeatFields profile={profile} setProfile={setProfile} />
          <div className="pt-2"><ExistingDietField profile={profile} setProfile={setProfile} /></div>
        </section>

        {/* Allergens */}
        <section className="space-y-4 p-6 sm:p-8" aria-labelledby="allergen-heading">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h3 id="allergen-heading" className="text-base font-semibold">
                Allergies &amp; foods to avoid
              </h3>
              <p className="mt-0.5 text-sm text-slate-500">Select anything you need us to exclude.</p>
            </div>
            <span className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-700">
              <ShieldCheck className="h-4 w-4" aria-hidden />
              Always strictly excluded
            </span>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {ALLERGEN_OPTIONS.map((alg) => {
              const excluded = profile.allergens.includes(alg.id);
              return (
                <button
                  key={alg.id}
                  type="button"
                  aria-pressed={excluded}
                  onClick={() => toggleAllergen(alg.id)}
                  className={cx(
                    'flex items-start gap-3 rounded-xl border p-3.5 text-left transition-colors',
                    excluded
                      ? 'border-red-300 bg-red-50 ring-1 ring-red-300'
                      : 'border-slate-300 bg-white hover:border-slate-400 hover:bg-slate-50'
                  )}
                >
                  <span
                    aria-hidden
                    className={cx(
                      'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded border transition-colors',
                      excluded ? 'border-red-600 bg-red-600 text-white' : 'border-slate-300 bg-white'
                    )}
                  >
                    {excluded && <Check className="h-3 w-3" strokeWidth={3} />}
                  </span>
                  <span className="min-w-0">
                    <span className={cx('block text-sm font-semibold', excluded ? 'text-red-900' : 'text-slate-900')}>
                      {alg.label}
                    </span>
                    <span className="block truncate text-xs text-slate-500">{alg.items}</span>
                  </span>
                </button>
              );
            })}
          </div>
          <CustomAllergyField profile={profile} setProfile={setProfile} />
        </section>

        {/* Action */}
        <div className="flex flex-col-reverse items-stretch justify-between gap-4 rounded-b-2xl bg-slate-50 px-6 py-5 sm:flex-row sm:items-center sm:px-8">
          <p className="text-sm text-slate-500">
            Matched against <strong className="font-semibold text-slate-700">180+ ICMR-NIN Indian foods</strong>.
          </p>
          <Button
            size="lg"
            onClick={handleSubmit}
            loading={isLoading}
            icon={<Sparkles className="h-4 w-4" aria-hidden />}
          >
            {isLoading ? 'Building your plan…' : 'Generate my plan'}
          </Button>
        </div>
      </Card>
    </div>
  );
};
