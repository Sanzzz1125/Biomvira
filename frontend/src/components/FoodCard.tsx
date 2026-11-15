import React from 'react';
import { Link2, UtensilsCrossed } from 'lucide-react';
import { FoodRecommendation } from '../types';
import { Badge } from './ui';

interface FoodCardProps {
  food: FoodRecommendation;
  targetNutrientName: string;
}

export const FoodCard: React.FC<FoodCardProps> = ({ food, targetNutrientName }) => {
  return (
    <article className="flex h-full flex-col rounded-xl border border-slate-200 bg-white p-4 shadow-card transition-all hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-card-lg">
      <div className="flex items-start justify-between gap-2">
        <Badge tone="neutral">{food.category}</Badge>
      </div>

      <div className="mt-3">
        <h4 className="text-[15px] font-semibold leading-snug text-slate-900">{food.name}</h4>
        {food.hindi_name && <p className="mt-0.5 text-sm text-slate-500">{food.hindi_name}</p>}
      </div>

      <div className="mt-3 rounded-lg bg-brand-50 px-3 py-2 ring-1 ring-inset ring-brand-100">
        <p className="text-sm font-semibold text-brand-800 tabular-nums">{food.key_nutrient_yield}</p>
        <p className="text-xs text-brand-700/80">
          {targetNutrientName} per {food.serving_size}
        </p>
      </div>

      {food.preparation_tip && (
        <p className="mt-3 flex items-start gap-2 text-sm leading-relaxed text-slate-600">
          <UtensilsCrossed className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" aria-hidden />
          <span>{food.preparation_tip}</span>
        </p>
      )}

      {food.synergies && food.synergies.length > 0 && (
        <div className="mt-auto pt-4">
          <ul className="space-y-1.5 border-t border-slate-100 pt-3">
            {food.synergies.map((syn, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs leading-relaxed text-brand-700">
                <Link2 className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
                <span>{syn}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
};
