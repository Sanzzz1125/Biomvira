import React from 'react';
import { useLanguage } from '../lib/i18n';
import { cx } from './ui';

type Name = { en: string; hi: string; te: string };
/** Real dishes from the plan catalogue (backend/app/plan/dishes), with their checked Hindi and Telugu names. */
const KITCHENS: { id: string; name: Name; meals: Name[][] }[] = [
 {
  "id": "telangana",
  "name": {
   "en": "Telangana",
   "hi": "तेलंगाना",
   "te": "తెలంగాణ"
  },
  "meals": [
   [
    {
     "en": "Sarva pindi",
     "hi": "सर्व पिंडी",
     "te": "సర్వపిండి"
    }
   ],
   [
    {
     "en": "Jowar roti (jonna rotte)",
     "hi": "ज्वार की रोटी",
     "te": "జొన్న రొట్టె"
    },
    {
     "en": "Spinach dal (palakura pappu)",
     "hi": "पालक दाल",
     "te": "పాలకూర పప్పు"
    },
    {
     "en": "Okra fry (bendakaya vepudu)",
     "hi": "भिंडी फ्राई",
     "te": "బెండకాయ వేపుడు"
    }
   ],
   [
    {
     "en": "Roasted corn (kalchina mokkajonna)",
     "hi": "भुना भुट्टा",
     "te": "కాల్చిన మొక్కజొన్న"
    }
   ],
   [
    {
     "en": "Ragi sankati (ragi mudda)",
     "hi": "रागी मुद्दा (संकटी)",
     "te": "రాగి సంకటి"
    },
    {
     "en": "Tomato dal (tomato pappu)",
     "hi": "टमाटर दाल",
     "te": "టమాటా పప్పు"
    }
   ]
  ]
 },
 {
  "id": "andhra",
  "name": {
   "en": "Andhra Pradesh",
   "hi": "आंध्र प्रदेश",
   "te": "ఆంధ్రప్రదేశ్"
  },
  "meals": [
   [
    {
     "en": "Pesarattu (green moong dosa)",
     "hi": "पेसरट्टू (हरी मूंग का डोसा)",
     "te": "పెసరట్టు"
    }
   ],
   [
    {
     "en": "Tamarind rice (pulihora)",
     "hi": "इमली चावल (पुलिहोरा)",
     "te": "చింతపండు పులిహోర"
    },
    {
     "en": "Stuffed brinjal curry (gutti vankaya)",
     "hi": "भरवां बैंगन (गुत्ति वंकाया)",
     "te": "గుత్తి వంకాయ కూర"
    }
   ],
   [
    {
     "en": "Uggani (puffed rice upma)",
     "hi": "उग्गानी (मुरमुरे का उपमा)",
     "te": "ఉగ్గాని"
    }
   ],
   [
    {
     "en": "Little millet rice (samala annam)",
     "hi": "सामा (कुटकी) चावल",
     "te": "సామల అన్నం"
    },
    {
     "en": "Moong dal (pesara pappu)",
     "hi": "मूंग दाल",
     "te": "పెసరపప్పు"
    }
   ]
  ]
 },
 {
  "id": "tamil_nadu",
  "name": {
   "en": "Tamil Nadu",
   "hi": "तमिलनाडु",
   "te": "తమిళనాడు"
  },
  "meals": [
   [
    {
     "en": "Ven pongal",
     "hi": "वेन पोंगल",
     "te": "వెన్ పొంగల్ (కట్టె పొంగలి)"
    }
   ],
   [
    {
     "en": "Coconut rice (thengai sadam)",
     "hi": "नारियल चावल",
     "te": "కొబ్బరి అన్నం"
    },
    {
     "en": "Plain dal with ghee (mudda pappu)",
     "hi": "घी के साथ सादी दाल",
     "te": "ముద్దపప్పు"
    }
   ],
   [
    {
     "en": "Kuzhi paniyaram",
     "hi": "पनियारम",
     "te": "పొంగనాలు"
    }
   ],
   [
    {
     "en": "Adai (mixed dal dosa)",
     "hi": "अडै (मिश्रित दाल डोसा)",
     "te": "అడై"
    }
   ]
  ]
 },
 {
  "id": "kerala",
  "name": {
   "en": "Kerala",
   "hi": "केरल",
   "te": "కేరళ"
  },
  "meals": [
   [
    {
     "en": "Puttu",
     "hi": "पुट्टु",
     "te": "పుట్టు"
    },
    {
     "en": "Black chickpea curry (kadala curry)",
     "hi": "काले चने की करी (कडला करी)",
     "te": "కడల కూర (నల్ల శనగల కూర)"
    }
   ],
   [
    {
     "en": "Kerala matta rice",
     "hi": "केरल मट्टा चावल",
     "te": "కేరళ మట్ట బియ్యం అన్నం"
    },
    {
     "en": "Kerala dal (parippu curry)",
     "hi": "केरल दाल (परिप्पु)",
     "te": "కేరళ పప్పు (పరిప్పు)"
    }
   ],
   [
    {
     "en": "Rice kanji with green gram (kanji payar)",
     "hi": "कांजी और हरी मूंग",
     "te": "గంజి, పెసలు"
    }
   ],
   [
    {
     "en": "Appam",
     "hi": "अप्पम",
     "te": "అప్పం"
    },
    {
     "en": "Vegetable stew (ishtu)",
     "hi": "वेज स्ट्यू (इष्टु)",
     "te": "వెజ్ స్టూ (ఇష్టు)"
    }
   ]
  ]
 },
 {
  "id": "punjab",
  "name": {
   "en": "Punjab",
   "hi": "पंजाब",
   "te": "పంజాబ్"
  },
  "meals": [
   [
    {
     "en": "Aloo paratha",
     "hi": "आलू पराठा",
     "te": "ఆలూ పరాటా"
    }
   ],
   [
    {
     "en": "Rajma",
     "hi": "राजमा",
     "te": "రాజ్మా"
    },
    {
     "en": "Jeera rice",
     "hi": "जीरा चावल",
     "te": "జీరా రైస్"
    }
   ],
   [
    {
     "en": "Sweet lassi",
     "hi": "मीठी लस्सी",
     "te": "తీపి లస్సీ"
    }
   ],
   [
    {
     "en": "Makki ki roti",
     "hi": "मक्की की रोटी",
     "te": "మొక్కజొన్న రొట్టె"
    },
    {
     "en": "Sarson ka saag",
     "hi": "सरसों का साग",
     "te": "ఆవాకు కూర (సర్సోం కా సాగ్)"
    }
   ]
  ]
 },
 {
  "id": "west_bengal",
  "name": {
   "en": "West Bengal",
   "hi": "पश्चिम बंगाल",
   "te": "పశ్చిమ బెంగాల్"
  },
  "meals": [
   [
    {
     "en": "Chirer pulao (flattened rice pulao)",
     "hi": "चिड़े का पुलाव",
     "te": "అటుకుల పులావ్"
    }
   ],
   [
    {
     "en": "Cholar dal",
     "hi": "छोलार दाल",
     "te": "ఛోలార్ దాల్ (శనగపప్పు)"
    },
    {
     "en": "Shukto (mixed vegetables)",
     "hi": "शुक्तो",
     "te": "శుక్తో"
    }
   ],
   [
    {
     "en": "Chana chaat",
     "hi": "चना चाट",
     "te": "శనగల చాట్"
    }
   ],
   [
    {
     "en": "Shorshe ilish (hilsa in mustard)",
     "hi": "सरसों हिल्सा (शोर्षे इलिश)",
     "te": "ఆవాలతో ఇలిష్ చేప"
    }
   ]
  ]
 },
 {
  "id": "maharashtra",
  "name": {
   "en": "Maharashtra",
   "hi": "महाराष्ट्र",
   "te": "మహారాష్ట్ర"
  },
  "meals": [
   [
    {
     "en": "Thalipeeth",
     "hi": "थालीपीठ",
     "te": "థాలీపీఠ్"
    }
   ],
   [
    {
     "en": "Varan (plain Maharashtrian dal)",
     "hi": "वरण (सादी दाल)",
     "te": "వరణ్ (సాదా పప్పు)"
    },
    {
     "en": "Matki usal (moth bean curry)",
     "hi": "मटकी उसळ",
     "te": "మట్కీ ఉసళ్ (మట్కీ కూర)"
    }
   ],
   [
    {
     "en": "Sabudana khichdi",
     "hi": "साबूदाना खिचड़ी",
     "te": "సగ్గుబియ్యం కిచిడీ"
    }
   ],
   [
    {
     "en": "Pithla (besan curry)",
     "hi": "पिठला",
     "te": "పిఠ్లా (శనగపిండి కూర)"
    },
    {
     "en": "Jowar roti (jonna rotte)",
     "hi": "ज्वार की रोटी",
     "te": "జొన్న రొట్టె"
    }
   ]
  ]
 }
];
const SLOTS = ['Breakfast', 'Lunch', 'Evening snack', 'Dinner'];

/** "Meals from your own kitchen": an example day of home dishes for a few states. */
export const RegionalKitchens: React.FC = () => {
  const language = useLanguage();
  const [active, setActive] = React.useState(KITCHENS[0].id);
  const kitchen = KITCHENS.find((k) => k.id === active) ?? KITCHENS[0];
  return (
    <section id="kitchens" className="flex scroll-mt-24 flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="max-w-2xl">
          <p className="eyebrow">Meals from your own kitchen</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Home dishes from your state, not a foreign diet chart</h2>
          <p className="mt-2 text-[15px] leading-relaxed text-slate-600">
            Plans are built from 276 home-style dishes cooked across India. Here is what one day can look like.
          </p>
        </div>
      </div>
      <div role="tablist" aria-label="States" className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:flex-wrap sm:px-0" translate="no">
        {KITCHENS.map((k) => (
          <button key={k.id} type="button" role="tab" aria-selected={k.id === active} onClick={() => setActive(k.id)}
            className={cx('h-10 shrink-0 rounded-full px-4 text-sm font-semibold transition-colors',
              k.id === active ? 'bg-brand-600 text-white' : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50')}>
            {k.name[language]}
          </button>
        ))}
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {kitchen.meals.map((dishes, i) => (
          <div key={SLOTS[i]} className="flex flex-col gap-2 rounded-2xl border border-slate-200 bg-white p-5">
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-700">{SLOTS[i]}</span>
            <ul className="space-y-1.5" translate="no">
              {dishes.map((d) => (
                <li key={d.en} className="text-[15px] font-medium leading-snug text-slate-900">{d[language]}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <p className="text-sm text-slate-500">
        An example day. Your own plan is built for your report, your calorie and nutrient targets, your diet and your allergies.
      </p>
    </section>
  );
};
