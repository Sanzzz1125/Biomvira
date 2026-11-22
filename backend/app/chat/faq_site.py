"""More questions and answers: every part of the website, problems users run into, and everyday nutrition.

Same format as faq.py: (id, example phrasings, answer, follow-up suggestions). Facts here are taken from the app
itself (button names, limits, error messages) so the assistant always describes the real website.
"""

FAQ_SITE = [
    # ---- Getting a diet plan ----
    ("get_plan", ["steps to get my diet plan", "get a diet plan from my blood report", "diet plan from my report", "upload my report and get a diet plan", "how do i get my diet plan", "how to get a diet plan", "where is my food plan", "how to generate my plan",
                  "give me a diet plan", "make a diet plan for me", "i want a diet chart", "diet plan kaise milega",
                  "how can i get food suggestions", "how do i get personalised foods", "create my nutrition plan",
                  "how to see my food recommendations"],
     'To get your diet plan:\n\n- **Upload your blood report** (PDF or photo) or choose **Paste text**, then '
     'click **Analyse my report**.\n- In **Your profile**, enter age, sex, **height and weight**, your '
     'state and activity, diet type and allergies, then click **Generate my plan**.\n- On the results page, '
     '**1. Pick foods**: tap **Add to plan** on foods you like, then **Build my diet plan**.\n- In **2. '
     'Diet plan**, choose one of the three plan options and click **Make my 7-day plan**.\n\nDiet plans are '
     'for adults (18+). Height and weight are needed to work out your calories.',
     ["Which file types can I upload?", "Can I download my plan?", "What is the food plan?"]),
    ("no_report", ["i dont have a report", "can i get a plan without a blood test", "i have not done any test",
                   "can i use it without a report", "can i enter my values manually", "i only know my hemoglobin value",
                   "can i type my results", "no lab report available"],
     "You can still use Biomvira:\n\n"
     "- If you know some values, choose **Paste text** and type them one per line, for example \"Haemoglobin 11.2 g/dL\".\n"
     "- Or just ask me, for example \"What is a normal vitamin D level?\" or \"Foods for low iron\".\n\n"
     "For a full picture, a routine health check-up report works best.",
     ["What foods help with low haemoglobin?", "Which tests should I get done?"]),
    ("which_tests_to_do", ["which blood test should i do", "which tests should i get done", "what tests for a full body checkup",
                           "recommended health checkup tests", "what tests should i take for vitamins",
                           "basic blood tests everyone should do"],
     "A routine adult check-up commonly includes:\n\n"
     "- **CBC** (haemoglobin and blood counts)\n"
     "- **HbA1c** or fasting glucose\n"
     "- **Lipid profile** (cholesterol)\n"
     "- **Liver and kidney function tests**\n"
     "- **TSH** (thyroid)\n"
     "- **Vitamin D and vitamin B12**, and **ferritin** if you feel tired\n\n"
     "Your doctor can advise which ones you need. Biomvira reads all of these.",
     ["Which tests are supported?", "Should I fast before a blood test?"]),
    ("results_page", ["what is on the results page", "explain the results page", "how to read my results",
                      "i dont understand my results", "what does the results page show", "how to understand this report",
                      "where do i see my results"],
     'The results page is titled **Your personalised diet plan**:\n\n- **Health score** band: how many '
     'results are in range, with counts of low, borderline, optimal and elevated.\n- **Please review these '
     'results with a doctor:** only when a result needs medical attention.\n- **1. Pick foods:** Indian '
     'foods that help your results; tap **Add to plan** on the ones you like.\n- **2. Diet plan:** three '
     'one-day plan options, then your 7-day plan with swaps, shopping list and PDF.\n- **Test results:** '
     'every test with a bar showing where your value sits, and a plain-language explanation.\n\nYou can ask '
     'me about any part, for example "What does my vitamin D mean?"',
     ["Summarise my results", "What is the health score?", "Can I download my plan?"]),
    ("range_bar", ["what is the coloured bar", "what does the bar under each test mean", "what is the range slider",
                   "what does the marker on the bar show", "why is the bar red", "green bar meaning"],
     "Each test has a bar showing its healthy range. The marker shows where **your value** sits: in the green middle "
     "part means healthy, while towards either end means low or high. The label under it says how far your value is from the range.",
     ["What do low, borderline and high mean?"]),
    ("filter_results", ["how to see only abnormal results", "show only bad results", "what is needs attention filter",
                        "hide normal results", "filter my results"],
     "Above **Your Test Results**, switch from **All** to **Needs attention** to see only the results outside the healthy range.",
     ["Summarise my results"]),
    ("doctor_section", ["what does please review with a doctor mean", "why do i see a doctor warning",
                        "why does it say see a doctor", "what is the doctor review section", "red warning on results",
                        "why is my result marked for doctor"],
     "The **Please review these results with a doctor** section appears when a result is far outside its range or is a "
     "test that diet alone can't fix (such as thyroid, kidney or electrolyte results). It doesn't mean something is "
     "definitely wrong, but please show those results to a doctor soon.",
     ["When should I see a doctor?", "Why is there no food plan for thyroid?"]),
    ("dos_donts", ["what are the dos and donts", "what are the tips in my plan", "what is foods to limit",
                   "what are absorption tips", "why does the plan say avoid tea"],
     "Each food plan ends with practical **tips** (for example, add lemon to iron-rich meals) and **foods to limit** "
     "(for example, tea or coffee with meals, or sugary drinks). They come from ICMR-NIN and clinical nutrition guidance "
     "and help the foods work better.",
     ["Does tea affect iron?", "What is the food plan?"]),
    ("explanation", ["what is what your results mean", "what is the explanation section", "who wrote the explanation",
                     "is the explanation written by ai"],
     "**What Your Results Mean** explains your results in plain language: what each out-of-range test does in the body and "
     "how the food plan helps. It is built from checked medical and nutrition notes, not generated by an AI model.",
     ["How does Biomvira work?"]),
    ("portions", ["how much should i eat", "what is the serving size", "what does per 100 g mean", "how many grams per day",
                  "portion size of these foods", "how much ragi should i eat daily"],
     'In the **7-day plan**, every dish already has a household portion (for example 1 katori dal, 2 '
     'phulkas, 1 cup cooked rice), chosen so the day meets your calorie and protein targets. In **Pick '
     'foods**, each food shows the amount of the key nutrient in a normal serving. Mixing several foods '
     'works better than eating a lot of one.',
     ["What is a healthy diet?", "What is the food plan?"]),
    ("meal_plan", ["give me a weekly meal plan", "can you make a diet chart", "give me recipes", "7 day diet plan",
                   "what should i eat for breakfast lunch and dinner", "daily menu for me", "meal timetable",
                   "can you plan my meals"],
     'Yes. Biomvira builds day-by-day meal plans:\n\n- **Three one-day options:** *Familiar* (dishes from '
     'your region plus the foods you picked), *Most nutritious* (the most nutrients for your calories) and '
     '*Regional* (only dishes cooked in your state).\n- Choose one and click **Make my 7-day plan**: '
     'breakfast, lunch, evening snack and dinner for 7 days, varied across the week.\n- **Swap** any dish '
     "you don't like; the day is rebalanced and your other meals stay the same.\n- Get the week's "
     '**shopping list**, download it as a **PDF**, and (when signed in) **save** it with your report.',
     ["What should I eat?", "What is a healthy diet?"]),
    ("dont_like_food", ["i dont like these foods", "can i replace a food in my plan", "alternatives to these foods",
                        "i cannot find these foods", "suggest other foods", "these foods are not available near me"],
     "You don't have to eat every food in the plan. Pick the ones you like and can find; any of them helps. For more "
     "options, ask me, for example \"more iron foods\" or \"calcium foods without dairy\".",
     ["Which foods are rich in iron?", "Which foods are rich in calcium?"]),
    ("regional", ["south indian foods", "do you have north indian foods", "telugu food names", "local foods",
                  "foods from my state", "do you include regional foods"],
     'Yes. Diet plans use **276 home-style dishes** from every Indian state and union territory: for '
     'example pesarattu and gongura pachadi from Andhra and Telangana, sambar and kootu from Tamil Nadu, '
     'puttu and avial from Kerala, rajma and makki roti from Punjab, poha and thalipeeth from Maharashtra, '
     'machher jhol from Bengal and litti chokha from Bihar. Choose your state in your profile; the '
     "*Regional* plan uses only your state's dishes. Foods also show their common Indian names.",
     ["Where does the food data come from?", "Are millets healthy?"]),
    ("change_profile", ["i selected the wrong diet type", "how do i change my diet type", "i chose the wrong diet", "change my age after results",
                        "edit my profile after analysis", "i entered wrong gender", "change allergies after plan"],
     "On the results page, click **New analysis** and run the report again with the corrected profile. If you're still "
     "before the results, use **Back** to return to **Your profile**.",
     ["How do I set my allergies?", "Why do you need my diet type?"]),
    ("start_over", ["how to start again", "how do i analyse another report", "new analysis", "upload a different report",
                    "reset everything", "how to go back", "clear my results"],
     "Click **New analysis** on the results page to start over with another report. Before the results, the **Back** "
     "button takes you to the previous step.",
     ["How do I upload my report?"]),
    ("remove_row", ["how do i remove a test", "delete a wrong value", "remove a result from the list",
                    "a test was read twice", "duplicate result", "remove a row"],
     "In **View or edit results**, use **Remove** on the row you don't want. If the same test appears twice, keep the "
     "correct one and remove the other; Biomvira asks you to resolve duplicates before analysing.",
     ["How do I edit a value?"]),
    ("units", ["which units are supported", "my lab uses different units", "mmol l or mg dl", "nmol l vitamin d",
               "do you convert units", "lakhs platelets", "what unit should i choose"],
     "Biomvira understands the common units Indian labs use and **converts them automatically**: for example vitamin D "
     "in nmol/L or ng/mL, glucose in mmol/L or mg/dL, and platelets written in lakhs. When you edit a value, choose the "
     "unit exactly as it's printed on your report.",
     ["How do I edit a value?"]),
    ("multi_page", ["my report has many pages", "can it read all pages", "multi page pdf", "long report with 10 pages",
                    "only first page was read"],
     "Yes, every page of a PDF is read. If one page is an unclear picture, Biomvira tells you which page couldn't be "
     "read, so you can add those values by hand.",
     ["Why was a value not read?"]),
    ("multiple_files", ["upload multiple pdfs", "upload two pdf files", "can i upload two reports", "upload multiple files", "combine two reports", "upload many photos",
                        "two separate reports at once", "upload more than one file"],
     "Upload **one file at a time**. A multi-page PDF is fine. If your results are in two reports, either analyse each one "
     "separately, or choose **Paste text** and paste the values from both.",
     ["Can I paste text?", "Where are my reports?"]),
    ("password_pdf", ["my pdf has a password", "locked pdf", "encrypted report", "pdf asks for password",
                      "protected pdf cannot upload"],
     "Password-protected PDFs can't be read. Open it with its password and save or print it as a new PDF without a "
     "password, or take a clear photo of the pages, or copy the values with **Paste text**.",
     ["Which file types can I upload?"]),
    ("handwritten", ["can it read handwritten reports", "handwritten values", "doctor wrote the values by hand",
                     "my report is handwritten"],
     "Biomvira is built for **printed** lab reports. Handwriting can't be read reliably, so please type those values using **Paste text**.",
     ["Can I paste text?"]),
    ("photo_tips", ["how to take a good photo", "photo is blurry", "image not clear", "tips for scanning report",
                    "what photo quality is needed"],
     "For a photo that reads well:\n\n"
     "- Use good light, without shadows or glare.\n"
     "- Keep the page flat and fill the frame with it.\n"
     "- Hold the phone steady so the numbers are sharp.\n"
     "- Take one photo per page.",
     ["Which file types can I upload?"]),
    ("ocr_error", ["ocr timed out", "it says ocr failed", "report processing failed", "taking too long to read",
                   "stuck on reading report", "no readable laboratory text found", "could not read this report",
                   "report processor is busy", "upload is not working", "error while uploading"],
     "This happens when a report is hard to read, for example a large scanned PDF or a blurry photo. Try one of these:\n\n"
     "- Upload the **original PDF** from the lab instead of a scan, if you have it.\n"
     "- Upload a **clearer or smaller** file (one page at a time works too).\n"
     "- Choose **Paste text** and type or paste the values.\n\n"
     "If it says the processor is busy, wait a few seconds and try again.",
     ["How to take a good photo?", "Can I paste text?"]),
    ("file_error", ["file type not supported", "mime type does not match", "file content is not a pdf", "wrong file format",
                    "image is corrupted", "file exceeds upload size limit", "can i upload word file", "can i upload docx",
                    "heic photo not working"],
     "Biomvira accepts **PDF, JPG, JPEG and PNG** files up to **10 MB**. If you get a file error:\n\n"
     "- Make sure the file really is one of these types (a renamed file is rejected).\n"
     "- For iPhone HEIC photos or Word files, save or export them as JPG or PDF first.\n"
     "- For a very large file, upload fewer pages or a smaller photo.",
     ["Which file types can I upload?"]),
    ("site_slow", ["website is slow", "page is not loading", "taking long to load", "site not opening", "it keeps loading",
                   "nothing happens when i click", "server error", "something went wrong"],
     "Please wait a few seconds and try again. The first request after a quiet period can take a little longer. If it still "
     "doesn't work, refresh the page and check your internet connection.",
     ["How do I upload my report?"]),
    ("badges", ["what does ai assisted mean", "what does added by you mean", "what does edited mean",
                "what does outside reference range mean in review", "what is the source column"],
     "In the review list, small labels show where each value came from:\n\n"
     "- **Edited:** you changed the value.\n"
     "- **Added by you:** you entered the test yourself.\n"
     "- **AI-assisted:** read by an optional AI helper; please check it carefully.\n"
     "- **Outside reference range:** the value is outside the range printed on your report.",
     ["Why do I have to review results?"]),
    ("all_normal", ["why is there no food plan", "i did not get any food plan", "my plan is empty",
                    "all my results are normal", "no foods suggested"],
     "If all your results are in range, you won't get an **improve** plan, which is good news. You'll still see "
     "**Keep Your Healthy Results Healthy**, with a few foods to keep nutrient-linked results where they are.",
     ["What is a healthy diet?", "Which tests get a food plan?"]),
    ("plan_changed", ["my food plan changed", "why is my plan different from last time", "why did my foods change", "different foods each time",
                      "plan changed after editing"],
     "The plan depends on your results and profile. If a value, your diet type or your allergies change, the foods change "
     "too. For the same report and profile, the plan is always the same.",
     ["How are foods chosen?"]),
    ("wrong_food", ["why did it suggest a food i cannot eat", "it suggested milk but i am vegan",
                    "it showed fish but i am vegetarian", "recommended food i am allergic to"],
     "Foods are filtered by the diet type and allergies you chose in **Your profile**. Please check those settings, then "
     "click **New analysis** to rebuild the plan. Only six allergy groups are supported (dairy, gluten, nuts, soy, eggs, "
     "seafood), so please skip any other food you can't eat.",
     ["How do I set my allergies?", "How do I change my diet type?"]),
    ("other_allergy", ["i am allergic to mustard", "sesame allergy", "can i exclude a specific food",
                       "my allergy is not in the list", "allergic to banana"],
     "Biomvira can exclude **dairy, gluten, nuts, soy, eggs and seafood**. For any other allergy, please skip that food "
     "in your plan; there are always other options to choose from.",
     ["How do I set my allergies?"]),
    ("jain", ["jain diet", "no onion no garlic", "i dont eat root vegetables", "satvik diet", "fasting food navratri"],
     "Choose **Vegetarian** as your diet type. Biomvira doesn't have a separate Jain option yet, so simply skip any root "
     "vegetables, onion or garlic in your plan; there are plenty of other foods, such as millets, dals, greens and fruits.",
     ["Why do you need my diet type?"]),
    ("sex_option", ["why only male and female", "other gender option", "i am non binary", "which sex should i choose"],
     "Sex is used only because labs print different reference ranges for some tests, such as haemoglobin. Please choose "
     "the option that matches the ranges your lab used for you.",
     ["Why do you need my age?"]),

    # ---- History, PDF, sharing ----
    ("history_compare", ["can i compare my reports", "track my progress", "see if my levels improved",
                         "compare old and new results", "trend of my vitamin d"],
     "Sign in and every analysis is saved in **My reports** (the menu under your name at the top right), newest first. Open two reports to compare your values over time. "
     "This is a good way to see whether your food changes are working.",
     ["Where are my reports?", "How often should I repeat my tests?"]),
    ("old_pdf", ["download an old report", "get pdf of previous analysis", "pdf from history", "reprint old plan"],
     "Open **My reports** from the menu under your name at the top right, click the report you want, and use **Download PDF** on that page.",
     ["Where are my reports?"]),
    ("share_doctor", ["how do i share my report with my doctor", "send my plan to doctor", "share with family",
                      "email my report", "whatsapp my plan", "share results"],
     "Click **Download PDF** on the results page, then share the PDF file however you like: email, WhatsApp or print. "
     "Biomvira doesn't send emails itself.",
     ["Can I download my plan?"]),
    ("export_formats", ["download as excel", "export csv", "can i get word file", "other download formats"],
     "Your plan can be downloaded as a **PDF**. Other formats aren't available.", ["Can I download my plan?"]),
    ("data_retention", ["how long do you keep my data", "when is my data deleted", "do you keep reports forever",
                        "how long are reports saved"],
     "Saved analyses and their assistant chats stay in your account until you delete them or delete your account. "
     "Guest analyses and chats aren't saved at all, and the uploaded file itself is never stored.",
     ["How do I delete my account?", "Is my data private?"]),
    ("delete_report", ["delete my old report", "how to delete one report", "remove a report from history", "delete an old analysis"],
     "Open **My reports** (the menu under your name at the top right) and choose **Delete** on the report, then confirm. Its assistant chats are deleted too. This can't "
     "be undone.",
     ["Where are my reports?"]),

    # ---- Account ----
    ("guest", ["using biomvira as a guest", "what happens if i do not log in", "what is guest mode", "continue as guest", "use without signing in", "difference between guest and account",
               "why sign up"],
     "As a **guest** you can analyse reports and download the PDF, but results aren't saved. With a free **account**, "
     "every analysis is saved in **My reports** so you can come back to it and track changes.",
     ["How do I sign up?"]),
    ("password_rules", ["password requirements", "my password is not accepted", "what password should i use",
                        "password rules", "password too weak"],
     "Your password needs **at least 8 characters, including a letter and a number**.",
     ["I forgot my password"]),
    ("email_exists", ["email already exists", "account with this email already exists", "cannot register with my email",
                      "it says try logging in"],
     "An account already uses that email. Choose **Log in** instead. If you've forgotten the password, ask an administrator for a reset link.",
     ["I forgot my password"]),
    ("reset_link", ["did not get the reset link", "reset link not working", "reset link expired", "invite link expired", "this link cant be used",
                    "how long is the reset link valid"],
     "Password reset and invite links work for **48 hours** and only once. If yours has expired or was already used, "
     "ask the administrator for a new link.",
     ["I forgot my password"]),
    ("session", ["how long do i stay logged in", "why was i logged out", "logged out automatically",
                 "session expired", "keep me signed in"],
     "For your safety you are signed out after **2 hours** without using Biomvira, and after **1 day** at most. Changing your password signs you out on your other devices.",
     ["How do I log in?"]),
    ("logout", ["how do i log out", "sign out", "logout button"],
     "Open the menu with your name at the top right and choose **Log out**.", ["How do I delete my account?"]),
    ("change_name_email", ["how do i change my name", "change my email", "update my profile name", "edit account details"],
     "Open **Account** from the menu with your name. You can change your **name** and **password** there. To change your "
     "email, please ask an administrator.",
     ["How do I change my password?"]),
    ("too_many_attempts", ["too many attempts", "it says wait a minute", "blocked from login", "login locked"],
     "For your security, logins are paused briefly after several attempts. Please wait a minute and try again.",
     ["I forgot my password"]),
    ("disabled", ["my account is disabled", "account blocked", "cannot access my account disabled"],
     "A disabled account can't sign in. Please contact a Biomvira administrator to have it reactivated.",
     ["I forgot my password"]),
    ("admin", ["what is the admin panel", "how do i become admin", "who is the administrator", "admin invite",
               "what can admins do"],
     "Administrators manage user accounts: for example sending password reset links or disabling accounts. Admin access "
     "is given only by invitation from the Biomvira owner. Regular users don't need it.",
     ["How do I change my password?"]),

    # ---- Website basics ----
    ("mobile", ["does it work on mobile", "is there an app", "android app", "iphone app", "download the app",
                "can i use it on my phone", "play store"],
     "Biomvira is a **website** that works on phones, tablets and computers. There's no separate app to install; just "
     "open the site in your phone's browser. You can upload a photo of your report straight from your phone.",
     ["How do I upload my report?"]),
    ("browser", ["which browser should i use", "does it work on safari", "chrome or firefox", "browser support"],
     "Any up-to-date browser works: Chrome, Safari, Edge or Firefox, on phone or computer.", ["Does it work on mobile?"]),
    ("language", ["is hindi supported", "can i use telugu", "other languages", "language options",
                  "can you answer in hindi", "regional language support"],
     'Yes. Biomvira works in **English, हिन्दी (Hindi) and తెలుగు (Telugu)**. Use the language button at '
     'the top of the page. The whole website, your results, your diet plan and both PDFs switch to that '
     'language.',
     ["What is Biomvira?"]),
    ("internet", ["does it work offline", "do i need internet", "can i use without internet"],
     "Yes, you need an internet connection, because reports are analysed on the Biomvira server.", ["Is my data private?"]),
    ("security", ["is the website secure", "is my password safe", "do you encrypt data", "is it https",
                  "can someone hack my account"],
     "The site uses **HTTPS**, passwords are stored only as secure hashes (never in plain text), and your saved reports can "
     "be seen only from your own account. Use a password you don't use elsewhere.",
     ["Is my data private?"]),
    ("cookies_ads", ["do you use cookies", "are there ads", "do you track me", "analytics tracking", "do you show advertisements"],
     "There are **no ads and no tracking**. Biomvira uses only the cookies needed to keep you signed in securely.",
     ["Is my data private?"]),
    ("contact", ["how do i contact you", "customer care number", "report a bug", "give feedback", "support email",
                 "i found a problem", "help desk"],
     "For account problems, please contact a Biomvira administrator. If something on the site isn't working, refresh the "
     "page and try again, and let the Biomvira team know what you were doing when it happened.",
     ["What is Biomvira?"]),
    ("who_for", ["can doctors use biomvira", "who is biomvira for", "who can use this", "is it for patients", "can doctors use it",
                 "is it for everyone"],
     "Biomvira is for **adults in India** who have a blood test report and want to understand it and eat better. Doctors "
     "and dietitians can also use the PDF as a starting point for a conversation.",
     ["Is this a medical diagnosis?"]),
    ("foreign_report", ["report from outside india", "usa lab report", "uk report", "does it work for foreign labs"],
     "It usually works if the report is in English and uses common units. Food suggestions are Indian foods.",
     ["Which file types can I upload?"]),
    ("old_report", ["is a year old report ok", "can i upload an old report", "report from last year", "does report date matter"],
     "Yes, you can analyse any report. For decisions about your health today, a recent report is best.",
     ["How often should I repeat my tests?"]),
    ("unsupported_reports", ["can i upload urine test", "x ray report", "ecg report", "ultrasound report",
                             "can it read scan reports", "stool test", "mri report"],
     "Biomvira reads **blood test** reports only. Urine, stool, X-ray, ECG, ultrasound and other scan reports aren't supported.",
     ["Which tests are supported?"]),
    ("other_features", ["dark mode", "can you send reminders", "notifications", "connect to google fit",
                        "book a doctor appointment", "talk to a nutritionist", "video consultation"],
     "That isn't available. Biomvira focuses on one job: turning your blood report into clear results and an Indian food plan.",
     ["What is Biomvira?"]),
    ("calories_bmi", ["calorie counter", "how many calories should i eat", "calculate my bmi", "what is my bmi",
                      "calorie plan"],
     'Biomvira works out your **daily calorie and protein targets** from your age, sex, height, weight '
     'and activity (the ICMR-NIN 2020 method: FAO/WHO/UNU equations, about 10% lower for Indian adults, times your activity level). If your BMI is 25 or more the target is about 15% '
     'lower, and under 18.5 about 10% higher. Each day of your diet plan shows its calories and protein '
     'next to your targets, plus the nutrients your report shows as low.',
     ["How to lose weight?"]),
    ("chatbot", ["are my chats saved", "where are my old chats", "how do i delete a chat", "continue my previous chat",
                 "how does this chatbot work", "do you store my chats", "is this chat private", "are you chatgpt",
                 "how do you know the answers", "is this chatbot accurate"],
     "I answer from Biomvira's **checked knowledge** of blood tests, Indian foods and the website, plus your own results "
     "when they're on screen. I don't make things up: if I don't know something, I'll say so.\n\n"
     "- **Signed in:** your chats are saved to your account. A chat started from a report is saved with that report, so "
     "opening the report again continues it. Find older chats under **Past chats**.\n"
     "- **Guest:** chats aren't saved; they stay in this browser tab only.",
     ["What can you do?"]),
    ("unsupported_test", ["is zinc supported", "can you read magnesium", "vitamin a test", "psa test", "cortisol",
                          "testosterone level", "insulin test", "homocysteine", "hbsag", "lipase amylase"],
     "That test isn't one of the **61 tests** Biomvira reads yet, so please discuss it with your doctor. Biomvira covers "
     "blood count, iron studies, vitamins D, B12 and folate, calcium, blood sugar, cholesterol, liver, kidney, thyroid, "
     "electrolytes and CRP.",
     ["Which tests are supported?"]),

    # ---- Everyday nutrition ----
    ("protein_need", ["how much protein do i need", "daily protein requirement", "protein per day",
                      "how many grams of protein"],
     "Indian guidelines (ICMR-NIN) suggest about **0.8 to 1 g of protein per kg of body weight a day** for healthy adults, "
     "for example around 50 to 60 g for a 60 kg adult. Dals, pulses, milk, curd, paneer, eggs, fish and chicken are good "
     "sources. If you have kidney disease, follow your doctor's advice.",
     ["Which foods are high in protein?"]),
    ("calcium_need", ["how much calcium per day", "daily calcium requirement", "calcium needed daily"],
     "Adults need about **1,000 mg of calcium a day** (ICMR-NIN). Milk, curd, paneer, ragi, sesame seeds and leafy greens "
     "are good sources, and vitamin D helps you absorb it.",
     ["Which foods are rich in calcium?"]),
    ("vitd_need", ["how much vitamin d per day", "daily vitamin d requirement"],
     "Adults need about **600 IU of vitamin D a day** (ICMR-NIN). Very few foods contain much, so safe sunlight matters. "
     "If your level is low, your doctor may advise a supplement.",
     ["How much sunlight for vitamin D?", "Which foods are rich in vitamin D?"]),
    ("fruits_diabetes", ["which fruits are good for diabetes", "can diabetics eat fruits", "best fruits for sugar patients",
                         "is mango ok for diabetes", "fruits to avoid in diabetes"],
     "Whole fruits are fine in **moderate portions**. Guava, apple, orange, pear, papaya, jamun and amla have a gentler effect "
     "on blood sugar. Keep very sweet fruits such as mango, chikoo and grapes to small portions, and avoid fruit juices.",
     ["Which foods are low GI?", "What foods help with high HbA1c?"]),
    ("nuts_daily", ["how many nuts per day", "are nuts fattening", "almonds daily", "walnuts benefits",
                    "which nuts are best"],
     "A small handful (about **20 to 30 g**) of nuts or seeds a day is a healthy amount. Almonds, walnuts, peanuts and "
     "flaxseeds give healthy fats and fibre. Choose unsalted and unfried.",
     ["Which foods help lower cholesterol?"]),
    ("eggs_cholesterol", ["how many eggs can i eat in a day", "are eggs bad for cholesterol", "how many eggs a day", "egg yolk cholesterol",
                          "can i eat eggs daily"],
     "For most healthy adults, **one egg a day** fits a healthy diet. If your LDL cholesterol is high, keep to a few whole "
     "eggs a week and use egg whites more often, and follow your doctor's advice.",
     ["Which foods help lower cholesterol?"]),
    ("intermittent_fasting", ["is intermittent fasting good", "keto diet", "is keto safe", "low carb diet",
                              "should i skip meals", "fasting diet"],
     "Popular diets such as keto or intermittent fasting don't suit everyone, especially people with diabetes, low "
     "haemoglobin or kidney problems. Regular, balanced meals are the safest base. Please check with your doctor before a "
     "major diet change.",
     ["What is a healthy diet?"]),
    ("gym", ["diet for gym", "muscle gain diet", "is whey protein safe", "protein powder", "bodybuilding food"],
     "For muscle gain, spread protein through the day: dal, paneer, curd, soy, eggs, fish or chicken, along with enough "
     "carbohydrate and regular strength training. Protein powders are supplements, so check with a doctor first, especially "
     "if your creatinine or kidney results are abnormal.",
     ["Which foods are high in protein?", "How much protein do I need?"]),
    ("sprouts", ["are sprouts healthy", "benefits of sprouts", "how to make sprouts", "sprouted moong"],
     "Sprouting moong, chana or other pulses makes iron and other minerals easier to absorb and adds vitamin C. Eat them "
     "lightly steamed or in a chaat with lemon, which helps iron absorption further.",
     ["Which foods are rich in iron?"]),
    ("night_food", ["what to eat at night", "dinner for diabetes", "late night snacks", "light dinner ideas"],
     "Keep dinner light and early: for example a millet roti or a small portion of rice with dal and vegetables, or a bowl of "
     "khichdi with curd. Avoid heavy, fried or sugary foods late at night.",
     ["What is a healthy diet?"]),
    ("snacks", ["healthy snacks", "evening snacks ideas", "snacks for diabetes", "what to eat when hungry"],
     "Healthy Indian snacks: roasted chana, sprouts chaat, a fruit, a handful of nuts, buttermilk, makhana, or vegetable "
     "upma or poha. Limit biscuits, namkeen, samosas and sweets.",
     ["Which foods are low GI?"]),
    ("vegetarian_b12", ["how can vegetarians get b12", "b12 for vegetarians", "pure veg b12 sources"],
     "Vegetarians get vitamin B12 mainly from **milk, curd, paneer and cheese**, plus fortified foods. Vegans need "
     "fortified foods or a supplement advised by a doctor, because plants don't naturally contain B12.",
     ["Which foods are good for vitamin B12?"]),
    ("iron_women", ["iron for women", "iron during periods", "women anemia diet", "heavy periods iron"],
     "Women need more iron than men because of monthly blood loss. Eat iron-rich foods (greens, dals, millets such as bajra, "
     "garden cress seeds, jaggery in small amounts) with vitamin C, and keep tea away from meals. Heavy periods should be "
     "checked by a doctor.",
     ["Which foods are rich in iron?", "Does tea affect iron?"]),
    ("elderly", ["diet for old age", "senior citizen diet", "elderly nutrition", "diet for parents above 60"],
     "Older adults especially need enough **protein, calcium, vitamin D and vitamin B12**, plus fibre and water. Soft, "
     "easy-to-chew foods such as dal, curd, khichdi, ragi porridge and cooked greens work well.",
     ["Which foods are rich in calcium?", "How much protein do I need?"]),
    ("hydration_drinks", ["is green tea healthy", "is coconut water good", "is buttermilk healthy", "best drinks", "soft drinks",
                          "is fruit juice healthy", "energy drinks"],
     "Water, buttermilk, coconut water and lemon water (without much sugar) are good choices. Limit soft drinks, packaged "
     "juices and energy drinks, which are high in sugar. People with kidney problems should check with their doctor about "
     "coconut water.",
     ["How much water should I drink?"]),
    ("processed_food", ["is maida bad", "junk food effects", "is bread healthy", "packaged food", "instant noodles"],
     "Refined flour (maida), white bread, instant noodles and packaged snacks are low in fibre and nutrients and often high "
     "in salt, sugar or fat. Keep them occasional and choose whole grains, millets and home-cooked food more often.",
     ["Are millets healthy?", "What is a healthy diet?"]),
    ("cooking_methods", ["healthy cooking methods", "is frying bad", "air fryer", "steaming vs boiling",
                         "how to cook vegetables to keep nutrients"],
     "Steaming, pressure-cooking, light sautéing and roasting keep more nutrients than deep frying. Don't overcook greens, "
     "use the cooking water in dals or soups, and avoid reusing frying oil.",
     ["Which oil is best?"]),

    # ---- Diet plans (added with the 7-day planner) ----
    ("plan_styles", ["what are the three plan options", "difference between familiar and regional plan",
                     "what is most nutritious plan", "which plan should i choose", "familiar vs nutritious",
                     "what is the regional plan"],
     "The three one-day options are built for the same targets:\n\n"
     "- **Familiar:** dishes from your region plus the foods you picked, the easiest to follow.\n"
     "- **Most nutritious:** the most nutrients for your calories, good when several results are low.\n"
     "- **Regional:** only dishes cooked in your state.\n\n"
     "Pick the one you like and click **Make my 7-day plan**.",
     ["How do I swap a dish?", "Can I get a shopping list?"]),
    ("swap_dish", ["how do i swap a dish", "i dont like this dish", "change a dish in my plan", "replace a food in the plan",
                   "can i change my meals", "remove a dish from the plan"],
     "In your 7-day plan, click **Swap** next to any dish. Biomvira picks a different dish for that meal, rebalances "
     "the day so it still meets your targets, and keeps your other meals the same.",
     ["Can I get a shopping list?", "Can I save my diet plan?"]),
    ("shopping_list", ["can i get a shopping list", "grocery list for the week", "what should i buy",
                       "how much to buy for the week", "shopping list"],
     "Yes. In your 7-day plan, click **Shopping list**. It adds up every ingredient for the week, with weights as "
     "bought (before peeling and cleaning), and it is included in the plan PDF.",
     ["Can I download my plan?", "Can I save my diet plan?"]),
    ("save_plan", ["can i save my diet plan", "how to save the 7 day plan", "where is my saved plan",
                   "will my diet plan be saved"],
     "When you are **signed in**, click **Save with my report** in your 7-day plan. Opening that report from "
     "**My reports** later shows the saved plan. Guests can download the plan as a PDF instead.",
     ["Where are my reports?", "Can I download my plan?"]),
    ("pick_foods", ["how do i add foods to my plan", "what is add to plan", "can i choose my own foods",
                    "how to include a food in diet plan", "pick foods", "update my diet plan"],
     "In **1. Pick foods**, tap **Add to plan** on the foods you like, then click **Build my diet plan** (or **Update "
     "my diet plan** if you already made one). The plan builds around those foods while still meeting your targets.",
     ["What are the three plan options?", "How do I swap a dish?"]),
    ("plan_not_showing", ["diet plan not showing", "build my diet plan button disabled", "why cant i get a diet plan",
                          "plan not building", "no diet plan for me", "diet plan error"],
     "Diet plans need two things:\n\n"
     "- **Age 18 or over:** plans are for adults.\n"
     "- **Height (120 to 220 cm) and weight (30 to 200 kg):** used to work out your calories. If you skipped them, "
     "enter them in the **2. Diet plan** tab and click **Build my diet plans**.\n\n"
     "If you see *Plan not built*, click **Try again**; the server may have been waking up.",
     ["How do I get my diet plan?", "What are the three plan options?"]),
    ("plan_targets", ["how are my calories calculated", "what are the targets in my plan", "why this many calories",
                      "how much protein is in my plan", "what does target mean in my plan", "calorie target"],
     "Each plan day shows **calories** and **protein** next to your targets, and the nutrients your report shows as low "
     "(for example iron or vitamin B12) next to the recommended amount. Calories come from your age, sex, height, "
     "weight and activity (the ICMR-NIN 2020 method, adjusted for BMI); protein and nutrient targets come from the "
     "ICMR-NIN 2020 recommended amounts.",
     ["How is the diet decided?", "Is this a weight-loss plan?"]),
    ("non_veg_meats", ["i eat only chicken", "choose which meats", "i dont eat beef", "fish only non veg",
                       "can i exclude pork", "custom allergy", "i dont like a food"],
     "In **Your profile**, choose **Non-vegetarian** and tick the meats you eat (for example chicken, fish, eggs, mutton); "
     "the others are never used. Biomvira does not use beef or pork in any dish. You can also type foods you are allergic to or don't eat, and dishes containing them "
     "are left out.",
     ["How do I get my diet plan?", "Which diets are supported?"]),
    ("plan_children", ["can my 15 year old use the diet plan", "diet plan for children", "plan for my kid",
                       "is the diet plan for teenagers", "diet plan for a child"],
     "The diet plans are made for **adults (18 and over)**, because children's calorie and nutrient needs change "
     "with growth. You can still read a child's test results and the foods that help, but please ask a paediatrician "
     "or dietitian for a child's meal plan.",
     ["How do I get my diet plan?", "Which tests are supported?"]),
    ("dish_count", ["how many dishes are there", "how many recipes do you have", "how many dishes in the planner",
                    "is my favourite dish there", "list of dishes"],
     "The planner uses **276 home-style dishes** from every Indian state and union territory: breakfasts, rice and "
     "roti, dals, curries, chutneys, snacks, drinks and a few sweets. Each dish's nutrients are calculated from its "
     "raw ingredients using the Indian Food Composition Tables. Choose your state in your profile to see your "
     "region's dishes more often.",
     ["What are the three plan options?", "Do you have South Indian foods?"]),
]

# Extra phrasings for topics defined in faq.py.
EXTRA_PHRASINGS = {
    "about": ["what is the use of this app", "what is this website for", "explain biomvira", "what does biomvira mean", "introduce yourself biomvira"],
    "upload": ["how to upload", "where to upload report", "upload steps", "how to upload pdf", "how to use the site",
               "how do i use biomvira", "guide me how to use", "first time user what to do", "report kaise upload kare"],
    "file_types": ["can i upload png", "does it accept pdf", "supported file formats", "max file size",
                   "can i upload screenshot", "can i take a photo of the report with my phone"],
    "not_read": ["values are wrong", "my hemoglobin value is wrong", "it missed some tests", "results are incorrect",
                 "reading mistake"],
    "review_step": ["why am i asked to check values", "what is review results page", "do i need to review every value"],
    "edit_values": ["add a test manually", "enter a value myself", "can i edit results", "fix a value", "change a unit", "add missing test"],
    "statuses": ["what does optimal mean", "what does elevated mean", "low vs high meaning", "what do red and green mean"],
    "health_score": ["what is score", "health score meaning", "2 of 4 results meaning"],
    "pdf": ["download report", "save as pdf", "print my report", "pdf download failed"],
    "history": ["my reports", "my saved reports list", "previous reports", "where are my old reports", "see my old results", "where are my reports saved"],
    "account": ["create account", "sign up", "register account", "is login required", "do i have to log in"],
    "password": ["forgot my password", "reset password", "password reset", "change password"],
    "delete_account": ["delete everything about me", "delete all my data"],
    "privacy": ["is my report shared", "who sees my report", "is my health data safe", "data privacy",
                "do you share data with anyone", "what happens to my report after upload"],
    "diagnosis": ["are you a doctor", "can you diagnose me", "is this medical advice or not"],
    "medicines": ["should i take vitamin d supplement", "iron supplement dose", "which multivitamin is best"],
    "is_free": ["free or paid", "any hidden charges", "do i need to pay for pdf"],
    "supported_tests": ["what tests are supported", "list of tests", "which blood tests can you read",
                        "what all can you analyse", "does it read cbc", "does it read lipid profile"],
    "retest": ["when should i recheck my blood test", "when to repeat blood test", "how often to do blood test",
               "how often should i get tested", "retest after how many months"],
    "sugar_intake": ["are sweeteners safe", "is sugar free ok for diabetes", "can i use stevia"],
    "healthy_plate": ["what should i eat daily", "healthy food habits", "daily diet for good health"],
}

EXTRA_PHRASINGS.update({
    "regional": ["do you have bengali food", "do you have punjabi dishes", "dishes from my state", "gujarati food",
                 "kerala dishes", "north east food", "maharashtrian dishes", "bihari food", "tamil food"],
    "non_veg_meats": ["i only eat chicken and fish", "i eat chicken but not mutton", "which meats can i choose"],
    "portions": ["what is a katori", "how big is a katori", "what does 1 katori mean", "what does serving mean in my plan"],
    "plan_targets": ["how is protein target calculated", "protein target in my plan", "how much protein in my diet plan",
                     "what is the calorie target in my plan"],
    "meal_plan": ["does the plan include snacks", "what meals are in the plan", "does it have breakfast lunch dinner"],
    "pdf": ["can i print the 7 day plan", "download diet plan pdf", "print shopping list", "download my weekly plan"],
    "language": ["why is my plan in english", "results still in english", "how to change language to telugu",
                 "pdf in telugu", "report in hindi"],
    "results_page": ["how do i see my test results", "where are my test results", "where is the test results tab"],
})
