"""Rows whose names contain a supported test but measure something else, and repeated differential tables.
Made-up rows in the layout of a common Indian lab template; no real report is used."""
from app.engine.unit_converter import convert_to_canonical
from app.parsers.regex_matcher import extract_biomarkers_with_regex, mentioned_keys


def rows(text):
    return [(m.biomarker_key, m.detected_value) for m in extract_biomarkers_with_regex(text)]


def test_lookalike_rows_are_not_read_as_the_test():
    text = ("Serum Calcium 9.7 mg/dl 8.8 - 10.6\nCorrected Calcium 9.46 mg/dL 8.5 - 10.5\n"
            "HDL Cholesterol 57.5 mg/dl 35 - 80\nNon-HDL Cholesterol 105 mg/dL < 130\nCA 19-9 18.5 U/mL 0 - 37")
    found = rows(text)
    assert ("calcium", 9.7) in found and ("hdl_cholesterol", 57.5) in found
    assert [k for k, _ in found].count("calcium") == 1 and [k for k, _ in found].count("hdl_cholesterol") == 1


def test_percentages_repeated_under_a_count_unit_are_dropped():
    text = ("Neutrophils 57.5 % 40 - 75\nNeutrophil (Abs) 4.31 ×10³/µL 1.8 - 7.7\n"
            "Differential Leukocyte Count (Absolute count)\nNeutrophils 57.5 x10^3/μL 40 - 75")
    found = rows(text)
    assert ("neutrophils", 57.5) in found and ("neutrophils_abs", 4.31) in found
    assert ("neutrophils_abs", 57.5) not in found
    assert all(m.verification_status != "conflict" for m in extract_biomarkers_with_regex(text))


def test_t4_in_ng_per_ml():
    assert convert_to_canonical("t4", 89.5, "ng/mL") == (8.95, "µg/dL")


def test_sentences_and_ignored_rows_are_not_unread_results():
    assert not mentioned_keys("Only free T4 is biologically active.\nRDW-SD 45.5 fL 37 - 54")
