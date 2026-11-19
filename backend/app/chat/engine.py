"""NutriLens assistant: answers questions about tests, foods, diets and the app from a checked knowledge base.

There is no text generation. Every reply is either written by hand (FAQ, safety messages) or assembled from the same
data the analyser uses (biomarkers.json, foods.json, the food-plan rules), so the assistant can never invent a value.

Pipeline for each message:
  1. Safety first: emergencies, self-harm, prompt-injection attempts, abuse, non-English text.
  2. Small talk (greetings, thanks, "who are you").
  3. Medicines and doses are declined and redirected to a doctor.
  4. Personal questions are answered from the user's own analysed results, when the page sends them.
  5. Entity and intent detection: which test, condition, nutrient or food is asked about, and what about it
     (meaning, normal range, low, high, foods, foods to avoid, when to see a doctor).
  6. Otherwise the FAQ is searched with TF-IDF weighted matching (BM25 breaks ties).
  7. Anything outside nutrition, blood tests and NutriLens is politely declined.
"""
from __future__ import annotations

import difflib
import math
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Optional

from app.chat.faq import FAQ
from app.chat.test_info import TEST_INFO
from app.engine.recommender import ABSORPTION_RULES, FOODS_DATABASE, TAG_LABELS, TAG_PROFILES, RecommendationEngine
from app.engine.rule_engine import BIOMARKERS_CONFIG
from app.models.schemas import DietType, UserProfile

ENGINE = RecommendationEngine()
FOODS_BY_ID = {f["id"]: f for f in FOODS_DATABASE}


@dataclass
class Reply:
    reply: str
    kind: str = "answer"  # answer | clarify | fallback | safety | refuse | smalltalk
    suggestions: list[str] = field(default_factory=list)
    topic: Optional[str] = None


# --------------------------------------------------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------------------------------------------------

def normalize(text: str) -> str:
    text = text.lower().replace("’", "'")
    text = re.sub(r"(\w)'(\w)", r"\1\2", text)  # don't -> dont, what's -> whats
    text = re.sub(r"\b(?:[a-z]\.){2,}[a-z]?\b", lambda m: m.group(0).replace(".", ""), text)  # e.s.r -> esr
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


SPELLING = {
    "cholestrol": "cholesterol", "colesterol": "cholesterol", "cholesteral": "cholesterol", "cholestral": "cholesterol",
    "diabetis": "diabetes", "diabities": "diabetes", "diabeties": "diabetes", "sugr": "sugar", "suger": "sugar",
    "shugar": "sugar", "thyriod": "thyroid", "thyroide": "thyroid", "protien": "protein", "calcuim": "calcium",
    "hemoglobine": "hemoglobin", "heamoglobin": "hemoglobin", "hemoglobin": "hemoglobin", "vitamine": "vitamin",
    "vitamins": "vitamin", "vit": "vitamin", "vitd": "vitamin d", "vitd3": "vitamin d", "vitb12": "vitamin b12",
    "anemia": "anaemia", "anemic": "anaemic", "fibre": "fibre", "fiber": "fibre", "tryglycerides": "triglycerides",
    "triglycerid": "triglycerides", "plateletes": "platelets", "platlets": "platelets", "creatinin": "creatinine",
    "kidny": "kidney", "livr": "liver", "foood": "food", "fod": "food", "foods": "foods", "eatt": "eat",
    "veggie": "veg", "nonveg": "non veg", "nonvegetarian": "non vegetarian", "pls": "please", "plz": "please",
    "u": "you", "r": "are", "ur": "your", "wat": "what", "wht": "what", "hw": "how",
    # Common Hinglish words
    "khana": "food", "khaana": "food", "khaye": "eat", "khayen": "eat", "khaen": "eat", "kya": "what", "kaise": "how",
    "kaun": "which", "badhaye": "increase", "badhane": "increase", "badhana": "increase", "kam": "low",
    "zyada": "high", "jyada": "high", "khoon": "blood", "kami": "deficiency",
}

STOP = {
    "a", "an", "the", "is", "are", "am", "was", "were", "be", "been", "i", "me", "my", "mine", "we", "our", "you", "your",
    "it", "its", "this", "that", "these", "those", "to", "of", "for", "in", "on", "at", "by", "with", "and", "or", "do",
    "does", "did", "can", "could", "should", "would", "will", "shall", "may", "might", "how", "what", "whats", "which",
    "there", "here", "please", "tell", "know", "need", "any", "some",
    "much", "many", "so", "if", "then", "than", "about", "just", "also", "very", "really", "im", "ive", "id", "us", "has",
    "have", "had", "from", "as", "into", "up", "out", "too", "hi", "hello", "hey", "pls", "please", "ok", "okay",
}


def stem(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        word = word[:-3] + "y"
    elif len(word) > 5 and word.endswith("ing"):
        word = word[:-3]
    elif len(word) > 4 and word.endswith("ed") and not word.endswith("eed"):
        word = word[:-2]
    elif len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        word = word[:-1]
    if len(word) > 4 and word.endswith("e"):
        word = word[:-1]
    return word


# Different ways of saying the same thing, folded into one word before FAQ matching.
CANON_PHRASES = [
    (r"\b(nutrilens|this site|this website|this app|the site|the website|the app|this tool|the tool)\b", "site"),
    (r"\b(not|cannot|cant|unable to|couldnt|could not|wont|will not) (upload\w*|open\w*|load\w*|process\w*|submit\w*)\b",
     "upload broken"),
    (r"\bkeep (\w+ ){0,3}(healthy|normal)\b", "maintain"),
    (r"\blast (month|year|week|time)\b", "old"),
    (r"\b(reset|password|forgot password) (e ?mail|mail|link|message)s?\b", "resetlink"),
    (r"\b(manually|by myself|myself|on my own)\b", "manual"),
    (r"\bhow (to|do i|do we|can i|should i|does one) use\b", "howuse"),
    (r"\b(work|works)\b", "supported"),
    (r"\b(can|does|will) (it|you|site) (understand|recognise|recognize|detect|identify|pick up)\b", "can read"),
    (r"\b(sugar ?free|artificial sweeteners?|sweeteners?|stevia)\b", "sweetener"),
    (r"\bdidnt\b", "did not"), (r"\bdoesnt\b", "does not"), (r"\bdont\b", "do not"), (r"\bcant\b", "cannot"),
    (r"\bwont\b", "will not"), (r"\bisnt\b", "is not"), (r"\bwasnt\b", "was not"), (r"\barent\b", "are not"),
    (r"\bhavent\b", "have not"), (r"\bcouldnt\b", "could not"),
    (r"\bkeep (it|them|my results?|results?|levels?)? ?(healthy|normal)\b", "maintain"),
    (r"\b(written by hand|by hand|hand ?written)\b", "handwritten"),
    (r"\b((ms )?word|docx?) (file|document|doc)s?\b|\bdocx\b", "wordfile"),
    (r"\b(together|at once|at the same time|multiple|several|more than one|both)\b|\b(two|2|three|3) (?=(pdf|file|report|photo|image|document)s?\b)", "multiple "),
    (r"\b(did not show up|not showing|not shown|not found|not detected|not visible|disappeared|missing|went missing|"
     r"left out|skipped)\b", "missing"),
    (r"\b(usa|uk|america|abroad|overseas|outside india|other country|another country|foreign)\b", "foreign"),
    (r"\b(per day|a day|daily|every day|each day|everyday)\b", "daily"),
    (r"\b(jpe?g|png|heic|gif|tiff?)\b", "format"),
    (r"\b(allowed|supported|accepted|accept|support|compatible)\b", "supported"),
    (r"\b(picked|pick|chose|chosen|choose|selected|select|selection|entered)\b", "choose"),
    (r"\b(verify|verification|confirm|double check)\b", "review"),
    (r"\b(analy[sz](e|es|ed|ing|is))\b", "analyse"),
    (r"\b(different|another|other|new|second|next)\b", "another"),
    (r"\b(save|saved|saving|saves)\b", "store"),
    (r"\b(blood|lab) tests?\b", "report"),
    (r"\b(log ?out|sign ?out|logging out|signing out|signed out|logged out|log me out)\b", "logout"),
    (r"\b(log ?in|sign ?in|logging in|signing in|signed in|logged in)\b", "login"),
    (r"\b(sign ?up|create (an |a |my )?account|new account|make (an |a )?account|registration)\b", "signup"),
    (r"\b((diet|food|meal|nutrition|eating|health) ?(plan|chart|schedule|programme|program)s?|"
     r"(food|diet) (suggestion|recommendation|advice|list)s?)\b", "dietplan"),
    (r"\b((lab|blood|tests?|testing|tested|medical|health|pathology|diagnostic|checkup|check up) ?"
     r"(report|result|test report)s?|blood test report|(tested|testing) (blood|sample)s?)\b", "report"),
    (r"\b(health ?score|my score)\b", "healthscore"),
    (r"\b((mobile|android|iphone|ios|phone) ?(app|application)|play ?store|app ?store|install (the |an )?app|"
     r"is there an app|download (the |an )?app)\b", "mobileapp"),
    (r"\b(dark ?mode|night ?mode)\b", "darkmode"),
    (r"\b(not working|doesnt work|does not work|isnt working|wont work|stopped working|not loading)\b", "broken"),
    (r"\b(time ?out|timed out|timeout)\b", "timeout"),
    (r"\b(how long)\b", "duration"),
    (r"\b(how much|how many)\b", "amount"),
]
TOKEN_SYNONYMS = {
    "using": "use", "used": "use", "uses": "use", "happens": "happen", "happened": "happen",
    "want": "get", "wanted": "get",
    "docs": "report", "document": "report", "documents": "report", "reports": "report", "pathology": "report",
    "uploading": "upload", "uploaded": "upload", "uploads": "upload", "attach": "upload", "submit": "upload",
    "generate": "get", "obtain": "get", "receive": "get", "create": "get", "make": "get", "build": "get",
    "picture": "photo", "pictures": "photo", "pic": "photo", "pics": "photo", "image": "photo", "images": "photo",
    "screenshot": "photo", "snap": "photo", "camera": "photo",
    "remove": "delete", "erase": "delete", "wipe": "delete",
    "secure": "safe", "safety": "safe", "security": "safe", "secured": "safe",
    "website": "site", "webpage": "site", "web": "site", "portal": "site", "platform": "site", "app": "site",
    "application": "site",
    "price": "cost", "pay": "cost", "paid": "cost", "charge": "cost", "charges": "cost", "fee": "cost",
    "fees": "cost", "money": "cost", "rupees": "cost",
    "chats": "chat", "conversation": "chat", "conversations": "chat", "chatbot": "chat", "bot": "chat",
    "assistant": "chat",
    "physician": "doctor", "doctors": "doctor",
    "incorrect": "wrong", "mistake": "wrong", "mistakes": "wrong", "inaccurate": "wrong",
    "stored": "store", "storing": "store", "keeps": "store", "keep": "store", "retain": "store",
    "previous": "old", "past": "old", "earlier": "old", "older": "old",
    "modify": "edit", "change": "edit", "correct": "edit", "update": "edit", "fix": "edit",
    "issue": "problem", "issues": "problem", "trouble": "problem", "bug": "problem", "glitch": "problem",
    "slowly": "slow", "lag": "slow", "lagging": "slow", "hang": "slow", "hanging": "slow", "stuck": "slow",
    "kids": "child", "kid": "child", "children": "child", "son": "child", "daughter": "child",
}


def canon(text: str) -> str:
    for pattern, replacement in _CANON_RES:
        text = pattern.sub(replacement, text)
    return " ".join(TOKEN_SYNONYMS.get(w, w) for w in text.split())


_CANON_RES = [(re.compile(p), r) for p, r in CANON_PHRASES]


def faq_tokens(text: str) -> list[str]:
    return [stem(t) for t in canon(text).split() if t not in STOP]


def fmt(number: Any) -> str:
    if number is None:
        return ""
    if isinstance(number, float) and number.is_integer():
        number = int(number)
    return f"{number:,}" if isinstance(number, int) and abs(number) >= 10000 else str(number)


def short_name(key: str) -> str:
    name = BIOMARKERS_CONFIG[key]["display_name"]
    return name.split(" (")[0]


# --------------------------------------------------------------------------------------------------------------------
# Knowledge: concepts (conditions and nutrients), test names, food names
# --------------------------------------------------------------------------------------------------------------------

NUTRIENTS = {  # plan key -> (nutrient name, unit)
    "iron_mg": ("iron", "mg"), "calcium_mg": ("calcium", "mg"), "vitamin_d_iu": ("vitamin D", "IU"),
    "vitamin_b12_mcg": ("vitamin B12", "µg"), "folate_mcg": ("folate", "µg"), "vitamin_c_mg": ("vitamin C", "mg"),
}
PLAN_NAMES = {
    "iron_mg": "iron", "calcium_mg": "calcium", "vitamin_d_iu": "vitamin D", "vitamin_b12_mcg": "vitamin B12",
    "folate_mcg": "folate", "vitamin_c_mg": "vitamin C", "glycemic_support": "blood sugar control",
    "lipid_support": "healthy cholesterol", "hdl_support": "raising HDL (good cholesterol)", "protein_support": "protein",
    "uric_acid_support": "lowering uric acid", "liver_support": "liver health", "tag:high_fibre": "fibre",
    "tag:low_gi": "steady blood sugar (low GI)", "tag:omega3": "omega-3 fats",
}
DIET_LABEL = {"veg": "vegetarian", "vegan": "vegan", "eggetarian": "eggetarian", "non_veg": "non-vegetarian"}

CONCEPTS = {
    "iron": dict(
        words=["iron", "anaemia", "anaemic", "iron deficiency", "low blood", "blood deficiency", "blood loss"],
        plan="iron_mg", test="serum_iron",
        about="Iron is needed to make haemoglobin, which carries oxygen in your blood. Low iron is the most common cause of "
              "anaemia in India and can cause tiredness, breathlessness and pale skin. Haemoglobin, ferritin, serum iron, "
              "TIBC and transferrin saturation are the tests that show it."),
    "blood_sugar": dict(
        words=["diabetes", "diabetic", "sugar", "blood sugar", "sugar level", "prediabetes", "pre diabetes",
               "prediabetic", "glucose", "blood glucose", "insulin resistance", "madhumeh"],
        plan="glycemic_support", test="hba1c",
        about="Blood sugar (glucose) is your body's main fuel. When the body can't control it well, it stays high, which is "
              "prediabetes or diabetes. HbA1c (your 3-month average), fasting glucose and post-meal glucose are the tests "
              "that show it."),
    "cholesterol": dict(
        words=["cholesterol", "lipid", "lipids", "lipid profile", "heart health", "heart disease", "healthy heart",
               "heart", "blood fat", "blood fats"],
        plan="lipid_support", test="total_cholesterol",
        about="Cholesterol and triglycerides are fats carried in your blood. High LDL ('bad') cholesterol and triglycerides, "
              "and low HDL ('good') cholesterol, raise the risk of heart disease over time. The lipid profile measures them."),
    "uric_acid": dict(
        words=["uric acid", "gout", "purine", "purines"], plan="uric_acid_support", test="uric_acid",
        about="Uric acid is a waste product from the breakdown of purines. High levels can cause gout (painful, swollen "
              "joints) and kidney stones."),
    "liver": dict(
        words=["liver", "fatty liver", "liver enzymes", "liver function", "liver function test", "lft", "jaundice"],
        plan="liver_support", test="sgpt_alt",
        about="The liver processes nutrients, medicines and alcohol. The liver function test (LFT) includes SGPT, SGOT, GGT, "
              "ALP, bilirubin and proteins. Raised liver enzymes most often come from fatty liver, alcohol, medicines or "
              "hepatitis. Yellow eyes or skin (jaundice) needs a doctor promptly."),
    "kidney": dict(
        words=["kidney", "kidneys", "kidney function", "kft", "rft", "renal", "renal function", "kidney stone",
               "kidney stones"],
        plan=None, test="creatinine",
        about="The kidneys filter waste from your blood. Creatinine, urea, BUN, eGFR and uric acid show how well they work. "
              "Kidney diets must be planned by a doctor or dietitian, because protein, potassium and phosphorus needs depend "
              "on the stage of kidney disease. NutriLens therefore flags abnormal kidney results for a doctor instead of "
              "giving a food plan."),
    "thyroid": dict(
        words=["thyroid", "hypothyroid", "hypothyroidism", "hyperthyroid", "hyperthyroidism", "thyroid function",
               "thyroid profile", "goitre", "goiter"],
        plan=None, test="tsh",
        about="The thyroid gland controls how fast your body uses energy. TSH, T3 and T4 (and their free forms) show whether "
              "it is underactive or overactive. Thyroid problems are treated with medicine, so NutriLens flags abnormal "
              "results for a doctor instead of giving a food plan. Using iodised salt helps prevent iodine deficiency."),
    "vitamin_d": dict(words=["vitamin d", "vitamin d3", "d3", "sunshine vitamin"], plan="vitamin_d_iu", test="vitamin_d"),
    "vitamin_b12": dict(words=["vitamin b12", "b12", "b 12", "cobalamin"], plan="vitamin_b12_mcg", test="vitamin_b12"),
    "folate": dict(words=["folate", "folic acid", "vitamin b9", "b9"], plan="folate_mcg", test="folate"),
    "calcium": dict(
        words=["calcium", "bone", "bones", "bone health", "strong bones", "osteoporosis"], plan="calcium_mg", test="calcium",
        about="Calcium builds bones and teeth and helps muscles, nerves and the heart work. Milk, curd, ragi, sesame and leafy "
              "greens are good sources, and vitamin D helps you absorb it."),
    "protein": dict(
        words=["protein", "proteins", "muscle", "muscles", "muscle building", "muscle gain"], plan="protein_support",
        test="total_protein",
        about="Protein builds and repairs muscles and tissues and keeps your immune system strong. Low total protein or "
              "albumin on a report can point to low protein intake."),
    "vitamin_c": dict(
        words=["vitamin c", "ascorbic acid", "immunity"], plan="vitamin_c_mg", test=None,
        about="Vitamin C supports immunity and skin, and greatly improves iron absorption from plant foods. Amla, guava, "
              "citrus fruits, capsicum and tomatoes are rich sources."),
    "fibre": dict(
        words=["fibre", "constipation", "roughage"], plan="tag:high_fibre", test=None,
        about="Fibre keeps digestion regular and helps control blood sugar and cholesterol. Whole grains, millets, pulses, "
              "vegetables and fruits are good sources."),
    "low_gi": dict(
        words=["low gi", "glycemic index", "glycaemic index", "low glycemic", "gi"], plan="tag:low_gi", test=None,
        about="Low-GI (glycaemic index) foods release sugar slowly, keeping blood sugar steadier. Most pulses, millets, "
              "vegetables and many whole fruits are low GI."),
    "omega3": dict(
        words=["omega 3", "omega3", "omega"], plan="tag:omega3", test=None,
        about="Omega-3 fats support heart health and can help lower triglycerides. Fish such as sardine and mackerel, "
              "flaxseeds, walnuts and chia seeds are good sources."),
    "cbc": dict(
        words=["cbc", "complete blood count", "blood count", "hemogram", "haemogram", "full blood count"], plan=None,
        test=None,
        about="The complete blood count (CBC) measures your red cells (haemoglobin, RBC, PCV, MCV, MCH, MCHC, RDW), white "
              "cells (total WBC and the differential count) and platelets. It helps detect anaemia, infection and many "
              "other conditions. NutriLens gives a food plan for anaemia-related results and flags the others for a doctor."),
    "electrolytes": dict(
        words=["electrolyte", "electrolytes", "serum electrolytes"], plan=None, test="sodium",
        about="Electrolytes (sodium, potassium, chloride) are salts that control fluid balance, nerves, muscles and heart "
              "rhythm. Abnormal levels need a doctor's review, so NutriLens doesn't give a food plan for them."),
}
for _key, _concept in CONCEPTS.items():
    if "about" not in _concept:
        _concept["about"] = TEST_INFO[_concept["test"]][0]

EXTRA_TEST_ALIASES = {
    "vitamin_d": ["vitamin d", "25 oh vitamin d", "vitamin d total"], "vitamin_b12": ["vitamin b12"],
    "folate": ["folic acid", "vitamin b9"], "hemoglobin": ["hb level", "hemoglobin level"],
    "hba1c": ["glycated hemoglobin", "glycated haemoglobin", "3 month sugar", "average sugar", "hba1c test"],
    "fasting_glucose": ["fasting sugar", "fasting glucose", "fasting blood sugar", "fbs"],
    "postprandial_glucose": ["post meal sugar", "postprandial", "post prandial", "pp sugar", "after food sugar",
                             "post lunch sugar", "after meal sugar", "ppbs"],
    "total_cholesterol": ["total cholesterol"], "ldl_cholesterol": ["ldl", "bad cholesterol", "ldl cholesterol"],
    "hdl_cholesterol": ["hdl", "good cholesterol", "hdl cholesterol"], "uric_acid": ["uric acid"],
    "wbc": ["white blood cells", "white blood cell", "white cells", "wbc count", "white blood count", "tlc"],
    "rbc": ["red blood cells", "red blood cell", "red cells", "rbc count"],
    "platelets": ["platelet count", "platelets", "platelet"], "tsh": ["tsh", "thyroid stimulating hormone"],
    "crp": ["c reactive protein", "crp"], "esr": ["esr", "sed rate"], "egfr": ["egfr", "gfr"],
    "sgot_ast": ["sgot"], "sgpt_alt": ["sgpt"], "ferritin": ["ferritin", "iron stores", "stored iron"],
    "serum_iron": ["serum iron", "iron test", "iron level"], "transferrin_saturation": ["transferrin saturation", "tsat"],
    "bilirubin_total": ["bilirubin", "total bilirubin"], "alkaline_phosphatase": ["alp", "alkaline phosphatase"],
}
BLOCKED_ALIASES = {"iron", "ca", "ast", "alt", "na", "k", "cl", "sugar", "glucose", "cholesterol", "protein", "gi"}
KEEP_SHORT = {"hb", "t3", "t4"}

FOOD_GENERIC = {"leaves", "leaf", "seeds", "seed", "powder", "flour", "raw", "cooked", "dry", "dried", "whole", "green",
                "red", "black", "white", "fresh", "boiled", "roasted", "sprouted", "split", "big", "small", "common",
                "patte", "ke", "ka", "ki", "beans", "bean", "oil", "juice", "meat", "fruit", "vegetable", "dal", "leafy"}


def _food_variants(food: dict) -> set[str]:
    variants = set()
    for source in (food["name"], food.get("hindi_name") or ""):
        for part in re.split(r"[/(),]", source):
            phrase = normalize(part)
            if not phrase:
                continue
            words = phrase.split()
            if len(words) == 1 and (words[0] in FOOD_GENERIC or len(words[0]) < 3):
                continue
            variants.add(phrase)
            if len(words) == 1 and not phrase.endswith("s"):
                variants.add(phrase + "s")
    return variants


# Everyday words for which several foods exist: map them to the plain, most common one.
COMMON_FOODS = {
    "milk": "Cow's Milk (Boiled)", "cow milk": "Cow's Milk (Boiled)", "rice": "White Rice (Raw, Milled)",
    "white rice": "White Rice (Raw, Milled)", "egg": "Boiled Chicken Egg (Whole)", "eggs": "Boiled Chicken Egg (Whole)",
    "boiled egg": "Boiled Chicken Egg (Whole)", "chicken": "Skinless Chicken Breast", "roti": "Whole Wheat Flour / Atta",
    "chapati": "Whole Wheat Flour / Atta", "chapathi": "Whole Wheat Flour / Atta", "wheat": "Whole Wheat",
    "apple": "Apple / Seb", "apples": "Apple / Seb", "dates": "Black Dates", "khajur": "Black Dates", "curd": "Plain Curd / Dahi", "yogurt": "Plain Curd / Dahi",
    "yoghurt": "Plain Curd / Dahi",
}


def _build_phrases() -> dict[str, list[tuple[str, str]]]:
    phrases: dict[str, list[tuple[str, str]]] = {}

    def add(phrase: str, entity: tuple[str, str]) -> None:
        phrase = normalize(phrase)
        if phrase and entity not in phrases.setdefault(phrase, []):
            phrases[phrase].append(entity)

    for key, cfg in BIOMARKERS_CONFIG.items():
        for alias in list(cfg.get("aliases", [])) + [cfg["display_name"], short_name(key)] + EXTRA_TEST_ALIASES.get(key, []):
            phrase = normalize(alias)
            if phrase in BLOCKED_ALIASES or (len(phrase) <= 2 and phrase not in KEEP_SHORT):
                continue
            add(phrase, ("test", key))
    for key, concept in CONCEPTS.items():
        for word in concept["words"]:
            add(word, ("concept", key))
    food_phrases: dict[str, list[str]] = {}
    for food in FOODS_DATABASE:
        for variant in _food_variants(food):
            food_phrases.setdefault(variant, []).append(food["id"])
    for phrase, name in COMMON_FOODS.items():
        food = next((f for f in FOODS_DATABASE if f["name"] == name), None)
        if food:
            food_phrases[normalize(phrase)] = [food["id"]]
    for phrase, ids in food_phrases.items():
        if (len(ids) > 3 and phrase not in COMMON_FOODS) or phrase in phrases:  # too generic ("rice" in many foods) or already a test/concept word
            continue
        best = min(ids, key=lambda i: len(FOODS_BY_ID[i]["name"]))
        add(phrase, ("food", best))
    return phrases


PHRASES = _build_phrases()
_PHRASE_RE = re.compile(r"(?<![a-z0-9])(?P<p>" + "|".join(re.escape(p) for p in sorted(PHRASES, key=len, reverse=True))
                        + r")(?:s|es)?(?![a-z0-9])")


# --------------------------------------------------------------------------------------------------------------------
# Intent, diet and allergen detection
# --------------------------------------------------------------------------------------------------------------------

INTENTS = [  # checked in priority order
    ("avoid", r"\b(avoid\w*|not eat|shouldnt eat|dont eat|do not eat|stay away|bad for|harmful|worst|foods? to limit|limit|restrict\w*|what not)\b"),
    ("foods", r"\b(eat|eating|food|foods|diet|diets|meal|meals|rich in|richest|source|sources|increase|improve|boost|raise|"
              r"reduce|lower|decrease|control|manage|bring down|bring up|fix|cure|treat|naturally|what to have|consume|recipe|"
              r"recipes|drink|drinks|breakfast|lunch|dinner|snack|snacks|nutrition|options|best for|good for|helps?|plan|most|"
              r"highest|best source|best sources|top)\b"),
    ("range", r"\b(normal|range|reference|ideal|healthy level|target|optimal|cut ?off|what value|should be|good level|"
              r"safe level|level should|normal value|limit for)\b"),
    ("doctor", r"\b(doctor|serious|dangerous|danger|worr\w*|emergency|urgent|concern\w*|risky|critical|alarming|bad sign)\b"),
    ("low", r"\b(low|lower than|less|deficien\w*|decreased|below|drop\w*|fall\w*|reduced|insufficien\w*|not enough)\b"),
    ("high", r"\b(high|higher|elevated|increased|above|raised|too much|excess\w*|more than)\b"),
    ("symptoms", r"\b(symptom\w*|signs?|feel|feeling|tired\w*|fatigue|weak\w*)\b"),
    ("causes", r"\b(cause\w*|why|reason\w*|due to)\b"),
    ("what", r"\b(what is|whats|what are|meaning|mean|means|stands? for|explain|tell me about|define|definition|full form|"
             r"purpose|about|info|information)\b"),
]
_INTENT_RES = [(name, re.compile(pattern)) for name, pattern in INTENTS]


def detect_intents(text: str) -> list[str]:
    found = [name for name, pattern in _INTENT_RES if pattern.search(text)]
    # "lower cholesterol" and "increase iron" are about foods; "low" and "high" then only set the direction.
    return found


def direction_of(intents: list[str]) -> Optional[str]:
    if "low" in intents and "high" not in intents:
        return "low"
    if "high" in intents and "low" not in intents:
        return "high"
    return None


def primary_intent(intents: list[str]) -> str:
    for name in ("avoid", "foods", "range", "doctor", "low", "high", "symptoms", "causes", "what"):
        if name in intents:
            return name
    return "general"


def detect_diet(text: str) -> Optional[str]:
    if re.search(r"\bvegan\b", text):
        return "vegan"
    if re.search(r"\b(eggetarian|egg vegetarian|veg (plus|with|and) eggs?)\b", text):
        return "eggetarian"
    if re.search(r"\b(non veg\w*|non vegetarian|meat eater|chicken|mutton|seafood|fish eater)\b", text):
        return "non_veg"
    if re.search(r"\b(veg|vegetarian|pure veg|jain)\b", text):
        return "veg"
    return None


ALLERGEN_WORDS = {
    "dairy": ["dairy", "milk", "lactose", "curd", "paneer", "cheese"], "gluten": ["gluten", "wheat", "celiac", "coeliac"],
    "nuts": ["nut", "nuts", "peanut", "peanuts", "groundnut", "almond", "almonds", "cashew"], "soy": ["soy", "soya", "tofu"],
    "eggs": ["egg", "eggs"], "seafood": ["seafood", "fish", "shellfish", "prawn", "prawns", "shrimp"],
}
_NEG = r"(?:no|without|avoid\w*|allergic to|allergy to|intoleran\w* to|except|exclud\w*|cant eat|cannot eat|dont eat|not eat)"


def detect_allergens(text: str) -> tuple[list[str], str]:
    found, cleaned = [], text
    for allergen, words in ALLERGEN_WORDS.items():
        for word in words:
            pattern = re.compile(rf"\b{_NEG}\s+(?:\w+\s+){{0,2}}?{word}\b|\b{word}\s*(?:free|allergy|allergic|intoleran\w*)\b")
            if pattern.search(cleaned):
                found.append(allergen)
                cleaned = pattern.sub(" ", cleaned)
                break
    if re.search(r"\blactose intoleran", text) and "dairy" not in found:
        found.append("dairy")
    return found, cleaned


# --------------------------------------------------------------------------------------------------------------------
# Spelling correction and FAQ search
# --------------------------------------------------------------------------------------------------------------------

DOMAIN_WORDS = {
    "health", "healthy", "blood", "test", "tests", "report", "reports", "lab", "result", "results", "value", "values",
    "level", "levels", "range", "food", "foods", "eat", "eating", "diet", "nutrition", "nutrient", "vitamin", "mineral",
    "doctor", "plan", "nutrilens", "upload", "pdf", "account", "login", "password", "history", "profile", "allergy",
    "allergic", "allergies", "vegetarian", "vegan", "veg", "meal", "breakfast", "lunch", "dinner", "weight", "fat", "fats",
    "fibre", "water", "exercise", "symptom", "symptoms", "deficiency", "supplement", "supplements", "medicine", "tablet",
    "pregnancy", "pregnant", "score", "data", "privacy", "website", "app", "site", "analyse", "analysis", "body", "sleep",
    "stress", "salt", "oil", "ghee", "millet", "millets", "fruit", "fruits", "vegetable", "vegetables", "pulses", "dal",
    "milk", "egg", "eggs", "fish", "chicken", "tea", "coffee", "sugar", "alcohol", "smoking", "drink", "snack", "fasting",
    "biomarker", "biomarkers", "parameter", "parameters", "marker", "markers", "unit", "units", "anaemia", "diabetes",
    "immunity", "energy", "tired", "fatigue", "hair", "skin", "bones", "heart", "liver", "kidney", "thyroid", "bp",
    "pressure", "cholesterol", "protein", "calorie", "calories", "carbs", "carbohydrate", "nutritious", "recipe", "cook",
    "cooking", "medical", "diagnosis", "scan", "photo", "image", "file", "download", "register", "signup", "sign",
}


MEDICAL_WORDS_SOURCE = (
    "fever cough headache migraine vomiting diarrhoea diarrhea rash infection covid corona cancer tumour tumor malaria "
    "typhoid dengue asthma injury fracture wound surgery operation ultrasound tablets capsules medicines medications "
    "dosage insulin metformin levothyroxine thyronorm eltroxin statins atorvastatin rosuvastatin injections antibiotics "
    "painkillers paracetamol prescription supplements multivitamins ayurvedic homeopathy breathe breathing unconscious "
    "fainted fainting seizure stroke paralysis bleeding overdose poisoning suicide"
)


def _faq_index():
    docs, df = [], {}
    for index, (faq_id, questions, _answer, _follow) in enumerate(FAQ):
        for question in questions:
            toks = faq_tokens(normalize(question))
            docs.append((index, toks))
            for tok in set(toks):
                df[tok] = df.get(tok, 0) + 1
    n = len(docs)
    idf = {tok: math.log(1 + (n - c + 0.5) / (c + 0.5)) for tok, c in df.items()}
    avg_len = sum(len(t) for _, t in docs) / n
    return docs, idf, avg_len


FAQ_DOCS, FAQ_IDF, FAQ_AVG_LEN = _faq_index()
FAQ_WORDS = {w for _, questions, _, _ in FAQ for q in questions for w in normalize(q).split()}
VOCAB = ({w for p in PHRASES for w in p.split()} | FAQ_WORDS | DOMAIN_WORDS | set(TOKEN_SYNONYMS)
         | {w for _, pattern in INTENTS for w in re.findall(r"[a-z]{4,}", pattern)} | set(SPELLING.values()))
# Everyday and medical words that must never be "corrected" into a different word (infection -> injection).
PROTECTED_WORDS = {
    "infection", "infections", "india", "indian", "capital", "weather", "question", "questions", "people", "person",
    "today", "tomorrow", "yesterday", "morning", "evening", "night", "please", "thanks", "thank", "report", "doctor",
    "medicine", "tablet", "tablets", "teacher", "student", "school", "college", "movie", "movies", "music", "cricket",
    "football", "politics", "money", "price", "prices", "phone", "computer", "program", "python", "joke", "jokes",
    "country", "world", "history", "travel", "hotel", "restaurant", "recipe", "recipes", "family", "friend", "friends",
    "mother", "father", "child", "children", "baby", "pregnant", "pregnancy", "fever", "headache", "cough", "allergy",
    "allergies", "pain", "sleep", "stress", "exercise", "walking", "running", "yoga", "season", "summer", "winter",
    "monsoon", "office", "house", "water", "drinking", "smoking", "alcohol", "coffee", "sugar", "sweets", "cancer",
    "dengue", "malaria", "typhoid", "covid", "injury", "surgery", "period", "periods", "result", "results", "normal",
    "these", "those", "there", "where", "which", "while", "should", "could", "would", "about", "after", "before",
} | {w for pattern in (MEDICAL_WORDS_SOURCE,) for w in re.findall(r"[a-z]{5,}", pattern)}
VOCAB |= PROTECTED_WORDS
VOCAB |= {w for pattern, _ in CANON_PHRASES for w in re.findall(r"[a-z]{4,}", pattern)}  # words the folding knows
VOCAB_LIST = sorted((w for w in VOCAB if len(w) >= 4 and w not in PROTECTED_WORDS), key=lambda w: w) + \
    sorted(k for k in SPELLING if len(k) >= 5)


def edit_distance(a: str, b: str) -> int:
    """Optimal string alignment distance: insertions, deletions, substitutions and swaps of neighbours."""
    prev2, prev = None, list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cost = a[i - 1] != b[j - 1]
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
    return prev[-1]


@lru_cache(maxsize=4096)
def _correct(word: str) -> str:
    if word in SPELLING:
        return SPELLING[word]
    if len(word) < 5 or word in VOCAB or word in STOP or word.isdigit():
        return word
    allowed = 1 if len(word) < 8 else 2
    candidates = difflib.get_close_matches(word, VOCAB_LIST, n=8, cutoff=0.7)
    scored = sorted((edit_distance(word, c), c[0] != word[0], -difflib.SequenceMatcher(None, word, c).ratio(), c)
                    for c in candidates)
    if scored and scored[0][0] <= allowed:
        best = scored[0][3]
        return SPELLING.get(best, best)
    return word


HINGLISH_PHRASES = [
    (r"\bkam (kare|karein|karen|karna|karne|karo|kaise|kese)\b", "reduce"),
    (r"\b(badhaye|badhaen|badhana|badhane|badhao) ?(kaise|kese)?\b", "increase"),
    (r"\bkya (khaye|khayen|khana|khaana|khau|khaun)\b", "what to eat"),
]


def clean(text: str) -> str:
    text = normalize(text)
    for pattern, replacement in HINGLISH_PHRASES:
        text = re.sub(pattern, replacement, text)
    return " ".join(_correct(w) for w in text.split())


UNKNOWN_WEIGHT = 6.0  # a word no FAQ uses (a test or food name) must stop the FAQ from claiming the question


def faq_search(text: str) -> list[tuple[float, int]]:
    query = faq_tokens(text)
    if not query:
        return []
    q_weight = sum(FAQ_IDF.get(t, UNKNOWN_WEIGHT) for t in set(query))
    best: dict[int, tuple[float, float]] = {}
    for index, toks in FAQ_DOCS:
        doc = set(toks)
        shared = set(query) & doc
        if not shared:
            continue
        overlap = sum(FAQ_IDF[t] for t in shared)
        recall = overlap / q_weight
        precision = overlap / sum(FAQ_IDF[t] for t in doc)
        f1 = 2 * precision * recall / (precision + recall)
        k1, b = 1.2, 0.75
        bm25 = sum(FAQ_IDF[t] * (k1 + 1) / (1 + k1 * (1 - b + b * len(toks) / FAQ_AVG_LEN)) for t in shared)
        if index not in best or (f1, bm25) > best[index]:
            best[index] = (f1, bm25)
    return sorted(((score[0], index) for index, score in best.items()), key=lambda x: (-x[0], -best[x[1]][1]))


# --------------------------------------------------------------------------------------------------------------------
# Answer builders
# --------------------------------------------------------------------------------------------------------------------

GROUP_LABEL = {"male": "Men", "female": "Women", "adult": "Adults", "all": "Everyone"}


def normal_ranges(key: str) -> list[tuple[str, str]]:
    cfg = BIOMARKERS_CONFIG[key]
    unit = cfg["canonical_unit"]
    rows = []
    for group, bands in cfg.get("standard_intervals", {}).items():
        band = bands.get("normal")
        if not band:
            continue
        low, high = band.get("min"), band.get("max")
        below = high is not None and round(high % 1, 2) >= 0.99
        if below:
            high = math.ceil(high)
        if low is not None and high is not None:
            text = f"{fmt(low)} to {'below ' if below else ''}{fmt(high)} {unit}"
        elif high is not None:
            text = f"{'below' if below else 'up to'} {fmt(high)} {unit}"
        else:
            text = f"{fmt(low)} {unit} or more"
        rows.append((GROUP_LABEL.get(group, group.title()), text))
    if len({t for _, t in rows}) == 1:
        rows = [("Adults", rows[0][1])]
    return rows


def classify_value(key: str, value: float, sex: Optional[str]) -> list[tuple[str, str]]:
    out = []
    for group, bands in BIOMARKERS_CONFIG[key].get("standard_intervals", {}).items():
        if sex and group in ("male", "female") and group != sex:
            continue
        for band_name, band in bands.items():
            low, high = band.get("min"), band.get("max")
            if (low is None or value >= low) and (high is None or value <= high):
                out.append((GROUP_LABEL.get(group, group.title()), band_name.replace("_", " ")))
                break
    return out


def problem_direction(key: str) -> Optional[str]:
    cfg = BIOMARKERS_CONFIG[key]
    if cfg.get("food_plan_on"):
        return next(iter(cfg["food_plan_on"]))
    return {"lower_is_worse": "low", "higher_is_worse": "high"}.get(cfg.get("direction"))


def plan_for(key: str, direction: Optional[str]) -> Optional[str]:
    cfg = BIOMARKERS_CONFIG[key]
    direction = direction or problem_direction(key)
    if cfg.get("food_plan_on"):
        return cfg["food_plan_on"].get(direction)
    if cfg.get("supports_food_plan", True) and cfg.get("target_nutrient_key") and direction == problem_direction(key):
        return cfg["target_nutrient_key"]
    return None


def ranked_foods(plan: str, diet: str, allergens: list[str], limit: int = 6) -> list[dict]:
    foods = ENGINE.filter_foods(UserProfile(diet_type=DietType(diet), allergens=allergens))
    if plan in TAG_PROFILES:
        ranked = ENGINE.rank_by_tags(foods, plan)
    elif plan.startswith("tag:"):
        tag = plan[4:]
        ranked = ENGINE._diverse(sorted((f for f in foods if tag in f.get("tags", [])),
                                        key=lambda f: (-len(f.get("tags", [])), f["id"])))
    else:
        ranked = ENGINE.rank_by_nutrient(foods, plan)
    return ranked[:limit]


def food_label(food: dict) -> str:
    hindi = (food.get("hindi_name") or "").split("/")[0].strip()
    if hindi and normalize(hindi) not in normalize(food["name"]):
        return f"{food['name']} ({hindi})"
    return food["name"]


def food_line(food: dict, plan: str) -> str:
    if plan in NUTRIENTS:
        name, unit = NUTRIENTS[plan]
        return f"- **{food_label(food)}**: {fmt(round(food['nutrients'].get(plan, 0), 1))} {unit} {name} per {food.get('serving_size', 'serving')}"
    tags = TAG_PROFILES.get(plan) or {plan[4:]: 1}
    labels = [TAG_LABELS[t] for t in tags if t in food.get("tags", [])]
    if plan == "protein_support" and food.get("protein_rank_g"):
        labels.insert(0, f"about {fmt(food['protein_rank_g'])} g protein per {food.get('serving_size', 'serving')}")
    return f"- **{food_label(food)}**: {', '.join(labels)}"


def foods_answer(plan: str, diet: Optional[str], allergens: list[str], heading: str, avoid: bool = False) -> str:
    chosen_diet = diet or "veg"
    foods = ranked_foods(plan, chosen_diet, allergens)
    without = f" (without {', '.join(allergens)})" if allergens else ""
    parts = [f"**{heading}**", ""]
    rules = ABSORPTION_RULES.get(plan, {})
    if avoid and rules.get("donts"):
        parts += ["**Limit or avoid:**"] + [f"- {tip}" for tip in rules["donts"]] + [""]
    if foods:
        parts.append(f"Good {DIET_LABEL[chosen_diet]} choices{without}:")
        parts += [food_line(f, plan) for f in foods]
    else:
        parts.append("I couldn't find suitable foods for that combination of diet and allergies.")
    if not avoid and rules.get("dos"):
        parts += ["", "**Tips:**"] + [f"- {tip}" for tip in rules["dos"][:2]]
    if not diet:
        parts += ["", "Showing vegetarian foods. Ask for vegan, eggetarian or non-veg options if you prefer."]
    return "\n".join(parts)


def doctor_text(key: str) -> str:
    cfg = BIOMARKERS_CONFIG[key]
    name, unit = short_name(key), cfg["canonical_unit"]
    limits = []
    if cfg.get("clinical_warning_threshold") is not None:
        limits.append(f"{fmt(cfg['clinical_warning_threshold'])} {unit} or lower")
    if cfg.get("clinical_warning_high_threshold") is not None:
        limits.append(f"{fmt(cfg['clinical_warning_high_threshold'])} {unit} or higher")
    if cfg.get("doctor_above_factor"):
        limits.append(f"more than {fmt(cfg['doctor_above_factor'])} times the upper limit of your report's range")
    text = f"NutriLens shows a doctor warning when {name} is {' or '.join(limits)}. " if limits else ""
    if cfg.get("abnormal_requires_consult"):
        text += f"Any {name} result outside the range should be reviewed by a doctor."
    else:
        text += "If it stays out of range after diet changes, or you have symptoms, please see a doctor."
    return text


def test_suggestions(key: str, used: str) -> list[str]:
    name = short_name(key)
    options = [("range", f"What is the normal range of {name}?")]
    direction = problem_direction(key)
    if plan_for(key, direction):
        options.append(("foods", f"What foods help with {direction} {name}?"))
    options += [("high", f"What does high {name} mean?"), ("low", f"What does low {name} mean?"),
                ("doctor", f"When should I see a doctor about {name}?")]
    return [q for intent, q in options if intent != used][:3]


def answer_test(key: str, intent: str, direction: Optional[str], diet, allergens, value=None, sex=None) -> Reply:
    cfg = BIOMARKERS_CONFIG[key]
    name, unit = cfg["display_name"], cfg["canonical_unit"]
    what, low_text, high_text = TEST_INFO[key]
    topic = f"test:{key}"
    if value is not None:
        verdicts = classify_value(key, value, sex)
        label = {"severe deficiency": "very low"}
        lines = [f"**Your {short_name(key)} value**", ""]
        if verdicts:
            lines += [f"- **{short_name(key) if len(verdicts) == 1 else group}**: {fmt(value)} {unit} "
                      f"({label.get(band, band)})" for group, band in verdicts]
        else:
            lines += ["I couldn't place that value in a range."]
        low_limit, high_limit = cfg.get("clinical_warning_threshold"), cfg.get("clinical_warning_high_threshold")
        if (low_limit is not None and value <= low_limit) or (high_limit is not None and value >= high_limit):
            lines += ["", "**This value is in a range that needs a doctor's review. Please see a doctor soon.**"]
        ranges = normal_ranges(key)
        lines += ["", "Usual healthy range: " + "; ".join(f"{g.lower()} {t}" for g, t in ranges) + "."]
        band = verdicts[0][1] if verdicts else ""
        if "low" in band or "deficien" in band:
            lines += ["", low_text]
        elif "high" in band:
            lines += ["", high_text]
        lines += ["", f"This assumes the value is in {unit}. Your lab's own range on the report is the best guide; "
                      "upload the report for a full analysis."]
        return Reply("\n".join(lines), suggestions=test_suggestions(key, "range"), topic=topic)
    if intent == "range":
        rows = normal_ranges(key)
        lines = [f"**Normal range for {name}**", ""] + [f"- {g}: {t}" for g, t in rows]
        lines += ["", "Labs can print slightly different ranges. NutriLens uses the range printed on your report when it is there."]
        return Reply("\n".join(lines), suggestions=test_suggestions(key, "range"), topic=topic)
    if intent in ("foods", "avoid"):
        direction = direction or problem_direction(key)
        plan = plan_for(key, direction)
        if plan:
            label = f"{direction} {short_name(key)}" if direction else short_name(key)
            heading = (f"Foods to limit with {label}" if intent == "avoid" else f"Foods that help with {label}")
            return Reply(foods_answer(plan, diet, allergens, heading, avoid=intent == "avoid"),
                         suggestions=test_suggestions(key, "foods"), topic=topic)
        text = (high_text if direction == "high" else low_text) if direction else what
        lines = [f"**{short_name(key)} and diet**", "", text, "",
                 f"Food can't reliably correct {direction + ' ' if direction else ''}{short_name(key)}, so NutriLens doesn't "
                 "give a food plan for it. Please review it with a doctor. A balanced plate with vegetables, whole grains, "
                 "pulses and enough water is still a good base."]
        return Reply("\n".join(lines), suggestions=test_suggestions(key, "foods"), topic=topic)
    if intent in ("low", "high"):
        text = low_text if intent == "low" else high_text
        lines = [f"**{intent.title()} {name}**", "", text]
        plan = plan_for(key, intent)
        if plan:
            lines += ["", f"NutriLens gives a food plan for {intent} {short_name(key)}, focused on {PLAN_NAMES.get(plan, plan)}."]
        elif cfg.get("abnormal_requires_consult"):
            lines += ["", "NutriLens flags this for a doctor's review rather than giving a food plan."]
        return Reply("\n".join(lines), suggestions=test_suggestions(key, intent), topic=topic)
    if intent == "doctor":
        lines = [f"**When to see a doctor about {short_name(key)}**", ""]
        if direction:
            lines += [low_text if direction == "low" else high_text, ""]
        lines += [doctor_text(key), "",
                  "Get help immediately for chest pain, severe breathlessness, fainting, confusion or bleeding."]
        return Reply("\n".join(lines), suggestions=test_suggestions(key, "doctor"), topic=topic)
    if intent in ("symptoms", "causes"):
        lines = [f"**{name}**", "", f"- **Low:** {low_text}", f"- **High:** {high_text}"]
        return Reply("\n".join(lines), suggestions=test_suggestions(key, intent), topic=topic)
    lines = [f"**{name}**", "", what, "", f"- **Low:** {low_text}", f"- **High:** {high_text}"]
    plans = [d for d in ("low", "high") if plan_for(key, d)]
    if plans:
        lines += ["", f"NutriLens gives a food plan when {short_name(key)} is {' or '.join(plans)}."]
    else:
        lines += ["", "NutriLens doesn't give a food plan for this test; results outside the range are flagged for a doctor."]
    return Reply("\n".join(lines), suggestions=test_suggestions(key, "what"), topic=topic)


CONCEPT_TITLES = {
    "iron": "iron", "blood_sugar": "diabetes", "cholesterol": "cholesterol", "uric_acid": "uric acid",
    "liver": "liver health", "kidney": "kidney health", "thyroid": "thyroid", "vitamin_d": "vitamin D",
    "vitamin_b12": "vitamin B12", "folate": "folate", "calcium": "calcium", "protein": "protein",
    "vitamin_c": "vitamin C", "fibre": "fibre", "low_gi": "low-GI foods", "omega3": "omega-3",
    "cbc": "the CBC test", "electrolytes": "electrolytes",
}


def concept_suggestions(key: str, used: str) -> list[str]:
    concept = CONCEPTS[key]
    topic = CONCEPT_TITLES.get(key, concept["words"][0])
    options = []
    if concept["plan"]:
        options += [("foods", f"Which foods are good for {topic}?"), ("avoid", f"What should I avoid for {topic}?")]
    if concept["test"]:
        options.append(("range", f"What is the normal range of {short_name(concept['test'])}?"))
    options.append(("what", f"Tell me about {topic}"))
    return [q for intent, q in options if intent != used][:3] or ["Which tests are supported?"]


def answer_concept(key: str, intent: str, direction, diet, allergens) -> Reply:
    concept = CONCEPTS[key]
    topic = f"concept:{key}"
    title = CONCEPT_TITLES.get(key, concept["words"][0])
    if intent in ("range", "low", "high", "doctor", "symptoms", "causes") and concept["test"]:
        reply = answer_test(concept["test"], intent, direction, diet, allergens)
        if key == "electrolytes" or key == "kidney" or key == "thyroid":
            reply.reply = concept["about"] + "\n\n" + reply.reply
        return reply
    if intent in ("foods", "avoid"):
        if concept["plan"]:
            plan = concept["plan"]
            heading = f"Foods to limit for {PLAN_NAMES[plan]}" if intent == "avoid" else f"Foods for {PLAN_NAMES[plan]}"
            if intent == "avoid" and not ABSORPTION_RULES.get(plan, {}).get("donts"):
                heading = f"Foods for {PLAN_NAMES[plan]}"
            return Reply(foods_answer(plan, diet, allergens, heading, avoid=intent == "avoid"),
                         suggestions=concept_suggestions(key, intent), topic=topic)
        lines = [f"**{title[0].upper() + title[1:]} and diet**", "", concept["about"], "",
                 "Please follow your doctor's or dietitian's advice for diet with this condition."]
        return Reply("\n".join(lines), suggestions=concept_suggestions(key, intent), topic=topic)
    lines = [concept["about"]]
    if concept["plan"]:
        foods = ranked_foods(concept["plan"], diet or "veg", allergens, limit=4)
        if foods:
            lines += ["", "A few good " + DIET_LABEL[diet or "veg"] + " foods: " + ", ".join(food_label(f) for f in foods) + "."]
    return Reply("\n".join(lines), suggestions=concept_suggestions(key, "what"), topic=topic)


DIET_TEXT = {"vegan": "Suitable for everyone, including vegans.", "veg": "Suitable for vegetarians.",
             "eggetarian": "Suitable for eggetarians and non-vegetarians.", "non_veg": "Non-vegetarian."}


def food_rank(food: dict, plan: str) -> tuple[int, int]:
    amount = lambda f: f.get("nutrients", {}).get(plan, 0) or 0
    ranked = sorted(FOODS_DATABASE, key=lambda f: -amount(f))
    return ranked.index(food) + 1, len(ranked)


def answer_food(food: dict, concept: Optional[str], diet, allergens) -> Reply:
    lines = [f"**{food_label(food)}**: {food['category'].lower()}", ""]
    diets = food.get("diet_type", [])
    lines.append(next(DIET_TEXT[d] for d in ("vegan", "veg", "eggetarian", "non_veg") if d in diets))
    plan = CONCEPTS[concept]["plan"] if concept else None
    if plan in NUTRIENTS:
        name, unit = NUTRIENTS[plan]
        amount = food["nutrients"].get(plan, 0) or 0
        position, total = food_rank(food, plan)
        if amount and position <= 40:
            lines += ["", f"**Yes.** It has {fmt(round(amount, 1))} {unit} {name} per {food.get('serving_size', 'serving')}, ranking #{position} of {total} foods for {name}."]
        else:
            better = ranked_foods(plan, diet or "veg", allergens, limit=3)
            lines += ["", f"It isn't a strong source of {name} ({fmt(round(amount, 1))} {unit} per {food.get('serving_size', 'serving')}). Better options: "
                          + ", ".join(food_label(f) for f in better) + "."]
    elif plan:
        weights = TAG_PROFILES.get(plan) or {plan[4:]: 1}
        helpful = [TAG_LABELS[t] for t in weights if t in food.get("tags", [])]
        if helpful:
            lines += ["", f"**Yes**, it suits {PLAN_NAMES[plan]}: {', '.join(helpful)}."]
        else:
            better = ranked_foods(plan, diet or "veg", allergens, limit=3)
            lines += ["", f"It isn't one of the best choices for {PLAN_NAMES[plan]}. Better options: "
                          + ", ".join(food_label(f) for f in better) + "."]
    nutrients = []
    for key, (name, unit) in NUTRIENTS.items():
        amount = food.get("nutrients", {}).get(key) or 0
        if amount >= (1 if unit in ("mg", "IU") else 0.5):
            nutrients.append(f"{name} {fmt(round(amount, 1))} {unit}")
    if food.get("protein_rank_g"):
        nutrients.insert(0, f"protein about {fmt(food['protein_rank_g'])} g")
    if nutrients:
        lines += ["", "**Per 100 g:** " + ", ".join(nutrients) + "."]
    tags = [TAG_LABELS[t] for t in food.get("tags", []) if t in TAG_LABELS]
    if tags:
        lines.append("**Good for:** " + ", ".join(tags) + ".")
    if food.get("allergens"):
        lines.append("**Contains:** " + ", ".join(food["allergens"]) + ".")
    if food.get("synergies"):
        lines += ["", food["synergies"][0]]
    if food.get("tip"):
        lines += ["", "**Tip:** " + food["tip"]]
    short = food["name"].split(" /")[0].split(" (")[0]
    options = [("blood_sugar", f"Is {short} good for diabetes?"), ("iron", f"Is {short} good for iron?"),
               ("cholesterol", f"Is {short} good for cholesterol?"), ("calcium", "Which foods are rich in calcium?")]
    return Reply("\n".join(lines), topic=f"food:{food['id']}",
                 suggestions=[q for key, q in options if key != concept][:3])


# --------------------------------------------------------------------------------------------------------------------
# Personal answers from the user's own analysed results
# --------------------------------------------------------------------------------------------------------------------

def _num(value: Any) -> str:
    return fmt(round(value, 2)) if isinstance(value, (int, float)) else str(value)


def personal_marker(marker: dict, plans: list[dict]) -> Reply:
    key = marker.get("key", "")
    name = marker.get("name") or (BIOMARKERS_CONFIG[key]["display_name"] if key in BIOMARKERS_CONFIG else key)
    status = (marker.get("status") or "").lower()
    low, high = marker.get("range_low"), marker.get("range_high")
    rng = f" (range {_num(low)} to {_num(high)})" if low is not None and high is not None else ""
    lines = [f"Your **{name}** is **{_num(marker.get('value'))} {marker.get('unit', '')}**{rng}, which is **{status or 'recorded'}**."]
    info = TEST_INFO.get(key)
    if info and status == "low":
        lines += ["", info[1]]
    elif info and status == "high":
        lines += ["", info[2]]
    elif status == "borderline":
        lines += ["", "It's at the edge of the healthy range, so it's worth keeping an eye on."]
    elif status == "normal":
        lines += ["", "That's in the healthy range."]
    for plan in plans:
        if normalize(name) in normalize(plan.get("name", "")) or normalize(plan.get("name", "")) in normalize(name):
            foods = plan.get("foods", [])[:4]
            if foods:
                lines += ["", f"Your food plan for it includes {', '.join(foods)}."]
            break
    if key in BIOMARKERS_CONFIG and status in ("low", "high") and BIOMARKERS_CONFIG[key].get("abnormal_requires_consult"):
        lines += ["", "Please review this result with a doctor."]
    short = short_name(key) if key in BIOMARKERS_CONFIG else name
    return Reply("\n".join(lines), topic=f"test:{key}" if key in BIOMARKERS_CONFIG else None,
                 suggestions=([f"What foods help with {status} {short}?"] if status in ("low", "high") else [])
                 + ["Summarise my results", "What should I eat?"])


# Everyday words for a body area -> the report categories that hold those tests (for "is my sugar high?").
TOPIC_CATEGORIES = [
    (re.compile(r"\b(sugar|diabet\w*|glucose|hba1c|insulin)\b"), {"Blood Sugar Control"}),
    (re.compile(r"\b(thyroid|tsh|t3|t4)\b"), {"Thyroid Function"}),
    (re.compile(r"\b(cholesterol|lipid\w*|ldl|hdl|triglyceride\w*|heart)\b"), {"Blood Fats (Lipids)"}),
    (re.compile(r"\b(iron|anaemi\w*|anemi\w*|haemoglobin|hemoglobin|hb|blood count|cbc|ferritin)\b"),
     {"Iron Studies", "Hematology", "Complete Blood Count"}),
    (re.compile(r"\b(kidney\w*|creatinine|urea|uric)\b"), {"Kidney Function"}),
    (re.compile(r"\b(liver|sgpt|sgot|alt|ast|bilirubin)\b"), {"Liver Function"}),
    (re.compile(r"\b(vitamin\w*|b12|vit d|vitamin d)\b"), {"Fat-Soluble Vitamin", "Water-Soluble Vitamin"}),
]
AVOID_PERSONAL = re.compile(r"\b(avoid|limit|not eat|stop eating|bad for me|should not eat|shouldnt eat|cut down)\b")
NORMAL_PERSONAL = re.compile(r"\b(normal|fine|good|ok|okay|in range|healthy)\b.*\b(results?|tests?|values?)\b|"
                             r"\bwhich (results?|tests?|values?) (are|is) (normal|fine|good|ok)\b")
PLAN_PERSONAL = re.compile(r"\b(diet plan|meal plan|7 day|weekly plan|my plan|today'?s? (meals?|menu))\b")


def personal_topic(text: str, context: dict) -> Optional[Reply]:
    """'is my sugar high?', 'do I have diabetes?', 'is my thyroid normal?': the person's own results in that area."""
    markers = context.get("markers") or []
    for pattern, categories in TOPIC_CATEGORIES:
        if pattern.search(text):
            own = [m for m in markers if BIOMARKERS_CONFIG.get(m.get("key"), {}).get("category") in categories]
            if own:
                reply = _join([personal_marker(m, context.get("plans", [])) for m in own[:4]])
                if re.search(r"\b(diabet\w*|do i have|am i)\b", text):
                    reply.reply += ("\n\nNutriLens can't diagnose a condition. Please ask your doctor what these "
                                    "results mean for you.")
                return reply
            names = ", ".join(sorted(categories)).lower()
            return Reply(f"Your report doesn't include tests for this ({names}), so I can't tell from it. "
                         "A doctor can advise which tests to do.", suggestions=_suggest(context))
    return None


def personal_normal(context: dict) -> Reply:
    normal = [m for m in context.get("markers") or [] if (m.get("status") or "").lower() == "normal"]
    if not normal:
        return Reply("None of your results is in the normal range in this report. Ask me about any one of them.",
                     suggestions=_suggest(context))
    lines = [f"**{len(normal)} of your results {'is' if len(normal) == 1 else 'are'} in the healthy range:**", ""]
    lines += [f"- **{m.get('name')}**: {_num(m.get('value'))} {m.get('unit', '')}" for m in normal]
    return Reply("\n".join(lines), suggestions=_suggest(context))


def personal_avoid(context: dict) -> Optional[Reply]:
    """Foods to limit for this person's out-of-range results (the same rules as their food plan)."""
    diet = context.get("diet_type") if context.get("diet_type") in DIET_LABEL else None
    allergens = [a.lower() for a in context.get("allergens") or []]
    parts, seen = [], set()
    for m in context.get("markers") or []:
        status = (m.get("status") or "").lower()
        if status not in ("low", "high", "borderline"):
            continue
        direction = "high" if status == "high" else "low" if status == "low" else problem_direction(m.get("key"))
        plan = plan_for(m.get("key"), direction)
        if plan and plan not in seen and ABSORPTION_RULES.get(plan, {}).get("donts"):
            seen.add(plan)
            parts.append(foods_answer(plan, diet, allergens, f"To limit for your {m.get('name')}", avoid=True))
    if not parts:
        return None
    return Reply("\n\n".join(parts[:3]), suggestions=_suggest(context))


def personal_week(context: dict) -> Optional[Reply]:
    plan = context.get("diet_plan") or {}
    days = plan.get("days") or []
    if not days:
        return None
    first = days[0]
    lines = [f"**Your 7-day plan** ({plan.get('style') or 'your chosen'} style), day 1, about {first.get('kcal', '?')} kcal:", ""]
    for slot, names in (first.get("meals") or {}).items():
        if names:
            lines.append(f"- **{slot.title()}**: {', '.join(names)}")
    lines += ["", "Open **2. Diet plan** to see every day, swap a dish or get the shopping list."]
    return Reply("\n".join(lines), suggestions=["Can I swap a dish?", "Where is the shopping list?"])


def personal_summary(context: dict) -> Reply:
    markers = context.get("markers", [])
    flagged = [m for m in markers if (m.get("status") or "").lower() not in ("normal", "")]
    if not markers:
        return Reply("I don't have your results yet. Analyse a report and I can answer using your own values.")
    if not flagged:
        return Reply(f"Good news: all **{len(markers)}** results in your report are in the healthy range. Your food plan "
                     "suggests a few foods to keep them there.", suggestions=["What should I eat?", "Is my data private?"])
    lines = [f"**{len(flagged)} of {len(markers)}** results need attention:", ""]
    for m in flagged:
        lines.append(f"- **{m.get('name') or m.get('key')}**: {_num(m.get('value'))} {m.get('unit', '')} ({m.get('status')})")
    improve = [p.get("name") for p in context.get("plans", []) if p.get("purpose", "improve") == "improve"]
    if improve:
        lines += ["", "Your food plan covers: " + ", ".join(improve) + "."]
    rest = len(markers) - len(flagged)
    if rest:
        lines += ["", f"The other {rest} result{'s are' if rest > 1 else ' is'} in the healthy range."]
    first = flagged[0].get("name") or flagged[0].get("key")
    return Reply("\n".join(lines), suggestions=["What should I eat?", f"What does my {first} mean?", "When should I see a doctor?"])


def personal_plan(context: dict) -> Reply:
    plans = context.get("plans", [])
    if not plans:
        return Reply("Your results don't need a specific food plan. A balanced plate with vegetables, whole grains, pulses "
                     "and enough water will keep them healthy.", suggestions=["What is a healthy diet?"])
    lines = ["**Your food plan at a glance**", ""]
    for plan in plans:
        foods = ", ".join(plan.get("foods", [])[:3])
        label = "keep healthy" if plan.get("purpose") == "maintain" else "improve"
        lines.append(f"- **{plan.get('name')}** ({label}): {foods}")
    lines += ["", "Open each plan on the results page for the full list, tips and foods to limit."]
    return Reply("\n".join(lines), suggestions=["Summarise my results", "Can I download my plan?"])


def personal_food_reason(food: dict, context: dict) -> Optional[Reply]:
    target = normalize(food["name"])
    for plan in context.get("plans", []):
        if any(normalize(f) == target for f in plan.get("foods", [])):
            reason = "to keep it healthy" if plan.get("purpose") == "maintain" else "to help bring it back into range"
            text = (f"**{food_label(food)}** is in your food plan for **{plan.get('name')}**, {reason}.\n\n"
                    + answer_food(food, None, None, []).reply.split("\n", 2)[-1])
            return Reply(text, topic=f"food:{food['id']}", suggestions=["What should I eat?", "Summarise my results"])
    return None


# --------------------------------------------------------------------------------------------------------------------
# Safety, small talk and scope
# --------------------------------------------------------------------------------------------------------------------

SELF_HARM = re.compile(r"\b(suicid\w*|kill myself|end my life|want to die|self harm|hurt myself|no reason to live|"
                       r"dont want to live|take my life)\b")
EMERGENCY = re.compile(r"\b(chest pain|pain in (?:my |the )?chest|chest (?:is )?(?:hurting|paining|tightness|tight)|"
                       r"heart attack|cant breathe|cannot breathe|can not breathe|difficulty breathing|"
                       r"trouble breathing|not breathing|unconscious|fainted|fainting|passed out|seizure|seizures|fits|"
                       r"stroke|paralys\w*|severe bleeding|bleeding heavily|heavy bleeding|vomiting blood|coughing blood|"
                       r"blood in vomit|black stool|overdose|poisoning|swallowed poison|collapsed?|collapsing|"
                       r"not responding|unresponsive|choking|cannot wake|cant wake|anaphyla\w*|severe allergic)\b")
INJECTION = re.compile(r"\b(ignore (all |your |the |previous |prior |above )*(instructions|rules|prompt)|system prompt|"
                       r"you are now|pretend (to be|you are)|act as|jailbreak|developer mode|reveal your|disregard)\b")
ABUSE = re.compile(r"\b(fuck\w*|shit\w*|bitch\w*|bastard|asshole|dumb ?ass|idiot|stupid|moron|useless|madarchod|bhenchod|"
                   r"behenchod|chutiya|chutiye|gandu|harami|kamina|bc|mc|wtf|stfu|shut up)\b")
MEDICINE = re.compile(r"\b(tablets?|capsules?|pills?|medicines?|medications?|drugs?|dose|dosage|doses|insulin|metformin|"
                      r"levothyroxine|thyronorm|eltroxin|statins?|atorvastatin|rosuvastatin|injections?|antibiotics?|"
                      r"painkillers?|paracetamol|dolo|prescri\w*|supplements?|multivitamins?|sachets?|ayurvedic|homeopath\w*)\b")
MEDICAL = re.compile(r"\b(fever|cough|cold|headache|migraine|vomit\w*|diarrh\w*|loose motion|rash|infection|covid|corona|"
                     r"cancer|tumou?r|hiv|aids|tb|tuberculosis|malaria|typhoid|dengue|asthma|pcos|pcod|period|periods|"
                     r"menstrua\w*|injury|fracture|wound|pain|ache|surgery|operation|x ray|mri|ct scan|ecg|ultrasound|"
                     r"allergy test|blood pressure reading)\b")

DRUGS = re.compile(r"\b(tablets?|capsules?|pills?|dose|dosage|doses|insulin|metformin|levothyroxine|thyronorm|"
                   r"eltroxin|statins?|atorvastatin|rosuvastatin|injections?|inject|antibiotics?|painkillers?|"
                   r"paracetamol|dolo|prescri\w*|sachets?|syrups?|tonics?|drops)\b")
GREETING = re.compile(r"^(hi+|hello+|hey+|hai|hola|namaste|namaskar|good (morning|afternoon|evening|night)|yo|sup|greetings)\b")
THANKS = re.compile(r"\b(thanks?|thank you|thx|ty|tq|thanku|dhanyavad|shukriya|appreciate)\b")
BYE = re.compile(r"^(bye+|goodbye|good bye|see you|see ya|tata|cya|take care)\b")
HOW_ARE_YOU = re.compile(r"\b(how are you|how r you|how are u|hows it going|how do you do|whats up|wassup)\b")
WHO = re.compile(r"\b(who are you|what are you|your name|are you (a )?(bot|robot|human|real|ai|person|chatgpt|gpt)|"
                 r"who am i talking|are you a doctor)\b")
CAPABILITY = re.compile(r"\b(what can you do|how can you help|what can i ask|what do you know|help me|can you help|"
                        r"what questions|what should i ask|help)\b")
ACK = re.compile(r"^(ok|okay|k|kk|cool|nice|great|good|fine|got it|alright|hmm+|oh|ohh|wow|super|perfect|awesome|sure|"
                 r"yes|yeah|yep|no|nope|nah|right|correct|understood|sounds good|i see)$")
PERSONAL = re.compile(r"\b(my|mine|me|i|im|i am|ive)\b")
SUMMARY = re.compile(r"\b(summar\w*|overview|my (report|results?|tests?|values?|levels?)|which (results?|tests?|values?)|"
                     r"am i (healthy|ok|okay|fine|normal|alright)|anything (wrong|abnormal|bad)|what is wrong|whats wrong|"
                     r"abnormal|out of range|explain my report)\b")
EAT_PERSONAL = re.compile(r"\b(what|which)\b.*\b(eat|food|foods|diet|plan)\b|\bmy (diet|food|plan|food plan|diet plan)\b")

CODE = re.compile(r"(<\s*/?\s*(script|img|iframe|svg|a|b|div)\b|\bselect\b.*\bfrom\b|\bdrop table\b|\binsert into\b|"
                  r"\bfunction\s*\(|\bconsole\.|\bimport\s+\w+|\{\{|\$\{|;\s*--)")
UNSUPPORTED_TEST = re.compile(
    r"\b(vitamin (a|b1|b2|b3|b5|b6|b7|e|k)|zinc|magnesium|copper|selenium|cortisol|testosterone|oestrogen|estrogen|"
    r"progesterone|prolactin|lh|fsh|amh|psa|insulin (test|level)|c peptide|lipase|amylase|troponin|d dimer|ige|"
    r"beta hcg|hcg|hbsag|hiv test|widal|ns1|homocysteine|lipoprotein a|apolipoprotein|ana test|rheumatoid factor|"
    r"ra factor|aso titre|procalcitonin|ldh|cpk|bnp|inr|aptt|blood group|g6pd|ammonia|lactate|bicarbonate|"
    r"urine routine|stool test|semen analysis|allergy panel)\b")
MANUAL_ENTRY = re.compile(r"\b(add|enter|type|put|input|fill)\b.*\b(manually|myself|by hand|on my own)\b")
UNIT_QUESTION = re.compile(r"(?=.*\b(units?|mmol|nmol|mg dl|ng ml|iu|lakhs?|lacs?)\b)"
                           r"(?=.*\b(lab|labs|report|use|uses|give|gives|written|shows?|convert\w*|which|different|choose)\b)")
SITE_WORDS = {
    "upload", "report", "pdf", "jpeg", "jpg", "png", "photo", "picture", "image", "file", "account", "login", "logout",
    "password", "history", "profile", "guest", "chat", "chats", "site", "website", "app", "mobile", "phone", "browser",
    "privacy", "cookies", "ads", "admin", "invite", "email", "register", "plan", "diet", "score", "review", "units",
    "page", "button", "download", "print", "share", "delete", "nutrilens", "ocr", "error", "slow", "loading", "docs",
    "document", "results", "result", "free", "cost", "safe", "secure", "data", "stored", "store", "saved", "save",
    "doctor", "dietitian", "food", "foods", "test", "tests", "lab", "value", "values",
}
APP_WORDS = re.compile(r"\b(manually|by myself|upload\w*|download\w*|pdf|history|save[ds]?|delete|account|login|log in|sign (up|in)|"
                       r"password|register|website|app|site|nutrilens|privacy|private|stored?|data)\b")

DEFAULT_SUGGESTIONS = ["What foods help with low haemoglobin?", "What is HbA1c?", "How do I upload my report?",
                       "Is my data private?"]
CONTEXT_SUGGESTIONS = ["Summarise my results", "What should I eat?", "When should I see a doctor?"]

SCOPE_LINE = ("I'm the NutriLens assistant, so I can help with **blood test results, food and nutrition, and using "
              "NutriLens**.")


def _suggest(context: Optional[dict]) -> list[str]:
    return CONTEXT_SUGGESTIONS if context and context.get("markers") else DEFAULT_SUGGESTIONS[:3]


def safety_and_smalltalk(text: str, raw: str, context: Optional[dict], has_entity: bool) -> Optional[Reply]:
    if SELF_HARM.search(text):
        return Reply("I'm really sorry you're feeling this way. You don't have to go through it alone.\n\n"
                     "- **Tele-MANAS (free, 24×7, India): 14416** or 1-800-891-4416\n"
                     "- **Emergency: 112**\n\n"
                     "Please reach out to one of them now, or to someone you trust nearby.", kind="safety")
    if EMERGENCY.search(text):
        return Reply("This sounds like it could be an emergency. **Please call 112 or 108 for an ambulance, or go to the "
                     "nearest emergency department now.**\n\nI'm an information assistant and can't help in an emergency.",
                     kind="safety")
    if INJECTION.search(text):
        return Reply(SCOPE_LINE + " I can't change how I work, but I'm happy to help with a question about your report.",
                     kind="refuse", suggestions=_suggest(context), topic="injection")
    if ABUSE.search(text):
        return Reply("I'm here to help. If something isn't working the way you expected, tell me what you're trying to do "
                     "and I'll do my best.", kind="refuse", suggestions=_suggest(context), topic="abuse")
    letters = re.findall(r"[^\W\d_]", raw)
    if letters and sum(1 for ch in letters if ord(ch) > 127) / len(letters) > 0.5:
        return Reply("Sorry, I can only understand **English** for now. Please ask in English, for example: "
                     "\"What foods help with low haemoglobin?\"", kind="fallback", suggestions=_suggest(context),
                     topic="non_english")
    if has_entity:
        return None
    words = text.split()
    if WHO.search(text):
        return Reply("I'm the **NutriLens assistant**, an automated helper (not a person or a doctor). I answer from "
                     "NutriLens's checked knowledge of blood tests and Indian foods, and from your own results once you "
                     "analyse a report.", kind="smalltalk", suggestions=_suggest(context))
    if HOW_ARE_YOU.search(text):
        return Reply("I'm doing well, thanks for asking! How can I help with your report or diet today?",
                     kind="smalltalk", suggestions=_suggest(context))
    if THANKS.search(text) and len(words) <= 8:
        return Reply("You're welcome! Is there anything else you'd like to know?", kind="smalltalk",
                     suggestions=_suggest(context))
    if BYE.search(text) and len(words) <= 5:
        return Reply("Take care! Come back any time you have a question about your report.", kind="smalltalk")
    if GREETING.search(text) and len(words) <= 4:
        return Reply("Hello! I'm the NutriLens assistant. Ask me about your blood test results, foods for a nutrient, or "
                     "how to use NutriLens.", kind="smalltalk", suggestions=_suggest(context))
    if CAPABILITY.search(text) and len(words) <= 8:
        return Reply("I can help you with:\n\n"
                     "- **Your results:** what a test means and whether your value is normal\n"
                     "- **Foods:** Indian foods for iron, vitamin D, B12, calcium, blood sugar, cholesterol and more, "
                     "for your diet and allergies\n"
                     "- **Using NutriLens:** uploading reports, the review step, your plan, PDF and history\n"
                     "- **Privacy and safety:** how your data is handled and when to see a doctor",
                     kind="smalltalk", suggestions=_suggest(context))
    if ACK.match(text):
        return Reply("Glad that helps. Is there anything else you'd like to know?", kind="smalltalk",
                     suggestions=_suggest(context))
    return None


# --------------------------------------------------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------------------------------------------------

def _extract_value(raw: str) -> Optional[float]:
    text = raw.lower()
    text = re.sub(r"\b(b ?12|b ?9|t ?3|t ?4|ft ?3|ft ?4|hba1c|a1c|25 ?\(?oh\)?|d ?3|omega ?3|3 ?months?)\b", " ", text)
    numbers = re.findall(r"(?<![\w.])(\d+(?:\.\d+)?)", text)
    return float(numbers[0]) if len(numbers) == 1 else None


def _detect_sex(text: str) -> Optional[str]:
    if re.search(r"\b(female|woman|women|girl|lady|ladies|she|her|wife|mother|mom)\b", text):
        return "female"
    if re.search(r"\b(male|man|men|boy|he|him|husband|father|dad)\b", text):
        return "male"
    return None


def find_entities(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for match in _PHRASE_RE.finditer(text):
        for entity in PHRASES[match.group("p")]:
            if entity not in found:
                found.append(entity)
    return found


def answer(message: str, topic: Optional[str] = None, context: Optional[dict] = None) -> Reply:
    raw = (message or "").strip()
    if not raw:
        return Reply("Please type a question, for example: \"What foods help with low vitamin D?\"", kind="fallback",
                     suggestions=_suggest(context))
    raw = raw[:500]
    text = clean(raw)
    allergens, text_for_foods = detect_allergens(text)
    if context and context.get("allergens"):
        allergens = sorted(set(allergens) | {a.lower() for a in context["allergens"]})
    diet = detect_diet(text) or (context.get("diet_type") if context else None)
    if diet not in DIET_LABEL:
        diet = None
    entities = [e for e in find_entities(text_for_foods)]
    tests = [k for kind, k in entities if kind == "test"]
    concepts = [k for kind, k in entities if kind == "concept"]
    foods = [k for kind, k in entities if kind == "food"]

    # Safety patterns also run on the uncorrected text, so spelling correction can never hide them.
    # Drop a leading greeting ("hi, is it free") when a real question follows it.
    rest = GREETING.sub("", text).strip()
    if rest and len(rest.split()) >= 2:
        text = rest
    early = (safety_and_smalltalk(normalize(raw), raw, context, True)
             or safety_and_smalltalk(text, raw, context, bool(entities)))
    if early:
        if early.topic == "non_english":  # Hindi or Telugu: the e5 model finds the answer or safety topic it means
            return _semantic_reply(raw, context) or early
        return early
    if CODE.search(raw.lower()):
        return Reply(SCOPE_LINE + " I can't help with that one, but feel free to ask me about your report or diet.",
                     kind="refuse", suggestions=_suggest(context))
    if UNSUPPORTED_TEST.search(text) and not (tests or concepts):
        return _faq_reply(next(i for i, f in enumerate(FAQ) if f[0] == "unsupported_test"))
    if MANUAL_ENTRY.search(text):
        return _faq_reply(next(i for i, f in enumerate(FAQ) if f[0] == "edit_values"))
    if UNIT_QUESTION.search(text) and not re.search(r"\d", raw):
        return _faq_reply(next(i for i, f in enumerate(FAQ) if f[0] == "units"))

    intents = detect_intents(text)
    intent, direction = primary_intent(intents), direction_of(intents)

    if DRUGS.search(text) or (MEDICINE.search(text) and not re.search(r"\b(food|foods|eat|diet)\b", text)):
        follow = []
        concept = next(iter(concepts), None) or next((c for c, v in CONCEPTS.items() if v.get("test") in tests), None)
        if concept and CONCEPTS[concept]["plan"]:
            follow = [f"Which foods are good for {CONCEPT_TITLES.get(concept, concept)}?"]
        return Reply("I can't advise on **medicines, supplements or doses**; that depends on your full health picture, so "
                     "please ask your doctor before starting, stopping or changing any of them.\n\nWhat I can do is suggest "
                     "foods that are naturally rich in what you need.", kind="refuse",
                     suggestions=follow + ["Which foods are rich in iron?", "Which foods are rich in vitamin D?"],
                     topic="medicine")

    faq_hits = faq_search(text)
    named_now = [m.group("p") for m in _PHRASE_RE.finditer(text_for_foods)]
    if named_now and len(faq_hits) > 1:
        def names_all(index):
            return all(any(re.search(rf"(?<![a-z0-9]){re.escape(n)}(?:s|es)?(?![a-z0-9])", normalize(q))
                           for q in FAQ[index][1]) for n in named_now)
        close = [h for h in faq_hits if h[0] >= faq_hits[0][0] - 0.1]
        preferred = [h for h in close if names_all(h[1])]
        if preferred and preferred[0] != faq_hits[0]:
            faq_hits = [preferred[0]] + [h for h in faq_hits if h != preferred[0]]
    faq_hits = _fuse(raw, faq_hits)
    faq_conf = faq_hits[0][0] if faq_hits else 0.0
    app_question = bool(APP_WORDS.search(text))
    has_context = bool(context and context.get("markers"))
    personal = bool(PERSONAL.search(text)) and not app_question

    # A short follow-up with no new subject ("is it serious?", "foods for it", "and the normal range?") continues the
    # previous topic instead of being matched against the FAQ.
    follow_up = (topic and not entities and len(text.split()) <= 8 and not app_question
                 and (re.search(r"\b(it|its|that|this|them|those|these|and|also|more|same)\b", text)
                      or intent in ("range", "low", "high", "foods", "avoid", "doctor", "symptoms", "causes")))
    if follow_up and not (has_context and personal and (SUMMARY.search(text) or EAT_PERSONAL.search(text))):
        reply = _topic_reply(topic, intent, direction, diet, allergens)
        if reply:
            return reply

    if has_context and personal:
        if PLAN_PERSONAL.search(text) and context.get("diet_plan"):
            return personal_week(context)
        if AVOID_PERSONAL.search(text):
            reply = personal_avoid(context)
            if reply:
                return reply
        if NORMAL_PERSONAL.search(text):
            return personal_normal(context)
        own_tests = [k for k in tests if any(m.get("key") == k for m in context["markers"])]
        if not own_tests:
            reply = personal_topic(text, context)
            if reply:
                return reply
    if has_context and personal and not entities and SUMMARY.search(text):
        return personal_summary(context)
    if has_context and personal and not entities and EAT_PERSONAL.search(text):
        return personal_plan(context)

    # With a test or food named, the FAQ wins only if its own phrasings name it too ("does tea affect iron").
    named = [m.group("p") for m in _PHRASE_RE.finditer(text_for_foods)]
    faq_names_them = bool(faq_hits) and all(
        any(re.search(rf"(?<![a-z0-9]){re.escape(n)}(?:s|es)?(?![a-z0-9])", normalize(q)) for q in FAQ[faq_hits[0][1]][1])
        for n in named)
    food_complaint = False
    if faq_hits and foods and not tests and not concepts and re.search(
            r"\b(suggest\w*|recommend\w*|show\w*|gave|giving|included|in my plan)\b", text):
        faq_kinds = {kind for q in FAQ[faq_hits[0][1]][1] for kind, _ in find_entities(normalize(q))}
        food_complaint = "food" in faq_kinds
    # "How much protein a day" is a requirement question, not a food list.
    asks_amount = "amount" in canon(text).split()
    asks_why_not = bool(re.search(r"\b(why|no|not)\b", text))
    faq_wins = faq_hits and (
        (faq_conf >= 0.72 and (not entities or app_question
                               or faq_conf >= (0.95 if intent == "what" and (tests or concepts) else 0.85)))
        or (faq_names_them and faq_conf >= 0.75 and intent not in ("foods", "avoid")
            and not (intent == "what" and (tests or concepts)))
        or (faq_names_them and faq_conf >= 0.6 and (asks_amount or asks_why_not))
        or (food_complaint and faq_conf >= 0.6))
    if faq_wins:
        return _faq_reply(faq_hits[0][1])

    if has_context:
        markers = {m.get("key"): m for m in context["markers"]}
        if foods and re.search(r"\b(why|plan|suggest\w*|recommend\w*|included|listed)\b", text):
            reply = personal_food_reason(FOODS_BY_ID[foods[0]], context)
            if reply:
                return reply
        own = [k for k in tests if k in markers]
        if not own:
            own = [CONCEPTS[c]["test"] for c in concepts if CONCEPTS[c].get("test") in markers]
        if own and personal and intent not in ("foods", "avoid", "range"):
            return personal_marker(markers[own[0]], context.get("plans", []))
        if not entities and SUMMARY.search(text) and "which" in text:
            return personal_summary(context)
    elif personal and not entities and faq_conf < 0.5 and (SUMMARY.search(text) or EAT_PERSONAL.search(text)):
        return Reply("I don't have your results yet. **Upload your report** on the home page and, once it's analysed, I can "
                     "answer using your own values and food plan.", kind="answer",
                     suggestions=["How do I upload my report?", "Which tests are supported?"])

    if entities:
        return _entity_reply(raw, text, tests, concepts, foods, intent, direction, diet, allergens)

    if faq_hits and faq_conf >= 0.5:
        return _faq_reply(faq_hits[0][1])

    if MEDICAL.search(text):
        return Reply("I can't advise on symptoms or illnesses. Please see a doctor, or call **112 / 108** if it's urgent.\n\n"
                     + SCOPE_LINE, kind="refuse", suggestions=_suggest(context))

    in_domain = bool(set(text.split()) & (DOMAIN_WORDS | SITE_WORDS))
    second = faq_hits[1][0] if len(faq_hits) > 1 else 0.0
    if faq_hits and in_domain and faq_conf >= 0.34 and faq_conf - second >= 0.06:
        return _faq_reply(faq_hits[0][1])
    if faq_hits and faq_conf >= 0.3 and in_domain:
        options = []
        for _, index in faq_hits[:3]:
            options.append(FAQ[index][1][0][0].upper() + FAQ[index][1][0][1:] + "?")
        return Reply("I can help with a few things close to that. Which one did you mean?", kind="clarify",
                     suggestions=options)

    semantic = _semantic_reply(raw, context)
    if semantic:
        return semantic
    if in_domain:
        return Reply("I don't have a good answer for that yet. Try asking about a specific test, nutrient or food, for "
                     "example: \"What foods help with low vitamin D?\"", kind="fallback", suggestions=_suggest(context))
    return Reply(SCOPE_LINE + " I can't help with that one, but feel free to ask me about your report or diet.",
                 kind="refuse", suggestions=_suggest(context))


# Fixed replies the e5 model's safety topics lead to (the same replies the English patterns give).
_SAFETY_PROBES = {"safety:emergency": "I have severe chest pain right now", "safety:self_harm": "I want to end my life",
                  "safety:medicine": "which tablet should i take for iron"}


def _semantic_reply(raw: str, context: Optional[dict]) -> Optional[Reply]:
    """An FAQ answer or safety reply for a question the patterns did not place, in any of the three languages."""
    from app.nlp import embed
    label, _score = embed.match_question(raw)
    if not label:
        return None
    if label in _SAFETY_PROBES:
        return answer(_SAFETY_PROBES[label], None, context)
    faq_id = label.split(":", 1)[1]
    index = next((i for i, f in enumerate(FAQ) if f[0] == faq_id), None)
    return _faq_reply(index) if index is not None else None


_FAQ_INDEX = {f[0]: i for i, f in enumerate(FAQ)}


def _fuse(raw: str, faq_hits: list) -> list:
    """Rank FAQ answers by meaning (e5 model) plus word overlap (rules): measured 96% / 89% top-1 on the hand-written
    and held-out question sets, against 92% / 66% for the rules alone (tests/data/chat_questions*.txt)."""
    from app.nlp import embed
    sims = embed.faq_similarities(raw)
    if not sims:
        return faq_hits
    rule = {FAQ[i][0]: s for s, i in faq_hits}
    best = max(sims, key=lambda f: sims[f] + 0.2 * min(rule.get(f, 0.0), 1.0))
    conf = max(rule.get(best, 0.0), sims[best] if sims[best] >= 0.82 else 0.0)
    index = _FAQ_INDEX[best]
    return [(conf, index)] + [h for h in faq_hits if h[1] != index]


def _topic_reply(topic: str, intent, direction, diet, allergens) -> Optional[Reply]:
    kind, _, key = topic.partition(":")
    if kind == "test" and key in BIOMARKERS_CONFIG:
        return answer_test(key, intent, direction, diet, allergens)
    if kind == "concept" and key in CONCEPTS:
        return answer_concept(key, intent, direction, diet, allergens)
    if kind == "food" and key in FOODS_BY_ID:
        return answer_food(FOODS_BY_ID[key], None, diet, allergens)
    return None


def _faq_reply(index: int) -> Reply:
    faq_id, _questions, text, follow = FAQ[index]
    return Reply(text, suggestions=list(follow), topic=f"faq:{faq_id}")


def _entity_reply(raw, text, tests, concepts, foods, intent, direction, diet, allergens) -> Reply:
    # A food question ("is ragi good for iron?") is answered about the food, focused on the concept asked about.
    if foods:
        concept = concepts[0] if concepts else next((c for c, v in CONCEPTS.items() if v.get("test") in tests), None)
        replies = [answer_food(FOODS_BY_ID[f], concept, diet, allergens) for f in foods[:2]]
        return _join(replies)
    number = _extract_value(raw)
    targets: list[tuple[str, str]] = []
    for key in tests:
        # A word that is both a test and a concept ("calcium", "b12"): foods questions go to the concept.
        concept = next((c for c in concepts if CONCEPTS[c].get("test") == key), None)
        if (concept and intent in ("foods", "avoid", "general", "what") and number is None
                and not re.search(r"\btest\b", text)):
            targets.append(("concept", concept))
        else:
            targets.append(("test", key))
    for key in concepts:
        if ("concept", key) not in targets and not any(k == CONCEPTS[key].get("test") for kind, k in targets if kind == "test"):
            targets.append(("concept", key))
    targets = targets[:3]
    value = number if len(targets) == 1 and targets[0][0] == "test" else None
    replies = []
    for kind, key in targets:
        if kind == "test":
            replies.append(answer_test(key, intent, direction, diet, allergens, value=value, sex=_detect_sex(text)))
        else:
            replies.append(answer_concept(key, intent, direction, diet, allergens))
    return _join(replies)


def _join(replies: list[Reply]) -> Reply:
    if len(replies) == 1:
        return replies[0]
    return Reply("\n\n".join(r.reply for r in replies), suggestions=replies[0].suggestions, topic=replies[0].topic)
