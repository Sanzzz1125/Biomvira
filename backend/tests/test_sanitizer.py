from app.parsers.sanitizer import sanitize_report_text

def test_sanitizer_removes_patient_name_and_phone():
    sample = """
    DR. LAL PATHLABS
    Patient Name: Rahul Sharma
    Age / Sex: 34 Y / Male
    Ref By: Dr. A. K. Verma
    Mobile: 9876543210
    UHID: DEL1234567
    
    Test Description         Result    Unit     Reference Interval
    25-OH Vitamin D          14.2      ng/mL    30.0 - 100.0
    """
    sanitized, modified = sanitize_report_text(sample)
    assert modified is True
    assert "Rahul Sharma" not in sanitized
    assert "9876543210" not in sanitized
    assert "[REDACTED_NAME]" in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    # Clinical values must be intact
    assert "14.2" in sanitized
    assert "30.0 - 100.0" in sanitized

def test_sanitizer_preserves_adjacent_clinical_fields():
    sample = "Patient Name: Jane Doe Age: 29 Sex: Female Ref By: Dr. Gupta\nHemoglobin: 11.2 g/dL"
    sanitized, modified = sanitize_report_text(sample)
    assert modified is True
    assert "Jane Doe" not in sanitized
    assert "[REDACTED_NAME]" in sanitized
    assert "Age: 29" in sanitized
    assert "Sex: Female" in sanitized
    assert "Hemoglobin: 11.2 g/dL" in sanitized

