"""Hand-written questions and answers about using NutriLens, privacy, safety and everyday nutrition.

Each entry: id, example phrasings (the matcher compares a user's question with these), answer, follow-up suggestions.
Answers use a small markdown subset that the chat window renders: **bold**, "- " bullets and blank-line paragraphs.
"""

FAQ = [
    # ---- About NutriLens ----
    ("about", ["what is nutrilens", "what does this website do", "what is this app", "tell me about nutrilens",
               "what can this site do", "how does nutrilens help me", "what is the purpose of this website"],
     'NutriLens reads your blood report and turns it into a **personalised Indian diet plan**.\n\n- Upload a '
     'PDF or photo of your report, or paste its text. It reads 61 common tests (blood count, sugar, '
     'cholesterol, liver, kidney, thyroid, iron and vitamins).\n- Each result is marked low, borderline, '
     'normal or high and explained in plain language.\n- You pick Indian foods that help your results, and '
     'NutriLens builds **diet plans** from 278 home-style dishes of your state: three one-day options, '
     'then a full **7-day plan** with a shopping list.\n- Everything works in **English, Hindi and '
     'Telugu**, including the PDFs.',
     ["How do I upload my report?", "Which tests are supported?", "Is my data private?"]),
    ("how_it_works", ["how does nutrilens work", "how does it analyse my report", "what algorithm do you use",
                      "is this ai", "do you use ai", "how are foods chosen", "how do you recommend foods",
                      "what is the logic behind the diet plan", "do you use machine learning", "how is the diet decided"],
     'NutriLens uses **checked data and fixed rules**, not guesses:\n\n- It reads the values, units and '
     "ranges from your report and marks each result against your lab's range (or a published range).\n- "
     'Foods for each result are ranked by real nutrient values from the **ICMR-NIN Indian Food Composition '
     'Tables (IFCT 2017)**, or by properties such as low GI or high fibre, and filtered by your diet and '
     'allergies.\n- Your daily **calorie and protein targets** come from your age, sex, height, weight and '
     'activity; nutrient targets come from the ICMR-NIN 2020 recommended amounts.\n- An **optimisation '
     'solver** then picks dishes and portions that meet those targets, favour the nutrients your report '
     'shows as low and respect your diet, allergies and region.\n\nEvery food shows why it was chosen, so '
     'you can check the reasoning.',
     ["Where does the food data come from?", "Which tests get a food plan?"]),
    ("who_made", ["who made nutrilens", "who built this", "who created you", "who developed this website",
                  "who are the developers"],
     "NutriLens was built as a capstone project by students of the School of CS & AI, SR University, Warangal.",
     ["What is NutriLens?", "How does NutriLens work?"]),
    ("is_free", ["is nutrilens free", "do i have to pay", "what is the cost", "is there any charge",
                 "is it paid", "subscription price"],
     "Yes, NutriLens is **free to use**. There are no charges or subscriptions.",
     ["Do I need an account?", "How do I upload my report?"]),
    ("supported_tests", ["which tests are supported", "what tests can you read", "which biomarkers do you analyse",
                         "list of supported tests", "what tests does nutrilens check", "can you read my thyroid test",
                         "which blood tests work", "what parameters are supported", "how many tests do you support"],
     "NutriLens reads **61 common tests** in these groups:\n\n"
     "- **Blood count (CBC):** haemoglobin, RBC, PCV, MCV, MCH, MCHC, RDW, WBC, differential count, platelets, ESR\n"
     "- **Iron studies:** ferritin, serum iron, TIBC, transferrin saturation\n"
     "- **Vitamins & minerals:** vitamin D, vitamin B12, folate, calcium, phosphorus\n"
     "- **Blood sugar:** HbA1c, fasting and post-meal glucose\n"
     "- **Lipid profile:** total cholesterol, LDL, HDL, triglycerides\n"
     "- **Liver:** SGPT, SGOT, GGT, ALP, bilirubin, total protein, albumin, globulin\n"
     "- **Kidney:** creatinine, urea, BUN, uric acid, eGFR\n"
     "- **Thyroid:** TSH, T3, T4, free T3, free T4\n"
     "- **Electrolytes & inflammation:** sodium, potassium, chloride, CRP",
     ["Which tests get a food plan?", "How do I upload my report?"]),
    ("plan_tests", ["which tests get a food plan", "why is there no food plan for thyroid",
                    "why no diet for my kidney test", "which results get food suggestions",
                    "why did i not get foods for some tests", "why only doctor review for some tests"],
     "Food plans are given where diet can genuinely help:\n\n"
     "- **Food plan:** blood count and iron, vitamin D, B12, folate, calcium, blood sugar and cholesterol.\n"
     "- **Food plan + doctor:** liver enzymes, low protein or albumin, and uric acid. Food helps, but a doctor should also review them.\n"
     "- **Doctor review only:** thyroid, electrolytes, most kidney tests, white cell counts and CRP. Diet cannot safely fix these, "
     "so NutriLens asks you to see a doctor instead of guessing.",
     ["Which tests are supported?", "How does NutriLens work?"]),
    ("food_source", ["where does the food data come from", "what is the source of nutrient values",
                     "are the nutrient values correct", "which food database do you use", "how many foods are there"],
     'Nutrient values come from the **Indian Food Composition Tables (IFCT 2017)** by ICMR-National '
     'Institute of Nutrition, Hyderabad, with USDA values for a few foods IFCT does not list. The food '
     'suggestions use **187 Indian foods**; the diet plans use **278 dishes** whose nutrients are '
     'calculated from their raw ingredients, with cooking losses from IFCT. Dishes were checked against '
     'lab-measured values of cooked food (UK CoFID) and typical days against the salt Indians actually '
     'eat.',
     ["How are foods chosen?", "Which foods are rich in iron?"]),
    ("ranges_source", ["where do the normal ranges come from", "which reference range do you use",
                       "why is my lab range different", "why does the range differ from my report"],
     "NutriLens **uses the range printed on your report** whenever it is there, because each lab calibrates its own machines. "
     "If the report has no range, it uses standard adult ranges from clinical guidelines, separate for men and women where needed.",
     ["How accurate is NutriLens?", "What do low, borderline and high mean?"]),

    # ---- Using the app ----
    ("upload", ["what is the next step after uploading", "what to do after uploading the report", "how do i upload my report", "how to use this website", "how to analyse my report", "where do i upload",
                "how do i start", "steps to use nutrilens", "how to use the website", "how to use the app", "how to check my report"],
     'It takes three steps:\n\n- **Upload** your report on the home page: drag in a PDF or photo, or choose '
     '**Paste text**, then check the values that were read.\n- **Your profile:** age, sex, height, weight, '
     'state, activity, diet type (and which meats, for non-veg), allergies, and optionally what you '
     'usually eat.\n- **Results:** first **pick foods** you like, then open **Diet plan** to get three plan '
     'options and a 7-day plan. Your test results are in the third tab. You can download everything as a '
     'PDF.',
     ["Which file types can I upload?", "Do I need an account?"]),
    ("file_types", ["which file types can i upload", "can i upload a photo", "can i upload an image", "is jpg supported",
                    "can i upload a scanned report", "what formats are supported", "can i take a picture of my report",
                    "what is the file size limit", "my file is too big"],
     "You can upload **PDF, JPG, JPEG or PNG** files up to **10 MB**, or paste the report text. iPhone HEIC photos "
     "and Word files need to be saved as JPG or PDF first.\n\n"
     "Scanned reports and phone photos work too. For the best results, take the photo in good light, keep the page flat and "
     "make sure the numbers are sharp.",
     ["Why was a value not read?", "How do I upload my report?"]),
    ("labs", ["which labs are supported", "does it work with my lab", "does it work for apollo report",
              "can it read thyrocare report", "does it support government lab reports", "which hospital reports work"],
     "NutriLens is designed to work with reports from **any Indian lab**: private chains, hospitals and government labs. "
     "It recognises the many different names labs use for the same test (for example Hb, Haemoglobin and Hemoglobin).",
     ["Which file types can I upload?", "Why was a value not read?"]),
    ("not_read", ["why was a value not read", "my test is missing", "some results are missing", "it did not detect my value",
                  "a test was not found", "the value is wrong", "it read the wrong number", "upload failed",
                  "it says no results found", "my report could not be read"],
     "If a result is missing or looks wrong:\n\n"
     "- Check the result list after upload; you can **edit any value** or use **Add a test** to enter one by hand.\n"
     "- For photos, retake it in good light with the page flat and the numbers in focus.\n"
     "- If a page is an unclear picture, NutriLens tells you which page could not be read.\n"
     "- Only the 61 supported tests are read; other tests on the report are skipped.",
     ["Which tests are supported?", "Which file types can I upload?"]),
    ("review_step", ["why do i have to review results", "why was a value marked for review",
                     "what does needs attention mean", "why is a result highlighted", "what is the review step"],
     "Most reports go straight to your profile. NutriLens only asks you to review when it is **not fully sure** about a value, "
     "for example when there is no unit, the value is written as \"< 5.0\", or the same test appears twice. Check those rows, "
     "correct them if needed, and continue.",
     ["Why was a value not read?", "How do I upload my report?"]),
    ("edit_values", ["how do i edit a value", "can i change a result", "how to add a test manually",
                     "can i enter values myself", "how do i correct a wrong value"],
     "Open **View or edit results** on the summary card after upload. You can change any value or unit, remove a row, "
     "or use **Add a test** to enter a result by hand.",
     ["Why was a value not read?"]),
    ("paste_text", ["can i paste text", "how to paste my report", "can i type my values", "what is paste text"],
     "Yes. On the upload box, choose **Paste text** and paste the text from your report (for example, copied from an email or PDF). "
     "Then click **Analyse my report**.",
     ["Which file types can I upload?"]),
    ("profile", ["why do you need my age", "why ask my gender", "why do you need my diet type", "what is the profile step",
                 "what should i choose in diet type", "what is eggetarian"],
     "Your profile makes the plan personal:\n\n"
     "- **Sex** is used because some normal ranges differ for men and women (for example haemoglobin).\n"
     "- **Diet type** (vegetarian, vegan, eggetarian or non-vegetarian) decides which foods can appear. "
     "Eggetarian means vegetarian plus eggs.\n"
     "- **Allergies** remove every food containing them.",
     ["How do I set my allergies?", "What do low, borderline and high mean?"]),
    ("allergies", ["how do i set my allergies", "can i exclude foods", "i am allergic to nuts", "i am lactose intolerant",
                   "will it remove foods i am allergic to", "which allergies are supported"],
     "In the profile step, select any of **dairy, gluten, nuts, soy, eggs or seafood**. Every food containing them is removed "
     "from your plan. You can also ask me, for example, \"iron foods without dairy\".",
     ["Which foods are rich in iron?", "Why do you need my diet type?"]),
    ("statuses", ["what do low borderline and high mean", "what does borderline mean", "what does normal mean",
                  "what do the colours mean", "what does the status mean", "what does out of range mean"],
     "- **Normal:** inside the healthy range.\n"
     "- **Borderline:** just outside or at the edge of the range; worth watching.\n"
     "- **Low / High:** outside the range. Results that diet can help get a food plan; others are flagged for a doctor's review.",
     ["What is the health score?", "Which tests get a food plan?"]),
    ("health_score", ["what is the health score", "how is the health score calculated", "what does my score mean",
                      "why is my score low"],
     "The **health score** is the percentage of your results that are inside the healthy range. For example, 18 of 20 results in "
     "range gives 90. It is a quick overview, not a medical rating; read each result for the full picture.",
     ["What do low, borderline and high mean?"]),
    ("food_plan", ["how do i read the food plan", "what is the food plan", "why these foods", "why 8 foods",
                   "what does keep it healthy mean", "what are maintain plans"],
     'The foods in **1. Pick foods** are linked to your results:\n\n- **Improve plans** (up to 8 foods) are '
     'for results outside the range.\n- **Keep healthy plans** (4 foods) help keep normal results normal.\n- '
     'Each food shows how much of the key nutrient a normal serving gives, a cooking tip and why it '
     'helps.\n\nTap **Add to plan** on the foods you like, then **Build my diet plan**: your diet plan will '
     'include them.',
     ["Can I download my plan?", "How does NutriLens work?"]),
    ("pdf", ["can i download my plan", "how to download pdf", "can i print my plan",
             "download pdf not working"],
     'Yes, there are two PDFs, both in the language you have chosen (English, Hindi or Telugu):\n\n- '
     '**Download PDF** at the top of the results page: your results, your 7-day diet plan (if you made '
     "one), the food plans and what your results mean.\n- **PDF** inside the 7-day plan: just the week's "
     'meals and the shopping list, handy for the kitchen.',
     ["Where is my history?"]),
    ("history", ["where is my history", "how do i see old reports", "are my analyses saved", "how to view previous results",
                 "my report is not in history"],
     "If you are **signed in**, every analysis is saved to **History** (top menu), where you can open or delete it. "
     "As a guest, results are not saved; sign in before analysing to keep them.",
     ["Do I need an account?", "Is my data private?"]),
    ("account", ["do i need an account", "how do i sign up", "how to register", "how to create an account",
                 "can i use it without login", "how do i log in"],
     "You can analyse a report **without an account**. Create a free account with **Sign up** if you want your analyses saved "
     "to History.",
     ["Where is my history?", "I forgot my password"]),
    ("password", ["i forgot my password", "how to reset password", "cannot log in", "login not working",
                  "how do i change my password"],
     "- **Change password:** open **Account** from the top menu while signed in.\n"
     "- **Forgot password:** ask a NutriLens administrator to send you a password reset link. It lets you choose a new password.",
     ["How do I delete my account?"]),
    ("delete_account", ["how do i delete my account", "remove my account", "delete my data", "erase my information"],
     "Open **Account** from the top menu and choose **Delete account**. This permanently removes your account, saved "
     "history and assistant chats.",
     ["Is my data private?"]),

    # ---- Privacy & safety ----
    ("privacy", ["is my data private", "is my report safe", "do you store my report", "who can see my data",
                 "is my personal information shared", "do you sell my data", "is it secure", "is my data stored"],
     "Your privacy is protected:\n\n"
     "- **Personal details** such as your name and phone number are removed from the report text before it is analysed.\n"
     "- The uploaded file itself is **not stored**.\n"
     "- Results and assistant chats are saved only if you are signed in, and only you can see them. You can delete them "
     "at any time.\n"
     "- Your data is never sold or shared.",
     ["How do I delete my account?", "Is this a medical diagnosis?"]),
    ("diagnosis", ["is this a medical diagnosis", "can i trust this instead of a doctor", "is this medical advice",
                   "can this replace my doctor", "do i still need a doctor", "is nutrilens a doctor"],
     "No. NutriLens gives **general nutrition guidance** based on your report; it is not a diagnosis or a substitute for a doctor. "
     "Always discuss abnormal results, and any change to medicines, with a qualified doctor.",
     ["When should I see a doctor?", "How accurate is NutriLens?"]),
    ("see_doctor", ["when should i see a doctor", "is my result serious", "should i be worried", "when is a result dangerous",
                    "what results need a doctor"],
     "Please see a doctor if:\n\n"
     "- NutriLens shows a **\"Please review these results with a doctor\"** warning.\n"
     "- A result is far outside its range, or several results are abnormal.\n"
     "- You have symptoms such as chest pain, breathlessness, fainting, bleeding, yellow eyes or severe weakness. For these, get care **immediately**.",
     ["Is this a medical diagnosis?"]),
    ("accuracy", ["how accurate is nutrilens", "can i trust the results", "is the reading correct", "how reliable is it"],
     "In testing on real and sample Indian lab reports, NutriLens read **all 103 printed values correctly**, and every food plan "
     "respected the user's diet and allergies. Still, always glance at the values it read; you can edit anything before analysis.",
     ["Why was a value not read?", "Is this a medical diagnosis?"]),
    ("medicines", ["should i take supplements", "can i take iron tablets", "which vitamin d tablet should i take",
                   "how much vitamin d should i take", "can i stop my medicine", "should i take b12 injections",
                   "what dose should i take", "can i take calcium tablets"],
     "I can't advise on **medicines, supplements or doses**; that depends on your full health picture, so please ask your doctor. "
     "What I can do is suggest foods that are naturally rich in the nutrient you need.",
     ["Which foods are rich in iron?", "Which foods are rich in vitamin D?"]),
    ("pregnancy", ["i am pregnant", "is this plan safe in pregnancy", "can pregnant women use this", "diet during pregnancy",
                   "breastfeeding diet"],
     "NutriLens uses adult ranges and general food plans; it is **not tailored for pregnancy or breastfeeding**, when needs and "
     "normal ranges change. Please follow your obstetrician's advice. Folate, iron, calcium and protein are especially important at this time.",
     ["Which foods are rich in folate?", "Which foods are rich in iron?"]),
    ("children", ["can children use this", "is it for kids", "my child's report", "age limit", "is this for teenagers"],
     "NutriLens is designed for **adults**. Children's normal ranges and nutritional needs are different, so please discuss a "
     "child's report with a paediatrician.",
     ["Which tests are supported?"]),

    # ---- Everyday nutrition ----
    ("fasting_test", ["should i fast before a blood test", "do i need to fast", "can i drink water before blood test",
                      "fasting for lipid profile", "how long to fast before test", "empty stomach test"],
     "For **fasting glucose** and usually the **lipid profile**, fast for **8 to 12 hours** (water is fine). "
     "Post-meal glucose is taken about 2 hours after eating. Most other tests do not need fasting, but follow your lab's instructions.",
     ["How often should I repeat my tests?"]),
    ("retest", ["how often should i repeat my tests", "when should i test again", "how soon will my levels improve",
                "how long does it take to improve", "when to recheck"],
     "It depends on the test and your doctor's advice, but as a rough guide:\n\n"
     "- **Haemoglobin and iron:** about 2 to 3 months after changes.\n"
     "- **HbA1c:** every 3 months (it reflects 3 months of sugar).\n"
     "- **Vitamin D and B12:** about 3 months.\n"
     "- **Cholesterol:** 3 to 6 months after diet changes.",
     ["Should I fast before a blood test?"]),
    ("tiredness", ["i feel tired all the time", "why am i always tired", "constant fatigue", "feeling weak and tired",
                   "low energy all day", "which tests for tiredness", "i feel dizzy and weak"],
     "Feeling tired all the time has many possible causes. On a blood report, these are worth checking:\n\n"
     "- **Haemoglobin and ferritin** (anaemia and low iron)\n"
     "- **Vitamin B12 and vitamin D**\n"
     "- **TSH** (an underactive thyroid)\n"
     "- **HbA1c or fasting sugar**\n\n"
     "Upload your report and NutriLens will show which of these are out of range. If tiredness is severe, sudden or comes "
     "with breathlessness or weight loss, please see a doctor.",
     ["What foods help with low haemoglobin?", "What does low vitamin B12 mean?", "How do I upload my report?"]),
    ("hair_fall", ["hair fall", "why is my hair falling", "hair loss diet", "foods for hair growth", "which test for hair fall",
                   "hair falling a lot"],
     "Hair fall is often linked to things a blood report can show:\n\n"
     "- **Low iron or ferritin**\n"
     "- **Low vitamin D or vitamin B12**\n"
     "- **Thyroid problems** (TSH)\n"
     "- **Low protein** (total protein, albumin)\n\n"
     "Eating enough protein (dal, paneer, eggs, fish), iron-rich foods and greens helps. If hair fall is sudden or patchy, "
     "please see a doctor or dermatologist.",
     ["Which foods are rich in iron?", "Which foods are high in protein?"]),
    ("tea_iron", ["does tea affect iron", "can i drink tea after meals", "is coffee bad for health", "is tea bad for health",
                  "how many cups of tea a day", "coffee and iron absorption", "tea with food iron",
                  "what blocks iron absorption"],
     "Yes. Tea and coffee contain tannins that **reduce iron absorption**. Keep them at least **1 hour away** from iron-rich meals, "
     "and take vitamin C foods (lemon, amla, guava, orange) with meals to boost absorption instead.",
     ["Which foods are rich in iron?", "Which foods are rich in vitamin C?"]),
    ("iron_cooking", ["does cooking in iron pan help", "iron kadai", "how to absorb more iron",
                      "how to improve iron absorption", "tips to increase iron absorption"],
     "To absorb more iron:\n\n"
     "- Add **vitamin C** (lemon, amla, tomato, guava) to iron-rich meals.\n"
     "- Cooking in an **iron kadai or tawa** adds a little iron to food.\n"
     "- **Sprouting, fermenting and soaking** pulses and millets (sprouts, idli, dosa) make iron easier to absorb.\n"
     "- Keep **tea, coffee and calcium supplements** away from iron-rich meals.",
     ["Which foods are rich in iron?"]),
    ("sunlight", ["how much sunlight for vitamin d", "does sunlight give vitamin d", "best time for sunlight",
                  "can i get vitamin d from sun"],
     "Sunlight on bare skin makes vitamin D. About **15 to 30 minutes** on the arms and face, a few times a week, usually between "
     "about 10 am and 3 pm, helps many people. Darker skin needs a little longer. Avoid sunburn. Food sources and, if your doctor "
     "advises, supplements also help.",
     ["Which foods are rich in vitamin D?"]),
    ("water", ["how much water should i drink", "daily water intake", "is drinking water important"],
     "Most adults need about **2 to 3 litres of fluid a day**, more in hot weather or with exercise. Pale yellow urine is a good "
     "sign you're drinking enough. If you have kidney or heart problems, follow your doctor's fluid advice.",
     ["Which foods are good for uric acid?"]),
    ("healthy_plate", ["what is a healthy diet", "what should a balanced meal look like", "healthy indian diet",
                       "general diet tips", "how to eat healthy", "balanced diet", "healthy plate"],
     "A simple balanced Indian plate (based on ICMR-NIN guidance):\n\n"
     "- **Half the plate:** vegetables, greens and some fruit.\n"
     "- **A quarter:** whole grains or millets (roti, brown rice, ragi, jowar).\n"
     "- **A quarter:** protein (dal, rajma, chana, paneer, curd, eggs, fish or chicken).\n"
     "- Use a little oil, limit salt, sugar and fried snacks, and drink enough water.",
     ["Which foods are low GI?", "Which foods are high in protein?"]),
    ("weight", ["how to lose weight", "diet for weight loss", "how to reduce belly fat", "how to gain weight",
                "is my weight ok", "obesity diet"],
     'NutriLens adjusts your diet plan to your body: if your BMI is 25 or more, the daily calorie target '
     'is set about 15% lower (at most 500 kcal less); if it is under 18.5, about 10% higher. A few safe '
     'principles also help:\n\n- Fill half your plate with vegetables and add protein at each meal.\n- Choose '
     'millets and whole grains over refined flour.\n- Limit sugar, sweet drinks, fried snacks and '
     'late-night eating.\n- Aim for about 150 minutes of activity a week.\n\nFor a medical weight-loss '
     'programme, please consult a doctor or dietitian.',
     ["What is a healthy diet?", "Which foods are low GI?"]),
    ("exercise", ["how much exercise should i do", "does exercise help", "best exercise for health",
                  "exercise for cholesterol", "walking after meals"],
     "Adults should aim for about **150 minutes of moderate activity a week** (for example, a brisk 30-minute walk on 5 days), plus "
     "some strength exercise twice a week. A short walk after meals helps blood sugar. Check with your doctor before starting "
     "intense exercise if you have heart problems.",
     ["What is a healthy diet?"]),
    ("salt_bp", ["blood pressure diet", "how much salt should i eat", "high bp food", "hypertension diet",
                 "do you check blood pressure"],
     "NutriLens doesn't analyse blood pressure, but for healthy BP: keep salt under about **5 g a day** (one teaspoon in total), "
     "limit pickles, papad and packaged snacks, eat more vegetables, fruit and pulses, and stay active. Follow your doctor's advice "
     "if you take BP medicines.",
     ["What is a healthy diet?"]),
    ("sugar_intake", ["is sugar bad", "can i eat sweets", "how much sugar per day", "jaggery vs sugar",
                      "is honey better than sugar"],
     "Added sugar, including jaggery and honey, should stay **low**: ideally under about 25 g (5 teaspoons) a day. Jaggery and "
     "honey are not much healthier than sugar for blood sugar. Whole fruit is a better way to enjoy sweetness.",
     ["Which foods are low GI?", "What foods help with high HbA1c?"]),
    ("oils", ["which oil is best", "best cooking oil", "is ghee healthy", "how much oil should i use", "is coconut oil good"],
     "Use a **mix of oils** such as groundnut, mustard, rice bran or sesame, and keep the total to about **3 to 4 teaspoons per person a day**. "
     "Ghee, butter and coconut oil are high in saturated fat, so use them sparingly, especially if your cholesterol is high. "
     "Avoid vanaspati and reused frying oil.",
     ["Which foods help lower cholesterol?"]),
    ("millets", ["are millets healthy", "benefits of millets", "which millet is best", "ragi vs rice",
                 "should i eat millets"],
     "Millets such as **ragi, jowar, bajra, foxtail and little millet** are rich in fibre and minerals. Ragi is one of the best "
     "plant sources of calcium, and bajra is rich in iron. Most millets have a gentler effect on blood sugar than polished rice "
     "or maida.",
     ["Tell me about ragi", "Which foods are low GI?"]),
    ("alcohol_smoking", ["is alcohol bad for liver", "can i drink alcohol", "does smoking affect blood test",
                         "effect of alcohol on results", "should i quit smoking"],
     "Alcohol raises liver enzymes (especially GGT), triglycerides and uric acid, and smoking lowers HDL and raises heart risk. "
     "Cutting down or stopping both is one of the most effective changes you can make. Ask your doctor for support if you want to quit.",
     ["What foods help the liver?", "Which foods help lower cholesterol?"]),
    ("sleep_stress", ["does sleep affect health", "stress and blood sugar", "how does stress affect my report"],
     "Poor sleep and long-term stress can raise blood sugar, blood pressure and some inflammation markers. Aim for **7 to 8 hours** "
     "of sleep, regular meals and some daily activity.",
     ["What is a healthy diet?"]),
]

# The website, troubleshooting and more nutrition topics live in faq_site.py.
from app.chat.faq_site import EXTRA_PHRASINGS, FAQ_SITE  # noqa: E402

_ids = {entry[0] for entry in FAQ}
FAQ = [(fid, questions + EXTRA_PHRASINGS.get(fid, []), answer, follow) for fid, questions, answer, follow in FAQ]
FAQ += [(fid, questions + EXTRA_PHRASINGS.get(fid, []), answer, follow)
        for fid, questions, answer, follow in FAQ_SITE if fid not in _ids]
