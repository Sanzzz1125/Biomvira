"""Plain-language notes for every supported test: what it measures, and what a low or high result usually means.

Written for patients, checked against standard laboratory and clinical references. They describe common causes only;
the chatbot always points users to a doctor for a diagnosis.
"""

_DIFF = "{name} are a type of white blood cell. The report shows them as a percentage of all white cells and, on some reports, as an absolute count."

TEST_INFO = {
    "vitamin_d": (
        "Vitamin D (25-OH) shows how much vitamin D your body has stored. Vitamin D is made in the skin from sunlight and helps you absorb calcium for strong bones and muscles.",
        "Low vitamin D is very common in India. It can cause bone pain, muscle weakness and tiredness. Safe sunlight, vitamin D foods and, if your doctor advises, supplements help.",
        "High vitamin D almost always comes from taking too many supplements. It can raise blood calcium, so stop extra supplements and check with your doctor.",
    ),
    "vitamin_b12": (
        "Vitamin B12 keeps your nerves healthy and helps make red blood cells. It comes mainly from animal foods such as milk, curd, eggs, fish and meat.",
        "Low B12 can cause tiredness, tingling or numbness in hands and feet, poor memory and anaemia. It is common in vegetarians and vegans.",
        "High B12 is usually from supplements or injections and is rarely a problem. If you take none, mention it to your doctor, as it can sometimes point to liver or blood conditions.",
    ),
    "folate": (
        "Folate (vitamin B9) helps make new cells and red blood cells. It is especially important before and during pregnancy.",
        "Low folate can cause anaemia with large red cells, tiredness and mouth ulcers. Leafy greens, pulses and fruits are good sources.",
        "High folate usually comes from supplements and is rarely harmful, but it can hide a vitamin B12 deficiency, so keep B12 in mind.",
    ),
    "ferritin": (
        "Ferritin shows how much iron your body has stored. It is the earliest sign of iron deficiency, often falling before haemoglobin does.",
        "Low ferritin means your iron stores are running out, even if haemoglobin is still normal. Iron-rich foods eaten with vitamin C help refill them.",
        "High ferritin can come from infection, inflammation, fatty liver, alcohol or too much stored iron. A doctor should find the reason.",
    ),
    "hemoglobin": (
        "Haemoglobin is the protein in red blood cells that carries oxygen around your body.",
        "Low haemoglobin is called anaemia. It can cause tiredness, breathlessness, pale skin and dizziness. In India it is most often due to low iron, and sometimes low B12 or folate.",
        "High haemoglobin can come from dehydration, smoking, living at high altitude, or some lung, heart or bone marrow conditions.",
    ),
    "calcium": (
        "Serum calcium measures calcium in your blood. Calcium is needed for bones, teeth, muscles, nerves and the heart.",
        "Low calcium is often linked to low vitamin D or low albumin. It can cause cramps and tingling. Calcium-rich foods and vitamin D help.",
        "High calcium can come from too many calcium or vitamin D supplements or from parathyroid problems. Please see a doctor.",
    ),
    "hba1c": (
        "HbA1c shows your average blood sugar over the past 2 to 3 months. Below 5.7% is normal, 5.7 to 6.4% is prediabetes and 6.5% or more is in the diabetes range.",
        "A low HbA1c is rarely a concern. It can read falsely low after blood loss or with some types of anaemia.",
        "High HbA1c means blood sugar has been high for weeks. Lower-GI, high-fibre meals, regular activity and your doctor's advice help bring it down.",
    ),
    "fasting_glucose": (
        "Fasting blood glucose is your blood sugar after at least 8 hours without food. Below 100 mg/dL is normal, 100 to 125 is prediabetes and 126 or more is in the diabetes range.",
        "Low fasting sugar (below 70 mg/dL) can make you shaky, sweaty or confused. Eat something with sugar and see a doctor if it keeps happening.",
        "High fasting sugar means your body is not controlling sugar well overnight. It needs a doctor's review; diet and activity help.",
    ),
    "postprandial_glucose": (
        "Post-meal (post-prandial) glucose is your blood sugar about 2 hours after eating. Below 140 mg/dL is normal, 140 to 199 is prediabetes and 200 or more is in the diabetes range.",
        "Low post-meal sugar is uncommon. If you feel shaky or sweaty after meals, talk to your doctor.",
        "High post-meal sugar means your body struggles with the sugar from meals. Smaller portions of refined carbs, more fibre and a walk after meals help.",
    ),
    "total_cholesterol": (
        "Total cholesterol is all the cholesterol in your blood. Below 200 mg/dL is desirable.",
        "Low cholesterol is rarely a concern on its own.",
        "High cholesterol raises the risk of heart disease over time. Less fried and processed food, more fibre and healthy fats, and regular activity help.",
    ),
    "triglycerides": (
        "Triglycerides are the main type of fat in your blood. Below 150 mg/dL is normal.",
        "Low triglycerides are not usually a concern.",
        "High triglycerides are often caused by sugar, refined carbs, alcohol and excess weight. Very high levels (500 mg/dL or more) need a doctor soon.",
    ),
    "ldl_cholesterol": (
        "LDL is often called 'bad' cholesterol because it can build up in the walls of arteries. Below 100 mg/dL is optimal.",
        "Low LDL is generally good.",
        "High LDL raises the risk of heart attack and stroke. Cutting fried food, ghee and vanaspati, and eating more fibre, nuts and seeds helps.",
    ),
    "hdl_cholesterol": (
        "HDL is often called 'good' cholesterol because it carries cholesterol away from the arteries. Above 40 mg/dL for men and 50 mg/dL for women is preferred.",
        "Low HDL raises heart risk. Regular exercise, healthy fats (nuts, seeds, fish), not smoking and less refined carbs help raise it.",
        "High HDL is generally good.",
    ),
    "creatinine": (
        "Creatinine is a waste product from your muscles that the kidneys clear from the blood. It is a key test of kidney function.",
        "Low creatinine usually reflects low muscle mass or low protein intake. NutriLens suggests protein-rich foods for this.",
        "High creatinine can mean the kidneys are not filtering well, or come from dehydration, a heavy meat meal or high muscle mass. A doctor should review it.",
    ),
    "urea": (
        "Blood urea is a waste product made when your body breaks down protein. The kidneys clear it from the blood.",
        "Low urea can come from low protein intake, liver problems or pregnancy.",
        "High urea can come from dehydration, a very high-protein diet or kidney problems. A doctor should review it.",
    ),
    "bun": (
        "BUN (blood urea nitrogen) is the nitrogen part of blood urea. It is another way of reporting urea and reflects kidney function.",
        "Low BUN can come from low protein intake or liver problems.",
        "High BUN can come from dehydration, high protein intake or kidney problems. A doctor should review it.",
    ),
    "uric_acid": (
        "Uric acid is made when the body breaks down purines, found in some foods and in your own cells. The kidneys clear it.",
        "Low uric acid is rarely a concern.",
        "High uric acid can cause gout (painful swollen joints) and kidney stones. Low-purine foods, plenty of water and avoiding alcohol and sugary drinks help.",
    ),
    "sgot_ast": (
        "SGOT (AST) is an enzyme found in the liver, heart and muscles. It is part of the liver function test.",
        "Low SGOT is not a concern.",
        "High SGOT can mean liver stress (fatty liver, alcohol, some medicines, hepatitis) or muscle strain after heavy exercise. A doctor should review it.",
    ),
    "sgpt_alt": (
        "SGPT (ALT) is an enzyme found mainly in the liver. It is the most specific routine marker of liver cell stress.",
        "Low SGPT is not a concern.",
        "High SGPT is most often due to fatty liver, alcohol, some medicines or viral hepatitis. A doctor should review it; a liver-friendly diet supports recovery.",
    ),
    "alkaline_phosphatase": (
        "Alkaline phosphatase (ALP) is an enzyme from the liver's bile ducts and from bones.",
        "Low ALP is uncommon and can be linked to low zinc or magnesium.",
        "High ALP can come from bile duct problems or bone conditions. It is normally higher in growing children, teenagers and in pregnancy.",
    ),
    "bilirubin_total": (
        "Bilirubin is a yellow pigment made when old red blood cells break down. The liver processes it and removes it in bile.",
        "Low bilirubin is not a concern.",
        "High bilirubin causes jaundice (yellow eyes or skin). It can come from liver problems, blocked bile flow or faster breakdown of red cells. A harmless condition called Gilbert's syndrome also raises it.",
    ),
    "bilirubin_direct": (
        "Direct bilirubin is the part of bilirubin that the liver has already processed.",
        "Low direct bilirubin is not a concern.",
        "High direct bilirubin suggests a liver or bile duct problem and should be reviewed by a doctor.",
    ),
    "bilirubin_indirect": (
        "Indirect bilirubin is the part of bilirubin that the liver has not processed yet.",
        "Low indirect bilirubin is not a concern.",
        "High indirect bilirubin often means red blood cells are breaking down faster, or Gilbert's syndrome, which is harmless.",
    ),
    "total_protein": (
        "Total protein measures the two main protein groups in blood: albumin and globulin.",
        "Low total protein can come from poor nutrition or from liver or kidney problems. NutriLens suggests protein-rich foods.",
        "High total protein can come from dehydration, long-term infection or inflammation, and rarely from blood disorders.",
    ),
    "albumin": (
        "Albumin is the main protein made by the liver. It keeps fluid inside blood vessels and carries nutrients and medicines.",
        "Low albumin can come from low protein intake, liver or kidney disease or inflammation. NutriLens suggests protein-rich foods.",
        "High albumin is usually due to dehydration.",
    ),
    "globulin": (
        "Globulins are blood proteins that include antibodies, which fight infection.",
        "Low globulin can be linked to immune, liver or kidney problems.",
        "High globulin can come from infection, inflammation or immune conditions.",
    ),
    "wbc": (
        "The total WBC count (TLC) measures white blood cells, which fight infection.",
        "A low WBC count can come from viral infections (including dengue), some medicines or bone marrow problems. A doctor should review it.",
        "A high WBC count usually means the body is fighting an infection or inflammation. Stress and some medicines also raise it.",
    ),
    "rbc": (
        "The RBC count is the number of red blood cells, which carry oxygen.",
        "A low RBC count usually means anaemia. NutriLens suggests iron-rich foods.",
        "A high RBC count can come from dehydration, smoking, high altitude or some medical conditions.",
    ),
    "platelets": (
        "Platelets are tiny blood cells that help blood clot and stop bleeding.",
        "Low platelets are common in viral fevers such as dengue, and can also come from some medicines or immune conditions. Very low platelets or any bleeding needs a doctor urgently.",
        "High platelets can come from infection, inflammation or iron deficiency, and rarely from bone marrow conditions.",
    ),
    "pcv": (
        "PCV (haematocrit) is the percentage of your blood made up of red blood cells.",
        "Low PCV usually means anaemia. NutriLens suggests iron-rich foods.",
        "High PCV is often due to dehydration, and sometimes smoking or high altitude.",
    ),
    "mcv": (
        "MCV is the average size of your red blood cells. It helps show the type of anaemia.",
        "Low MCV (small red cells) usually points to iron deficiency, or thalassaemia trait, which is common in India.",
        "High MCV (large red cells) often points to low vitamin B12 or folate, alcohol, thyroid or liver problems.",
    ),
    "mch": (
        "MCH is the average amount of haemoglobin in each red blood cell.",
        "Low MCH usually points to iron deficiency or thalassaemia trait.",
        "High MCH is often seen with low vitamin B12 or folate.",
    ),
    "mchc": (
        "MCHC is how concentrated the haemoglobin is inside red blood cells.",
        "Low MCHC usually points to iron deficiency.",
        "High MCHC is uncommon. It can come from some inherited red cell conditions or a sample problem.",
    ),
    "rdw": (
        "RDW shows how much your red blood cells vary in size.",
        "Low RDW is not a concern.",
        "High RDW means red cells of mixed sizes. It is often an early sign of iron, B12 or folate deficiency.",
    ),
    "mpv": (
        "MPV is the average size of your platelets.",
        "Low MPV can mean the bone marrow is making fewer platelets.",
        "High MPV means many young platelets, often made quickly after platelets were used up or destroyed.",
    ),
    "neutrophils": (
        _DIFF.format(name="Neutrophils") + " They are the main defence against bacteria.",
        "Low neutrophils can come from viral infections, some medicines or bone marrow problems.",
        "High neutrophils usually mean a bacterial infection, inflammation, stress or steroid medicines.",
    ),
    "lymphocytes": (
        _DIFF.format(name="Lymphocytes") + " They fight viruses and make antibodies.",
        "Low lymphocytes can come from stress, steroid medicines or some infections.",
        "High lymphocytes are most often seen with viral infections.",
    ),
    "eosinophils": (
        _DIFF.format(name="Eosinophils") + " They are involved in allergies and fighting parasites.",
        "Low eosinophils are usually not a concern.",
        "High eosinophils are common with allergies, asthma and worm infections.",
    ),
    "monocytes": (
        _DIFF.format(name="Monocytes") + " They clean up dead cells and help fight long-lasting infections.",
        "Low monocytes are usually not a concern.",
        "High monocytes can come from long-lasting infection or inflammation, or the recovery phase after an infection.",
    ),
    "basophils": (
        _DIFF.format(name="Basophils") + " They are involved in allergic reactions.",
        "Low basophils are normal; they are often reported as 0.",
        "High basophils can come from allergies and, rarely, from blood disorders.",
    ),
    "esr": (
        "ESR shows how quickly red blood cells settle in a tube. It is a general marker of inflammation in the body.",
        "Low ESR is not a concern.",
        "High ESR can come from infection, inflammation, anaemia, pregnancy or older age. It does not point to a specific disease.",
    ),
    "tsh": (
        "TSH is a hormone from the brain's pituitary gland that tells the thyroid how hard to work. It is the main thyroid screening test.",
        "Low TSH usually means an overactive thyroid (hyperthyroidism), which can cause weight loss, a fast heartbeat and anxiety.",
        "High TSH usually means an underactive thyroid (hypothyroidism), which can cause tiredness, weight gain, feeling cold and hair fall.",
    ),
    "t3": (
        "T3 is the active thyroid hormone that controls how fast your body uses energy.",
        "Low T3 can come with an underactive thyroid or during any serious illness.",
        "High T3 usually points to an overactive thyroid.",
    ),
    "t4": (
        "T4 is the main hormone made by the thyroid gland. The body converts it to T3.",
        "Low T4, especially with high TSH, points to an underactive thyroid.",
        "High T4, especially with low TSH, points to an overactive thyroid.",
    ),
    "sodium": (
        "Sodium is a salt in the blood that controls fluid balance and helps nerves and muscles work.",
        "Low sodium can come from vomiting, diarrhoea, drinking very large amounts of water, some medicines or heart, kidney or liver problems. Very low sodium can cause confusion and needs urgent care.",
        "High sodium is usually caused by dehydration.",
    ),
    "potassium": (
        "Potassium is a salt in the blood that keeps the heart rhythm and muscles working properly.",
        "Low potassium can come from vomiting, diarrhoea or water tablets (diuretics). It can cause weakness and cramps.",
        "High potassium can come from kidney problems, some medicines or a damaged blood sample. Very high or very low potassium can affect the heart, so a doctor should review it.",
    ),
    "chloride": (
        "Chloride is a salt that works with sodium to keep fluid and acid balance in the body.",
        "Low chloride can come from vomiting or some medicines.",
        "High chloride is usually due to dehydration or diarrhoea.",
    ),
    "serum_iron": (
        "Serum iron is the amount of iron in your blood right now. It changes during the day and after meals, so it is read together with ferritin and TIBC.",
        "Low serum iron usually means iron deficiency. Iron-rich foods eaten with vitamin C help.",
        "High serum iron can come from recent iron tablets or too much stored iron.",
    ),
    "tibc": (
        "TIBC (total iron binding capacity) shows how much iron your blood is able to carry.",
        "Low TIBC can come from inflammation, liver disease, poor nutrition or too much stored iron.",
        "High TIBC usually means iron deficiency: the body makes more carriers to grab whatever iron it can.",
    ),
    "transferrin_saturation": (
        "Transferrin saturation is the percentage of the blood's iron carriers that are actually carrying iron.",
        "Low transferrin saturation (below about 20%) points to iron deficiency. Iron-rich foods help.",
        "High transferrin saturation (above about 45%) can mean too much iron in the body and should be checked by a doctor.",
    ),
    "ggt": (
        "GGT is a liver and bile duct enzyme. It is very sensitive to alcohol.",
        "Low GGT is not a concern.",
        "High GGT is commonly due to alcohol, fatty liver, some medicines or bile duct problems.",
    ),
    "egfr": (
        "eGFR is an estimate of how well your kidneys filter blood, calculated from creatinine, age and sex. 90 or above is normal.",
        "A low eGFR means the kidneys are filtering less well. Below 60 for three months or more is chronic kidney disease, so a doctor should review it.",
        "A high eGFR is not usually a concern.",
    ),
    "phosphorus": (
        "Phosphorus works with calcium to build bones and helps the body make energy.",
        "Low phosphorus can come from poor nutrition, vitamin D deficiency or some medicines.",
        "High phosphorus is most often linked to kidney problems.",
    ),
    "crp": (
        "CRP (C-reactive protein) is made by the liver when there is inflammation or infection in the body.",
        "Low CRP is normal and good.",
        "High CRP means there is inflammation or infection somewhere. It does not show where; very high values need a doctor.",
    ),
}

# Variants of a test share the main test's notes.
TEST_INFO["ft3"] = ("Free T3 is the part of T3 that is not bound to proteins and is active in the body.",) + TEST_INFO["t3"][1:]
TEST_INFO["ft4"] = ("Free T4 is the part of T4 that is not bound to proteins and is available to the body.",) + TEST_INFO["t4"][1:]
for _cell in ("neutrophils", "lymphocytes", "eosinophils", "monocytes", "basophils"):
    TEST_INFO[f"{_cell}_abs"] = TEST_INFO[_cell]
