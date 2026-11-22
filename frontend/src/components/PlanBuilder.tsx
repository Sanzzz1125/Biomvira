import React from 'react';
import { ArrowLeft, BookmarkCheck, CalendarDays, Check, Download, Loader2, RefreshCw, ShoppingBasket, Sparkles } from 'lucide-react';
import { downloadDietPlanPdf, getShoppingList, planOptions, planSwap, planWeek, PlanInput, PlanMarker, saveDietPlan } from '../services/api';
import { FullAnalysisResponse, MealSlot, PlanDay, PlanStyle, ShoppingItem, UserProfile } from '../types';
import { Alert, Badge, Button, Card, cx } from './ui';
import { localizeWords, StringKey, useLanguage, useT } from '../lib/i18n';

const SLOTS: MealSlot[] = ['breakfast', 'lunch', 'snack', 'dinner'];
const AISLES = ['grains', 'pulses', 'vegetables', 'greens', 'fruits', 'dairy', 'meat_fish', 'nuts_seeds', 'spices', 'oils', 'other'];
const UNITS: Record<string, string> = {
  iron_mg: 'mg', calcium_mg: 'mg', folate_ug: 'µg', vitamin_c_mg: 'mg', vitamin_b12_ug: 'µg', vitamin_d_iu: 'IU',
  zinc_mg: 'mg', magnesium_mg: 'mg', fibre_g: 'g',
};

const PLURALS: Record<string, string> = {
  cup: 'cups', roti: 'rotis', katori: 'katoris', glass: 'glasses', phulka: 'phulkas', chapati: 'chapatis', plate: 'plates',
  bowl: 'bowls', paratha: 'parathas', dosa: 'dosas', egg: 'eggs', puttu: 'puttus', rotti: 'rottis', ball: 'balls',
  tablespoon: 'tablespoons', handful: 'handfuls', piece: 'pieces', laddu: 'laddus', medium: 'medium', bhatura: 'bhaturas',
  samosa: 'samosas', parotta: 'parottas', pesarattu: 'pesarattus', uttapam: 'uttapams', adai: 'adais',
};
/** "2" and "1 cup cooked" -> "2 cups cooked"; anything else -> "2 × 2 idlis". */
export const portion = (servings: number, serving: string) => {
  if (servings === 1) return serving;
  const m = serving.match(/^1 (small |big )?([a-z]+)(.*)$/i);
  if (m && PLURALS[m[2].toLowerCase()]) return `${servings} ${m[1] ?? ''}${PLURALS[m[2].toLowerCase()]}${m[3]}`;
  return `${servings} × ${serving}`;
};

const fmt = (n: number) => (n >= 100 ? Math.round(n).toLocaleString('en-IN') : String(Math.round(n * 10) / 10));

const Meals: React.FC<{ day: PlanDay; onSwap?: (slot: MealSlot, dishId: string) => void; busy?: string | null }> = ({
  day,
  onSwap,
  busy,
}) => {
  const t = useT();
  const language = useLanguage();
  return (
  <div className="divide-y divide-slate-100">
    {SLOTS.map((slot) => (
      <div key={slot} className="py-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{t(`slot_${slot}` as StringKey)}</p>
        <ul className="mt-1.5 space-y-1.5">
          {day.meals[slot].map((item) => (
            <li key={item.dish_id} className="flex items-center justify-between gap-3">
              <span className="min-w-0 text-sm text-slate-800">
                <span className="font-medium">{(language !== 'en' && item.names?.[language]) || item.name}</span>
                <span className="text-slate-500"> · {localizeWords(portion(item.servings, item.serving), language)}</span>
              </span>
              {onSwap && (
                <button type="button" onClick={() => onSwap(slot, item.dish_id)} disabled={!!busy}
                  aria-label={`${t('swap')} ${item.name}`}
                  className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-slate-300 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50">
                  {busy === `${slot}:${item.dish_id}` ? <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden /> : <RefreshCw className="h-3.5 w-3.5" aria-hidden />}
                  {t('swap')}
                </button>
              )}
            </li>
          ))}
        </ul>
      </div>
    ))}
  </div>
  );
};

const Totals: React.FC<{ day: PlanDay }> = ({ day }) => {
  const tr = useT();
  const t = day.targets;
  const watched = t.low.length ? t.low : ['iron_mg', 'calcium_mg'];
  const short = Object.entries(day.shortfalls ?? {});
  return (
    <div className="space-y-3">
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      <Stat label={tr('calories')} value={`${fmt(day.totals.energy_kcal)} kcal`} hint={`${tr('target')} ${fmt(t.energy_kcal)}`} />
      <Stat label={tr('protein')} value={`${fmt(day.totals.protein_g)} g`} hint={`${tr('target')} ${fmt(t.protein_g)} g`} />
      {watched.slice(0, 2).map((key) => {
        const unit = UNITS[key] ?? '';
        return (
          <Stat key={key} label={tr(`nut_${key}` as StringKey)} value={`${fmt(day.totals[key] ?? 0)} ${unit}`} hint={`${tr('need')} ${fmt(t.rda[key])} ${unit}`}
            good={day.rda_met[key]} />
        );
      })}
    </div>
    {short.length > 0 && (
      <div className="rounded-xl border border-amber-200 bg-amber-50/80 p-3 text-xs leading-relaxed text-amber-900">
        <p className="font-semibold text-amber-950">{tr('shortfallTitle')}</p>
        {short.map(([key, s]) => {
          const unit = UNITS[key] ?? '';
          const vars = { n: tr(`nut_${key}` as StringKey), a: `${fmt(s.actual)} ${unit}`, b: `${fmt(s.target)} ${unit}`, p: fmt(s.pct_met) };
          return <p key={key} className="mt-1">{tr(key === 'vitamin_d_iu' ? 'shortfallVitD' : 'shortfall', vars)}</p>;
        })}
      </div>
    )}
    </div>
  );
};

const Stat: React.FC<{ label: string; value: string; hint: string; good?: boolean }> = ({ label, value, hint, good }) => (
  <div className={cx('rounded-xl border px-3 py-2', good ? 'border-brand-200 bg-brand-50' : 'border-slate-200 bg-white')}>
    <p className={cx('text-xs', good ? 'text-brand-700' : 'text-slate-500')}>{label}</p>
    <p className="text-[15px] font-semibold tabular-nums text-slate-900">{value}</p>
    <p className="text-[11px] text-slate-500">{hint}</p>
  </div>
);

export type WeekPlan = { style: PlanStyle; days: PlanDay[]; shopping_list: ShoppingItem[] };

const Step: React.FC<{ n: number; title: string; hint: string; active: boolean }> = ({ n, title, hint, active }) => (
  <div className="flex items-start gap-3">
    <span className={cx('flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-bold',
      active ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-500')}>{n}</span>
    <div>
      <p className={cx('text-[15px] font-semibold', active ? 'text-slate-900' : 'text-slate-500')}>{title}</p>
      <p className="text-sm text-slate-600">{hint}</p>
    </div>
  </div>
);

export const PlanBuilder: React.FC<{
  result: FullAnalysisResponse;
  profile: UserProfile;
  picked: string[];
  reportId?: string | null;
  /** Bumped by the page when the picked foods change and the plan should be rebuilt with them. */
  rebuildToken?: number;
  onWeekChange?: (week: WeekPlan | null) => void;
  onChooseFoods?: () => void;
}> = ({ result, profile: initialProfile, picked, reportId = null, rebuildToken = 0, onWeekChange, onChooseFoods }) => {
  const language = useLanguage();
  const t = useT();
  const [profile, setProfile] = React.useState<UserProfile>(initialProfile);
  const [options, setOptions] = React.useState<PlanDay[] | null>(null);
  const savedPlan = result.diet_plan;
  const [week, setWeek] = React.useState<{ style: PlanStyle; days: PlanDay[]; shopping: ShoppingItem[] } | null>(
    savedPlan ? { style: savedPlan.style, days: savedPlan.days, shopping: savedPlan.shopping_list } : null
  );
  const [saved, setSaved] = React.useState(!!savedPlan);
  const [dayIndex, setDayIndex] = React.useState(0);
  const [showList, setShowList] = React.useState(false);
  const [loading, setLoading] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  React.useEffect(() => setProfile(initialProfile), [initialProfile]);

  const markers: PlanMarker[] = result.marker_analyses.map((m) => ({
    biomarker_key: m.biomarker_key, status: m.status, target_nutrient_key: m.target_nutrient_key || null,
  }));
  const input = (style?: PlanStyle): PlanInput => ({ profile, markers, picked_foods: picked, style });
  const inRange = (v: number | null | undefined, lo: number, hi: number) => !!v && v >= lo && v <= hi;
  // The same limits the plan service accepts (height 120-220 cm, weight 30-200 kg, adults only).
  const ready = inRange(profile.height_cm, 120, 220) && inRange(profile.weight_kg, 30, 200) && profile.age >= 18;

  const run = async (key: string, work: () => Promise<void>) => {
    setLoading(key);
    setError(null);
    try {
      await work();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not build the plan. Please try again.');
    } finally {
      setLoading(null);
    }
  };

  const buildOptions = () => ready && run('options', async () => {
    const r = await planOptions(input());
    setOptions(r.options);
    setWeek(null);
  });
  const buildWeek = (style: PlanStyle) => run(`week:${style}`, async () => {
    const r = await planWeek(input(style));
    setWeek({ style, days: r.days, shopping: r.shopping_list });
    setDayIndex(0);
    setSaved(false);
  });
  // Plans are the main result: build the three options as soon as the page opens (unless a plan was saved).
  React.useEffect(() => {
    if (ready && !week && !options && !loading) buildOptions();
    // Only on opening: while height or weight is being typed in, the person presses the button instead.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  // Foods were picked or removed: rebuild what is on screen with them.
  React.useEffect(() => {
    if (!rebuildToken || !ready) return;  // 0 on opening: the opening build above already uses the picks
    if (week) buildWeek(week.style);
    else buildOptions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rebuildToken]);
  React.useEffect(() => {
    onWeekChange?.(week ? { style: week.style, days: week.days, shopping_list: week.shopping } : null);
  }, [week, onWeekChange]);

  const swap = (slot: MealSlot, dishId: string) => week && run(`${slot}:${dishId}`, async () => {
    const r = await planSwap(input(week.style), week.days[dayIndex], slot, dishId);
    const days = week.days.map((d, i) => (i === dayIndex ? r.day : d));
    // The shopping list follows the swapped dish; if that request fails, the old list stays rather than none.
    const shopping = await getShoppingList(days).then((s) => s.shopping_list).catch(() => week.shopping);
    setWeek({ ...week, days, shopping });
    setSaved(false);
  });

  return (
    <Card className="overflow-hidden shadow-card">
      <div className="space-y-4 border-b border-slate-200 bg-slate-50 px-6 py-5">
        <div>
          <p className="eyebrow">{t('dietPlan')}</p>
          <h3 className="mt-0.5 text-lg font-semibold text-slate-900">{t('planTitle')}</h3>
          <p className="mt-1 text-sm text-slate-600">{t('planPromise')}</p>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <Step n={1} title={t('step1')} hint={t('step1Hint')} active={!week} />
          <Step n={2} title={t('step2')} hint={t('step2Hint')} active={!!week} />
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700">
          <span>{picked.length === 1 ? t('foodsInPlanOne') : picked.length > 1 ? t('foodsInPlan', { n: picked.length }) : t('noFoodsPicked')}</span>
          {onChooseFoods && (
            <button type="button" onClick={onChooseFoods} className="font-semibold text-brand-700 hover:underline">
              {picked.length > 0 ? t('changeFoods') : t('chooseFoods')}
            </button>
          )}
        </div>
      </div>
      <div className="space-y-5 p-6">
        {error && (
          <Alert tone="error" title={t('planError')}>
            {error}{' '}
            <button type="button" className="font-semibold underline" onClick={() => (week ? buildWeek(week.style) : buildOptions())}>
              {t('tryAgain')}
            </button>
          </Alert>
        )}

        <div className="grid gap-4 sm:grid-cols-3">
          {profile.age < 18 ? (
            <p className="text-sm text-slate-600 sm:col-span-3">{t('adultsOnly')}</p>
          ) : (
            <>
              <label className="text-sm font-medium text-slate-700">{t('height')}
                <input type="number" min={120} max={220} className="field mt-1.5" value={profile.height_cm ?? ''}
                  onChange={(e) => setProfile({ ...profile, height_cm: Number(e.target.value) || null })} />
              </label>
              <label className="text-sm font-medium text-slate-700">{t('weight')}
                <input type="number" min={30} max={200} className="field mt-1.5" value={profile.weight_kg ?? ''}
                  onChange={(e) => setProfile({ ...profile, weight_kg: Number(e.target.value) || null })} />
              </label>
              <p className="self-end text-xs text-slate-500">{t('neededForCalories')}</p>
            </>
          )}
        </div>

        {!week && (!options || !ready) && (
          <Button onClick={buildOptions} loading={loading === 'options'} disabled={!ready || !!loading}
            icon={<Sparkles className="h-4 w-4" aria-hidden />}>
            {loading === 'options' ? t('building') : options ? t('rebuild') : t('build')}
          </Button>
        )}

        {!week && !options && loading === 'options' && (
          <div className="grid gap-4 lg:grid-cols-3" aria-hidden>
            {[0, 1, 2].map((i) => <div key={i} className="h-80 animate-pulse rounded-2xl bg-slate-100" />)}
          </div>
        )}

        {options && !week && (
          <div className="grid gap-4 lg:grid-cols-3">
            {options.map((o) => (
              <div key={o.style} className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="text-base font-semibold text-slate-900">{t(`style_${o.style}` as StringKey)}</h4>
                    <p className="text-xs text-slate-500">{t(`note_${o.style}` as StringKey)}</p>
                  </div>
                  <Badge tone="brand">{fmt(o.totals.energy_kcal)} kcal</Badge>
                </div>
                <div className="mt-3"><Totals day={o} /></div>
                <div className="mt-2 flex-1"><Meals day={o} /></div>
                <Button className="mt-4" onClick={() => buildWeek(o.style as PlanStyle)}
                  loading={loading === `week:${o.style}`} disabled={!!loading}
                  icon={<CalendarDays className="h-4 w-4" aria-hidden />}>
                  {t('makeWeek')}
                </Button>
              </div>
            ))}
          </div>
        )}

        {week && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <button type="button" onClick={() => setWeek(null)}
                className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-slate-900">
                <ArrowLeft className="h-4 w-4" aria-hidden /> {t('backToOptions')}
              </button>
              <div className="flex flex-wrap gap-2">
                <Button variant="secondary" size="sm" onClick={() => setShowList((s) => !s)}
                  icon={<ShoppingBasket className="h-4 w-4" aria-hidden />}>
                  {showList ? t('showMeals') : t('shoppingList')}
                </Button>
                <Button variant="secondary" size="sm" loading={loading === 'pdf'} disabled={!!loading}
                  onClick={() => run('pdf', () => downloadDietPlanPdf(week.days, week.shopping))}
                  icon={<Download className="h-4 w-4" aria-hidden />}>
                  PDF
                </Button>
                {!reportId && <span className="self-center text-xs text-slate-500">{t('signInToSave')}</span>}
                {reportId && (
                  <Button size="sm" loading={loading === 'save'} disabled={!!loading || saved}
                    onClick={() => run('save', async () => { await saveDietPlan(reportId, week.style, week.days, week.shopping); setSaved(true); })}
                    icon={<BookmarkCheck className="h-4 w-4" aria-hidden />}>
                    {saved ? t('savedWithReport') : t('saveWithReport')}
                  </Button>
                )}
              </div>
            </div>
            {loading?.startsWith('week:') && (
              <p className="flex items-center gap-2 rounded-xl bg-brand-50 px-3 py-2 text-sm font-medium text-brand-800" role="status">
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> {t('updatingPlan')}
              </p>
            )}
            {showList ? (
              <div className="space-y-4">
                <p className="text-sm text-slate-600">{t('shoppingHint')}</p>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {AISLES.filter((a) => week.shopping.some((i) => (i.aisle ?? 'other') === a && i.buy_g >= 5)).map((a) => {
                    const items = week.shopping.filter((i) => (i.aisle ?? 'other') === a && i.buy_g >= 5);
                    return (
                      <section key={a} className="rounded-2xl border border-slate-200 bg-white p-4">
                        <h4 className="flex items-center justify-between text-sm font-semibold text-slate-900">
                          {t(`aisle_${a}` as StringKey)}
                          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">{items.length}</span>
                        </h4>
                        <ul className="mt-3 divide-y divide-slate-100">
                          {items.map((i) => (
                            <li key={i.name} className="flex items-center justify-between gap-3 py-1.5 text-sm">
                              <span className="min-w-0 truncate capitalize text-slate-800">{(language !== 'en' && i.names?.[language]) || i.name}</span>
                              <span className="shrink-0 rounded-md bg-brand-50 px-2 py-0.5 text-xs font-semibold tabular-nums text-brand-800">
                                {i.buy_g >= 1000 ? `${(i.buy_g / 1000).toFixed(1)} kg` : `${Math.ceil(i.buy_g / 10) * 10} g`}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </section>
                    );
                  })}
                </div>
              </div>
            ) : (
              <>
                <div role="tablist" aria-label="Day" className="flex gap-2 overflow-x-auto">
                  {week.days.map((_, i) => (
                    <button key={i} type="button" role="tab" aria-selected={i === dayIndex} onClick={() => setDayIndex(i)}
                      className={cx('h-10 min-w-12 rounded-xl px-3 text-sm font-semibold',
                        i === dayIndex ? 'bg-brand-600 text-white' : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50')}>
                      {t('days').split(' ')[i]}
                    </button>
                  ))}
                </div>
                <Totals day={week.days[dayIndex]} />
                <Meals day={week.days[dayIndex]} onSwap={swap} busy={loading} />
                <p className="flex items-center gap-1.5 text-xs text-slate-500">
                  <Check className="h-3.5 w-3.5 text-brand-600" aria-hidden />
                  {t('saltNote', { g: week.days[dayIndex].salt_g })}
                </p>
              </>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};
