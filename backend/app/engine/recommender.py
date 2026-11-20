import json
import re
import os
from typing import List, Dict, Any, Optional
from app.engine.rule_engine import BIOMARKERS_CONFIG
from app.models.schemas import (
    UserProfile,
    MarkerAnalysisResult,
    MarkerStatus,
    FoodRecommendation,
    NutrientRecommendationPlan,
    DietType
)

FOODS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "foods.json")

def load_foods_data() -> List[Dict[str, Any]]:
    with open(FOODS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["foods"]

FOODS_DATABASE = load_foods_data()

# Blood-sugar and blood-fat advice ranks foods by qualitative properties (no invented nutrient numbers).
TAG_PROFILES = {
    "glycemic_support": {"low_gi": 2, "high_fibre": 1},
    "lipid_support": {"heart_healthy_fat": 2, "omega3": 2, "high_fibre": 1},
    "hdl_support": {"heart_healthy_fat": 2, "omega3": 2},
    "protein_support": {"high_protein": 2},
    "uric_acid_support": {"low_purine": 2, "high_fibre": 1},
    "liver_support": {"high_fibre": 2, "low_gi": 1, "omega3": 1, "heart_healthy_fat": 1},
}
TAG_LABELS = {"low_gi": "Low GI", "high_fibre": "High fibre", "heart_healthy_fat": "Healthy fats", "omega3": "Omega-3",
              "high_protein": "High protein", "low_purine": "Low purine"}
TAG_NOTES = {
    "low_gi": "Releases its energy slowly, which helps keep blood sugar steadier than refined foods.",
    "high_fibre": "Fibre slows digestion and supports healthy blood sugar and cholesterol.",
    "heart_healthy_fat": "Provides unsaturated fats that can replace saturated fats in the diet.",
    "omega3": "A source of omega-3 fats.",
    "high_protein": "A good source of protein for building and repairing body tissues.",
    "low_purine": "Low in purines, which the body breaks down into uric acid.",
}
MAX_PER_CATEGORY = 2
FOODS_PER_PLAN = 8
FOODS_PER_MAINTAIN_PLAN = 4

ABSORPTION_RULES = {
    "glycemic_support": {
        "dos": [
            "Build meals around whole grains and millets (ragi, jowar, bajra), pulses and non-starchy vegetables; eat grains with dal, sprouts or curd rather than on their own.",
            "Choose whole fruit instead of fruit juice and keep portions modest.",
            "Stay physically active as your doctor advises; a short walk after meals is a common habit."
        ],
        "donts": [
            "Keep sugar, sweets, sweetened drinks and refined flour (maida) products small; national dietary guidance asks for added sugar to stay low.",
            "Do not stop or change any diabetes medicine because of diet changes without asking your doctor."
        ]
    },
    "lipid_support": {
        "dos": [
            "Eat pulses, whole grains, millets, vegetables and fruit every day for fibre.",
            "Include a small handful of nuts or seeds (almonds, flaxseed, sesame, pumpkin or sunflower seeds) as part of your daily fat; non-vegetarians can choose fish such as mackerel.",
            "Use cooking oil in moderation and vary the oils you use."
        ],
        "donts": [
            "Limit ghee, butter, deep-fried snacks, bakery items, vanaspati and processed meats.",
            "Do not stop or change cholesterol medicines because of diet changes without asking your doctor."
        ]
    },
    "hdl_support": {
        "dos": [
            "Replace some saturated fat with unsaturated fat from nuts, seeds and, for non-vegetarians, fish.",
            "Stay physically active as your doctor advises."
        ],
        "donts": [
            "Avoid vanaspati, bakery fats and deep-fried packaged snacks.",
            "Do not start supplements to raise HDL without asking your doctor."
        ]
    },
    "protein_support": {
        "dos": [
            "Include a protein food at every meal: dal, sprouts, curd, paneer or soya for vegetarians; eggs, fish or chicken for non-vegetarians.",
            "Combine cereals with pulses (rice with dal, roti with chana) so the proteins complement each other.",
            "Eat regular meals; low protein often comes with low overall food intake."
        ],
        "donts": [
            "If you have kidney disease, do not increase protein without your doctor's advice.",
            "Do not rely on protein powders or supplements without medical advice."
        ]
    },
    "uric_acid_support": {
        "dos": [
            "Drink plenty of water through the day unless your doctor has asked you to limit fluids.",
            "Build meals around vegetables, whole grains, low-fat milk and curd; these are low in purines.",
            "Keep a healthy weight; lose weight gradually if you are overweight."
        ],
        "donts": [
            "Limit organ meats (liver, kidney), red meat and shellfish, which are high in purines.",
            "Avoid alcohol, especially beer, and sugary drinks or packaged fruit juices.",
            "Do not crash diet or fast for long periods; this can raise uric acid."
        ]
    },
    "liver_support": {
        "dos": [
            "Choose whole grains, millets, pulses, vegetables and fruit for fibre.",
            "Use small amounts of cooking oil and prefer nuts, seeds and fish for healthy fats.",
            "Stay active and aim for gradual weight loss if you are overweight; this is the main treatment for fatty liver."
        ],
        "donts": [
            "Avoid alcohol completely until your doctor reviews your liver tests.",
            "Limit sugar, sweets, sugary drinks, maida products and deep-fried snacks.",
            "Do not take herbal or 'liver detox' products without asking your doctor."
        ]
    },
    "iron_mg": {
        "dos": [
            "Pair non-heme plant iron (palak, chana, moringa) with Vitamin C rich foods (fresh lemon juice, amla, guava) to increase absorption up to 300%.",
            "Cook in traditional cast-iron pans to naturally leach bioavailable iron into food.",
            "Soak whole pulses and legumes overnight to break down phytic acid that binds iron."
        ],
        "donts": [
            "Avoid drinking black tea, green tea, or coffee within 1 hour before or after meals (tannins and polyphenols inhibit iron uptake by up to 60%).",
            "Do not take high-dose calcium or dairy foods simultaneously with iron meals, as calcium competes for absorption pathways."
        ]
    },
    "calcium_mg": {
        "dos": [
            "Ensure adequate Vitamin D levels (or 15-20 mins daily morning sunlight) for your intestines to absorb dietary calcium efficiently.",
            "Distribute calcium-rich snacks across the day rather than eating all in one sitting for optimal fractional absorption."
        ],
        "donts": [
            "Avoid high-sodium foods and excessive carbonated drinks which accelerate urinary calcium excretion."
        ]
    },
    "vitamin_d_iu": {
        "dos": [
            "Consume Vitamin D foods with healthy culinary fats (ghee, cold-pressed oils, nuts, or whole milk) because Vitamin D is fat-soluble.",
            "Get 15-20 minutes of midday sunlight (11 AM to 1 PM) exposure on arms and face whenever feasible."
        ],
        "donts": [
            "Avoid relying solely on diet if levels are severely depleted (<10 ng/mL), as natural dietary quantities are often insufficient without clinical guidance."
        ]
    },
    "vitamin_b12_mcg": {
        "dos": [
            "Lacto-vegetarians should regularly include fermented curd (dahi), paneer, and milk.",
            "Strict vegans must consume fortified plant milks or fortified nutritional yeast to fulfill daily B12 requirements."
        ],
        "donts": [
            "Do not assume plant greens, spirulina, or unfortified foods provide active human Vitamin B12 (they mostly contain inactive pseudovitamin B12 analogues)."
        ]
    },
    "folate_mcg": {
        "dos": [
            "Consume freshly steamed or lightly stir-fried greens, sprouted moong, and fresh fruits.",
            "Pair folate with B12 to ensure proper cellular red blood cell maturation."
        ],
        "donts": [
            "Avoid prolonged boiling or discarding cooking water of green vegetables, as water-soluble folate is rapidly destroyed by high heat."
        ]
    }
}

class RecommendationEngine:
    def __init__(self, foods_db: Optional[List[Dict[str, Any]]] = None):
        self.foods_db = foods_db or FOODS_DATABASE

    def filter_foods(self, profile: UserProfile) -> List[Dict[str, Any]]:
        """Applies hard constraints for diet type and allergens."""
        from app.plan import allergy
        from app.plan.engine import food_facts
        eligible_foods = []
        user_allergens = {a.strip().lower() for a in profile.allergens}
        user_diet = profile.diet_type.value
        avoids = [allergy.resolve(w) for w in getattr(profile, "custom_allergies", []) or [] if w.strip()]
        meats = set(getattr(profile, "meats", []) or [])

        for food in self.foods_db:
            # 1. Allergen Check: strict zero tolerance. The card's own labels plus those of the ingredients it is
            # made of (the same data the dishes use), then typed allergies ("peanut", "eggplant", "पालक").
            codes, food_allergens, food_meats = food_facts(food)
            if user_allergens.intersection(a.lower() for a in food_allergens):
                continue  # Disqualified due to allergen
            if any(allergy.blocks_food(food, codes, food_allergens, a) for a in avoids):
                continue
            # A non-vegetarian who picked the meats they eat sees only those (the planner does the same).
            if meats and food_meats - meats:
                continue

            # 2. Diet Type Check
            food_diets = food.get("diet_type", [])
            if user_diet not in food_diets:
                # Vegetarians can also eat vegan foods
                if user_diet == "veg" and "vegan" in food_diets:
                    pass
                # Eggetarians can also eat veg and vegan
                elif user_diet == "eggetarian" and ("veg" in food_diets or "vegan" in food_diets):
                    pass
                # Non-veg can eat anything
                elif user_diet == "non_veg":
                    pass
                else:
                    continue  # Disqualified due to diet preference

            eligible_foods.append(food)

        return eligible_foods

    @staticmethod
    def needs_plan(marker: MarkerAnalysisResult) -> bool:
        """Markers where lower is worse need food when LOW/BORDERLINE; blood sugar and fats when BORDERLINE/HIGH.
        Tests without a food plan (kidney, liver) are only reported."""
        config = BIOMARKERS_CONFIG.get(marker.biomarker_key, {})
        if config.get("food_plan_on"):
            return marker.status.value in config["food_plan_on"]
        if not config.get("supports_food_plan", True):
            return False
        if config.get("direction", "lower_is_worse") == "higher_is_worse":
            return marker.status in (MarkerStatus.BORDERLINE, MarkerStatus.HIGH)
        return marker.status in (MarkerStatus.LOW, MarkerStatus.BORDERLINE)

    @staticmethod
    def _diverse(ranked):
        """Take the best foods in order, at most MAX_PER_CATEGORY from any one food group, so a plan
        mixes greens, pulses, grains, fruit and so on instead of listing one group."""
        chosen, per_category = [], {}
        for food in ranked:
            category = food.get("category", "General")
            if per_category.get(category, 0) >= MAX_PER_CATEGORY:
                continue
            per_category[category] = per_category.get(category, 0) + 1
            chosen.append(food)
            if len(chosen) == FOODS_PER_PLAN:
                break
        return chosen

    @staticmethod
    def can_maintain(marker: MarkerAnalysisResult) -> bool:
        """A healthy result of a nutrient-linked test gets a short plan to keep it there."""
        config = BIOMARKERS_CONFIG.get(marker.biomarker_key, {})
        return (marker.status == MarkerStatus.NORMAL and config.get("supports_food_plan", True)
                and not config.get("food_plan_on") and bool(marker.target_nutrient_key))

    @classmethod
    def rank_by_tags(cls, foods, nutrient_key):
        weights = TAG_PROFILES[nutrient_key]
        scored = [(sum(w for tag, w in weights.items() if tag in f.get("tags", [])), f) for f in foods]
        # Among equally tagged foods, the protein plan prefers the richest sources per serving.
        richness = (lambda f: -f.get("protein_rank_g", 0)) if nutrient_key == "protein_support" else (lambda f: 0)
        scored = sorted([x for x in scored if x[0] > 0], key=lambda x: (-x[0], richness(x[1]), x[1]["id"]))
        return cls._diverse(food for _, food in scored)

    @classmethod
    def rank_by_nutrient(cls, foods, nutrient_key):
        amount = lambda f: f.get("nutrients", {}).get(nutrient_key, 0.0) or 0.0
        ranked = sorted((f for f in foods if amount(f) > 0), key=lambda f: (-amount(f), f["id"]))
        return cls._diverse(ranked)

    def generate_recommendations(
        self,
        marker_analyses: List[MarkerAnalysisResult],
        profile: UserProfile
    ) -> List[NutrientRecommendationPlan]:
        eligible_foods = self.filter_foods(profile)
        plans = []

        flagged_markers = [m for m in marker_analyses if self.needs_plan(m)]
        improving = {m.target_nutrient_key for m in flagged_markers}
        maintained = [m for m in marker_analyses if self.can_maintain(m) and m.target_nutrient_key not in improving]

        for marker in flagged_markers + maintained:
            nutrient_key = marker.target_nutrient_key
            purpose = "maintain" if marker in maintained else "improve"
            
            tag_based = nutrient_key in TAG_PROFILES
            if tag_based:
                top_foods = self.rank_by_tags(eligible_foods, nutrient_key)
            else:
                top_foods = self.rank_by_nutrient(eligible_foods, nutrient_key)
            if purpose == "maintain":
                top_foods = top_foods[:FOODS_PER_MAINTAIN_PLAN]

            formatted_foods = []
            for food in top_foods:
                if tag_based:
                    shown = [t for t in TAG_PROFILES[nutrient_key] if t in food.get("tags", [])]
                    yield_desc = " \u00b7 ".join(TAG_LABELS[t] for t in shown)
                    synergies = [TAG_NOTES[t] for t in shown]
                else:
                    val = food["nutrients"].get(nutrient_key, 0.0)
                    unit_label = nutrient_key.split("_")[-1].upper()
                    yield_desc = f"{val} {unit_label}"
                    synergies = food.get("synergies", [])

                formatted_foods.append(
                    FoodRecommendation(
                        id=food["id"],
                        name=food["name"],
                        hindi_name=food.get("hindi_name"),
                        category=food.get("category", "General"),
                        serving_size=food.get("serving_size", "1 serving"),
                        key_nutrient_yield=yield_desc,
                        synergies=synergies,
                        preparation_tip=food.get("tip")
                    )
                )

            # Get absorption guidelines
            rules = ABSORPTION_RULES.get(nutrient_key, {"dos": [], "donts": []})

            plans.append(
                NutrientRecommendationPlan(
                    target_biomarker=marker.biomarker_key,
                    biomarker_display_name=marker.display_name,
                    status=marker.status,
                    recommended_foods=formatted_foods,
                    absorption_dos=rules.get("dos", []),
                    absorption_donts=rules.get("donts", []),
                    purpose=purpose,
                )
            )

        return self._merge_shared_plans(plans, marker_analyses)

    @staticmethod
    def _merge_shared_plans(plans, marker_analyses):
        """Markers that lead to the same foods and advice (haemoglobin, ferritin and serum iron; HbA1c and glucose;
        cholesterol and triglycerides) are shown as one plan named after all the markers behind it."""
        severity = {MarkerStatus.NORMAL: 0, MarkerStatus.LOW: 1, MarkerStatus.BORDERLINE: 2, MarkerStatus.HIGH: 3}
        merged, groups = [], {}
        for plan in plans:
            marker = next((m for m in marker_analyses if m.biomarker_key == plan.target_biomarker), None)
            key = (marker.target_nutrient_key if marker else None, plan.purpose)
            if key not in groups:
                groups[key] = {"plan": plan, "names": [plan.biomarker_display_name]}
                merged.append(plan)
                continue
            group = groups[key]
            group["names"].append(plan.biomarker_display_name)
            if severity[plan.status] > severity[group["plan"].status]:
                group["plan"].status = plan.status
            seen = {f.id for f in group["plan"].recommended_foods}
            group["plan"].recommended_foods += [f for f in plan.recommended_foods if f.id not in seen]
            limit = FOODS_PER_PLAN if plan.purpose == "improve" else FOODS_PER_MAINTAIN_PLAN
            group["plan"].recommended_foods = group["plan"].recommended_foods[:limit]
        for group in groups.values():
            if len(group["names"]) > 1:
                short = [" ".join(re.sub(r"\s*\([^)]*\)", "", n).split()) for n in group["names"]]
                group["plan"].biomarker_display_name = " \u00b7 ".join(short)
        return merged

