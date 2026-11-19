"""Dish values checked against independent references, so a recipe that drifts away from reality fails a test.

1. Energy per 100 g of cooked dish against the UK Composition of Foods Integrated Dataset (CoFID 2021, Public Health
   England; Open Government Licence v3.0), which holds analysed and recipe values for South Asian home dishes. This
   checks the recipe proportions and the cooked serving weight together. The closest CoFID dish is used for each.
   Not compared, because no CoFID dish is cooked the same way: kakarakaya and thotakura vepudu (Telugu fries are much
   drier than UK bhaji), and sambar (lies between CoFID's UK samples and Indian textbook recipes).
2. A typical day of Telugu meals against national intake: salt near the 8.0 g/day measured in India's National NCD
   Monitoring Survey (Scientific Reports 2023; 8.9 g men, 7.1 g women) and fat at 20-35% of energy.
"""
import pytest

from app.plan.catalog import catalog

# dish id: (CoFID code, CoFID food name, kcal per 100 g)
COFID = {
    "steamed_rice": ("11-862", "Rice, white, long grain, boiled in unsalted water", 131),
    "brown_rice": ("11-869", "Rice, brown, wholegrain, boiled in unsalted water", 132),
    "phulka": ("11-459", "Chapatis, made without fat", 202),
    "chapati": ("11-987", "Chapatis, made with fat, retail", 328),
    "boiled_egg": ("12-940", "Eggs, chicken, whole, boiled", 143),
    "onion_omelette": ("12-946", "Omelette, plain, homemade", 191),
    "oats_milk": ("11-1108", "Porridge, made with whole milk", 112),
    "tomato_pappu": ("15-780", "Curry, pigeon pea dahl, with vegetable oil, homemade", 116),
    "mudda_pappu": ("15-779", "Curry, pigeon pea dahl, with butter, homemade", 108),
    "pesara_pappu": ("15-132", "Curry, mung bean dahl and tomato, homemade", 95),
    "palakura_pappu": ("15-767", "Curry, mung bean dahl and spinach, homemade", 102),
    "bendakaya_fry": ("15-685", "Bhaji, okra, Bangladeshi, with vegetable oil, homemade", 97),
    "cabbage_kura": ("15-740", "Curry, cabbage, masala, homemade", 83),
    "beans_kura": ("15-024", "Bhaji, green bean", 91),
    "aloo_fry": ("15-693", "Bhaji, potato, with vegetable oil, homemade", 161),
    "egg_curry": ("15-753", "Curry, egg, with butter, homemade", 135),
    "chicken_curry": ("19-322", "Curry, chicken, average, takeaway", 145),
    "mutton_curry": ("19-595", "Curry, lamb rogan josh, homemade", 149),
    "chepala_pulusu": ("16-364", "Curry, fish, homemade", 139),
    "chicken_biryani": ("19-454", "Biryani, chicken, takeaway", 163),
    "mutton_biryani": ("19-591", "Curry, lamb biryani, homemade", 195),
    "veg_pulao": ("11-968", "Rice, pilau, plain, homemade", 134),
    "perugu_pachadi": ("17-832", "Raita, homemade", 57),
    "semiya_payasam": ("11-915", "Sevyian, homemade", 119),
    "onion_pakoda": ("15-828", "Pakora/bhajia, onion, fried in vegetable oil, homemade", 270),
    "mirchi_bajji": ("15-826", "Pakora/bhajia, aubergine, fried in vegetable oil, homemade", 294),
    "plain_paratha": ("11-1104", "Paratha, homemade", 333),
    "puri": ("11-911", "Puri, homemade", 366),
    "gulab_jamun": ("11-1083", "Gulab jamen/jambu, retail", 306),
    "sweet_lassi": ("12-373", "Lassi, sweetened", 65),
    "cucumber_raita": ("17-832", "Raita, homemade", 57),
    "rogan_josh": ("19-595", "Curry, lamb rogan josh, homemade", 149),
    "chicken_curry_north": ("19-322", "Curry, chicken, average, takeaway", 145),
    "butter_chicken": ("19-296", "Curry, chicken tikka masala, retail, reheated", 156),
    "chole": ("15-108", "Curry, chick pea, whole and tomato, Punjabi, with vegetable oil, homemade", 112),
    "dal_makhani": ("15-735", "Curry, black gram, whole and red kidney bean, homemade", 94),
    "masoor_dal": ("15-760", "Curry, lentil, red/masoor dahl and tomato, with vegetable oil, homemade", 113),
    "dhuli_moong_dal": ("15-132", "Curry, mung bean dahl and tomato, homemade", 95),
    "sarson_ka_saag": ("15-683", "Bhaji, mustard leaves and spinach, homemade", 84),
    "jeera_aloo": ("15-693", "Bhaji, potato, with vegetable oil, homemade", 161),
}

TYPICAL_DAYS = {
    "Telangana vegetarian": [
        ("idli", 1.5), ("sambar", 1), ("kobbari_pachadi", 1), ("tea", 1), ("steamed_rice", 2), ("tomato_pappu", 1),
        ("bendakaya_fry", 1), ("rasam", 1), ("curd", 1), ("tea", 1), ("banana", 1), ("chapati", 2),
        ("vankaya_tomato", 1), ("curd", 1)],
    "Andhra non-vegetarian": [
        ("pesarattu", 2), ("allam_pachadi", 1), ("filter_coffee", 1), ("steamed_rice", 2), ("chicken_curry", 1),
        ("pappu_charu", 1), ("cabbage_kura", 1), ("curd", 1), ("tea", 1), ("guava", 1), ("steamed_rice", 1.5),
        ("dosakaya_pappu", 1), ("aloo_fry", 1), ("buttermilk", 1)],
    "Tamil Nadu vegetarian": [
        ("idli", 1.5), ("sambar", 1), ("kobbari_pachadi", 1), ("filter_coffee", 1), ("steamed_rice", 2),
        ("kara_kuzhambu", 1), ("beans_kura", 1), ("rasam", 1), ("curd", 1), ("filter_coffee", 1), ("guggillu", 1),
        ("plain_dosa", 2), ("tomato_pachadi", 1)],
    "Kerala non-vegetarian": [
        ("puttu", 1), ("kadala_curry", 1), ("tea", 1), ("matta_rice", 2), ("kerala_fish_curry", 1),
        ("cabbage_thoran", 1), ("sambar", 1), ("buttermilk", 1), ("tea", 1), ("banana", 1), ("appam", 1),
        ("veg_stew", 1)],
    "Karnataka vegetarian": [
        ("rava_upma", 1), ("kobbari_pachadi", 1), ("filter_coffee", 1), ("ragi_sankati", 1), ("steamed_rice", 1),
        ("sambar", 1), ("beans_kura", 1), ("rasam", 1), ("curd", 1), ("tea", 1), ("kosambari", 1), ("chapati", 2),
        ("tovve", 1), ("cabbage_kura", 1)],
    "Punjab vegetarian": [
        ("aloo_paratha", 2), ("curd", 1), ("tea", 1), ("chapati", 3), ("rajma", 1), ("steamed_rice", 1),
        ("cucumber_raita", 1), ("tea", 1), ("apple", 1), ("chapati", 2), ("dal_tadka", 1), ("aloo_gobi", 1)],
}


@pytest.mark.parametrize("dish_id", sorted(COFID))
def test_energy_per_100g_matches_cofid(dish_id):
    dish = catalog()[dish_id]
    ours = 100 * dish["per_serving"]["energy_kcal"] / dish["serving_g"]
    code, name, reference = COFID[dish_id]
    assert 0.7 <= ours / reference <= 1.4, f"{dish_id}: {ours:.0f} kcal/100 g vs CoFID {code} {name}: {reference}"


@pytest.mark.parametrize("day", sorted(TYPICAL_DAYS))
def test_a_typical_day_has_realistic_salt_and_fat(day):
    dishes = catalog()
    kcal = fat = sodium = 0.0
    for dish_id, servings in TYPICAL_DAYS[day]:
        values = dishes[dish_id]["per_serving"]
        kcal += servings * values["energy_kcal"]
        fat += servings * values["fat_g"]
        sodium += servings * values["sodium_mg"]
    salt_g = sodium * 2.54 / 1000
    assert 6.5 <= salt_g <= 9.5, f"{day}: {salt_g:.1f} g salt"
    assert 20 <= 100 * fat * 9 / kcal <= 35, f"{day}: {100 * fat * 9 / kcal:.0f}% of energy from fat"
    assert 1600 <= kcal <= 2400, f"{day}: {kcal:.0f} kcal"
