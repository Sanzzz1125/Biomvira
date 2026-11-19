"""Hindi and Telugu results: every translation lines up, numbers survive, and localised results stay valid."""
import re

import pytest

from app.i18n import FOLDER, localize_analysis, table, warning

ANALYSIS = {
    "user_profile": {"age": 30, "gender": "female", "diet_type": "veg", "allergens": []},
    "biomarkers": [
        {"biomarker_key": "hemoglobin", "value": 10.2, "unit": "g/dL"},
        {"biomarker_key": "vitamin_d", "value": 8, "unit": "ng/mL"},
        {"biomarker_key": "hba1c", "value": 6.0, "unit": "%"},
        {"biomarker_key": "creatinine", "value": 2.5, "unit": "mg/dL"},
    ],
}


@pytest.mark.parametrize("lang", ["hi", "te"])
def test_translation_files_line_up(lang):
    english = (FOLDER / "strings_en.txt").read_text(encoding="utf-8").strip("\n").split("\n")
    translated = (FOLDER / f"{lang}.txt").read_text(encoding="utf-8").strip("\n").split("\n")
    assert len(english) == len(translated)
    for e, t in zip(english, translated):
        assert sorted(re.findall(r"\d+(?:\.\d+)?", e)) == sorted(re.findall(r"\d+(?:\.\d+)?", t)), e
    script = "[ऀ-ॿ]" if lang == "hi" else "[ఀ-౿]"
    assert all(re.search(script, t) or not re.search("[A-Za-z]{4}", e.replace("ESR", "")) for e, t in zip(english, translated)
               if e not in ("MCHC", "RDW-CV", "eGFR", "SGOT / AST", "SGPT / ALT", "ESR"))


def test_every_result_text_is_in_the_table():
    from app.engine.recommender import ABSORPTION_RULES, TAG_LABELS
    for lang in ("hi", "te"):
        t = table(lang)
        assert all(v in t for v in TAG_LABELS.values())
        assert all(x in t for r in ABSORPTION_RULES.values() for x in r["dos"] + r["donts"])


def test_warning_templates_keep_the_test_name_translated():
    text = "Serum Creatinine is above its reference range. NutriLens does not give food advice for this test; please review it with your doctor."
    assert "सीरम क्रिएटिनिन" in warning(text, "hi")
    assert "సీరం క్రియాటినిన్" in warning(text, "te")


@pytest.mark.parametrize("lang,script", [("hi", "[ऀ-ॿ]"), ("te", "[ఀ-౿]")])
def test_localized_results(api, lang, script):
    client = api()
    english = client.post("/api/v1/analyze-and-recommend", json=ANALYSIS).json()
    r = client.post(f"/api/v1/localize-analysis?lang={lang}", json=english)
    assert r.status_code == 200, r.text
    shown = r.json()
    for m in shown["marker_analyses"]:
        assert re.search(script, m["display_name"]), m["display_name"]
        assert m["value"] in [x["value"] for x in english["marker_analyses"]]
    for plan in shown["recommendations"]:
        assert all(re.search(script, f["name"]) for f in plan["recommended_foods"])
    assert re.search(script, shown["grounded_explanation"].split("\n")[0])
    assert all(re.search(script, w) for w in shown["consult_reasons"])
    assert english == localize_analysis(english, "en")


def test_frontend_copies_match_the_backend():
    frontend = FOLDER.parents[3] / "frontend" / "src" / "lib" / "i18n"
    for backend_name, frontend_name in (("strings_en.txt", "data_en.txt"), ("hi.txt", "data_hi.txt"), ("te.txt", "data_te.txt")):
        assert (FOLDER / backend_name).read_text(encoding="utf-8") == (frontend / frontend_name).read_text(encoding="utf-8")


@pytest.mark.parametrize("lang", ["hi", "te"])
def test_ui_translation_files_line_up(lang):
    folder = FOLDER.parents[3] / "frontend" / "src" / "lib" / "i18n"
    english = (folder / "ui_en.txt").read_text(encoding="utf-8").split("\n")
    translated = (folder / f"ui_{lang}.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    assert len(english) == len(translated)
    for e, t in zip(english, translated):
        assert sorted(re.findall(r"\d+(?:\.\d+)?", e)) == sorted(re.findall(r"\d+(?:\.\d+)?", t)), e


# ── Hindi and Telugu PDFs ─────────────────────────────────────────────────────
def test_pdf_wording_has_both_languages_and_same_placeholders():
    from app.utils.pdf_text import TEXT
    for english, (hindi, telugu) in TEXT.items():
        wanted = sorted(re.findall(r"{\w+}", english))
        assert sorted(re.findall(r"{\w+}", hindi)) == wanted, english
        assert sorted(re.findall(r"{\w+}", telugu)) == wanted, english
        assert re.search(r"[ऀ-ॿ]", hindi) and re.search(r"[ఀ-౿]", telugu), english


def test_every_shopping_ingredient_has_hindi_and_telugu_names():
    from app.plan.ingredient_local import NAMES
    from app.plan.ingredient_names import INGREDIENTS
    assert set(INGREDIENTS) <= set(NAMES)
    for hindi, telugu in NAMES.values():
        assert re.search(r"[ऀ-ॿ]", hindi) and re.search(r"[ఀ-౿]", telugu)


def test_every_serving_word_is_translated():
    from app.plan.catalog import catalog
    from app.utils.diet_plan_pdf import localize_words
    dishes = catalog()
    for d in (dishes.values() if isinstance(dishes, dict) else dishes):
        for lang in ("hi", "te"):
            left = set(re.findall(r"[A-Za-z]+", localize_words(d["serving"], lang))) - {"ml"}
            assert not left, (d["serving"], lang, left)


@pytest.mark.parametrize("lang", ["hi", "te"])
def test_report_and_diet_plan_pdfs_in_indian_languages(lang):
    from app.plan.engine import Person, shopping_list, week
    from app.utils.diet_plan_pdf import generate_diet_plan_pdf
    from app.utils.pdf_generator import generate_plan_pdf
    from app.utils.pdf_text import LANG
    days = week(Person(age=30, sex="female", height_cm=160, weight_kg=57, activity="none", diet="veg",
                       region="telangana"))[:2]
    data = {"analysis_id": "abc12345", "timestamp": "2026-01-01T10:00:00Z", "marker_analyses": [],
            "recommendations": [], "status_summary": {}, "grounded_explanation": "", "requires_physician_consult": False,
            "consult_reasons": [], "user_profile": {"age": 30, "gender": "female", "diet_type": "veg", "allergens": []},
            "diet_plan": {"style": "familiar", "days": days, "shopping_list": shopping_list(days)}}
    for pdf in (generate_plan_pdf(data, lang), generate_diet_plan_pdf(days, shopping_list(days), lang=lang)):
        assert pdf.startswith(b"%PDF") and (b"NotoSansHi" if lang == "hi" else b"NotoSansTe") in pdf
    assert LANG.get() == "en"  # the language never leaks into the next request
