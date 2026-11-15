import json
import os
from typing import List, Dict, Any, Optional
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

ABSORPTION_RULES = {
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
        eligible_foods = []
        user_allergens = {a.strip().lower() for a in profile.allergens}
        user_diet = profile.diet_type.value

        for food in self.foods_db:
            # 1. Allergen Check: Strict zero tolerance
            food_allergens = {a.lower() for a in food.get("allergens", [])}
            if user_allergens.intersection(food_allergens):
                continue  # Disqualified due to allergen

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

    def generate_recommendations(
        self,
        marker_analyses: List[MarkerAnalysisResult],
        profile: UserProfile
    ) -> List[NutrientRecommendationPlan]:
        eligible_foods = self.filter_foods(profile)
        plans = []

        # Focus on markers that are LOW or BORDERLINE
        flagged_markers = [m for m in marker_analyses if m.status in (MarkerStatus.LOW, MarkerStatus.BORDERLINE)]

        for marker in flagged_markers:
            nutrient_key = marker.target_nutrient_key
            
            # Sort eligible foods by the specific target nutrient content descending
            ranked_foods = sorted(
                eligible_foods,
                key=lambda f: f.get("nutrients", {}).get(nutrient_key, 0.0),
                reverse=True
            )

            # Pick top 4 foods that have meaningful amounts (> 0)
            top_foods = [f for f in ranked_foods if f.get("nutrients", {}).get(nutrient_key, 0.0) > 0.0][:4]

            formatted_foods = []
            for food in top_foods:
                val = food["nutrients"].get(nutrient_key, 0.0)
                unit_label = nutrient_key.split("_")[-1].upper()
                yield_desc = f"{val} {unit_label}"

                formatted_foods.append(
                    FoodRecommendation(
                        id=food["id"],
                        name=food["name"],
                        hindi_name=food.get("hindi_name"),
                        category=food.get("category", "General"),
                        serving_size=food.get("serving_size", "1 serving"),
                        key_nutrient_yield=yield_desc,
                        synergies=food.get("synergies", []),
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
                    absorption_donts=rules.get("donts", [])
                )
            )

        return plans

