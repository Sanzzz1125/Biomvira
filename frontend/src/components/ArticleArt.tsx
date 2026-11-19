import React from 'react';
import { Coffee, HeartPulse, Leaf, Scale, Salad, TestTube, Wheat } from 'lucide-react';
import { cx } from './ui';

/** Illustrations for article cards, drawn in the site's own style (no outside images: nothing to license or break). */
const ART: Record<string, { icon: React.ElementType; from: string; to: string; ink: string; items: React.ElementType[] }> = {
  'balanced-indian-plate': { icon: Salad, from: '#fdf3e3', to: '#fde7c2', ink: '#b45309', items: [Wheat, Leaf] },
  'iron-vegetarian': { icon: Leaf, from: '#e7f5ef', to: '#c9ecdc', ink: '#136352', items: [Salad, Wheat] },
  'weight-loss-without-crash-diets': { icon: Scale, from: '#f3eefb', to: '#e4d9f7', ink: '#6d28d9', items: [Salad, Leaf] },
  'reading-your-blood-report': { icon: TestTube, from: '#eaf0fb', to: '#d5e2f8', ink: '#1e3a8a', items: [HeartPulse, Leaf] },
  'tea-and-iron': { icon: Coffee, from: '#fbefe7', to: '#f5dccb', ink: '#9a3412', items: [Leaf, Leaf] },
  'millets-blood-sugar': { icon: Wheat, from: '#fdf6dd', to: '#f8e8a6', ink: '#a16207', items: [Leaf, Salad] },
  'lipid-profile': { icon: HeartPulse, from: '#fdecef', to: '#f9d3da', ink: '#be123c', items: [Leaf, TestTube] },
};

/** A real photo for each article (public/articles, from Unsplash; see CREDITS.txt), with the drawn version as fallback. */
export const ArticleArt: React.FC<{ slug: string; className?: string }> = ({ slug, className }) => {
  const [failed, setFailed] = React.useState(false);
  if (!failed) {
    return (
      <span className={cx('relative block overflow-hidden bg-slate-100', className)}>
        <img src={`/articles/${slug}.jpg`} alt="" loading="lazy" onError={() => setFailed(true)}
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]" />
      </span>
    );
  }
  const art = ART[slug] ?? ART['balanced-indian-plate'];
  const Icon = art.icon;
  return (
    <span className={cx('relative flex items-center justify-center overflow-hidden', className)} aria-hidden
      style={{ background: `linear-gradient(135deg, ${art.from}, ${art.to})` }}>
      <span className="absolute -left-6 -top-8 h-28 w-28 rounded-full opacity-40" style={{ background: art.to }} />
      <span className="absolute -bottom-10 -right-4 h-36 w-36 rounded-full opacity-50" style={{ background: art.from }} />
      {art.items.map((Item, i) => (
        <Item key={i} className={cx('absolute h-7 w-7 opacity-30', i ? 'bottom-4 left-6 -rotate-12' : 'right-6 top-4 rotate-12')}
          style={{ color: art.ink }} />
      ))}
      <span className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-white/80 shadow-sm">
        <Icon className="h-8 w-8" style={{ color: art.ink }} />
      </span>
    </span>
  );
};
