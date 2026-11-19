/**
 * Shows the site in Hindi or Telugu.
 *
 * Every UI text, placeholder and label is written in English in the components. When another language is chosen,
 * this layer swaps each English text for its translation as it is displayed, using the English text itself as the
 * key (lib/i18n/ui_*.txt, and data_*.txt for test, food and advice names shared with the backend). Report results
 * come from the server already translated. Anything the person typed, and anything marked translate="no", is left
 * alone. Choosing English restores the original text.
 */
import { Language, onLanguageChange, storedLanguage } from './i18n';

type Table = Map<string, string>;
const tables: Partial<Record<Language, Table>> = {};
let active: Language = 'en';
let table: Table | null = null;

const SOURCES: Record<'hi' | 'te', () => Promise<string[]>> = {
  hi: () => Promise.all([import('./i18n/ui_en.txt?raw'), import('./i18n/ui_hi.txt?raw'), import('./i18n/data_en.txt?raw'),
    import('./i18n/data_hi.txt?raw')]).then((m) => m.map((x) => x.default)),
  te: () => Promise.all([import('./i18n/ui_en.txt?raw'), import('./i18n/ui_te.txt?raw'), import('./i18n/data_en.txt?raw'),
    import('./i18n/data_te.txt?raw')]).then((m) => m.map((x) => x.default)),
};

// Short fragments React renders as separate text nodes around numbers ("3" + " results read from your report").
const FRAGMENTS: Record<'hi' | 'te', Record<string, string>> = {
  hi: { result: 'परिणाम', results: 'परिणाम', 'read from your report': 'आपकी रिपोर्ट से पढ़े गए', 'min read': 'मिनट में पढ़ें',
    'results ·': 'परिणाम ·', 'need attention': 'पर ध्यान ज़रूरी', 'Ref #': 'संदर्भ #', of: 'में से' },
  te: { result: 'ఫలితం', results: 'ఫలితాలు', 'read from your report': 'మీ రిపోర్టు నుండి చదవబడ్డాయి', 'min read': 'నిమిషాల చదువు',
    'results ·': 'ఫలితాలు ·', 'need attention': 'కి శ్రద్ధ అవసరం', 'Ref #': 'సూచిక #', of: 'లో' },
};
const PATTERNS: Record<'hi' | 'te', [RegExp, (m: RegExpMatchArray) => string][]> = {
  hi: [[/^(\d+) results? need attention$/, (m) => `${m[1]} परिणामों पर ध्यान ज़रूरी`],
    [/^(\d+) min read$/, (m) => `${m[1]} मिनट में पढ़ें`]],
  te: [[/^(\d+) results? need attention$/, (m) => `${m[1]} ఫలితాలకు శ్రద్ధ అవసరం`],
    [/^(\d+) min read$/, (m) => `${m[1]} నిమిషాల చదువు`]],
};

const norm = (s: string) => s.replace(/\s+/g, ' ').trim();

async function loadTable(lang: 'hi' | 'te'): Promise<Table> {
  const cached = tables[lang];
  if (cached) return cached;
  const [uiEn, uiTr, dataEn, dataTr] = await SOURCES[lang]();
  const map: Table = new Map();
  const add = (en: string, tr: string) => {
    const e = en.split('\n');
    const t = tr.split('\n');
    e.forEach((line, i) => {
      if (line && t[i]) map.set(norm(line), t[i]);
    });
  };
  add(dataEn, dataTr);
  add(uiEn, uiTr);
  for (const [k, v] of Object.entries(FRAGMENTS[lang])) map.set(k, v);
  tables[lang] = map;
  return map;
}

export function translateText(text: string): string {
  if (active === 'en' || !table) return text;
  const m = text.match(/^(\s*)([\s\S]*?)(\s*)$/);
  if (!m || !m[2]) return text;
  const key = norm(m[2]);
  const hit = table.get(key);
  if (hit) return m[1] + hit + m[3];
  for (const [re, fn] of PATTERNS[active as 'hi' | 'te']) {
    const p = key.match(re);
    if (p) return m[1] + fn(p) + m[3];
  }
  return text;
}

const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'TEXTAREA', 'CODE', 'PRE', 'NOSCRIPT']);
const ATTRS = ['placeholder', 'aria-label', 'title', 'alt'];
const textSource = new WeakMap<Text, string>();
const textShown = new WeakMap<Text, string>();
const attrSource = new WeakMap<Element, Record<string, string>>();
const attrShown = new WeakMap<Element, Record<string, string>>();

function skipped(el: Element | null): boolean {
  for (let e = el; e; e = e.parentElement) {
    if (SKIP_TAGS.has(e.tagName) || e.getAttribute('translate') === 'no' || (e as HTMLElement).isContentEditable) return true;
  }
  return false;
}

function doText(node: Text) {
  if (skipped(node.parentElement)) return;
  const current = node.nodeValue ?? '';
  if (textShown.get(node) !== current) textSource.set(node, current); // React wrote new English text
  const source = textSource.get(node) ?? current;
  const next = translateText(source);
  textShown.set(node, next);
  if (next !== current) node.nodeValue = next;
}

function doAttrs(el: Element) {
  if (skipped(el)) return;
  for (const name of ATTRS) {
    const current = el.getAttribute(name);
    if (current == null) continue;
    const shown = attrShown.get(el) ?? {};
    const source = attrSource.get(el) ?? {};
    if (shown[name] !== current) source[name] = current;
    const next = translateText(source[name] ?? current);
    shown[name] = next;
    attrSource.set(el, source);
    attrShown.set(el, shown);
    if (next !== current) el.setAttribute(name, next);
  }
}

function walk(root: Node) {
  if (root.nodeType === Node.TEXT_NODE) return doText(root as Text);
  if (root.nodeType !== Node.ELEMENT_NODE) return;
  doAttrs(root as Element);
  const it = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
  for (let n = it.nextNode(); n; n = it.nextNode()) {
    if (n.nodeType === Node.TEXT_NODE) doText(n as Text);
    else doAttrs(n as Element);
  }
}

async function apply(lang: Language) {
  table = lang === 'en' ? null : await loadTable(lang);
  active = lang;
  document.documentElement.lang = lang;
  walk(document.body);
}

export function startTranslation() {
  const observer = new MutationObserver((records) => {
    for (const r of records) {
      if (r.type === 'characterData') doText(r.target as Text);
      else if (r.type === 'attributes') doAttrs(r.target as Element);
      else r.addedNodes.forEach((n) => walk(n));
    }
  });
  observer.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRS });
  onLanguageChange((lang) => void apply(lang));
  const initial = storedLanguage();
  if (initial && initial !== 'en') void apply(initial);
}
