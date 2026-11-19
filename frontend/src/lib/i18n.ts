import { useEffect, useState } from 'react';

export type Language = 'en' | 'hi' | 'te';
export const LANGUAGES: { id: Language; native: string; label: string }[] = [
  { id: 'en', native: 'English', label: 'English' },
  { id: 'hi', native: 'हिन्दी', label: 'Hindi' },
  { id: 'te', native: 'తెలుగు', label: 'Telugu' },
];
const KEY = 'nl_language';
const listeners = new Set<(l: Language) => void>();

export const storedLanguage = (): Language | null => {
  try {
    const value = localStorage.getItem(KEY);
    return value === 'en' || value === 'hi' || value === 'te' ? value : null;
  } catch {
    return null;
  }
};

let current: Language = storedLanguage() ?? 'en';

export const setLanguage = (language: Language) => {
  current = language;
  try {
    localStorage.setItem(KEY, language);
  } catch {
    /* private browsing: keep it for this visit */
  }
  document.documentElement.lang = language;
  listeners.forEach((l) => l(language));
};

export const onLanguageChange = (fn: (l: Language) => void) => {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
};

export const currentLanguage = () => current;

export const useLanguage = (): Language => {
  const [language, set] = useState(current);
  useEffect(() => {
    listeners.add(set);
    return () => {
      listeners.delete(set);
    };
  }, []);
  return language;
};

const STRINGS = {
  // profile
  bodyHeading: { en: 'Body, activity and region', hi: 'शरीर, गतिविधि और क्षेत्र', te: 'శరీరం, చురుకుదనం, ప్రాంతం' },
  bodyHint: {
    en: 'Used to work out how much energy and protein you need for your diet plans.',
    hi: 'इससे हम आपके आहार योजना के लिए ज़रूरी ऊर्जा और प्रोटीन निकालते हैं।',
    te: 'మీ ఆహార ప్రణాళికకు కావలసిన శక్తి, ప్రోటీన్ లెక్కించడానికి ఇది ఉపయోగపడుతుంది.',
  },
  height: { en: 'Height (cm)', hi: 'लंबाई (सेमी)', te: 'ఎత్తు (సెం.మీ.)' },
  weight: { en: 'Weight (kg)', hi: 'वज़न (किग्रा)', te: 'బరువు (కి.గ్రా.)' },
  heightError: { en: 'Enter a height between 120 and 220 cm.', hi: '120 से 220 सेमी के बीच लंबाई लिखें।', te: '120 నుండి 220 సెం.మీ. మధ్య ఎత్తు నమోదు చేయండి.' },
  weightError: { en: 'Enter a weight between 30 and 200 kg.', hi: '30 से 200 किग्रा के बीच वज़न लिखें।', te: '30 నుండి 200 కి.గ్రా. మధ్య బరువు నమోదు చేయండి.' },
  region: { en: 'Which region are you from?', hi: 'आप किस क्षेत्र से हैं?', te: 'మీరు ఏ ప్రాంతానికి చెందినవారు?' },
  chooseState: { en: 'Choose your state', hi: 'अपना राज्य चुनें', te: 'మీ రాష్ట్రాన్ని ఎంచుకోండి' },
  otherState: { en: 'Another state', hi: 'कोई और राज्य', te: 'ఇతర రాష్ట్రం' },
  regionHint: { en: 'We suggest dishes cooked in your region first.', hi: 'हम पहले आपके क्षेत्र में बनने वाले व्यंजन सुझाते हैं।', te: 'మీ ప్రాంతంలో వండే వంటకాలను ముందుగా సూచిస్తాము.' },
  activity: { en: 'How active are you on most days?', hi: 'ज़्यादातर दिनों में आप कितने सक्रिय रहते हैं?', te: 'చాలా రోజుల్లో మీరు ఎంత చురుకుగా ఉంటారు?' },
  act_none: { en: 'Mostly sitting', hi: 'ज़्यादातर बैठे रहना', te: 'ఎక్కువగా కూర్చుని' },
  act_none_hint: { en: 'Desk work, little exercise', hi: 'बैठकर काम, कम व्यायाम', te: 'కూర్చుని పని, తక్కువ వ్యాయామం' },
  act_walking: { en: 'Walking', hi: 'पैदल चलना', te: 'నడక' },
  act_walking_hint: { en: '30+ minutes most days', hi: 'ज़्यादातर दिन 30+ मिनट', te: 'చాలా రోజులు 30+ నిమిషాలు' },
  act_cycling: { en: 'Cycling', hi: 'साइकिल चलाना', te: 'సైక్లింగ్' },
  act_cycling_hint: { en: 'Regular rides or brisk activity', hi: 'नियमित साइकिल या तेज़ गतिविधि', te: 'క్రమం తప్పకుండా సైకిల్ లేదా చురుకైన పని' },
  act_running: { en: 'Running or sports', hi: 'दौड़ना या खेल', te: 'పరుగు లేదా క్రీడలు' },
  act_running_hint: { en: 'Hard exercise most days', hi: 'ज़्यादातर दिन कड़ा व्यायाम', te: 'చాలా రోజులు కఠిన వ్యాయామం' },
  meatsQuestion: { en: 'Which of these do you eat?', hi: 'इनमें से आप क्या खाते हैं?', te: 'వీటిలో మీరు ఏవి తింటారు?' },
  meatsHint: { en: 'Leave all unselected to include everything.', hi: 'सब शामिल करने के लिए कुछ भी न चुनें।', te: 'అన్నీ చేర్చాలంటే ఏదీ ఎంచుకోకండి.' },
  meat_chicken: { en: 'Chicken', hi: 'चिकन', te: 'కోడి మాంసం' },
  meat_mutton: { en: 'Mutton', hi: 'मटन', te: 'మటన్' },
  meat_fish: { en: 'Fish', hi: 'मछली', te: 'చేపలు' },
  meat_shellfish: { en: 'Prawns & crab', hi: 'झींगा और केकड़ा', te: 'రొయ్యలు, పీతలు' },
  meat_egg: { en: 'Eggs', hi: 'अंडे', te: 'గుడ్లు' },
  meat_beef: { en: 'Beef', hi: 'बीफ़', te: 'బీఫ్' },
  meat_pork: { en: 'Pork', hi: 'पोर्क', te: 'పోర్క్' },
  customAllergy: { en: 'Allergic to something else? Add it here', hi: 'किसी और चीज़ से एलर्जी है? यहाँ जोड़ें', te: 'ఇంకేదైనా పడదా? ఇక్కడ చేర్చండి' },
  customAllergyHint: {
    en: 'For example brinjal, mushroom or prawns. We leave out every dish that contains it.',
    hi: 'जैसे बैंगन, मशरूम या झींगा। जिस व्यंजन में यह होगा, उसे हम हटा देंगे।',
    te: 'ఉదాహరణకు వంకాయ, పుట్టగొడుగులు లేదా రొయ్యలు. ఇవి ఉన్న ప్రతి వంటకాన్ని తొలగిస్తాము.',
  },
  typeFood: { en: 'Type a food', hi: 'खाने का नाम लिखें', te: 'ఆహారం పేరు రాయండి' },
  add: { en: 'Add', hi: 'जोड़ें', te: 'చేర్చండి' },
  remove: { en: 'Remove', hi: 'हटाएँ', te: 'తొలగించండి' },
  dietNow: { en: 'Do you follow a diet now?', hi: 'क्या आप अभी कोई डाइट लेते हैं?', te: 'మీరు ఇప్పుడు ఏదైనా ఆహార ప్రణాళిక పాటిస్తున్నారా?' },
  no: { en: 'No', hi: 'नहीं', te: 'లేదు' },
  yes: { en: 'Yes', hi: 'हाँ', te: 'అవును' },
  dietUpload: { en: 'Upload or type what you usually eat', hi: 'आप आमतौर पर जो खाते हैं, अपलोड करें या लिखें', te: 'మీరు సాధారణంగా తినేది అప్‌లోడ్ చేయండి లేదా రాయండి' },
  dietUploadHint: { en: 'We keep the dishes you already eat in your plan where they fit.', hi: 'आप जो पहले से खाते हैं, वे व्यंजन जहाँ ठीक बैठें, योजना में रखते हैं।', te: 'మీరు ఇప్పటికే తినే వంటకాలను సరిపోయే చోట ప్రణాళికలో ఉంచుతాము.' },
  dietPlaceholder: { en: 'Breakfast: 2 idli with sambar. Lunch: rice, tomato pappu, bendakaya fry…', hi: 'नाश्ता: 2 इडली सांभर के साथ। दोपहर: चावल, दाल, भिंडी…', te: 'ఉదయం: 2 ఇడ్లీ సాంబారుతో. మధ్యాహ్నం: అన్నం, టమాటా పప్పు, బెండకాయ వేపుడు…' },
  uploadText: { en: 'Upload a photo, PDF or text file', hi: 'फ़ोटो, PDF या टेक्स्ट फ़ाइल अपलोड करें', te: 'ఫోటో, PDF లేదా టెక్స్ట్ ఫైల్ అప్‌లోడ్ చేయండి' },
  readingFile: { en: 'Reading the file…', hi: 'फ़ाइल पढ़ी जा रही है…', te: 'ఫైల్ చదువుతోంది…' },
  dietReadError: { en: 'Could not read that file. Try a clearer photo or type your meals.', hi: 'फ़ाइल पढ़ी नहीं जा सकी। साफ़ फ़ोटो लें या अपना भोजन लिखें।', te: 'ఆ ఫైల్ చదవలేకపోయాం. స్పష్టమైన ఫోటో ప్రయత్నించండి లేదా మీ భోజనం టైప్ చేయండి.' },
  skip: { en: 'Skip', hi: 'छोड़ें', te: 'దాటవేయండి' },
  // foods
  addToPlan: { en: 'Add to plan', hi: 'योजना में जोड़ें', te: 'ప్రణాళికలో చేర్చండి' },
  inPlan: { en: 'In my plan', hi: 'मेरी योजना में', te: 'నా ప్రణాళికలో' },
  // plans
  dietPlan: { en: 'Diet plan', hi: 'आहार योजना', te: 'ఆహార ప్రణాళిక' },
  planTitle: { en: 'Your meals, built around this report', hi: 'इस रिपोर्ट के अनुसार आपके भोजन', te: 'ఈ రిపోర్టు ఆధారంగా మీ భోజనం' },
  pickedSome: { en: 'foods you picked will be included.', hi: 'चुने गए खाद्य शामिल किए जाएँगे।', te: 'మీరు ఎంచుకున్న ఆహారాలు చేర్చబడతాయి.' },
  pickHint: { en: 'Tick foods above to include them in your plan.', hi: 'योजना में शामिल करने के लिए ऊपर खाद्य चुनें।', te: 'ప్రణాళికలో చేర్చడానికి పైన ఆహారాలను ఎంచుకోండి.' },
  planPromise: {
    en: 'Plans meet your calorie and protein needs and the nutrients this report shows as low.',
    hi: 'योजनाएँ आपकी कैलोरी, प्रोटीन और रिपोर्ट में कम पाए गए पोषक तत्वों की ज़रूरत पूरी करती हैं।',
    te: 'ప్రణాళికలు మీ కేలరీలు, ప్రోటీన్, రిపోర్టులో తక్కువగా ఉన్న పోషకాల అవసరాన్ని తీరుస్తాయి.',
  },
  adultsOnly: { en: 'Diet plans are for adults aged 18 and over.', hi: 'आहार योजनाएँ 18 वर्ष और उससे अधिक उम्र के लिए हैं।', te: 'ఆహార ప్రణాళికలు 18 ఏళ్లు పైబడిన వారికి మాత్రమే.' },
  neededForCalories: { en: 'Needed to work out your daily calories.', hi: 'आपकी रोज़ की कैलोरी निकालने के लिए ज़रूरी।', te: 'మీ రోజువారీ కేలరీలు లెక్కించడానికి అవసరం.' },
  build: { en: 'Build my diet plans', hi: 'मेरी आहार योजनाएँ बनाएँ', te: 'నా ఆహార ప్రణాళికలు తయారు చేయండి' },
  rebuild: { en: 'Rebuild plan options', hi: 'विकल्प फिर से बनाएँ', te: 'ఎంపికలు మళ్లీ తయారు చేయండి' },
  building: { en: 'Building 3 plan options…', hi: '3 विकल्प बन रहे हैं…', te: '3 ఎంపికలు తయారవుతున్నాయి…' },
  style_familiar: { en: 'Familiar', hi: 'जाना-पहचाना', te: 'అలవాటైనది' },
  style_nutritious: { en: 'Most nutritious', hi: 'सबसे पौष्टिक', te: 'అత్యంత పోషకమైనది' },
  style_regional: { en: 'Regional', hi: 'क्षेत्रीय', te: 'ప్రాంతీయం' },
  note_familiar: { en: 'Dishes from your region and the foods you picked', hi: 'आपके क्षेत्र के व्यंजन और आपके चुने खाद्य', te: 'మీ ప్రాంత వంటకాలు, మీరు ఎంచుకున్న ఆహారాలు' },
  note_nutritious: { en: 'The most nutrients for your calories', hi: 'कैलोरी के हिसाब से सबसे ज़्यादा पोषण', te: 'కేలరీలకు తగ్గట్టు అత్యధిక పోషకాలు' },
  note_regional: { en: 'Only dishes cooked in your state', hi: 'केवल आपके राज्य के व्यंजन', te: 'మీ రాష్ట్రంలో వండే వంటకాలు మాత్రమే' },
  makeWeek: { en: 'Make my 7-day plan', hi: 'मेरी 7-दिन की योजना बनाएँ', te: 'నా 7 రోజుల ప్రణాళిక తయారు చేయండి' },
  backToOptions: { en: 'Back to the 3 options', hi: '3 विकल्पों पर वापस', te: '3 ఎంపికలకు తిరిగి' },
  shoppingList: { en: 'Shopping list', hi: 'ख़रीदारी सूची', te: 'కొనుగోలు జాబితా' },
  showMeals: { en: 'Show meals', hi: 'भोजन दिखाएँ', te: 'భోజనం చూపించు' },
  pdf: { en: 'PDF', hi: 'PDF', te: 'PDF' },
  saveWithReport: { en: 'Save with my report', hi: 'रिपोर्ट के साथ सहेजें', te: 'రిపోర్టుతో సేవ్ చేయండి' },
  savedWithReport: { en: 'Saved with this report', hi: 'रिपोर्ट के साथ सहेजा गया', te: 'రిపోర్టుతో సేవ్ అయింది' },
  shoppingHint: { en: 'For the whole week, as bought (before peeling and cleaning).', hi: 'पूरे हफ़्ते के लिए, ख़रीदते समय का वज़न (छीलने-साफ़ करने से पहले)।', te: 'వారం మొత్తానికి, కొనేటప్పటి బరువు (తొక్క తీయకముందు, శుభ్రం చేయకముందు).' },
  swap: { en: 'Swap', hi: 'बदलें', te: 'మార్చండి' },
  saltNote: { en: 'Salt about {g} g a day. Sweets and fried snacks at most once or twice a week.', hi: 'नमक लगभग {g} ग्राम रोज़। मिठाई और तली चीज़ें हफ़्ते में एक-दो बार ही।', te: 'ఉప్పు రోజుకు సుమారు {g} గ్రా. తీపి, వేయించిన చిరుతిళ్లు వారానికి ఒకటి రెండు సార్లు మాత్రమే.' },
  planError: { en: 'Plan not built', hi: 'योजना नहीं बनी', te: 'ప్రణాళిక తయారు కాలేదు' },
  slot_breakfast: { en: 'Breakfast', hi: 'नाश्ता', te: 'అల్పాహారం' },
  slot_lunch: { en: 'Lunch', hi: 'दोपहर का भोजन', te: 'మధ్యాహ్న భోజనం' },
  slot_snack: { en: 'Evening snack', hi: 'शाम का नाश्ता', te: 'సాయంత్రం చిరుతిండి' },
  slot_dinner: { en: 'Dinner', hi: 'रात का भोजन', te: 'రాత్రి భోజనం' },
  calories: { en: 'Calories', hi: 'कैलोरी', te: 'కేలరీలు' },
  protein: { en: 'Protein', hi: 'प्रोटीन', te: 'ప్రోటీన్' },
  target: { en: 'target', hi: 'लक्ष्य', te: 'లక్ష్యం' },
  need: { en: 'need', hi: 'ज़रूरत', te: 'అవసరం' },
  nut_iron_mg: { en: 'Iron', hi: 'आयरन', te: 'ఇనుము' },
  nut_calcium_mg: { en: 'Calcium', hi: 'कैल्शियम', te: 'కాల్షియం' },
  nut_folate_ug: { en: 'Folate', hi: 'फ़ोलेट', te: 'ఫోలేట్' },
  nut_vitamin_c_mg: { en: 'Vitamin C', hi: 'विटामिन C', te: 'విటమిన్ C' },
  nut_vitamin_b12_ug: { en: 'Vitamin B12', hi: 'विटामिन B12', te: 'విటమిన్ B12' },
  nut_vitamin_d_iu: { en: 'Vitamin D', hi: 'विटामिन D', te: 'విటమిన్ D' },
  nut_zinc_mg: { en: 'Zinc', hi: 'ज़िंक', te: 'జింక్' },
  nut_magnesium_mg: { en: 'Magnesium', hi: 'मैग्नीशियम', te: 'మెగ్నీషియం' },
  nut_fibre_g: { en: 'Fibre', hi: 'फ़ाइबर', te: 'పీచు పదార్థం' },
  days: { en: 'Mon Tue Wed Thu Fri Sat Sun', hi: 'सोम मंगल बुध गुरु शुक्र शनि रवि', te: 'సోమ మంగళ బుధ గురు శుక్ర శని ఆది' },
  language: { en: 'Language', hi: 'भाषा', te: 'భాష' },
  // results
  allCount: { en: 'All ({n})', hi: 'सभी ({n})', te: 'అన్నీ ({n})' },
  needsAttentionCount: { en: 'Needs attention ({n})', hi: 'ध्यान ज़रूरी ({n})', te: 'శ్రద్ధ అవసరం ({n})' },
  formulated: { en: 'Formulated for a {diet} diet', hi: '{diet} आहार के लिए बनाई गई', te: '{diet} ఆహారం కోసం రూపొందించబడింది' },
  excluding: { en: ', strictly excluding {list}.', hi: ', {list} को पूरी तरह हटाकर।', te: ', {list} పూర్తిగా లేకుండా.' },
  noExclusions: { en: ', with zero dietary exclusions.', hi: ', बिना किसी परहेज़ के।', te: ', ఏ మినహాయింపులూ లేకుండా.' },
  diet_veg: { en: 'veg', hi: 'शाकाहारी', te: 'శాకాహార' },
  diet_vegan: { en: 'vegan', hi: 'वीगन', te: 'వీగన్' },
  diet_eggetarian: { en: 'eggetarian', hi: 'अंडाहारी', te: 'గుడ్లు తినే శాకాహార' },
  diet_non_veg: { en: 'non veg', hi: 'मांसाहारी', te: 'మాంసాహార' },
  allergen_dairy: { en: 'dairy', hi: 'डेयरी', te: 'పాలు' },
  allergen_gluten: { en: 'gluten', hi: 'ग्लूटेन', te: 'గ్లూటెన్' },
  allergen_nuts: { en: 'nuts', hi: 'मेवे', te: 'గింజలు' },
  allergen_soy: { en: 'soy', hi: 'सोया', te: 'సోయా' },
  allergen_eggs: { en: 'eggs', hi: 'अंडे', te: 'గుడ్లు' },
  allergen_seafood: { en: 'seafood', hi: 'समुद्री भोजन', te: 'సముద్ర ఆహారం' },
  allergen_sesame: { en: 'sesame', hi: 'तिल', te: 'నువ్వులు' },
  allergen_mustard: { en: 'mustard', hi: 'सरसों', te: 'ఆవాలు' },
  inHealthyRange: { en: '{a} of {n} results in the healthy range', hi: '{n} में से {a} परिणाम स्वस्थ सीमा में', te: '{n} లో {a} ఫలితాలు ఆరోగ్యకర పరిధిలో' },
  needOneSentence: { en: '1 result needs attention. Your diet plan is below, and anything for a doctor is marked clearly.',
    hi: '1 परिणाम पर ध्यान ज़रूरी है। आपकी आहार योजना नीचे है, और डॉक्टर को दिखाने वाली बातें साफ़ दिखाई गई हैं।',
    te: '1 ఫలితానికి శ్రద్ధ అవసరం. మీ ఆహార ప్రణాళిక కింద ఉంది, డాక్టర్‌కు చూపించాల్సినవి స్పష్టంగా గుర్తించబడ్డాయి.' },
  needManySentence: { en: '{n} results need attention. Your diet plan is below, and anything for a doctor is marked clearly.',
    hi: '{n} परिणामों पर ध्यान ज़रूरी है। आपकी आहार योजना नीचे है, और डॉक्टर को दिखाने वाली बातें साफ़ दिखाई गई हैं।',
    te: '{n} ఫలితాలకు శ్రద్ధ అవసరం. మీ ఆహార ప్రణాళిక కింద ఉంది, డాక్టర్‌కు చూపించాల్సినవి స్పష్టంగా గుర్తించబడ్డాయి.' },
  needOne: { en: '1 result need attention', hi: '1 परिणाम पर ध्यान ज़रूरी', te: '1 ఫలితానికి శ్రద్ధ అవసరం' },
  needMany: { en: '{n} results need attention', hi: '{n} परिणामों पर ध्यान ज़रूरी', te: '{n} ఫలితాలకు శ్రద్ధ అవసరం' },
  pctInRange: { en: '{n}% in range', hi: '{n}% सीमा में', te: '{n}% పరిధిలో' },
  allTested: { en: 'All {n} tested biomarkers are within standard reference intervals. Your results look balanced across the tests included in this report.',
    hi: 'सभी {n} जाँचें मानक संदर्भ सीमाओं में हैं। इस रिपोर्ट की सभी जाँचों में आपके परिणाम संतुलित दिखते हैं।',
    te: 'మొత్తం {n} పరీక్షలు ప్రామాణిక సూచన పరిధుల్లో ఉన్నాయి. ఈ రిపోర్టులోని అన్ని పరీక్షల్లో మీ ఫలితాలు సమతుల్యంగా కనిపిస్తున్నాయి.' },
  labSummary: { en: 'Laboratory analysis reveals that {a} of {n} parameters are outside their reference intervals ({low} Low, {border} Borderline, {high} Elevated). Where a food plan applies, it uses Indian staples matched to your diet and allergies; it never replaces medical care.',
    hi: 'लैब जाँच से पता चलता है कि {n} में से {a} मान अपनी संदर्भ सीमा से बाहर हैं ({low} कम, {border} सीमा पर, {high} अधिक)। जहाँ भोजन योजना लागू होती है, वहाँ यह आपके आहार और एलर्जी के अनुसार भारतीय भोजन लेती है; यह कभी इलाज की जगह नहीं लेती।',
    te: 'ల్యాబ్ విశ్లేషణ ప్రకారం {n} లో {a} విలువలు సూచన పరిధి బయట ఉన్నాయి ({low} తక్కువ, {border} సరిహద్దులో, {high} ఎక్కువ). ఆహార ప్రణాళిక వర్తించే చోట, ఇది మీ ఆహార రకం, అలర్జీలకు తగిన భారతీయ ఆహారాలు వాడుతుంది; ఇది ఎప్పుడూ వైద్యానికి ప్రత్యామ్నాయం కాదు.' },
  status_low: { en: 'low', hi: 'कम', te: 'తక్కువ' },
  status_borderline: { en: 'borderline', hi: 'सीमा पर', te: 'సరిహద్దులో' },
  status_high: { en: 'elevated', hi: 'अधिक', te: 'ఎక్కువ' },
  statusPct: { en: '{status} ({n}% optimal)', hi: '{status} (उचित स्तर का {n}%)', te: '{status} (సరైన స్థాయిలో {n}%)' },
  valueBelow: { en: 'Value is below the reference range ({x}). Follow the food protocol where one is listed, and discuss it with your doctor.',
    hi: 'मान संदर्भ सीमा ({x}) से कम है। जहाँ भोजन योजना दी गई है उसे अपनाएँ, और डॉक्टर से बात करें।',
    te: 'విలువ సూచన పరిధి ({x}) కంటే తక్కువ ఉంది. ఆహార ప్రణాళిక ఇచ్చిన చోట దాన్ని పాటించండి, డాక్టర్‌తో మాట్లాడండి.' },
  valueAbove: { en: 'Value is above the reference range ({x}). Follow the food protocol where one is listed, and discuss it with your doctor.',
    hi: 'मान संदर्भ सीमा ({x}) से अधिक है। जहाँ भोजन योजना दी गई है उसे अपनाएँ, और डॉक्टर से बात करें।',
    te: 'విలువ సూచన పరిధి ({x}) కంటే ఎక్కువ ఉంది. ఆహార ప్రణాళిక ఇచ్చిన చోట దాన్ని పాటించండి, డాక్టర్‌తో మాట్లాడండి.' },
  valueBorder: { en: 'Value is on the borderline. Small, steady dietary changes are recommended and the test is worth repeating.',
    hi: 'मान सीमा पर है। खान-पान में छोटे, लगातार बदलाव की सलाह है और जाँच दोबारा कराना ठीक रहेगा।',
    te: 'విలువ సరిహద్దులో ఉంది. ఆహారంలో చిన్న, స్థిరమైన మార్పులు సూచించబడ్డాయి, పరీక్ష మళ్లీ చేయించడం మంచిది.' },
  belowHealthy: { en: '{x} below the healthy range', hi: 'स्वस्थ सीमा से {x} कम', te: 'ఆరోగ్యకర పరిధి కంటే {x} తక్కువ' },
  aboveHealthy: { en: '{x} above the healthy range', hi: 'स्वस्थ सीमा से {x} अधिक', te: 'ఆరోగ్యకర పరిధి కంటే {x} ఎక్కువ' },
  closeLower: { en: 'Close to the lower limit of {x}', hi: 'निचली सीमा {x} के क़रीब', te: 'దిగువ పరిమితి {x} కి దగ్గరగా' },
  perServing: { en: '{x} per {serving}', hi: '{serving} में {x}', te: '{serving} లో {x}' },
  perOnly: { en: 'Per {serving}', hi: 'प्रति {serving}', te: 'ప్రతి {serving}' },
  statusLabel: { en: '{label} Status', hi: 'स्थिति: {label}', te: 'స్థితి: {label}' },
  target_iron_mg: { en: 'iron mg', hi: 'आयरन', te: 'ఇనుము' },
  target_calcium_mg: { en: 'calcium mg', hi: 'कैल्शियम', te: 'కాల్షియం' },
  target_folate_mcg: { en: 'folate mcg', hi: 'फ़ोलेट', te: 'ఫోలేట్' },
  target_vitamin_d_iu: { en: 'vitamin d iu', hi: 'विटामिन D', te: 'విటమిన్ D' },
  target_vitamin_b12_mcg: { en: 'vitamin b12 mcg', hi: 'विटामिन B12', te: 'విటమిన్ B12' },
  target_glycemic_support: { en: 'glycemic support', hi: 'ब्लड शुगर नियंत्रण', te: 'రక్తంలో చక్కెర నియంత్రణ' },
  target_lipid_support: { en: 'lipid support', hi: 'रक्त वसा नियंत्रण', te: 'రక్త కొవ్వుల నియంత్రణ' },
  target_hdl_support: { en: 'hdl support', hi: 'HDL सहायता', te: 'HDL సహాయం' },
  target_protein_support: { en: 'protein support', hi: 'प्रोटीन सहायता', te: 'ప్రోటీన్ సహాయం' },
  target_uric_acid_support: { en: 'uric acid support', hi: 'यूरिक एसिड नियंत्रण', te: 'యూరిక్ యాసిడ్ నియంత్రణ' },
  target_liver_support: { en: 'liver support', hi: 'लिवर सहायता', te: 'కాలేయ సహాయం' },
  step1: { en: 'Choose a plan style', hi: 'योजना का तरीका चुनें', te: 'ప్రణాళిక రకాన్ని ఎంచుకోండి' },
  step1Hint: { en: 'Three sample days built for your targets. Pick the one that suits you.', hi: 'आपके लक्ष्यों के अनुसार बने तीन नमूना दिन। जो आपको ठीक लगे, वह चुनें।', te: 'మీ లక్ష్యాలకు తగ్గట్టు తయారైన మూడు నమూనా రోజులు. మీకు నచ్చినది ఎంచుకోండి.' },
  step2: { en: 'Your 7-day plan', hi: 'आपकी 7-दिन की योजना', te: 'మీ 7 రోజుల ప్రణాళిక' },
  step2Hint: { en: 'Swap any dish you do not like, get the shopping list and download it.', hi: 'जो व्यंजन पसंद न हो उसे बदलें, ख़रीदारी सूची लें और डाउनलोड करें।', te: 'నచ్చని వంటకాన్ని మార్చండి, కొనుగోలు జాబితా తీసుకుని డౌన్‌లోడ్ చేయండి.' },
  foodsInPlan: { en: '{n} foods you picked are in this plan.', hi: 'आपके चुने {n} खाद्य इस योजना में हैं।', te: 'మీరు ఎంచుకున్న {n} ఆహారాలు ఈ ప్రణాళికలో ఉన్నాయి.' },
  noFoodsPicked: { en: 'Want particular foods in your plan?', hi: 'योजना में कोई ख़ास खाद्य चाहिए?', te: 'ప్రణాళికలో ప్రత్యేకంగా ఏవైనా ఆహారాలు కావాలా?' },
  chooseFoods: { en: 'Choose foods that help', hi: 'मददगार खाद्य चुनें', te: 'సహాయపడే ఆహారాలు ఎంచుకోండి' },
  changeFoods: { en: 'Change foods', hi: 'खाद्य बदलें', te: 'ఆహారాలు మార్చండి' },
  tryAgain: { en: 'Try again', hi: 'फिर से कोशिश करें', te: 'మళ్లీ ప్రయత్నించండి' },
  signInToSave: { en: 'Sign in to save plans with your report.', hi: 'योजना रिपोर्ट के साथ सहेजने के लिए लॉग इन करें।', te: 'ప్రణాళికను రిపోర్టుతో సేవ్ చేయడానికి లాగిన్ అవ్వండి.' },
  resultsTitle: { en: 'Your personalised diet plan', hi: 'आपकी व्यक्तिगत आहार योजना', te: 'మీ వ్యక్తిగత ఆహార ప్రణాళిక' },
  tabTests: { en: 'Test results ({n})', hi: 'जाँच नतीजे ({n})', te: 'పరీక్ష ఫలితాలు ({n})' },
  tabFoods: { en: 'Foods that help', hi: 'मददगार खाद्य', te: 'సహాయపడే ఆహారాలు' },
  resultTabs: { en: 'Result sections', hi: 'नतीजों के भाग', te: 'ఫలితాల విభాగాలు' },
  foodsPickedBar: { en: '{n} foods picked for your diet plan', hi: 'आहार योजना के लिए {n} खाद्य चुने गए', te: 'ఆహార ప్రణాళిక కోసం {n} ఆహారాలు ఎంచుకున్నారు' },
  updatePlan: { en: 'Update my diet plan', hi: 'मेरी आहार योजना अपडेट करें', te: 'నా ఆహార ప్రణాళికను నవీకరించండి' },
  foodsIntro: { en: 'These Indian foods help the results that need attention. Tap “Add to plan” on the ones you like, then build your diet plan: it will include them.', hi: 'ये भारतीय खाद्य उन नतीजों में मदद करते हैं जिन पर ध्यान देना है। पसंद के खाद्यों पर “योजना में जोड़ें” दबाएँ, फिर अपनी आहार योजना बनाएँ: उसमें ये शामिल होंगे।', te: 'శ్రద్ధ అవసరమైన ఫలితాలకు ఈ భారతీయ ఆహారాలు సహాయపడతాయి. నచ్చిన వాటిపై “ప్రణాళికలో చేర్చండి” నొక్కి, తర్వాత మీ ఆహార ప్రణాళిక తయారు చేయండి: అవి అందులో ఉంటాయి.' },
  tabStepFoods: { en: '1. Pick foods', hi: '1. खाद्य चुनें', te: '1. ఆహారాలు ఎంచుకోండి' },
  tabStepPlan: { en: '2. Diet plan', hi: '2. आहार योजना', te: '2. ఆహార ప్రణాళిక' },
  noPicksYet: { en: 'Pick foods you like, or build the plan straight away.', hi: 'पसंद के खाद्य चुनें, या सीधे योजना बनाएँ।', te: 'నచ్చిన ఆహారాలు ఎంచుకోండి, లేదా నేరుగా ప్రణాళిక తయారు చేయండి.' },
  buildPlanNow: { en: 'Build my diet plan', hi: 'मेरी आहार योजना बनाएँ', te: 'నా ఆహార ప్రణాళిక తయారు చేయండి' },
  seePlan: { en: 'See my diet plan', hi: 'मेरी आहार योजना देखें', te: 'నా ఆహార ప్రణాళిక చూడండి' },
  updatingPlan: { en: 'Updating your plan with your foods…', hi: 'आपके खाद्यों के साथ योजना अपडेट हो रही है…', te: 'మీ ఆహారాలతో ప్రణాళిక నవీకరించబడుతోంది…' },
  foodsPickedOne: { en: '1 food picked for your diet plan', hi: 'आहार योजना के लिए 1 खाद्य चुना गया', te: 'ఆహార ప్రణాళిక కోసం 1 ఆహారం ఎంచుకున్నారు' },
  foodsInPlanOne: { en: 'The food you picked is in this plan.', hi: 'आपका चुना खाद्य इस योजना में है।', te: 'మీరు ఎంచుకున్న ఆహారం ఈ ప్రణాళికలో ఉంది.' },
  aisle_grains: { en: 'Grains & millets', hi: 'अनाज और मोटे अनाज', te: 'ధాన్యాలు, చిరుధాన్యాలు' },
  aisle_pulses: { en: 'Pulses & dals', hi: 'दालें', te: 'పప్పులు' },
  aisle_vegetables: { en: 'Vegetables', hi: 'सब्ज़ियाँ', te: 'కూరగాయలు' },
  aisle_greens: { en: 'Leafy greens', hi: 'हरी पत्तेदार सब्ज़ियाँ', te: 'ఆకుకూరలు' },
  aisle_fruits: { en: 'Fruits', hi: 'फल', te: 'పండ్లు' },
  aisle_dairy: { en: 'Milk & dairy', hi: 'दूध और डेयरी', te: 'పాలు, పాల ఉత్పత్తులు' },
  aisle_meat_fish: { en: 'Meat, fish & eggs', hi: 'मांस, मछली और अंडे', te: 'మాంసం, చేపలు, గుడ్లు' },
  aisle_nuts_seeds: { en: 'Nuts & seeds', hi: 'मेवे और बीज', te: 'గింజలు, విత్తనాలు' },
  aisle_spices: { en: 'Spices & masalas', hi: 'मसाले', te: 'మసాలాలు' },
  aisle_oils: { en: 'Oils & ghee', hi: 'तेल और घी', te: 'నూనెలు, నెయ్యి' },
  aisle_other: { en: 'Other', hi: 'अन्य', te: 'ఇతరాలు' },
  forName: { en: 'For {name}', hi: '{name} के लिए', te: '{name} కోసం' },
  doctorReview: { en: 'Doctor review', hi: 'डॉक्टर की जाँच', te: 'డాక్టర్ పరిశీలన' },
} as const;

export type StringKey = keyof typeof STRINGS;

export const translate = (language: Language, key: StringKey, vars: Record<string, string | number> = {}) => {
  let text: string = STRINGS[key][language] ?? STRINGS[key].en;
  for (const [k, v] of Object.entries(vars)) text = text.replace(`{${k}}`, String(v));
  return text;
};

/** t('key') in the person's chosen language, re-rendering when they switch. */
/** For keys built at run time (status_low, target_iron_mg); falls back to the given text. */
export const hasKey = (key: string): key is StringKey => key in STRINGS;

export const useT = () => {
  const language = useLanguage();
  return (key: StringKey, vars?: Record<string, string | number>) => translate(language, key, vars);
};

const UNIT_WORDS: Record<string, { hi: string; te: string }> = {
  cup: { hi: 'कप', te: 'కప్పు' }, cups: { hi: 'कप', te: 'కప్పులు' }, cooked: { hi: 'पका हुआ', te: 'వండిన' },
  katori: { hi: 'कटोरी', te: 'గిన్నె' }, katoris: { hi: 'कटोरी', te: 'గిన్నెలు' }, glass: { hi: 'गिलास', te: 'గ్లాసు' },
  glasses: { hi: 'गिलास', te: 'గ్లాసులు' }, plate: { hi: 'प्लेट', te: 'ప్లేటు' }, plates: { hi: 'प्लेट', te: 'ప్లేట్లు' },
  bowl: { hi: 'कटोरा', te: 'బౌల్' }, bowls: { hi: 'कटोरे', te: 'బౌల్స్' }, small: { hi: 'छोटी', te: 'చిన్న' },
  big: { hi: 'बड़ा', te: 'పెద్ద' }, medium: { hi: 'मध्यम', te: 'మధ్యస్థ' }, piece: { hi: 'टुकड़ा', te: 'ముక్క' },
  pieces: { hi: 'टुकड़े', te: 'ముక్కలు' }, tablespoon: { hi: 'बड़ा चम्मच', te: 'టేబుల్ స్పూన్' },
  tablespoons: { hi: 'बड़े चम्मच', te: 'టేబుల్ స్పూన్లు' }, handful: { hi: 'मुट्ठी', te: 'గుప్పెడు' },
  slices: { hi: 'स्लाइस', te: 'ముక్కలు' }, roti: { hi: 'रोटी', te: 'రొట్టె' }, rotis: { hi: 'रोटियाँ', te: 'రొట్టెలు' },
  idlis: { hi: 'इडली', te: 'ఇడ్లీలు' }, dosa: { hi: 'डोसा', te: 'దోశ' }, dosas: { hi: 'डोसे', te: 'దోశలు' },
  egg: { hi: 'अंडा', te: 'గుడ్డు' }, eggs: { hi: 'अंडे', te: 'గుడ్లు' }, phulka: { hi: 'फुलका', te: 'పుల్కా' },
  phulkas: { hi: 'फुलके', te: 'పుల్కాలు' }, chapati: { hi: 'चपाती', te: 'చపాతీ' }, chapatis: { hi: 'चपातियाँ', te: 'చపాతీలు' },
  paratha: { hi: 'पराठा', te: 'పరాటా' }, parathas: { hi: 'पराठे', te: 'పరాటాలు' }, puris: { hi: 'पूरियाँ', te: 'పూరీలు' },
  vadas: { hi: 'वड़े', te: 'గారెలు' }, ball: { hi: 'गोला', te: 'ముద్ద' }, laddu: { hi: 'लड्डू', te: 'లడ్డు' },
  ladoo: { hi: 'लड्डू', te: 'లడ్డు' }, coconut: { hi: 'नारियल', te: 'కొబ్బరి' }, with: { hi: 'के साथ', te: 'తో' },
  rotti: { hi: 'रोट्टी', te: 'రొట్టె' }, rottis: { hi: 'रोट्टियाँ', te: 'రొట్టెలు' },
  adai: { hi: 'अडै', te: 'అడై' },
  appams: { hi: 'अप्पम', te: 'అప్పం' },
  ariselu: { hi: 'अरिसेलु', te: 'అరిసెలు' },
  baatis: { hi: 'बाटियाँ', te: 'బాటీలు' },
  bajjis: { hi: 'बज्जी', te: 'బజ్జీలు' },
  balls: { hi: 'गोले', te: 'ముద్దలు' },
  bhatura: { hi: 'भटूरा', te: 'భటూరా' },
  bobbattu: { hi: 'बोब्बट्टू', te: 'బొబ్బట్టు' },
  chillas: { hi: 'चीले', te: 'చిల్లాలు' },
  chokha: { hi: 'चोखा', te: 'చోఖా' },
  cob: { hi: 'भुट्टा', te: 'కంకి' },
  dal: { hi: 'दाल', te: 'పప్పు' },
  ghee: { hi: 'घी', te: 'నెయ్యి' },
  gulab: { hi: 'गुलाब', te: 'గులాబ్' },
  jamuns: { hi: 'जामुन', te: 'జామూన్లు' },
  idiyappam: { hi: 'इडियप्पम', te: 'ఇడియప్పం' },
  littis: { hi: 'लिट्टी', te: 'లిట్టీలు' },
  luchis: { hi: 'लूची', te: 'లూచీలు' },
  momos: { hi: 'मोमो', te: 'మోమోలు' },
  neer: { hi: 'नीर', te: 'నీర్' },
  omelette: { hi: 'ऑमलेट', te: 'ఆమ్లెట్' },
  paniyaram: { hi: 'पनियारम', te: 'పొంగనాలు' },
  parotta: { hi: 'परोटा', te: 'పరోటా' },
  pesarattu: { hi: 'पेसरट्टू', te: 'పెసరట్టు' },
  pindi: { hi: 'पिंडी', te: 'పిండి' },
  podi: { hi: 'पोडी', te: 'పొడి' },
  punugulu: { hi: 'पुनुगुलु', te: 'పునుగులు' },
  puttu: { hi: 'पुट्टू', te: 'పుట్టు' },
  rava: { hi: 'रवा', te: 'రవ్వ' },
  rosogollas: { hi: 'रसगुल्ले', te: 'రసగుల్లాలు' },
  samosa: { hi: 'समोसा', te: 'సమోసా' },
  sarva: { hi: 'सर्व', te: 'సర్వ' },
  seeds: { hi: 'बीज', te: 'గింజలు' },
  tbsp: { hi: 'बड़ा चम्मच', te: 'టేబుల్ స్పూన్' },
  thalipeeth: { hi: 'थालीपीठ', te: 'థాలిపీఠ్' },
  thepla: { hi: 'थेपला', te: 'తేప్లా' },
  tikkis: { hi: 'टिक्की', te: 'టిక్కీలు' },
  tsp: { hi: 'छोटा चम्मच', te: 'టీ స్పూన్' },
  uttapam: { hi: 'उत्तपम', te: 'ఊతప్పం' },
};

/** "2 cups cooked" -> "2 कप पका हुआ"; words without a translation stay as they are. */
export const localizeWords = (text: string, language: Language): string => {
  if (language === 'en') return text;
  const joined = /^(.+?) with (.+)$/.exec(text); // "2 baatis with dal" -> "dal with 2 baatis" word order
  if (joined) {
    const [first, second] = [localizeWords(joined[1], language), localizeWords(joined[2], language)];
    return language === 'hi' ? `${second} के साथ ${first}` : `${second}తో ${first}`;
  }
  return text
        .replace(/(\d+) (cups?) cooked/, (_, n: string, cup: string) =>
          language === 'te' ? `${n} ${UNIT_WORDS[cup].te} (వండినది)` : `${n} ${UNIT_WORDS[cup].hi} (पका हुआ)`)
        .replace(/[A-Za-z]+/g, (w) => UNIT_WORDS[w.toLowerCase()]?.[language] ?? w);
};
