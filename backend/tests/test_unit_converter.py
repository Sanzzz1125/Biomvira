import pytest
from app.engine.unit_converter import convert_to_canonical

def test_vitamin_d_canonical():
    val, unit = convert_to_canonical("vitamin_d", 25.0, "ng/mL")
    assert val == 25.0
    assert unit == "ng/mL"

def test_vitamin_d_conversion_from_nmol():
    # 50 nmol/L should be ~20.03 ng/mL
    val, unit = convert_to_canonical("vitamin_d", 50.0, "nmol/L")
    assert unit == "ng/mL"
    assert 19.8 <= val <= 20.2

def test_calcium_conversion_from_mmol():
    # 2.2 mmol/L should be ~8.82 mg/dL
    val, unit = convert_to_canonical("calcium", 2.2, "mmol/L")
    assert unit == "mg/dL"
    assert 8.7 <= val <= 8.9

def test_hemoglobin_conversion_from_g_per_l():
    # 135 g/L should be 13.5 g/dL
    val, unit = convert_to_canonical("hemoglobin", 135.0, "g/L")
    assert unit == "g/dL"
    assert val == 13.5

def test_b12_conversion_from_pmol():
    # 200 pmol/L should be ~271.08 pg/mL
    val, unit = convert_to_canonical("vitamin_b12", 200.0, "pmol/L")
    assert unit == "pg/mL"
    assert 270 <= val <= 272

def test_hemoglobin_g_percent():
    val, unit = convert_to_canonical("hemoglobin", 12.5, "g%")
    assert unit == "g/dL"
    assert val == 12.5

def test_calcium_mg_percent():
    val, unit = convert_to_canonical("calcium", 9.1, "mg%")
    assert unit == "mg/dL"
    assert val == 9.1

