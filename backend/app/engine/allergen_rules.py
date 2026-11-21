"""Advice text that never suggests a food the person excludes.

The tips under each food plan and the explanation's repletion advice are written for everyone ("a handful of nuts",
"curd, paneer and milk"). For a person who avoids nuts or dairy, or who is vegetarian, those words are rewritten or
dropped here. Every rewritten sentence has its Hindi and Telugu in app/data/i18n.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set

# Standard allergen canonical keys and all their common aliases / sub-types
ALLERGEN_NORMALIZATION_MAP = {
    "nuts": {"nuts", "tree_nuts", "tree nuts", "peanuts", "peanut", "tree nuts & peanuts"},
    "peanuts": {"peanuts", "peanut", "groundnut", "groundnuts"},
    "dairy": {"dairy", "milk", "lactose", "dairy & lactose"},
    "gluten": {"gluten", "wheat", "gluten / wheat"},
    "soy": {"soy", "soya", "soybeans"},
    "eggs": {"eggs", "egg"},
    "seafood": {"seafood", "fish", "shellfish", "fish & shellfish"},
    "sesame": {"sesame", "til"},
    "mustard": {"mustard", "sarson", "rai"},
}

# Individual ingredient words mapped to allergen groups for deep recipe checks
ALLERGEN_INGREDIENT_STEMS = {
    "nuts": {
        "almond", "almonds", "badam", "cashew", "cashews", "kaju", "walnut", "walnuts",
        "akhrot", "pistachio", "pistachios", "pista", "hazelnut", "hazelnuts", "pecan",
        "pecans", "peanut", "peanuts", "groundnut", "groundnuts", "moongphali", "mungfali",
        "palli", "shenga", "singdana", "peanut butter", "groundnut oil", "tree nut", "tree nuts"
    },
    "dairy": {
        "milk", "curd", "dahi", "yogurt", "paneer", "ghee", "butter", "makhan", "buttermilk",
        "chaas", "khoa", "mawa", "cheese", "cream", "malai", "whey", "lactose"
    },
    "gluten": {
        "wheat", "atta", "maida", "suji", "sooji", "rava", "semolina", "dalia", "bulgur",
        "barley", "roti", "phulka", "chapati", "naan", "poori", "puri", "bread", "vermicelli"
    },
    "soy": {
        "soy", "soya", "soybean", "soybeans", "tofu", "tempeh", "edamame", "soy milk", "soya chunks"
    },
    "eggs": {
        "egg", "eggs", "anda", "egg white", "egg yolk", "boiled egg", "omelette", "albumin"
    },
    "seafood": {
        "fish", "machhli", "prawn", "prawns", "shrimp", "jheenga", "crab", "shellfish",
        "mackerel", "sardine", "rohu", "catla", "hilsa", "seer fish", "anchovy"
    },
    "sesame": {
        "sesame", "til", "gingelly", "tahini", "sesame seeds", "sesame oil"
    },
    "mustard": {
        "mustard", "sarson", "rai", "mustard seeds", "mustard oil", "mustard leaves"
    }
}


def normalize_allergens(allergens: List[str] | Set[str] | tuple) -> Set[str]:
    """Expands user allergen choices so that composite choices (e.g. 'Tree nuts & peanuts') cover all variants."""
    raw = {a.strip().lower() for a in allergens if a and a.strip()}
    normalized: Set[str] = set()

    for item in raw:
        normalized.add(item)
        for canon, aliases in ALLERGEN_NORMALIZATION_MAP.items():
            if item == canon or item in aliases:
                normalized.add(canon)
                # Combined exclusion rule: "nuts" always covers both tree nuts and peanuts
                if canon in ("nuts", "peanuts"):
                    normalized.add("nuts")
                    normalized.add("peanuts")
                    normalized.add("tree_nuts")

    return normalized


def sanitize_tip_text(text: str, allergens: Set[str] | List[str], diet_type: str = "veg") -> str:
    """
    Rewrites absorption tips, guidelines, and lifestyle notes so that excluded allergens
    and non-matching diets are NEVER recommended to the user.
    """
    if not text:
        return text

    norm_allergens = normalize_allergens(allergens)
    t = text

    # 1. Nut exclusion rules
    if "nuts" in norm_allergens or "peanuts" in norm_allergens or "tree_nuts" in norm_allergens:
        # LDL / lipid tips
        t = t.replace(
            "Include a small handful of nuts or seeds (almonds, flaxseed, sesame, pumpkin or sunflower seeds)",
            "Include healthy seeds (flaxseed, sesame, pumpkin or sunflower seeds)"
        )
        t = t.replace(
            "almonds, flaxseed, sesame, pumpkin or sunflower seeds",
            "flaxseed, sesame, pumpkin or sunflower seeds"
        )
        t = t.replace(
            "unsaturated fat from nuts, seeds and, for non-vegetarians, fish",
            "unsaturated fat from seeds and, for non-vegetarians, fish"
        )
        t = t.replace("nuts, seeds and, for non-vegetarians, fish", "seeds and, for non-vegetarians, fish")
        t = t.replace("prefer nuts, seeds and fish", "prefer seeds and fish")
        t = t.replace("replace some saturated fat with nuts and seeds", "replace some saturated fat with seeds")
        t = t.replace("ghee, cold-pressed oils, nuts, or whole milk", "ghee, cold-pressed oils, or whole milk")
        t = t.replace("cold-pressed oils, ghee, nuts, whole milk", "cold-pressed oils, ghee, whole milk")
        t = t.replace(", nuts,", ",")
        t = t.replace(", nuts", "")
        t = t.replace("nuts, ", "")
        # Remove any remaining mentions of specific nuts
        t = re.sub(r"\b(almonds?|walnuts?|cashews?|pistachios?|peanuts?|groundnuts?|badam|kaju|pista)\b", "seeds", t, flags=re.IGNORECASE)
        t = re.sub(r"\bnuts\b", "seeds", t, flags=re.IGNORECASE)
        t = re.sub(r"\bseeds\s+and\s+seeds\b", "seeds", t, flags=re.IGNORECASE)
        t = re.sub(r"\bseeds\s*,\s*seeds\b", "seeds", t, flags=re.IGNORECASE)

    # 2. Dairy exclusion or vegan diet
    if "dairy" in norm_allergens or diet_type == "vegan":
        t = t.replace("ghee, cold-pressed oils, nuts, or whole milk", "cold-pressed oils or nuts")
        t = t.replace("cold-pressed oils, nuts, or whole milk", "cold-pressed oils or nuts")
        t = t.replace("ghee, cold-pressed oils, or whole milk", "cold-pressed vegetable oils")
        t = t.replace("cold-pressed oils, ghee, whole milk", "cold-pressed vegetable oils")
        t = t.replace("ghee, ", "")
        t = t.replace(", whole milk", "")
        t = t.replace("whole milk, ", "")
        t = t.replace("Lacto-vegetarians should regularly include fermented curd (dahi), paneer, and milk.",
                      "Choose fortified plant milks or breakfast cereals to meet daily vitamin B12 needs.")
        t = t.replace("curd, paneer, and milk", "fortified plant beverages")
        t = t.replace("curd, paneer or soya", "soya or pulses")
        t = t.replace("low-fat milk and curd", "low-fat plant milks, legumes and pulses")
        t = t.replace("fermented dairy (curd, paneer) or fortified plant beverages", "fortified plant beverages")
        t = t.replace("dal, sprouts or curd rather", "dal or sprouts rather")
        t = t.replace("dal, sprouts, curd or vegetables", "dal, sprouts or vegetables")
        t = t.replace("sesame seeds (til), curd, and", "sesame seeds (til), and")
        t = t.replace("ragi (finger millet), curd, and", "ragi (finger millet), and")

    # Sesame, soy and egg allergies
    if "sesame" in norm_allergens:
        t = t.replace("sesame seeds (til), ", "")
        t = t.replace("flaxseed, sesame, pumpkin", "flaxseed, pumpkin")
    if "soy" in norm_allergens:
        t = t.replace("curd, paneer or soya", "curd or paneer")
        t = t.replace(", soya or pulses", " or pulses")
    if "eggs" in norm_allergens:
        t = t.replace("eggs, fish or chicken", "fish or chicken")
        t = t.replace("benefit from eggs, fish, and lean poultry", "benefit from fish and lean poultry")

    # 3. Seafood exclusion or vegetarian / vegan / eggetarian
    if "seafood" in norm_allergens or diet_type in ("veg", "vegan", "eggetarian"):
        t = t.replace("nuts, seeds and, for non-vegetarians, fish", "nuts and seeds")
        t = t.replace("nuts, seeds and fish", "nuts and seeds")
        t = t.replace("eggs, fish or chicken", "eggs or chicken").replace("fish or chicken", "chicken")
        t = t.replace("eggs, fish, and lean poultry", "eggs and lean poultry")
        t = t.replace("from fish and lean poultry", "from lean poultry")
        t = t.replace("; non-vegetarians can choose fish such as mackerel", "")
        t = t.replace(" and, for non-vegetarians, fish", "")
        t = t.replace(" and fish", "")
        t = t.replace("or, for non-vegetarians, fish", "")

    # Clean up double punctuation / whitespace
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r",\s*,", ",", t)
    t = re.sub(r"\s+([.,;:)])", r"\1", t)  # no space before punctuation after a removal
    t = t.replace("ragi (finger millet), and", "ragi (finger millet) and")
    t = t.replace("( ", "(").replace(" )", ")")
    return t


