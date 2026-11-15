import pytest
from app.parsers.llm_fallback import parse_llm_json_response, extract_with_gemini_fallback

def test_parse_llm_json_markdown_wrapped():
    raw = """```json
    [
      {
        "biomarker_key": "vitamin_d",
        "detected_value": 14.2,
        "detected_unit": "ng/mL",
        "ref_low": 30.0,
        "ref_high": 100.0,
        "confidence": 0.98
      }
    ]
    ```"""
    markers = parse_llm_json_response(raw)
    assert len(markers) == 1
    assert markers[0].biomarker_key == "vitamin_d"
    assert markers[0].detected_value == 14.2
    assert markers[0].detected_unit == "ng/mL"
    assert markers[0].report_reference_range.low == 30.0
    assert markers[0].report_reference_range.high == 100.0

def test_parse_llm_json_nested_dict():
    raw = """{
      "biomarkers": [
        {
          "biomarker_key": "Serum Ferritin",
          "detected_value": "9.5 ug/L",
          "detected_unit": "ug/L",
          "ref_low": "11.0",
          "ref_high": "307.0",
          "confidence": "0.92"
        }
      ]
    }"""
    markers = parse_llm_json_response(raw)
    assert len(markers) == 1
    assert markers[0].biomarker_key == "ferritin"
    assert markers[0].canonical_value == 9.5
    assert markers[0].report_reference_range.low == 11.0

def test_parse_llm_json_alias_resolution():
    raw = """[
      {"biomarker_key": "Hemoglobin", "detected_value": 11.5, "detected_unit": "g/dL"},
      {"biomarker_key": "Cobalamin", "detected_value": 150.0, "detected_unit": "pg/mL"},
      {"biomarker_key": "Folic Acid", "detected_value": 3.8, "detected_unit": "ng/mL"}
    ]"""
    markers = parse_llm_json_response(raw)
    keys = {m.biomarker_key for m in markers}
    assert keys == {"hemoglobin", "vitamin_b12", "folate"}

def test_parse_llm_json_invalid_inputs():
    assert parse_llm_json_response("") == []
    assert parse_llm_json_response("This is not JSON at all") == []
    assert parse_llm_json_response("[]") == []

def test_extract_with_gemini_fallback_no_api_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    from app.config import settings
    settings.gemini_api_key = ""
    res = extract_with_gemini_fallback("Sample text")
    assert res == []

