"""The existing-diet upload: text from a PDF or photo, with names and phone numbers removed."""
from io import BytesIO

from reportlab.pdfgen import canvas


def _pdf(lines):
    stream = BytesIO()
    page = canvas.Canvas(stream)
    for i, line in enumerate(lines):
        page.drawString(72, 760 - 20 * i, line)
    page.save()
    return stream.getvalue()


def test_diet_chart_pdf_becomes_text(api):
    client = api()
    pdf = _pdf(["Patient: Ravi Kumar  Mobile: 9876543210", "Breakfast: 2 idli with sambar", "Lunch: rice, tomato pappu, curd"])
    response = client.post("/api/v1/diet-text", files={"file": ("diet.pdf", pdf, "application/pdf")})
    assert response.status_code == 200, response.text
    text = response.json()["text"]
    assert "idli" in text and "tomato pappu" in text
    assert "9876543210" not in text


def test_diet_upload_rejects_other_files(api):
    client = api()
    response = client.post("/api/v1/diet-text", files={"file": ("diet.docx", b"PK\x03\x04", "application/msword")})
    assert response.status_code == 422
