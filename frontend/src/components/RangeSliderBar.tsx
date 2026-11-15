import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { MarkerAnalysisResult } from '../types';
import { Badge, Card, STATUS_META, cx } from './ui';

interface RangeSliderBarProps {
  analysis: MarkerAnalysisResult;
}

export const RangeSliderBar: React.FC<RangeSliderBarProps> = ({ analysis }) => {
  const { display_name, value, unit, status, range_low, range_high, percentage_of_optimal, clinical_warning } =
    analysis;

  // Visual bounds: 40% below the lower limit to 35% above the upper limit
  const visualMin = Math.max(0, range_low * 0.4);
  const visualMax = range_high * 1.35;
  const span = visualMax - visualMin || 1;
  const clampedVal = Math.min(Math.max(value, visualMin), visualMax);

  const lowPercent = Math.max(0, Math.min(100, ((range_low - visualMin) / span) * 100));
  const highPercent = Math.max(0, Math.min(100, ((range_high - visualMin) / span) * 100));
  const pointerPercent = Math.max(2, Math.min(98, ((clampedVal - visualMin) / span) * 100));

  const meta = STATUS_META[status];

  const delta = (() => {
    switch (status) {
      case 'low':
        return `${Math.abs(range_low - value).toFixed(1)} ${unit} below the healthy range`;
      case 'borderline':
        return `Close to the lower limit of ${range_low} ${unit}`;
      case 'normal':
        return 'Within the healthy range';
      case 'high':
        return `${(value - range_high).toFixed(1)} ${unit} above the healthy range`;
    }
  })();

  return (
    <Card className="p-5 transition-shadow hover:shadow-card-lg">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h4 className="truncate text-[15px] font-semibold text-slate-900">{display_name}</h4>
          <p className={cx('mt-0.5 text-sm', status === 'normal' ? 'text-slate-500' : meta.text)}>{delta}</p>
        </div>
        <Badge tone={meta.tone}>
          <span className={cx('h-1.5 w-1.5 rounded-full', meta.dot)} aria-hidden />
          {meta.label}
        </Badge>
      </div>

      <div className="mt-4 flex items-baseline gap-1.5">
        <span className="text-3xl font-bold tracking-tight text-slate-900 tabular-nums">{value}</span>
        <span className="text-sm font-medium text-slate-500">{unit}</span>
      </div>

      {/* Range track */}
      <div
        className="mt-5"
        role="img"
        aria-label={`${display_name} is ${value} ${unit}. Healthy range ${range_low} to ${range_high} ${unit}. Status: ${meta.label}.`}
      >
        <div className="relative h-2 rounded-full bg-slate-100">
          <div
            style={{ width: `${lowPercent}%` }}
            className="absolute inset-y-0 left-0 rounded-l-full bg-red-100"
          />
          <div
            style={{ left: `${lowPercent}%`, width: `${Math.max(0, highPercent - lowPercent)}%` }}
            className="absolute inset-y-0 bg-brand-200"
          />
          <div
            style={{ left: `${highPercent}%`, width: `${Math.max(0, 100 - highPercent)}%` }}
            className="absolute inset-y-0 right-0 rounded-r-full bg-indigo-100"
          />
          <span
            style={{ left: `${pointerPercent}%` }}
            className={cx(
              'absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white shadow-md ring-1 ring-slate-300 transition-all duration-500',
              meta.bar
            )}
          />
        </div>

        <div className="relative mt-2 h-4 text-xs tabular-nums text-slate-500">
          <span style={{ left: `${lowPercent}%` }} className="absolute -translate-x-1/2">
            {range_low}
          </span>
          <span style={{ left: `${highPercent}%` }} className="absolute -translate-x-1/2">
            {range_high}
          </span>
        </div>
      </div>

      <p className="mt-3 flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-500">
        <span>
          Healthy range{' '}
          <span className="font-medium text-slate-700 tabular-nums">
            {range_low}–{range_high} {unit}
          </span>
        </span>
        <span>
          <span className="font-semibold text-slate-700 tabular-nums">{percentage_of_optimal}%</span> of optimal
        </span>
      </p>

      {clinical_warning && (
        <div className="mt-4 flex items-start gap-2.5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" aria-hidden />
          <span className="leading-relaxed">{clinical_warning}</span>
        </div>
      )}
    </Card>
  );
};
