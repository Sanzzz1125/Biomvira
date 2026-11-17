import React from 'react';
import { Ban, Lightbulb } from 'lucide-react';

/**
 * Renders the assistant's small markdown subset as designed UI:
 * - a lone **bold** line is a heading;
 * - "- **Name**: value" bullets become rows (food with a nutrient pill, or a result with a status pill);
 * - "**Tips:**" and "**Limit or avoid:**" bullet groups become callout boxes;
 * - everything else is paragraphs and plain bullets with inline **bold**.
 * Text is always rendered as text nodes, never as HTML.
 */

const STATUS_TONE: Record<string, string> = {
  low: 'bg-rose-50 text-rose-700',
  high: 'bg-orange-50 text-orange-800',
  borderline: 'bg-amber-50 text-amber-800',
  normal: 'bg-brand-50 text-brand-700',
};

export const Inline: React.FC<{ text: string }> = ({ text }) => (
  <>
    {text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
      part.startsWith('**') && part.endsWith('**') && part.length > 4 ? (
        <strong key={i} className="font-semibold text-slate-900">
          {part.slice(2, -2)}
        </strong>
      ) : (
        <React.Fragment key={i}>{part}</React.Fragment>
      )
    )}
  </>
);

interface Row {
  name: string;
  sub?: string;
  pill?: string;
  tone?: string;
}

export function parseRow(line: string): Row | null {
  const match = /^\*\*(.+?)\*\*:\s*(.+)$/.exec(line);
  if (!match) return null;
  let name = match[1];
  const value = match[2].trim();
  const status = /^(.*?)\s*\(((?:very )?(?:low|high)|borderline|normal)\)\s*$/i.exec(value);
  if (status) {
    const word = status[2].toLowerCase();
    const tone = STATUS_TONE[word.replace('very ', '')];
    return { name, sub: status[1] || undefined, pill: word[0].toUpperCase() + word.slice(1), tone };
  }
  let sub: string | undefined;
  const paren = /^(.*?)\s*\(([^()]+)\)\s*$/.exec(name);
  if (paren && paren[1]) {
    name = paren[1];
    sub = paren[2];
  }
  const perServing = /^(.*?)\s+per 100 g$/.exec(value);
  const pill = perServing ? perServing[1] : value;
  if (pill.length > 34) return { name, sub: sub ? `${sub} · ${pill}` : pill };
  return { name, sub, pill, tone: STATUS_TONE.normal };
}

const RowList: React.FC<{ rows: Row[] }> = ({ rows }) => (
  <ul className="overflow-hidden rounded-xl border border-slate-100">
    {rows.map((row, i) => (
      <li
        key={i}
        className="flex items-center justify-between gap-3 border-b border-slate-100 px-3 py-2.5 last:border-b-0"
      >
        <span className="flex min-w-0 flex-col">
          <span className="text-[13.5px] font-semibold leading-snug text-slate-900">{row.name}</span>
          {row.sub && <span className="text-xs leading-snug text-slate-500">{row.sub}</span>}
        </span>
        {row.pill && (
          <span className={`shrink-0 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold ${row.tone}`}>
            {row.pill}
          </span>
        )}
      </li>
    ))}
  </ul>
);

const Bullets: React.FC<{ lines: string[] }> = ({ lines }) => (
  <ul className="space-y-1.5 pl-4">
    {lines.map((line, i) => (
      <li key={i} className="list-disc marker:text-brand-500">
        <Inline text={line.slice(2)} />
      </li>
    ))}
  </ul>
);

const Block: React.FC<{ lines: string[] }> = ({ lines }) => {
  const [first, ...rest] = lines;
  if (lines.length === 1 && /^\*\*[^*]+\*\*$/.test(first)) {
    return <h3 className="text-[15px] font-semibold leading-snug text-slate-900">{first.slice(2, -2)}</h3>;
  }
  const callout = /^\*\*(Tips?|Limit or avoid):\*\*$/.exec(first);
  if (callout && rest.length > 0 && rest.every((l) => l.startsWith('- '))) {
    const tip = callout[1].startsWith('Tip');
    return (
      <div
        className={
          tip
            ? 'flex gap-2.5 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5 text-[13px] text-amber-900'
            : 'flex gap-2.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-[13px] text-slate-700'
        }
      >
        {tip ? (
          <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" aria-hidden />
        ) : (
          <Ban className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" aria-hidden />
        )}
        <div className="min-w-0 space-y-1">
          <p className="font-semibold">{tip ? 'Tips' : 'Limit or avoid'}</p>
          <ul className="space-y-1 pl-4">
            {rest.map((line, i) => (
              <li key={i} className="list-disc">
                <Inline text={line.slice(2)} />
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  }
  const intro = lines.filter((l) => !l.startsWith('- '));
  const bullets = lines.filter((l) => l.startsWith('- '));
  const rows = bullets.map((l) => parseRow(l.slice(2)));
  const asRows = bullets.length > 0 && rows.every(Boolean);
  return (
    <div className="space-y-2">
      {intro.map((line, i) => (
        <p key={i}>
          <Inline text={line} />
        </p>
      ))}
      {bullets.length > 0 && (asRows ? <RowList rows={rows as Row[]} /> : <Bullets lines={bullets} />)}
    </div>
  );
};

export const RichAnswer: React.FC<{ text: string }> = ({ text }) => {
  const blocks = text
    .split(/\n{2,}/)
    .map((block) => block.split('\n').filter((line) => line.trim()))
    .filter((lines) => lines.length > 0);
  return (
    <div className="space-y-3">
      {blocks.map((lines, i) => (
        <Block key={i} lines={lines} />
      ))}
    </div>
  );
};

/** Plain text for copying: no markdown symbols. */
export function plainText(text: string): string {
  return text.replace(/\*\*/g, '').replace(/^- /gm, '• ');
}
