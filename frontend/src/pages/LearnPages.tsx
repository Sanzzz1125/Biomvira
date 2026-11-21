import { ArticleArt } from '../components/ArticleArt';
import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, BookOpen, Scale } from 'lucide-react';
import { Card, PageHeader } from '../components/ui';

/* ------------------------------------------------------------------ Science */

const SOURCES = [
  ['Indian Food Composition Tables 2017', 'ICMR-National Institute of Nutrition. Nutrients of 542 Indian foods, the base of our nutrient values.'],
  ['Nutrient Requirements for Indians 2020', 'ICMR-NIN. Daily needs (RDA) for iron, calcium, B12, vitamin D and more, by age and sex.'],
  ['USDA FoodData Central', 'US Department of Agriculture. Vitamin B12 and vitamin D, which the Indian tables do not list, and a few foods they do not include.'],
  ['Nutrient retention factors', 'IFCT 2017 and USDA Release 6. How much of each vitamin survives boiling, frying or steaming.'],
  ['UK Composition of Foods (CoFID 2021)', 'Measured values of South Asian home dishes, used to check our recipes are realistic.'],
  ['Nutritive Value of Indian Foods', 'ICMR-NIN. Used only for foxtail millet and makhana, which the 2017 tables do not include.'],
  ['National NCD Monitoring Survey', 'ICMR, published 2023. Indians eat about 8 g of salt a day; our typical days are checked against it.'],
];

export const SciencePage: React.FC = () => (
  <div className="mx-auto max-w-4xl space-y-8">
    <PageHeader eyebrow="Science" title="How NutriLens works"
      description="Every number comes from a published source, and every step can be checked." />
    <Card className="space-y-4 p-6 text-[15px] leading-relaxed text-slate-700 sm:p-8">
      <h2 className="text-lg font-semibold text-slate-900">Reading your report</h2>
      <p>Values are read from the PDF or photo and converted to standard units, and you can check and correct them before the analysis. Each result is compared with the range printed on your report or a clinical reference range.</p>
      <h2 className="text-lg font-semibold text-slate-900">Dishes measured, not guessed</h2>
      <p>Each of our 276 dishes is a standard home recipe written in grams of raw ingredients. Its nutrients are added up from the Indian Food Composition Tables, with cooking losses applied to the vitamins heat destroys. Diet type and allergens are worked out from the ingredients, never typed by hand. Dishes are checked against lab-measured values of similar South Asian dishes where these exist, and the salt in a typical day is checked against what Indian adults actually eat.</p>
      <h2 className="text-lg font-semibold text-slate-900">Building your plan</h2>
      <p>Your energy need comes from your age, sex, weight and activity (the ICMR-NIN 2020 method), adjusted for your BMI, and protein from 0.83 g per kg of body weight. A mathematical optimiser then chooses dishes and servings so that each day meets your calories within 5% and your protein, and aims for the nutrients your report shows as low, while keeping salt and fat within limits, sweets to a few times a week, and following how Indian meals are actually eaten.</p>
      <h2 className="text-lg font-semibold text-slate-900">What we do not do</h2>
      <p>NutriLens does not diagnose or treat. It does not replace your doctor or dietitian, and plans are for adults. Vitamin D in fish varies a lot, so plans count it at half.</p>
    </Card>
    <section>
      <h2 className="text-lg font-semibold text-slate-900">Sources</h2>
      <ul className="mt-3 grid gap-3 sm:grid-cols-2">
        {SOURCES.map(([name, text]) => (
          <li key={name}><Card className="h-full p-4"><p className="text-sm font-semibold text-slate-900">{name}</p><p className="mt-1 text-sm text-slate-600">{text}</p></Card></li>
        ))}
      </ul>
    </section>
  </div>
);

/* ------------------------------------------------------------------ FAQ */

export const FAQS = [
  ['Is my report kept private?', 'Names, phone numbers and IDs are removed before a report is read. As a guest nothing is saved; with an account your reports are kept in your History, which only you can see, and you can delete them at any time.'],
  ['Which tests can NutriLens read?', 'Over 60 common blood tests, including haemoglobin, ferritin, vitamin D, vitamin B12, folate, HbA1c, glucose, cholesterol, thyroid, kidney and liver tests.'],
  ['How are my calories worked out?', 'From your age, sex, weight and activity, the way ICMR-NIN 2020 does it: the FAO/WHO/UNU equations, about 10% lower for Indian adults, times your activity level. If your BMI is 25 or more, the plan aims about 15% lower (at most 500 kcal) for gentle weight loss; under 18.5, about 10% higher.'],
  ['Why three plan options?', 'Familiar keeps dishes from your region and the foods you picked, Most nutritious packs in the most nutrients, and Regional uses only dishes cooked in your state. Pick the one that suits you, then make a 7-day plan from it.'],
  ['Can I change a dish I do not like?', 'Yes. Press Swap next to any dish in your 7-day plan; the rest of the day stays the same and the numbers are rebalanced.'],
  ['I have an allergy that is not in the list.', 'Type it in the highlighted box on the profile page. Every dish that contains it is left out of your plans.'],
  ['Does it work for vegetarians and vegans?', 'Yes. Plans respect vegetarian, vegan, egg and non-vegetarian diets, and non-vegetarians can choose which meats they eat.'],
  ['Should I stop my medicines or supplements?', 'No. NutriLens gives food guidance only. Talk to your doctor before changing any treatment, especially if a result is very low or very high.'],
];

export const FaqPage: React.FC = () => (
  <div className="mx-auto max-w-3xl space-y-6">
    <PageHeader eyebrow="FAQ" title="Questions people ask" />
    <Card className="divide-y divide-slate-200">
      {FAQS.map(([q, a]) => (
        <details key={q} className="group p-5">
          <summary className="cursor-pointer list-none text-[15px] font-semibold text-slate-900 marker:hidden">{q}</summary>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">{a}</p>
        </details>
      ))}
    </Card>
  </div>
);

/* ------------------------------------------------------------------ Articles */

interface Article { slug: string; category: string; title: string; summary: string; body: string[]; source: string; minutes: number }

export const ARTICLES: Article[] = [
  {
    slug: 'balanced-indian-plate', minutes: 4, category: 'Diet', title: 'Building a balanced Indian plate',
    summary: 'Half vegetables, a quarter grains, a quarter dal or protein: the everyday thali, adjusted.',
    body: [
      'A good meal does not need special foods. ICMR-NIN suggests filling about half the plate with vegetables and fruit, and splitting the rest between cereals (rice, roti, millets) and pulses, eggs, fish or meat.',
      'In practice: one or two rotis or a cup of rice, a katori of dal or sambar, a katori of vegetable curry, and curd or buttermilk. Swap some rice for jowar, bajra, ragi or little millet a few times a week for more fibre and minerals.',
      'Keep cooking oil to about 4-5 teaspoons a day for the whole day, and salt under a teaspoon. Fried snacks and sweets are fine once or twice a week.',
    ],
    source: 'ICMR-NIN Dietary Guidelines for Indians, 2024.',
  },
  {
    slug: 'iron-vegetarian', minutes: 4, category: 'Nutrition', title: 'Getting more iron from vegetarian food',
    summary: 'Greens, dals and millets carry iron; vitamin C and good habits help you absorb it.',
    body: [
      'Iron-rich vegetarian foods include amaranth (thotakura), gongura, drumstick leaves, bajra, ragi, horse gram and most dals.',
      'Plant iron is absorbed less well than iron from meat, but vitamin C helps a lot: add lemon to dal, eat guava, orange or amla with meals, and use tomato in curries.',
      'Tea and coffee reduce iron absorption, so have them an hour away from meals rather than with them. Calcium supplements are best taken at a different time from iron-rich meals.',
    ],
    source: 'Indian Food Composition Tables 2017; ICMR-NIN Nutrient Requirements 2020.',
  },
  {
    slug: 'weight-loss-without-crash-diets', minutes: 4, category: 'Weight loss', title: 'Losing weight without crash dieting',
    summary: 'A small, steady gap between what you eat and what you use works better than skipping meals.',
    body: [
      'Eating about 300-500 kcal less than you use each day leads to a steady loss of around a quarter to half a kilogram a week, which is easier to keep off than fast loss.',
      'Keep protein up (dal, curd, eggs, paneer, fish, chicken) so you stay full and keep muscle. Fill up on vegetables and salads, and reduce portions of rice, rotis, oil and sweets rather than cutting whole meals.',
      'Walking 30 minutes most days and sleeping well help as much as the diet. If your BMI is 25 or more, NutriLens plans aim about 15% below your need, never more than 500 kcal.',
    ],
    source: 'ICMR-NIN Dietary Guidelines for Indians, 2024; WHO guidance on healthy weight.',
  },
  {
    slug: 'reading-your-blood-report', minutes: 4, category: 'Health', title: 'Reading your blood report: low, normal and high',
    summary: 'What the reference range means, and why one result outside it is not a diagnosis.',
    body: [
      'Each result has a reference range: the values seen in most healthy people. A result just outside it is common and often not serious; a result far outside it needs a doctor’s attention.',
      'Some results are linked to food: low haemoglobin or ferritin to iron, low B12 to milk, curd, eggs and meat, low vitamin D to sunlight and fortified milk. Others, like kidney or thyroid tests, need medical advice rather than diet changes.',
      'Ranges differ slightly between labs and by age and sex, so NutriLens uses the range printed on your report when there is one.',
    ],
    source: 'Clinical reference intervals as printed by accredited laboratories.',
  },
];

ARTICLES.unshift(
  {
    slug: 'tea-and-iron', minutes: 5, category: 'Nutrition', title: 'Why tea after a meal can lower the iron you absorb',
    summary: 'Tannins in tea and coffee bind plant iron in the gut. Timing your chai fixes most of it.',
    body: [
      'Tea and coffee contain tannins and other polyphenols. In the gut they bind the iron from plant foods such as dal, greens and millets, so less of it is absorbed. Studies show a cup of tea with a meal can cut iron absorption from that meal by more than half.',
      'You do not need to give up chai. Have it at least an hour before or after meals instead of with them, especially at breakfast and lunch when you eat iron-rich foods.',
      'At the same meal, add vitamin C: a squeeze of lemon on dal, a guava or orange, amla, or tomato in the curry. Vitamin C can offset much of what tea takes away.',
    ],
    source: 'ICMR-NIN Dietary Guidelines for Indians, 2024; studies on polyphenols and non-haem iron absorption.',
  },
  {
    slug: 'millets-blood-sugar', minutes: 6, category: 'Diet', title: 'Millets for steadier blood sugar: jowar, bajra and ragi compared',
    summary: 'Millets carry about four times the fibre of polished rice, and each has its own strength.',
    body: [
      'Per 100 g dry, the Indian Food Composition Tables list about 10 g of fibre in jowar, 11.5 g in bajra and 11 g in ragi, against under 3 g in polished white rice. Fibre slows how fast sugar enters the blood after a meal.',
      'Each millet has a strength: bajra has the most iron (about 6.4 mg per 100 g), ragi is exceptionally rich in calcium (about 364 mg per 100 g), and jowar is mild and easy to make into rotis.',
      'Millets still carry carbohydrate, so portions matter. Eat them as rotis or sankati with dal and vegetables, swap them for some of your rice a few times a week, and keep sugar and refined flour low.',
    ],
    source: 'Indian Food Composition Tables 2017, ICMR-NIN.',
  },
  {
    slug: 'lipid-profile', minutes: 7, category: 'Health', title: 'Reading your lipid profile: LDL, HDL and triglycerides explained',
    summary: 'Four numbers, what each one means, and which food changes help.',
    body: [
      'Total cholesterol is everything carried in the blood. LDL is the cholesterol that can build up in artery walls, so lower is better. HDL helps carry cholesterol away, so higher is better. Triglycerides are blood fats that rise with sugar, refined flour, fried food and alcohol.',
      'Food changes that help: more fibre from dals, whole grains, millets, vegetables and fruit; nuts and seeds such as almonds, flaxseed and sesame; and less ghee, butter, vanaspati, bakery items and deep-fried snacks.',
      'Very high values, for example LDL of 190 mg/dL or more or triglycerides of 500 mg/dL or more, need a doctor’s assessment, and cholesterol medicines should never be stopped without asking your doctor.',
    ],
    source: 'ICMR-NIN Dietary Guidelines for Indians, 2024; clinical lipid guidelines.',
  },
);

export const ArticlesPage: React.FC = () => (
  <div className="mx-auto max-w-5xl space-y-6">
    <PageHeader eyebrow="Articles" title="Eat well, the Indian way" description="Short, sourced reads on diet, nutrition, weight and health." />
    <div className="grid gap-4 sm:grid-cols-2">
      {ARTICLES.map((a) => (
        <Link key={a.slug} to={`/articles/${a.slug}`} className="group">
          <Card className="h-full overflow-hidden transition-colors group-hover:border-brand-300">
            <ArticleArt slug={a.slug} className="h-40" />
            <div className="p-6">
            <p className="eyebrow">{a.category}</p>
            <h2 className="mt-1 text-lg font-semibold text-slate-900">{a.title}</h2>
            <p className="mt-2 text-sm text-slate-600">{a.summary}</p>
            <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-brand-700">
              Read <ArrowRight className="h-4 w-4" aria-hidden />
            </span>
            </div>
          </Card>
        </Link>
      ))}
    </div>
  </div>
);

export const ArticlePage: React.FC = () => {
  const { slug } = useParams();
  const article = ARTICLES.find((a) => a.slug === slug);
  if (!article) {
    return <p className="text-center text-slate-600">Article not found. <Link to="/articles" className="font-semibold text-brand-700">See all articles</Link></p>;
  }
  return (
    <article className="mx-auto max-w-2xl space-y-5">
      <Link to="/articles" className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-slate-900">
        <ArrowLeft className="h-4 w-4" aria-hidden /> All articles
      </Link>
      <p className="eyebrow">{article.category}</p>
      <h1 className="text-3xl font-bold tracking-tight text-slate-900">{article.title}</h1>
      <p className="text-lg text-slate-600">{article.summary}</p>
      {article.body.map((p, i) => <p key={i} className="text-[15px] leading-relaxed text-slate-700">{p}</p>)}
      <p className="flex items-start gap-2 border-t border-slate-200 pt-4 text-sm text-slate-500">
        <BookOpen className="mt-0.5 h-4 w-4 shrink-0" aria-hidden /> Source: {article.source}
      </p>
      <p className="flex items-start gap-2 text-sm text-slate-500">
        <Scale className="mt-0.5 h-4 w-4 shrink-0" aria-hidden /> General information, not medical advice.
      </p>
    </article>
  );
};
