"""Diet plans built by mixed-integer linear programming (Google OR-Tools, Apache 2.0).

For each day the solver chooses dishes and whole servings for breakfast, lunch, an evening snack and dinner so that:
- energy is within 5% of the person's need and protein meets 0.83 g per kg (ICMR-NIN 2020);
- the nutrients the person's report shows as low reach the RDA (ICMR-NIN 2020), others are kept close to it;
- sodium, fat and saturated fat stay within limits, more strictly for raised blood pressure, sugar or cholesterol;
- meals look like real Indian meals (a staple with dal or curry, idli with chutney or sambar), respecting diet type,
  allergies, foods the person never eats, and how often a dish is eaten (sweets and fried snacks once a week);
- the foods the person picked from their report are included.

Three one-day options differ in what they favour: dishes from the person's region and the foods they picked
(Familiar), the most nutrients for the energy (Most nutritious), or only the region's own dishes (Regional). A
7-day plan is solved day by day with weekly limits and variety. Values that are estimates (vitamin D in fish) count
at half, so a plan never relies on them.
"""
from collections import defaultdict
from dataclasses import dataclass, field

from app.plan import allergy
from app.plan.catalog import catalog, lines_of
from app.plan.ingredient_local import local_names
from app.plan.ingredient_names import expand, INGREDIENTS
from app.plan.nutrition import ingredients, meat_type

SLOTS = ("breakfast", "lunch", "snack", "dinner")
# States where plain rice is the everyday staple, so it counts as a regional dish there.
RICE_STATES = {"telangana", "andhra", "tamil_nadu", "kerala", "karnataka", "west_bengal", "odisha", "assam", "goa",
               "tripura", "manipur", "meghalaya", "mizoram", "nagaland", "arunachal_pradesh", "sikkim", "jharkhand",
               "chhattisgarh", "bihar"}
RICE_DISHES = {"steamed_rice", "brown_rice"}
MAX_SERVINGS = {"staple": 4, "breakfast": 3, "rice_dish": 2, "dal": 2, "curry": 2, "liquid": 2, "chutney": 2,
                "side": 2, "snack": 1, "drink": 1, "fruit": 1, "sweet": 1}
REPEATABLE_ROLES = {"staple", "drink"}  # roles never counted as a "main" dish
REPEATABLE_DISHES = {"tea", "filter_coffee", "milk", "fortified_milk"}  # may appear at two meals of a day
# Physical activity level (PAL): energy need = BMR x PAL. Anchored on ICMR-NIN 2020 (1.53 sedentary, 1.8 moderate,
# 2.3 heavy) and kept inside the FAO/WHO/UNU 2004 bands (1.40-1.69 light, 1.70-1.99 active, 2.00-2.40 vigorous).
ACTIVITY_PAL = {
    "sedentary": 1.40,     # little or no exercise (ICMR-NIN 2020 sedentary)
    "light": 1.55,         # exercise 1-3 times a week
    "moderate": 1.70,      # exercise 4-5 times a week
    "active": 1.80,        # daily exercise, or intense exercise 3-4 times a week (ICMR-NIN 2020 moderate)
    "very_active": 2.00,   # intense exercise 6-7 times a week
    "extra_active": 2.30,  # very intense exercise daily, or a physical job (ICMR-NIN 2020 heavy)
}
# ICMR-NIN 2020 lowers the FAO/WHO/UNU BMR by 10% for men and 9% for women for Indian adults, then multiplies by
# PAL 1.4 / 1.8 / 2.3. This gives its published needs: 2,110 kcal for a sedentary 65 kg man; 1,660 / 2,130 /
# 2,720 kcal for a 55 kg woman. The levels in between stay inside the FAO bands (1.40-1.69, 1.70-1.99, 2.00-2.40).
ICMR_BMR_FACTOR = {"male": 0.90, "female": 0.91}
# Values saved before the six levels existed (none, walking, cycling, running) -> nearest level.
LEGACY_ACTIVITY = {"none": "sedentary", "walking": "light", "cycling": "active", "running": "very_active"}


def activity_level(value: str | None) -> str:
    value = LEGACY_ACTIVITY.get(value or "", value or "")
    return value if value in ACTIVITY_PAL else "sedentary"
DIET_ALLOWS = {"vegan": {"vegan"}, "veg": {"vegan", "vegetarian"}, "vegetarian": {"vegan", "vegetarian"},
               "eggetarian": {"vegan", "vegetarian", "eggetarian"},
               "non_veg": {"vegan", "vegetarian", "eggetarian", "non_veg"}}
# Report nutrient keys (foods.json) to dish nutrient keys.
REPORT_KEYS = {"iron_mg": "iron_mg", "calcium_mg": "calcium_mg", "folate_mcg": "folate_ug", "folate_ug": "folate_ug",
               "vitamin_c_mg": "vitamin_c_mg", "vitamin_d_iu": "vitamin_d_iu", "vitamin_b12_mcg": "vitamin_b12_ug",
               "vitamin_b12_ug": "vitamin_b12_ug", "zinc_mg": "zinc_mg", "magnesium_mg": "magnesium_mg"}
TRACKED = ["iron_mg", "calcium_mg", "folate_ug", "vitamin_c_mg", "vitamin_b12_ug", "vitamin_d_iu", "zinc_mg",
           "magnesium_mg", "fibre_g"]
OPTION_STYLES = ("familiar", "nutritious", "regional")
STYLE_TITLES = {"familiar": "Familiar", "nutritious": "Most nutritious", "regional": "Regional"}


@dataclass
class Person:
    age: int
    sex: str  # "male" or "female"
    height_cm: float
    weight_kg: float
    activity: str = "sedentary"
    diet: str = "veg"
    meats: tuple = ()  # for non-vegetarians: kinds they eat, e.g. ("chicken", "egg", "fish"); empty = all
    allergens: tuple = ()  # ingredient allergen groups: nuts, sesame, mustard, dairy, gluten, soy, eggs, seafood
    avoid_words: tuple = ()  # custom allergies or dislikes, matched against dish and ingredient names
    region: str = ""  # state code, e.g. "telangana"
    low_nutrients: tuple = ()  # nutrient keys the report flagged as low, e.g. ("iron_mg", "vitamin_b12_mcg")
    conditions: tuple = ()  # "diabetes", "hypertension", "high_cholesterol"
    picked_foods: tuple = ()  # foods.json ids the person selected from their report
    usual_diet: str = ""  # what the person says they usually eat; dishes named in it are preferred


# ----------------------------------------------------------------------------------------------- targets

def bmr(person: Person) -> float:
    """FAO/WHO/UNU (Schofield) equations, which ICMR-NIN uses for adults."""
    w, age, male = person.weight_kg, person.age, person.sex == "male"
    if age < 18:
        raise ValueError("Diet plans are for adults (18 and over).")
    if age < 30:
        return 15.3 * w + 679 if male else 14.7 * w + 496
    if age < 60:
        return 11.6 * w + 879 if male else 8.7 * w + 829
    return 13.5 * w + 487 if male else 10.5 * w + 596


def targets(person: Person) -> dict:
    pal = ACTIVITY_PAL[activity_level(person.activity)]
    bmr_kcal = bmr(person) * ICMR_BMR_FACTOR.get(person.sex, 0.91)
    energy = bmr_kcal * pal
    bmi = person.weight_kg / (person.height_cm / 100) ** 2
    if bmi >= 25:  # gentle loss: about 15% below need, never more than 500 kcal
        energy -= min(0.15 * energy, 500)
    elif bmi < 18.5:
        energy *= 1.10
    male = person.sex == "male"
    rda = {"iron_mg": 19 if male else 29, "calcium_mg": 1000, "folate_ug": 300 if male else 220,
           "vitamin_c_mg": 80 if male else 65, "vitamin_b12_ug": 2.5, "vitamin_d_iu": 600,
           "zinc_mg": 17 if male else 13.2, "magnesium_mg": 440 if male else 370,
           "fibre_g": round(15 * energy / 1000)}  # 30 g per 2000 kcal
    low = {REPORT_KEYS[k] for k in person.low_nutrients if k in REPORT_KEYS}
    sodium = 1500 if "hypertension" in person.conditions else 2000
    return {"energy_kcal": round(energy), "bmr_kcal": round(bmr_kcal), "pal": pal,
            "protein_g": round(0.83 * person.weight_kg, 1), "rda": rda, "low": sorted(low), "sodium_mg": sodium,
            "bmi": round(bmi, 1)}


# ----------------------------------------------------------------------------------------------- dishes

def dish_codes(dish_id: str) -> set:
    d = next(x for x in _all_dishes() if x.id == dish_id)
    codes = set()
    for c, _, _ in lines_of(d):
        codes.update([c] if isinstance(c, str) else c)
    return codes


def _all_dishes():
    from app.plan.catalog import all_dishes
    return all_dishes()


FOOD_CODES = {  # foods.json ids that are not named after an IFCT code
    "moringa_leaves": {"C019"}, "palak_spinach": {"C033"}, "methi_leaves": {"C020"},
    "amaranth_leaves": {"C002", "C003", "C004"}, "curry_leaves": {"G010"}, "ragi_flour": {"A010"},
    "bajra_pearl_millet": {"A003"}, "sesame_seeds_til": {"H009", "H010", "H011"}, "roasted_chana": {"B001"},
    "rajma_kidney_beans": {"B020"}, "chana_dal": {"B001"}, "black_urad_dal": {"B003", "B004"},
    "paneer_cottage_cheese": {"L003"}, "curd_yogurt": {"X001", "X016"}, "cow_milk_whole": {"L002", "X018"},
    "whole_egg_boiled": {"M001"}, "chicken_breast": {"N001", "N002", "N003", "N004"}, "chicken_liver": {"N005"},
    "mutton_goat_meat": {"O001", "O002", "O003"}, "rohu_freshwater_fish": {"S006"}, "mackerel_bangda": {"P034"},
    "fortified_milk_fssai": {"X018"}, "sun_exposed_mushrooms": {"X017", "J001"}, "lemon_citrus": {"E033"},
    "guava_peru": {"E028"}, "beetroot": {"F001"}, "almonds_badam": {"H001"}, "black_raisins_kishmish": {"E057"},
    "tofu_firm": {"X006"}, "horse_gram_kulthi": {"B012"}, "moth_beans_matki": {"B016"},
    "lobia_black_eyed_peas": {"B005", "B006"}, "drumstick_vegetable": {"D046"},
    "bitter_gourd_karela": {"D004", "D005", "D006"}, "bottle_gourd_lauki": {"D007", "D008", "D009"},
    "raw_banana_plantain": {"D063"}, "sweet_potato": {"F013", "F014"}, "cashewnuts_kaju": {"H005"},
    "jowar_sorghum": {"A005"}, "little_millet_kutki": {"A016"}, "prawn_shrimp": {"S008", "S009", "S010", "Q007"},
    "mutton_liver": {"O008"}, "papaya_ripe": {"E049"}, "orange_mosambi": {"E047"}, "ghee_clarified_butter": {"T013"},
    "tamarind_imli": {"E064"}, "jaggery_gud": {"I001"}, "soybean_cooked": {"X007"}, "coconut_oil_virgin": {"T001"},
    "garden_cress_seeds_aliv": {"H008"}, "pumpkin_seeds": {"X020"}, "fortified_soy_milk": {"X024"},
    "amla_indian_gooseberry": {"E021"}, "dates_khajoor": {"E017", "E018"}, "lotus_seeds_makhana": {"X027"},
    "flaxseeds_alsi": {"H014"}, "sunflower_seeds": {"H020"}, "foxtail_millet_kangni": {"X026"},
    "cod_liver_oil_capsule": {"X022"}, "hilsa_fish_ilish": {"P017"}, "dried_figs_anjeer": {"X025"},
    "dried_apricots_khumani": {"E005"}, "wheat_germ": {"X021"}, "tempeh": {"X023"},
}


def food_facts(food: dict) -> tuple[set, set, set]:
    """A food card's ingredient codes, full allergen set and kinds of meat, from the same ingredient data the dishes
    use, so a card can never be labelled differently from the dishes made of it."""
    table = ingredients()
    codes = {c for c in food_codes(food["id"]) if c in table}
    allergens = set(food.get("allergens", [])) | {a for c in codes for a in table[c]["allergens"]}
    meats = {m for c in codes if (m := meat_type(c, table[c]))}
    return codes, allergens, meats


def food_codes(food_id: str) -> set:
    if food_id in FOOD_CODES:
        return FOOD_CODES[food_id]
    if food_id.startswith("ifct_"):
        code = food_id.split("_")[1].upper()
        if code[0] == "M":
            return {code, "M001"}  # any egg
        if code[0] == "N" and int(code[1:]) <= 10:
            return {code, "N001", "N002", "N003", "N004"}
        return {code}
    return set()


def eligible(person: Person) -> list:
    """Dishes this person can eat: diet, kinds of meat, allergens and words to avoid."""
    allowed = DIET_ALLOWS.get(person.diet, DIET_ALLOWS["veg"])
    allergens = set(person.allergens)
    meats = set(person.meats)
    # Typed allergies in any language or spelling ("groundnut", "eggplant", "मूंगफली", "వేరుశనగ"): see plan/allergy.py.
    avoids = [allergy.resolve(w) for w in person.avoid_words if w.strip()]
    blocked = set()
    if avoids:
        from app.nlp import embed  # extra matches once e5 name matching meets its target (off until then)
        for word in person.avoid_words:
            blocked |= set(embed.match_items(word, "ingredient"))
    out = []
    for d in catalog().values():
        if d["diet"] not in allowed or set(d["allergens"]) & allergens:
            continue
        if meats and set(d["meat_types"]) - meats:
            continue
        if any(allergy.blocks_dish(d, a) for a in avoids):
            continue
        if blocked and {n for i in d["ingredients"] for n, _ in expand(i["name"], i["grams"])} & blocked:
            continue
        if "diabetes" in person.conditions and d["role"] == "sweet":
            continue
        out.append(d)
    return out


def credited(d: dict, key: str) -> float:
    """A nutrient value the plan may count on: estimates count at half."""
    value = d["per_serving"].get(key) or 0.0
    return value * 0.5 if key in d["uncertain"] else value


# ----------------------------------------------------------------------------------------------- one day

@dataclass
class DayRequest:
    style: str = "familiar"
    avoid: dict = field(default_factory=dict)  # dish id -> extra cost (used to make options and days differ)
    banned: set = field(default_factory=set)  # dish ids not allowed today
    fixed: dict = field(default_factory=dict)  # (dish id, slot) -> servings that must stay (for swaps)
    banned_in_slot: set = field(default_factory=set)  # (dish id, slot) not allowed
    time_limit_s: float = 4.0


def solve_day(person: Person, dishes: list, request: DayRequest):
    from ortools.linear_solver import pywraplp

    t = targets(person)
    solver = pywraplp.Solver.CreateSolver("SCIP") or pywraplp.Solver.CreateSolver("CBC")
    solver.SetTimeLimit(int(request.time_limit_s * 1000))
    region = person.region
    if request.style == "regional" and region:
        dishes = [d for d in dishes if region in d["regions"] or d["role"] in ("drink", "fruit", "side")
                  or d["id"] in ("steamed_rice", "phulka", "chapati", "curd")]
    dishes = [d for d in dishes if d["id"] not in request.banned]
    by_id = {d["id"]: d for d in dishes}

    n, z = {}, {}
    for d in dishes:
        for s in d["meals"]:
            if (d["id"], s) in request.banned_in_slot:
                continue
            z[d["id"], s] = solver.BoolVar("")
            n[d["id"], s] = solver.IntVar(0, MAX_SERVINGS[d["role"]], "")
            solver.Add(n[d["id"], s] >= z[d["id"], s])
            solver.Add(n[d["id"], s] <= MAX_SERVINGS[d["role"]] * z[d["id"], s])
    locked = {s for _, s in request.fixed}
    for k in z:  # meals that are not being changed keep exactly their dishes and servings
        if k[1] in locked:
            solver.Add(n[k] == request.fixed.get(k, 0))

    def count(slot, roles):
        return solver.Sum([z[k] for k in z if k[1] == slot and by_id[k[0]]["role"] in roles])

    accomp = ("chutney", "liquid", "curry", "dal", "side")
    # breakfast: one main; dry mains (idli, dosa, roti) come with chutney, sambar, curry or curd
    main_b = count("breakfast", ("breakfast", "staple", "rice_dish"))
    solver.Add(main_b == 1)
    solver.Add(count("breakfast", accomp) >= count("breakfast", ("breakfast", "staple")) - _self_contained("breakfast", z, by_id, solver))
    solver.Add(count("breakfast", accomp) <= 2)
    solver.Add(count("breakfast", ("curry", "dal")) >= count("breakfast", ("staple",)))  # roti, puri need a curry
    solver.Add(count("breakfast", ("chutney",)) <= 1)
    solver.Add(count("breakfast", ("drink",)) <= 1)
    solver.Add(count("breakfast", ("fruit",)) <= 1)
    extra_starches = []
    for slot in ("lunch", "dinner"):
        bread, rd, bf = count(slot, ("staple",)), count(slot, ("rice_dish",)), count(slot, ("breakfast",))
        solver.Add(rd + bf <= 1)
        solver.Add(bread <= 2 - 2 * (rd + bf))
        solver.Add(bread + rd + bf >= 1)
        # a second kind of staple (rice and roti together) only when the targets need it
        extra_starch = solver.NumVar(0, 1, "")
        solver.Add(bread - extra_starch <= 1)
        extra_starches.append(extra_starch)
        staple_n = [n[k] for k in n if k[1] == slot and by_id[k[0]]["role"] == "staple"]
        solver.Add(solver.Sum(staple_n) <= 4)
        solver.Add(solver.Sum([n[k] for k in n if k[1] == slot and by_id[k[0]]["role"] == "staple"
                               and "cup" in by_id[k[0]]["serving"]]) <= 2)
        solver.Add(solver.Sum([z[k] for k in z if k[1] == slot and by_id[k[0]]["role"] == "staple"
                               and "cup" in by_id[k[0]]["serving"]]) <= 1)  # one kind of rice per meal
        main_side = count(slot, ("dal", "curry", "liquid"))
        solver.Add(main_side >= 2 * (1 - rd - bf) - (1 if slot == "dinner" else 0))
        solver.Add(main_side <= 3)
        solver.Add(count(slot, ("dal", "curry")) >= 1 - rd - bf)
        solver.Add(count(slot, ("chutney", "liquid", "curry", "dal", "side")) >= bf)
        for roles, most in ((("dal",), 1), (("liquid",), 1), (("curry",), 2), (("side",), 1), (("chutney",), 1),
                            (("drink",), 1), (("fruit",), 1), (("sweet",), 1 if slot == "lunch" else 0)):
            solver.Add(count(slot, roles) <= most)
    snack_items = count("snack", ("snack", "fruit", "drink", "sweet"))
    solver.Add(snack_items >= 1)
    solver.Add(snack_items <= 2)
    solver.Add(count("snack", ("snack", "sweet")) <= 1)
    solver.Add(count("snack", ("chutney",)) <= count("snack", ("snack", "breakfast")))
    solver.Add(count("snack", ("side", "staple", "dal", "curry", "liquid", "rice_dish")) == 0)
    for d in dishes:  # a dish once a day, except staples and drinks; at most one sweet a day
        uses = [z[k] for k in z if k[0] == d["id"]]
        if uses and d["role"] != "staple" and d["id"] not in REPEATABLE_DISHES:
            solver.Add(solver.Sum(uses) <= 1)
    solver.Add(solver.Sum([z[k] for k in z if by_id[k[0]]["role"] == "sweet"]) <= 1)

    def total(key, credit=False):
        return solver.Sum([n[k] * (credited(by_id[k[0]], key) if credit else (by_id[k[0]]["per_serving"].get(key) or 0))
                           for k in n])

    energy, protein = total("energy_kcal"), total("protein_g")
    solver.Add(energy >= 0.95 * t["energy_kcal"])
    solver.Add(energy <= 1.05 * t["energy_kcal"])
    protein_short = solver.NumVar(0, solver.infinity(), "")
    solver.Add(protein + protein_short >= t["protein_g"])
    fat, sat = total("fat_g"), total("saturated_fat_g")
    solver.Add(9 * fat <= 0.35 * energy)
    fat_excess, sat_excess = solver.NumVar(0, solver.infinity(), ""), solver.NumVar(0, solver.infinity(), "")
    solver.Add(9 * fat - fat_excess <= 0.30 * energy)
    sat_limit = 0.07 if "high_cholesterol" in person.conditions else 0.10
    solver.Add(9 * sat - sat_excess <= sat_limit * energy)
    sodium = total("sodium_mg")
    sodium_excess = solver.NumVar(0, solver.infinity(), "")
    solver.Add(sodium - sodium_excess <= t["sodium_mg"])
    solver.Add(sodium <= t["sodium_mg"] + 1500)

    cost = [150 * protein_short / max(t["protein_g"], 1), 20 * fat_excess / 100, 20 * sat_excess / 100,
            (40 if "hypertension" in person.conditions else 15) * sodium_excess / 1000] + [3.0 * s for s in extra_starches]
    for key, rda in t["rda"].items():
        short = solver.NumVar(0, rda, "")
        solver.Add(total(key, credit=True) + short >= rda)
        low = key in t["low"]
        weight = 120 if low else (12 if request.style == "nutritious" else 4)
        cost.append(weight * short / rda)

    picked = [food_codes(f) for f in person.picked_foods]
    for codes in picked:  # each picked food in at least one dish today, if any eligible dish has it
        having = [z[k] for k in z if dish_codes(k[0]) & codes]
        if having:
            missing = solver.BoolVar("")
            solver.Add(solver.Sum(having) + missing >= 1)
            cost.append((25 if request.style == "familiar" else 12) * missing)

    usual = usual_dishes(person.usual_diet, dishes)
    for k in z:  # style preferences
        if k[0] in usual and request.style != "nutritious":
            cost.append(-2.0 * z[k])
        d = by_id[k[0]]
        local = region and (region in d["regions"] or (d["id"] in RICE_DISHES and region in RICE_STATES))
        if request.style in ("familiar", "regional"):
            cost.append((-3.0 if local else (0 if "all" in d["regions"] else 2.0)) * z[k])
        else:
            cost.append((0 if local or "all" in d["regions"] else 0.4) * z[k])
        if d["role"] in ("sweet", "snack") and d["max_per_week"] <= 2:
            cost.append(1.0 * z[k])
        cost.append(request.avoid.get(k[0], 0) * z[k])
        cost.append(0.05 * n[k])  # prefer fewer, larger-looking servings to many small items

    solver.Minimize(solver.Sum(cost))
    status = solver.Solve()
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return None
    chosen = {k: int(round(n[k].solution_value())) for k in n if n[k].solution_value() > 0.5}
    return describe_day(chosen, by_id, t)


def usual_dishes(text: str, dishes: list) -> set:
    """Dishes whose name or another name for them appears in the person's own words."""
    text = " " + " ".join(text.lower().replace(",", " ").split()) + " "
    if not text.strip():
        return set()
    found = set()
    for d in dishes:
        names = [d["name"].split(" (")[0], *d["name"].split("(")[1:], *d["also_called"]]
        for name in names:
            name = name.strip(" )").lower()
            if len(name) >= 4 and f" {name} " in text:
                found.add(d["id"])
    # Other spellings and languages ("pesarattu", "పెసరట్టు", "moong dosa") through the e5 model.
    from app.nlp import embed
    ids = {d["id"] for d in dishes}
    return found | {dish for dish in embed.match_items(text, "dish") if dish in ids}


SELF_CONTAINED = {"poha", "rava_upma", "semiya_upma", "ven_pongal", "uggani", "oats_milk", "whole_wheat_bread",
                  "sarva_pindi", "namkeen_dalia", "meetha_dalia", "kuzhi_paniyaram", "bisi_bele_bath"}


def _self_contained(slot, z, by_id, solver):
    return solver.Sum([z[k] for k in z if k[1] == slot and k[0] in SELF_CONTAINED])


def describe_day(chosen: dict, by_id: dict, t: dict) -> dict:
    meals = {s: [] for s in SLOTS}
    totals = defaultdict(float)
    for (dish_id, slot), servings in sorted(chosen.items(), key=lambda kv: SLOTS.index(kv[0][1])):
        d = by_id[dish_id]
        meals[slot].append({"dish_id": dish_id, "name": d["name"], "names": d.get("names", {}), "servings": servings,
                            "serving": d["serving"],
                            "role": d["role"], "energy_kcal": servings * d["per_serving"]["energy_kcal"]})
        for key, value in d["per_serving"].items():
            totals[key] += servings * (value or 0)
    totals = {k: round(v, 1) for k, v in totals.items()}
    met = {k: totals.get(k, 0) >= rda for k, rda in t["rda"].items()}
    # Low nutrients the day still falls short of, shown openly (vitamin D rarely comes from food alone).
    shortfalls = {k: {"actual": totals.get(k, 0), "target": t["rda"][k],
                      "pct_met": round(100 * totals.get(k, 0) / t["rda"][k], 1)}
                  for k in t.get("low", []) if k in t["rda"] and totals.get(k, 0) < t["rda"][k]}
    return {"meals": meals, "totals": totals, "targets": t, "rda_met": met, "shortfalls": shortfalls,
            "salt_g": round(totals.get("sodium_mg", 0) * 2.54 / 1000, 1)}


# ----------------------------------------------------------------------------------------------- plans

def _main_dishes(day: dict) -> set:
    return {i["dish_id"] for items in day["meals"].values() for i in items if i["role"] not in REPEATABLE_ROLES
            and i["role"] not in ("side", "fruit", "chutney")}


def options(person: Person) -> list:
    """Three one-day options that share as few main dishes as possible."""
    dishes, used, out = eligible(person), {}, []
    for style in OPTION_STYLES:
        day = solve_day(person, dishes, DayRequest(style=style, avoid=dict(used)))
        if day is None:
            continue
        day["style"], day["title"] = style, STYLE_TITLES[style]
        out.append(day)
        for dish_id in _main_dishes(day):
            used[dish_id] = used.get(dish_id, 0) + 3.0
    return out


def week(person: Person, style: str = "familiar") -> list:
    """Seven days: weekly limits per dish, no main dish two days running, and variety across the week."""
    dishes, days, weekly, seen = eligible(person), [], defaultdict(int), defaultdict(int)
    limits = {d["id"]: d["max_per_week"] for d in dishes}
    for _ in range(7):
        yesterday = _main_dishes(days[-1]) if days else set()
        banned = {i for i, c in weekly.items() if c >= limits.get(i, 7)} | yesterday
        avoid = {i: 1.5 * c for i, c in seen.items()}
        day = solve_day(person, dishes, DayRequest(style=style, banned=banned, avoid=avoid))
        if day is None:  # relax variety before giving up
            day = solve_day(person, dishes, DayRequest(style=style, banned={i for i, c in weekly.items()
                                                                             if c >= limits.get(i, 7)}))
        if day is None:
            break
        for items in day["meals"].values():
            for item in items:
                weekly[item["dish_id"]] += 1
                if item["role"] not in REPEATABLE_ROLES:
                    seen[item["dish_id"]] += 1
        days.append(day)
    return days


def swap(person: Person, day: dict, slot: str, dish_id: str, style: str = "familiar"):
    """Replace one dish in one meal; the rest of the day stays as it is, servings may adjust."""
    fixed = {(i["dish_id"], s): i["servings"] for s, items in day["meals"].items() if s != slot for i in items}
    keep = {(i["dish_id"], slot): None for i in day["meals"][slot] if i["dish_id"] != dish_id}
    request = DayRequest(style=style, fixed=fixed, banned_in_slot={(dish_id, slot)},
                         avoid={i: 0.5 for i, _ in keep})
    return solve_day(person, eligible(person), request)


def shopping_list(days: list) -> list:
    """Raw ingredients to buy for the given days, as purchase weight (edible weight / IFCT yield)."""
    by_id, table = catalog(), ingredients()
    need = defaultdict(float)
    for day in days:
        for items in day["meals"].values():
            for item in items:
                for line in by_id[item["dish_id"]]["ingredients"]:
                    for name, grams in expand(line["name"], line["grams"]):
                        need[name] += grams * item["servings"]
    out = []
    for name, grams in sorted(need.items(), key=lambda kv: -kv[1]):
        codes = INGREDIENTS[name][0]
        code = codes if isinstance(codes, str) else codes[0]
        yield_factor = table[code].get("yield_factor") or 1.0
        out.append({"name": name, "names": local_names(name), "edible_g": round(grams),
                    "buy_g": round(grams / max(yield_factor, 0.3)), "aisle": aisle(name, table[code])})
    return out


AISLES = ("grains", "pulses", "vegetables", "greens", "fruits", "dairy", "meat_fish", "nuts_seeds", "spices", "oils",
          "other")
_GROUP_AISLE = {
    "Cereals and Millets": "grains", "Grain Legumes": "pulses", "Green Leafy Vegetables": "greens",
    "Other Vegetables": "vegetables", "Roots and Tubers": "vegetables", "Mushrooms": "vegetables", "Fruits": "fruits",
    "Milk and Milk Products": "dairy", "Egg and Egg Products": "meat_fish", "Poultry": "meat_fish",
    "Animal Meat": "meat_fish", "Marine Fish": "meat_fish", "Marine Shellfish": "meat_fish",
    "Marine Mollusks": "meat_fish", "Fresh Water Fish and Shellfish": "meat_fish", "Nuts and Oil Seeds": "nuts_seeds",
    "Condiments and Spices": "spices", "Edible Oils and Fats": "oils", "Indian foods (NVIF)": "grains",
}
_NAME_AISLE = {"curd": "dairy", "butter": "dairy", "fresh cream": "dairy", "milk": "dairy", "fortified milk": "dairy",
               "buttermilk": "dairy", "paneer": "dairy", "khoa": "dairy", "tofu": "pulses", "soya chunks": "pulses",
               "kabuli chana": "pulses", "oats": "grains", "whole wheat bread": "grains", "sago": "grains",
               "cornflour": "grains", "coconut milk": "other", "mushroom": "vegetables", "onion": "vegetables",
               "small onion": "vegetables", "spring onion": "vegetables", "coriander leaves": "greens",
               "mint leaves": "greens", "curry leaves": "greens", "drumstick leaves": "greens"}


def aisle(name: str, food: dict) -> str:
    """The shopping-list section an ingredient belongs to (from its IFCT food group)."""
    return _NAME_AISLE.get(name) or _GROUP_AISLE.get(food.get("group"), "other")
