import React from 'react';
import { Check, Link2, Plus, UtensilsCrossed } from 'lucide-react';
import { FoodRecommendation } from '../types';
import { Badge, cx } from './ui';
import { useLanguage, useT } from '../lib/i18n';

interface FoodCardProps {
  food: FoodRecommendation;
  /** Kept for callers; the card shows the amount per serving, which is clearer than the test name. */
  targetNutrientName?: string;
  selected?: boolean;
  onToggle?: () => void;
}

export const FoodCard: React.FC<FoodCardProps> = ({ food, selected = false, onToggle }) => {
  const t = useT();
  const language = useLanguage();
  const hasAmount = /\d/.test(food.key_nutrient_yield);
  return (
    <article className={cx('flex h-full min-w-0 flex-col overflow-hidden rounded-2xl border bg-white transition-colors',
      selected ? 'border-brand-600 bg-brand-50/40 ring-1 ring-brand-600' : 'border-slate-200 hover:border-brand-300')}>
      <div className="flex min-w-0 flex-1 flex-col gap-3 p-4">
        <div className="min-w-0">
          <Badge tone="neutral" className="max-w-full truncate">{food.category}</Badge>
          <h4 className="mt-2 break-words text-[15px] font-semibold leading-snug text-slate-900">{food.name}</h4>
          {food.hindi_name && language === 'en' && (
            <p className="mt-0.5 break-words text-sm text-slate-500">{food.hindi_name}</p>
          )}
        </div>

        <div className="rounded-xl bg-brand-50 px-3 py-2 ring-1 ring-inset ring-brand-100">
          <p className="text-base font-semibold tabular-nums text-brand-800">{food.key_nutrient_yield}</p>
          <p className="break-words text-xs text-brand-700/90">
            {hasAmount ? t('perOnly', { serving: food.serving_size }) : food.serving_size}
          </p>
        </div>

        {food.preparation_tip && (
          <p className="flex items-start gap-2 text-sm leading-relaxed text-slate-600">
            <UtensilsCrossed className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" aria-hidden />
            <span className="min-w-0 break-words">{food.preparation_tip}</span>
          </p>
        )}

        {food.synergies && food.synergies.length > 0 && (
          <ul className="mt-auto space-y-1.5 border-t border-slate-100 pt-3">
            {food.synergies.map((syn, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs leading-relaxed text-brand-700">
                <Link2 className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
                <span className="min-w-0 break-words">{syn}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {onToggle && (
        <button type="button" onClick={onToggle} aria-pressed={selected}
          aria-label={`${selected ? t('inPlan') : t('addToPlan')}: ${food.name}`}
          className={cx('flex h-11 w-full items-center justify-center gap-1.5 border-t text-sm font-semibold transition-colors',
            selected ? 'border-brand-600 bg-brand-600 text-white hover:bg-brand-700'
              : 'border-slate-200 bg-slate-50 text-brand-700 hover:bg-brand-50')}>
          {selected ? <Check className="h-4 w-4" strokeWidth={3} aria-hidden /> : <Plus className="h-4 w-4" aria-hidden />}
          {selected ? t('inPlan') : t('addToPlan')}
        </button>
      )}
    </article>
  );
};
