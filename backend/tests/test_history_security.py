"""Guest workflow, PDF export, input validation and private-file protection."""
import io

import pdfplumber
import pytest


def analysis_request(age=25):
    return {
        'user_profile': {'age': age, 'gender': 'female', 'diet_type': 'veg', 'allergens': []},
        'biomarkers': [{'biomarker_key': 'vitamin_d', 'value': 12.5, 'unit': 'ng/mL'}],
    }


@pytest.mark.parametrize('path', [
    '/..%2f..%2fbackend%2fnutrilens.db',
    '/%2e%2e/%2e%2e/backend/nutrilens.db',
    '/..%2f..%2fbackend%2fapp%2fconfig.py',
    '/assets/..%2f..%2f..%2fbackend%2fnutrilens.db',
    '/..%2f..%2fbackend%2f.env',
])
def test_frontend_cannot_serve_private_files(api, path):
    response = api().get(path)
    assert response.status_code == 404
    assert 'SQLite format' not in response.text
    assert 'DATABASE_URL' not in response.text


def test_history_detail_routes_need_sign_in(api):
    client = api()
    for path in ('/api/v1/history', '/api/v1/history/some-id'):
        assert client.get(path).status_code == 401
    assert client.delete('/api/v1/history/some-id').status_code == 401


def test_pdf_export_never_reads_stored_reports_by_id(api):
    client = api()
    assert client.post('/api/v1/export-plan-pdf', json={'analysis_id': 'someone-else'}).status_code == 422
    assert client.get('/api/v1/export-plan-pdf?analysis_id=someone-else').status_code in (404, 405)


def test_guest_analysis_and_current_pdf_work(api):
    client = api()
    for age in (21, 65):
        response = client.post('/api/v1/analyze-and-recommend', json=analysis_request(age))
        assert response.status_code == 200
        result = response.json()
        assert result['user_profile']['age'] == age
        assert result['recommendations']
        exported = client.post('/api/v1/export-plan-pdf', json=result)
        assert exported.status_code == 200
        assert exported.headers['cache-control'] == 'no-store'
        assert exported.content.startswith(b'%PDF-')
        with pdfplumber.open(io.BytesIO(exported.content)) as pdf:
            assert pdf.pages


@pytest.mark.parametrize('invalid_age', ['', 0, -1, 121, 18.5, None, 'invalid'])
def test_api_rejects_invalid_ages(api, invalid_age):
    response = api().post('/api/v1/analyze-and-recommend', json=analysis_request(invalid_age))
    assert response.status_code == 422


def test_upload_to_results_and_export_regression(api):
    from reportlab.pdfgen import canvas
    stream = io.BytesIO()
    pdf = canvas.Canvas(stream)
    pdf.drawString(40, 750, 'Vitamin D 12.5 ng/mL 30-100')
    pdf.save()
    client = api()
    response = client.post('/api/v1/extract-report', files={'file': ('synthetic.pdf', stream.getvalue(), 'application/pdf')})
    assert response.status_code == 200, response.text
    extracted = response.json()['extracted_biomarkers'][0]
    request = analysis_request(30)
    # This simulates the original verification step submitting reviewed values.
    request['biomarkers'] = [{
        'biomarker_key': extracted['biomarker_key'], 'value': extracted['detected_value'],
        'unit': extracted['detected_unit'], 'reference_low': extracted['report_reference_range']['low'],
        'reference_high': extracted['report_reference_range']['high'],
    }]
    response = client.post('/api/v1/analyze-and-recommend', json=request)
    assert response.status_code == 200
    result = response.json()
    assert result['marker_analyses'][0]['status'] == 'low'
    assert result['recommendations'][0]['recommended_foods']
    assert client.post('/api/v1/export-plan-pdf', json=result).content.startswith(b'%PDF-')


def test_api_responses_carry_security_headers(api):
    response = api().get('/api/health')
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['x-frame-options'] == 'DENY'
