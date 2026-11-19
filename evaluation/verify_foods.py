"""Recalculate the hand-entered foods in foods.json from IFCT 2017 (plus USDA SR Legacy / ICMR-NIN NVIF where IFCT has no entry).

Each food's stated serving is written as raw ingredients and a cooking method, then run through the same calculator the
diet-plan dishes use (app/plan/nutrition.py: IFCT values per 100 g raw, cooking losses from IFCT, B12 from USDA).
Cooked servings are converted to raw weight with standard yields: pulses 150 g cooked = 50 g raw; leafy greens
100 g cooked = 130 g raw; other vegetables lose about 10%; meat about 25-30%; fish and prawns about 20%.

Usage (from the repository root):  python evaluation/verify_foods.py [--write]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.plan.nutrition import calculate, ingredients  # noqa: E402

FOODS = ROOT / "backend" / "app" / "data" / "foods.json"
AMLA = next(code for code, f in ingredients().items() if f["name"] == "Goosberry")
B, N, R, F = "boiling", "none", "roasting", "frying"

# food id -> [(IFCT/USDA codes, raw grams, method)] for the serving stated in foods.json
RECIPES = {
    "moringa_leaves": [(["C019"], 130, B)], "palak_spinach": [(["C033"], 130, B)], "methi_leaves": [(["C020"], 130, B)],
    "amaranth_leaves": [(["C002", "C003", "C004"], 130, B)], "curry_leaves": [(["G010"], 15, F)],
    "ragi_flour": [(["A010"], 60, B)], "bajra_pearl_millet": [(["A003"], 60, R)],
    "sesame_seeds_til": [(["H009", "H010", "H011"], 25, N)], "garden_cress_seeds_aliv": [(["H008"], 10, N)],
    "pumpkin_seeds": [(["X020"], 30, N)], "roasted_chana": [(["B001"], 50, R)],
    "rajma_kidney_beans": [(["B020"], 50, B)], "chana_dal": [(["B001"], 50, B)], "black_urad_dal": [(["B003", "B004"], 50, B)],
    "paneer_cottage_cheese": [(["L003"], 100, N)], "curd_yogurt": [(["X001"], 200, N)], "cow_milk_whole": [(["L002"], 250, B)],
    "whole_egg_boiled": [(["M001"], 100, B)], "chicken_breast": [(["N003"], 200, B)], "chicken_liver": [(["N005"], 125, B)],
    "mutton_goat_meat": [(["O001", "O002", "O003"], 143, B)], "rohu_freshwater_fish": [(["S006"], 188, B)],
    "mackerel_bangda": [(["P034"], 150, R)], "fortified_milk_fssai": [(["X018"], 250, B)],
    "fortified_soy_milk": [(["X024"], 250, N)], "sun_exposed_mushrooms": [(["X017"], 140, F)],
    "amla_indian_gooseberry": [([AMLA], 50, N)], "lemon_citrus": [(["E033"], 30, N)], "guava_peru": [(["E028", "E029"], 120, N)],
    "beetroot": [(["F001"], 100, N)], "dates_khajoor": [(["E017", "E018"], 40, N)], "almonds_badam": [(["H001"], 25, N)],
    "black_raisins_kishmish": [(["E057"], 30, N)], "tofu_firm": [(["X006"], 100, N)], "horse_gram_kulthi": [(["B012"], 50, B)],
    "moth_beans_matki": [(["B016"], 50, B)], "soybean_cooked": [(["B024", "B025"], 50, B)],
    "lobia_black_eyed_peas": [(["B005", "B006"], 50, B)], "drumstick_vegetable": [(["D046"], 110, B)],
    "bitter_gourd_karela": [(["D004", "D005", "D006"], 110, B)], "bottle_gourd_lauki": [(["D007", "D008", "D009"], 165, B)],
    "raw_banana_plantain": [(["D063"], 110, B)], "sweet_potato": [(["F013", "F014"], 150, B)],
    "lotus_seeds_makhana": [(["X027"], 30, R)], "flaxseeds_alsi": [(["H014"], 15, N)], "sunflower_seeds": [(["H020"], 30, N)],
    "cashewnuts_kaju": [(["H005"], 30, N)], "jowar_sorghum": [(["A005"], 60, R)], "foxtail_millet_kangni": [(["X026"], 60, B)],
    "little_millet_kutki": [(["A016"], 60, B)], "cod_liver_oil_capsule": [(["X022"], 4.5, N)], "hilsa_fish_ilish": [(["P017"], 125, B)],
    "prawn_shrimp": [(["S008", "S009", "S010"], 125, B)], "mutton_liver": [(["O008"], 125, B)], "papaya_ripe": [(["E049"], 150, N)],
    "orange_mosambi": [(["E047", "E034"], 150, N)], "dried_figs_anjeer": [(["X025"], 40, N)],
    "dried_apricots_khumani": [(["E005"], 40, N)], "ghee_clarified_butter": [(["T013"], 5, N)],
    "coconut_oil_virgin": [(["T001"], 14, N)], "tamarind_imli": [(["E064"], 20, N)], "jaggery_gud": [(["I001"], 20, N)],
    "wheat_germ": [(["X021"], 30, N)], "tempeh": [(["X023"], 100, N)],
}
REMOVE = {"nutritional_yeast"}  # B12 depends on each brand's fortification: no brand-independent source
KEYS = {"iron_mg": "iron_mg", "calcium_mg": "calcium_mg", "folate_mcg": "folate_ug", "vitamin_c_mg": "vitamin_c_mg",
        "vitamin_d_iu": "vitamin_d_iu", "vitamin_b12_mcg": "vitamin_b12_ug"}


def main(write: bool) -> None:
    data = json.loads(FOODS.read_text(encoding="utf-8"))
    hand = [f for f in data["foods"] if not f["id"].startswith("ifct_")]
    missing = {f["id"] for f in hand} - set(RECIPES) - REMOVE
    assert not missing, f"no recipe for {missing}"
    for food in hand:
        if food["id"] in REMOVE:
            continue
        result = calculate([(codes, grams, method) for codes, grams, method in RECIPES[food["id"]]])
        new = {key: round(result["per_serving"][src], 1) for key, src in KEYS.items()}
        old = food["nutrients"]
        flag = " <-- off by >30%" if any(abs(new[k] - (old.get(k) or 0)) > 0.3 * max(new[k], old.get(k) or 0, 0.5)
                                         for k in ("iron_mg", "calcium_mg")) else ""
        print(f"{food['id'][:26]:26} {food['serving_size'][:22]:22} Fe {old.get('iron_mg')}->{new['iron_mg']} "
              f"Ca {old.get('calcium_mg')}->{new['calcium_mg']} Fol {old.get('folate_mcg')}->{new['folate_mcg']} "
              f"B12 {old.get('vitamin_b12_mcg')}->{new['vitamin_b12_mcg']} D {old.get('vitamin_d_iu')}->{new['vitamin_d_iu']}{flag}")
        food["nutrients"].update(new)
        food["source"] = "IFCT 2017 (ICMR-NIN) via evaluation/verify_foods.py" + (
            "; USDA SR Legacy / NVIF where IFCT has no entry" if any(c.startswith("X") for c, *_ in
                                                                    [(cs[0],) for cs, _, _ in RECIPES[food["id"]]]) else "")
        if result["uncertain"]:
            food["uncertain"] = result["uncertain"]
    data["foods"] = [f for f in data["foods"] if f["id"] not in REMOVE]
    if write:
        FOODS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"written: {len(data['foods'])} foods")


if __name__ == "__main__":
    main("--write" in sys.argv)
