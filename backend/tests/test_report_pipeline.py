import io
import pytest
from PIL import Image
from reportlab.pdfgen import canvas
from app.parsers import pdf_extractor as pdf
from app.parsers.regex_matcher import extract_biomarkers_with_regex as parse
from app.parsers.sanitizer import clinical_evidence_only
from app.api.v1 import extract
from app.config import settings
from app.engine.unit_converter import convert_to_canonical


def make_pdf(lines, password=None):
    stream = io.BytesIO(); c = canvas.Canvas(stream, encrypt=password)
    for line in lines:
        c.drawString(40,750,line); c.showPage()
    c.save(); return stream.getvalue()


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(settings,'gemini_api_key',''); monkeypatch.setenv('GEMINI_API_KEY','')


def test_native_multipage():
    markers = parse(pdf.extract_upload(make_pdf(['Vitamin D 12.5 ng/mL','Hb 11 g/dL']),'x.pdf','application/pdf'))
    assert [m.source_page for m in markers] == [1,2]


@pytest.mark.parametrize('ext,mime,fmt',[('jpg','image/jpeg','JPEG'),('jpeg','image/jpeg','JPEG'),('png','image/png','PNG')])
def test_images(monkeypatch,ext,mime,fmt):
    stream=io.BytesIO(); Image.new('RGB',(500,500),'white').save(stream,fmt)
    monkeypatch.setattr(pdf,'ocr_image',lambda image,deadline:'Calcium 9.2 mg/dL')
    assert parse(pdf.extract_upload(stream.getvalue(),'x.'+ext,mime))[0].extraction_method == 'ocr_regex'


def test_scanned(monkeypatch):
    monkeypatch.setattr(pdf,'ocr_image',lambda image,deadline:'Vitamin B12 180 pg/mL')
    assert parse(pdf.extract_upload(make_pdf(['']),'x.pdf','application/pdf'))[0].detected_value == 180


@pytest.mark.parametrize('data,name,mime',[(b'','x.pdf','application/pdf'),(b'broken','x.pdf','application/pdf'),(b'hello','x.txt','text/plain'),(b'%PDF-1.7','x.pdf','image/png'),(b'broken','x.png','image/png')])
def test_invalid(data,name,mime):
    with pytest.raises(pdf.ReportError): pdf.extract_upload(data,name,mime)


def test_password():
    with pytest.raises(pdf.ReportError,match='Password'): pdf.extract_upload(make_pdf(['secret'],'secret'),'x.pdf','application/pdf')


def test_limits(monkeypatch):
    monkeypatch.setattr(settings,'max_upload_bytes',2)
    with pytest.raises(pdf.ReportError,match='size'): pdf.extract_upload(b'123','x.pdf','application/pdf')


def test_page_limit(monkeypatch):
    monkeypatch.setattr(settings,'max_report_pages',1)
    with pytest.raises(pdf.ReportError,match='page limit'): pdf.extract_text_and_tables_from_pdf(make_pdf(['one','two']))


def test_six():
    markers=parse('Vitamin D 12,5 ng/mL 30–100\nCobalamin 180 pg/mL\nFolate 4 ng/mL\nFerritin 10 ug/L\nHaemoglobin 120 g/L\nCalcium 2.2 mmol/L')
    assert len(markers)==6 and markers[0].detected_value==12.5 and markers[4].canonical_value==12


def test_reordered():
    marker=parse('Test | Reference Range | Unit | Previous | Result\nVitamin D | 30-100 | ng/mL | 20 | 12.5')[0]
    assert marker.detected_value==12.5 and marker.report_reference_range.low==30


@pytest.mark.parametrize('row',['Vitamin D 12 15 ng/mL','Vitamin D previous 12 ng/mL','Vitamin D 12 strange','Vitamin D <12 ng/mL'])
def test_uncertainty(row):
    assert parse(row)[0].warnings and parse(row)[0].confidence is None


def test_reference_only():
    assert parse('Vitamin D 30-100 ng/mL')==[]


def test_conflicts():
    assert len(parse('Hb 12 g/dL\nHb 12 g/dL'))==1
    markers=parse('Hb 12 g/dL\nHb 9 g/dL')
    assert len(markers)==2 and all(m.verification_status=='conflict' for m in markers)


def test_multiline():
    marker=parse('Vitamin D\n12.5 ng/mL L 30-100')[0]
    assert marker.detected_value==12.5 and marker.abnormal_flag=='L'


@pytest.mark.parametrize('unit',['','g','madeup','ng/mlBAD'])
def test_strict_units(unit):
    with pytest.raises(ValueError): convert_to_canonical('vitamin_d',12,unit)


def test_privacy():
    evidence=clinical_evidence_only('Name: Secret Person\nAddress: Private street\nVitamin D 12 ng/mL Patient: Secret')
    assert 'Secret' not in evidence and 'Private' not in evidence
    assert clinical_evidence_only('Name Secret\nVitamin D unknown')==''


def test_ai_failure(monkeypatch):
    def fail(text): raise ValueError('private')
    monkeypatch.setattr(extract,'extract_with_gemini_fallback',fail)
    result=extract.process_report(None,'','','Vitamin D 12 ng/mL\nFolate unknown')
    assert len(result.extracted_biomarkers)==1 and any('Gemini unavailable' in w for w in result.warnings)


def test_no_ocr(monkeypatch):
    monkeypatch.setattr(pdf.shutil,'which',lambda _:None)
    with pytest.raises(pdf.ReportError,match='unavailable'): pdf.ocr_image(Image.new('RGB',(200,200)),float('inf'))


def test_http_paste_and_invalid():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    app=FastAPI(); app.include_router(extract.router)
    with TestClient(app) as client:
        response=client.post('/extract-report',data={'raw_text':'Vitamin D 12.5 ng/mL 30-100'})
        assert response.status_code==200, response.text
        assert response.json()['extracted_biomarkers'][0]['detected_value']==12.5
        response=client.post('/extract-report',files={'file':('bad.pdf',b'bad','application/pdf')})
        assert response.status_code==422 and 'not a PDF' in response.json()['detail']


@pytest.mark.parametrize('response,expected',[
    ('not json',0),
    ('[{"biomarker_key":"potassium","detected_value":5,"detected_unit":"mmol/L"}]',0),
    ('[{"biomarker_key":"vitamin_d","detected_value":99,"detected_unit":"ng/mL"}]',0),
    ('[{"biomarker_key":"vitamin_d","detected_value":12,"detected_unit":"ng/mL"}]',1),
    ('[{"biomarker_key":"vitamin_d","detected_value":"<12","detected_unit":"ng/mL"}]',0),
])
def test_mock_gemini_grounding(monkeypatch,response,expected):
    from types import SimpleNamespace
    from google import genai
    from app.parsers.llm_fallback import extract_with_gemini_fallback
    def generate(**kwargs):
        assert 'Secret' not in kwargs['contents']
        assert kwargs['config'].response_schema is not None
        return SimpleNamespace(text=response)
    monkeypatch.setattr(settings,'gemini_api_key','test-only')
    monkeypatch.setattr(genai,'Client',lambda **kw: SimpleNamespace(models=SimpleNamespace(generate_content=generate)))
    result=extract_with_gemini_fallback('Patient Name: Secret Person\nVitamin D 12 ng/mL')
    assert len(result)==expected


def test_ocr_timeout(monkeypatch):
    import subprocess, time
    monkeypatch.setattr(pdf.shutil,'which',lambda _: '/fake/tesseract')
    def timeout(*args,**kwargs): raise subprocess.TimeoutExpired('tesseract',1)
    monkeypatch.setattr(pdf.subprocess,'run',timeout)
    with pytest.raises(pdf.ReportError,match='timed out'):
        pdf.ocr_image(Image.new('RGB',(500,500)),time.monotonic()+30)


def test_real_ocr_when_installed():
    import shutil,time
    from PIL import ImageDraw,ImageFont
    if not shutil.which('tesseract'): pytest.skip('Tesseract not installed')
    from pathlib import Path
    fonts=['/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    font_path=next((p for p in fonts if Path(p).exists()),None)
    if not font_path: pytest.skip('Integration test needs a TrueType font')
    image=Image.new('RGB',(1800,500),'white')
    font=ImageFont.truetype(font_path,48)
    ImageDraw.Draw(image).text((50,100),'Vitamin D 12.5 ng/mL',fill='black',font=font)
    assert parse(pdf.ocr_image(image,time.monotonic()+60))[0].detected_value==12.5


@pytest.mark.parametrize('kind',['png','jpg','pdf','rotated'])
def test_real_ocr_uploads(kind):
    import shutil
    from PIL import ImageDraw,ImageFont
    from reportlab.lib.utils import ImageReader
    if not shutil.which('tesseract'): pytest.skip('Tesseract not installed')
    fonts=['/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    from pathlib import Path
    font_path=next((p for p in fonts if Path(p).exists()),None)
    if not font_path: pytest.skip('Integration test needs a TrueType font')
    image=Image.new('RGB',(1800,600),'white')
    ImageDraw.Draw(image).text((80,150),'Vitamin D 12.5 ng/mL',fill='black',font=ImageFont.truetype(font_path,48))
    stream=io.BytesIO()
    if kind=='pdf':
        c=canvas.Canvas(stream,pagesize=(600,200)); c.drawImage(ImageReader(image),0,0,width=600,height=200); c.showPage(); c.save()
        filename,mime='scan.pdf','application/pdf'
    else:
        if kind=='rotated': image=image.rotate(90,expand=True)
        image.save(stream,'JPEG' if kind=='jpg' else 'PNG')
        filename,mime=('photo.jpg','image/jpeg') if kind=='jpg' else ('photo.png','image/png')
    markers=parse(pdf.extract_upload(stream.getvalue(),filename,mime))
    assert markers[0].detected_value==12.5 and markers[0].extraction_method=='ocr_regex'


def test_pixel_limit(monkeypatch):
    stream=io.BytesIO(); Image.new('RGB',(100,100)).save(stream,'PNG')
    monkeypatch.setattr(settings,'max_image_pixels',100)
    with pytest.raises(pdf.ReportError,match='pixel'):
        pdf.extract_upload(stream.getvalue(),'x.png','image/png')


def test_misleading_extension():
    stream=io.BytesIO(); Image.new('RGB',(100,100)).save(stream,'PNG')
    with pytest.raises(pdf.ReportError,match='extension'):
        pdf.extract_upload(stream.getvalue(),'x.jpg','image/jpeg')


def test_corrupt_pdf_signature():
    with pytest.raises(pdf.ReportError,match='corrupted'):
        pdf.extract_upload(b'%PDF-1.7\nbroken','x.pdf','application/pdf')


def test_worker_deadline(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    monkeypatch.setattr(settings,'processing_timeout_seconds',.001)
    app=FastAPI(); app.include_router(extract.router)
    with TestClient(app) as client:
        response=client.post('/extract-report',data={'raw_text':'Hb 12 g/dL'})
        assert response.status_code==504
