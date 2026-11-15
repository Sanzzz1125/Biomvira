import asyncio
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import base64
import json
import os
import sys
import signal
from pathlib import Path
from app.config import settings
from app.models.schemas import ExtractionResponse
from app.parsers.sanitizer import sanitize_report_text, clinical_evidence_only
from app.parsers.pdf_extractor import extract_upload, ReportError
from app.parsers.regex_matcher import extract_biomarkers_with_regex, mentioned_keys
from app.parsers.llm_fallback import extract_with_gemini_fallback

router = APIRouter()
_slots = asyncio.Semaphore(settings.max_parallel_reports)


def process_report(data, filename, mime, raw_text):
    text = extract_upload(data, filename, mime) if data is not None else raw_text
    if not text or not text.strip():
        raise ReportError('Report is empty. Upload a readable report or paste text.')
    if len(text) > settings.max_text_chars:
        raise ReportError('Report exceeds the configured text limit.')
    sanitized, _ = sanitize_report_text(text)
    markers = extract_biomarkers_with_regex(sanitized)
    missing = mentioned_keys(sanitized) - {m.biomarker_key for m in markers}
    warnings = [f'{key}: mentioned but no reliable result extracted; add manually.' for key in sorted(missing)]
    if not markers or missing or any(m.warnings for m in markers):
        evidence = clinical_evidence_only(sanitized)
        if not evidence:
            warnings.append('AI fallback withheld: no verifiably de-identified clinical evidence. Review manually.')
        else:
            try:
                candidates = extract_with_gemini_fallback(sanitized)
                # Keep disagreements rather than silently overriding local evidence.
                for candidate in candidates:
                    if not any(m.biomarker_key == candidate.biomarker_key and m.canonical_value == candidate.canonical_value for m in markers):
                        candidate.verification_status = 'conflict'
                        candidate.warnings.append('AI/local disagreement requires manual verification.')
                        markers.append(candidate)
                if not candidates:
                    warnings.append('AI fallback did not recover validated values; review missing or uncertain results manually.')
            except ValueError:
                warnings.append('Gemini unavailable or invalid response; local results retained for review.')
    if not markers:
        warnings.append('No supported biomarkers extracted. Retry with a clearer report or add results manually.')
    # Do not expose arbitrary report headers as an allegedly anonymous preview.
    return ExtractionResponse(session_id=str(uuid.uuid4()), sanitized_preview=clinical_evidence_only(sanitized)[:400],
                              extracted_biomarkers=markers, warnings=warnings,
                              unmatched_text_lines=sorted(missing))


@router.post('/extract-report', response_model=ExtractionResponse)
async def extract_report(file: Optional[UploadFile] = File(None), raw_text: Optional[str] = Form(None)):
    if file is not None and raw_text:
        raise HTTPException(400, 'Provide a file or text, not both.')
    data = None
    if file is not None:
        try:
            data = await file.read(settings.max_upload_bytes + 1)
        finally:
            await file.close()
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(413, 'File exceeds the configured upload size limit.')
    elif not raw_text:
        raise HTTPException(400, 'Upload PDF, JPG, JPEG, PNG or paste report text.')
    if raw_text and len(raw_text) > settings.max_text_chars:
        raise HTTPException(413, 'Report exceeds text limit.')
    if _slots.locked():
        raise HTTPException(503, 'Report processor is busy. Please retry shortly.')
    async with _slots:
        try:
            payload = json.dumps(dict(data=base64.b64encode(data).decode() if data is not None else None,
                                      filename=file.filename if file else '', mime=file.content_type if file else '', text=raw_text)).encode()
            env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[3]))
            worker = await asyncio.create_subprocess_exec(sys.executable, '-m', 'app.parsers.worker',
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                env=env, start_new_session=True)
            try:
                stdout, _ = await asyncio.wait_for(worker.communicate(payload), timeout=settings.processing_timeout_seconds)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                os.killpg(worker.pid, signal.SIGKILL)
                await worker.wait()
                raise HTTPException(504, 'Report processing timed out. Try fewer pages or paste text.') from None
            response = json.loads(stdout)
            if 'error' in response:
                raise ReportError(response['error'])
            return ExtractionResponse(**response['result'])
        except HTTPException:
            raise
        except ReportError as exc:
            raise HTTPException(422, str(exc)) from None
        except Exception:
            raise HTTPException(422, 'Report processing failed. Try a clearer report or paste text.') from None
