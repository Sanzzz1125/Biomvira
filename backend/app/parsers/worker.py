"""One disposable report worker; stdout is a machine-only response channel."""
import base64
import json
import sys
from app.api.v1.extract import process_report
from app.parsers.pdf_extractor import ReportError, extract_upload
from app.parsers.sanitizer import sanitize_report_text


def diet_text(data, filename, mime):
    """Text of a diet chart (Tesseract for photos and scans), with names and phone numbers removed."""
    import re
    text, _ = sanitize_report_text(extract_upload(data, filename, mime))
    text = re.sub(r"\[\[PAGE \d+[^\]]*\]\]", " ", text)
    return " ".join(text.split())[:4000]


def main():
    request = json.load(sys.stdin)
    try:
        data = base64.b64decode(request['data']) if request['data'] is not None else None
        if request.get('mode') == 'diet':  # a photo or PDF of what the person usually eats: just its text
            print(json.dumps({'result': {'text': diet_text(data, request['filename'], request['mime'])}}))
            return
        result = process_report(data, request['filename'], request['mime'], request['text'])
        print(json.dumps({'result': result.model_dump()}))
    except ReportError as exc:
        print(json.dumps({'error': str(exc)}))
    except Exception:
        print(json.dumps({'error': 'Report processing failed. Try a clearer report or paste text.'}))


if __name__ == '__main__':
    main()
