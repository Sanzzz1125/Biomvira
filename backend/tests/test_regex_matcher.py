import pytest
from app.parsers.regex_matcher import extract_biomarkers_with_regex

def test_extract_biomarkers_with_embedded_numbers_in_name():
    # Report line where test name contains a number like '25-OH' or 'Vit B9' or 'B12'
    text = """
    Test Description              Result    Unit      Reference Interval
    25-OH Vitamin D (Total)       14.2      ng/mL     30.0 - 100.0
    Serum Folate (Vit B9)         3.5       ng/mL     4.0 - 20.0
    Vitamin B12 (Cyanocobalamin)  185.0     pg/mL     211.0 - 911.0
    """
    markers = extract_biomarkers_with_regex(text)
    m_dict = {m.biomarker_key: m for m in markers}

    assert "vitamin_d" in m_dict
    assert m_dict["vitamin_d"].detected_value == 14.2
    assert m_dict["vitamin_d"].report_reference_range.low == 30.0
    assert m_dict["vitamin_d"].report_reference_range.high == 100.0

    assert "folate" in m_dict
    assert m_dict["folate"].detected_value == 3.5
    assert m_dict["folate"].report_reference_range.low == 4.0

    assert "vitamin_b12" in m_dict
    assert m_dict["vitamin_b12"].detected_value == 185.0

def test_extract_biomarkers_pipe_separated_tables():
    text = """
    Hemoglobin | 11.5 | g/dL | 12.0 - 15.5
    Total Calcium | 9.2 | mg/dL | 8.8 - 10.2
    Serum Ferritin | 8.0 | ng/mL | 15.0 - 307.0
    """
    markers = extract_biomarkers_with_regex(text)
    m_dict = {m.biomarker_key: m for m in markers}

    assert "hemoglobin" in m_dict
    assert m_dict["hemoglobin"].detected_value == 11.5

    assert "calcium" in m_dict
    assert m_dict["calcium"].detected_value == 9.2

    assert "ferritin" in m_dict
    assert m_dict["ferritin"].detected_value == 8.0

