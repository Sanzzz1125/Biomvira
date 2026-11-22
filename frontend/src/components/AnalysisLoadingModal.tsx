import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { CheckCircle2, Loader2, Sparkles, ShieldCheck, Database, Sliders, Dna } from 'lucide-react';
import { UserProfile } from '../types';

interface AnalysisLoadingModalProps {
  isOpen: boolean;
  profile: UserProfile;
  markerCount: number;
  onAnimationComplete?: () => void;
}

const STAGES = [
  {
    title: 'Comparing your results with healthy ranges',
    detail: 'Units are standardised and each result is checked against your lab\'s range or clinical guidelines.',
    icon: Sliders,
    threshold: 20,
  },
  {
    title: 'Finding the right Indian foods',
    detail: 'Searching 180+ Indian foods from the ICMR-NIN food composition tables.',
    icon: Database,
    threshold: 45,
  },
  {
    title: 'Matching your diet and allergies',
    detail: 'Only foods that suit your diet, without anything you excluded.',
    icon: ShieldCheck,
    threshold: 70,
  },
  {
    title: 'Adding helpful habits',
    detail: 'Tips that help your body use these foods, such as pairing iron foods with vitamin C.',
    icon: Dna,
    threshold: 90,
  },
  {
    title: 'Preparing your plan',
    detail: 'Your food plan, notes on each result, and anything to discuss with a doctor.',
    icon: Sparkles,
    threshold: 100,
  },
];

export const AnalysisLoadingModal: React.FC<AnalysisLoadingModalProps> = ({
  isOpen,
  profile,
  markerCount,
  onAnimationComplete,
}) => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!isOpen) {
      setProgress(0);
      return;
    }

    const duration = 2400; // 2.4 seconds total deliberate pacing
    const intervalTime = 30;
    const increment = 100 / (duration / intervalTime);

    const timer = setInterval(() => {
      setProgress((prev) => {
        const next = prev + increment;
        if (next >= 100) {
          clearInterval(timer);
          if (onAnimationComplete) {
            setTimeout(onAnimationComplete, 200);
          }
          return 100;
        }
        return next;
      });
    }, intervalTime);

    return () => clearInterval(timer);
  }, [isOpen, onAnimationComplete]);

  // Keep the page behind the overlay from scrolling while the analysis runs.
  useEffect(() => {
    if (!isOpen) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previous;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const currentStageIndex = STAGES.findIndex((s) => progress <= s.threshold);
  const activeIndex = currentStageIndex === -1 ? STAGES.length - 1 : currentStageIndex;

  // Rendered on <body> so the overlay covers the whole window, navbar included (an animated
  // ancestor would otherwise limit a fixed overlay to the page content area).
  return createPortal(
    <div className="fixed inset-0 z-[70] flex items-center justify-center overflow-y-auto bg-slate-900/60 p-4 backdrop-blur-md animate-fade-in">
      <div className="w-full max-w-xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl animate-fade-up">
        {/* Header */}
        <div className="relative border-b border-slate-100 bg-gradient-to-r from-brand-50/70 via-white to-brand-50/30 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white shadow-sm ring-4 ring-brand-100">
                <Sparkles className="h-5 w-5 animate-pulse" />
              </span>
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  Preparing your nutrition plan
                </h3>
                <p className="text-xs text-slate-500">
                  {markerCount} results for a{' '}
                  <span className="font-semibold text-brand-700 capitalize">
                    {profile.diet_type.replace('_', ' ')}
                  </span>{' '}
                  diet
                </p>
              </div>
            </div>
            <div className="text-right">
              <span className="font-mono text-2xl font-bold tracking-tight text-brand-700">
                {Math.round(progress)}%
              </span>
              <p className="text-[11px] font-medium text-slate-400">Processing</p>
            </div>
          </div>

          {/* Progress bar */}
          <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-100 ring-1 ring-inset ring-slate-200/60">
            <div
              className="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-600 transition-all duration-150 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Steps List */}
        <div className="space-y-3.5 p-6">
          {STAGES.map((stage, idx) => {
            const isCompleted = progress > stage.threshold || progress >= 100;
            const isCurrent = idx === activeIndex && progress < 100;
            const isPending = idx > activeIndex;
            const Icon = stage.icon;

            return (
              <div
                key={stage.title}
                className={`flex items-start gap-3 rounded-xl p-3 transition-all duration-300 ${
                  isCurrent
                    ? 'border border-brand-200 bg-brand-50/50 shadow-sm'
                    : isCompleted
                    ? 'bg-slate-50/60'
                    : 'opacity-40'
                }`}
              >
                <div className="mt-0.5 shrink-0">
                  {isCompleted ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                  ) : isCurrent ? (
                    <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
                  ) : (
                    <Icon className="h-5 w-5 text-slate-400" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p
                    className={`text-sm font-semibold leading-tight ${
                      isCurrent
                        ? 'text-brand-900'
                        : isCompleted
                        ? 'text-slate-800'
                        : 'text-slate-500'
                    }`}
                  >
                    {stage.title}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500 leading-relaxed">
                    {stage.detail}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer info banner */}
        <div className="border-t border-slate-100 bg-slate-50 px-6 py-3 text-center">
          <p className="text-xs text-slate-500">
            Food data: ICMR-NIN Indian Food Composition Tables. Biomvira does not replace medical advice.
          </p>
        </div>
      </div>
    </div>,
    document.body
  );
};
