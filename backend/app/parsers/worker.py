"""One disposable report worker; stdout is a machine-only response channel."""
import base64
import json
import sys
from app.api.v1.extract import process_report
from app.parsers.pdf_extractor import ReportError


def main():
    request = json.load(sys.stdin)
    try:
        data = base64.b64decode(request['data']) if request['data'] is not None else None
        result = process_report(data, request['filename'], request['mime'], request['text'])
        print(json.dumps({'result': result.model_dump()}))
    except ReportError as exc:
        print(json.dumps({'error': str(exc)}))
    except Exception:
        print(json.dumps({'error': 'Report processing failed. Try a clearer report or paste text.'}))


if __name__ == '__main__':
    main()
