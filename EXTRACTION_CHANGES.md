# Report extraction implementation and validation

This records the earlier extraction work. The later [age and history security fix](SECURITY_FIXES.md) supersedes shared-history persistence and access behavior described here.

## Root causes

Uploads previously checked only the PDF filename and decoded every other file as UTF-8. PDF extraction had no quality assessment or OCR. Text and tables were appended together, losing page identity and duplicating table rows.

Regex selected the first number following an alias, supplied canonical units when missing, assigned 95% confidence without calibration, and ignored all later occurrences of a biomarker. Unit conversion accepted partial unit matches and silently relabelled unsupported units. Gemini was triggered only below two results, trusted returned measurements without source grounding, and logged exception details. Verification submitted cached canonical values despite edits, and sent original reference ranges alongside converted values.

## Files changed

- `backend/app/config.py`: configurable upload, page, pixel, text, OCR, concurrency and processing limits; Gemini timeout.
- `backend/app/api/v1/extract.py`: bounded upload reading, validation, isolated worker, deadlines, evidence-based completeness, warnings, safe AI merge and preview.
- `backend/app/parsers/worker.py` (new): disposable report subprocess; generic failure response; killed with its OCR process group at the request deadline.
- `backend/app/parsers/pdf_extractor.py`: content/MIME/extension checks, native tables without overlapping plain text, page markers, local OCR, orientation/preprocessing, cleanup, explicit errors.
- `backend/app/parsers/regex_matcher.py`: aliases, column headers, multiline rows, decimal commas, qualifiers, units, flags, reference ranges, duplicate/conflict handling and traceability.
- `backend/app/parsers/llm_fallback.py`: structured Gemini response schema, finite numeric/unit validation, allowlisted evidence, source-grounded acceptance, no exception-content logging or invented confidence.
- `backend/app/parsers/sanitizer.py`: fail-closed clinical-token projection for external AI and preview; existing sanitizer preserved.
- `backend/app/engine/unit_converter.py`: exact normalized unit matching; reject unknown units, negative/nonfinite values and unknown markers.
- `backend/app/models/schemas.py`: optional uncalibrated confidence, nullable canonical values, status, qualifier, source, flags and warnings.
- `backend/app/api/v1/recommend.py`: understandable invalid-unit and duplicate-marker errors before analysis.
- `backend/requirements.txt`: direct Pillow and httpx requirements.
- `backend/tests/test_report_pipeline.py` (new): synthetic format, extraction, security, API, mocked Gemini and real OCR tests.
- `frontend/src/components/UploadZone.tsx`: PDF/image selection, size/extension feedback; existing retry and processing UI preserved.
- `frontend/src/components/VerificationTable.tsx`: warnings, page/method/status, qualifiers, confirmation gate, duplicate guard and editing.
- `frontend/src/types/index.ts`: additive extraction metadata and nullable confidence/canonical value.
- `frontend/src/App.tsx`: warnings passed to verification; submit edited original values/units/ranges together.
- `frontend/src/services/api.ts`: extraction request timeout.
- `frontend/package-lock.json` (new): installed frontend dependency lock.
- `frontend/dist/index.html`, `frontend/dist/assets/index-CWWIdjfs.js`, `frontend/tsconfig.tsbuildinfo`: regenerated production output; CSS content unchanged. Earlier bundled JS remains on disk.
- `README.md`, this document: installation, formats, limits, verification and limitations.

## Dependencies and execution

Python dependencies were installed in `/private/tmp/nutrilens-venv`. Pillow is used directly for decoding, EXIF orientation and preprocessing; httpx supports API testing (also used by Gemini). PDF rendering uses pdfplumber's existing PDFium dependency. OCR invokes the free local Tesseract executable without a shell; no paid OCR service or raw image transmission.

Install Tesseract with `brew install tesseract` on macOS, or `apt-get install tesseract-ocr` on Debian/Ubuntu. English trained data must be installed. This environment's approved Homebrew install installed Tesseract 5.5.4 and upgraded/installed its system dependencies.

## Actual validation

Final command:

```
DEBUG=false DATABASE_URL=sqlite:////private/tmp/nutrilens-tests.db /private/tmp/nutrilens-venv/bin/python -m pytest -q
```

**70 passed in 2.91s**, no failures or skips. Includes all existing tests, real OCR on synthetic printed PNG/JPG/rotated images/scanned PDF, mocked Gemini grounding/hallucination rejection, subprocess-backed HTTP extraction, and invalid input tests. Normal tests make no real Gemini calls. Initial runs exposed password exception wrapping; fixed and retested. An initial collection run failed because this environment exports `DEBUG=release`; validation explicitly sets `DEBUG=false`.

`cd frontend && npm run build`: **passed**, TypeScript and Vite; 1,606 modules transformed. `npm install`: 0 reported vulnerabilities.

Manual parser evaluation of six bundled PDFs: 4, 4, 4, 6, 4, 6 biomarkers respectively; all displayed values/units match the representative reports on inspection of extracted results. This is synthetic evaluation, not a clinical accuracy study.

Unexecuted: real Gemini service integration, browser interaction automation, load/soak testing, representative mobile-camera/poor-light evaluation, production deployment.

## Supported inputs and limitations

PDF (native, scanned or mixed pages), JPG/JPEG, PNG and pasted printed report text. No handwritten-report support is claimed. OCR is English; severe blur, perspective distortion, shadows, non-Latin text and OCR substitutions remain unreliable. Rotation trials do not guarantee correct orientation in every image.

Default limits: 10 MiB upload, 20 PDF pages, 20 million pixels per image/rendered page, 200,000 text characters, two simultaneous processing jobs per server process, 90-second worker deadline, 15-second OCR invocation deadline. Set corresponding uppercase settings through environment variables. Deploy behind an HTTP body-size limit and OS/container memory limits as well: multipart parsing happens before endpoint execution, and PDF page enumeration may allocate memory before its page-count check. Worker isolation and size limits are not a substitute for container resource limits. Process-group termination targets the current macOS/Linux deployment; Windows requires a different worker cancellation strategy.

Gemini fallback is deliberately conservative: only clinically reconstructed, locally validated token rows are transmitted. Arbitrary free text, unknown identifiers and raw images are never sent. AI values must match locally grounded measurements. Consequently it does **not** independently recover values that cannot first be safely parsed locally. Missing/ambiguous rows are surfaced for manual entry. This limits the requested AI recovery criterion; do not characterize it as general missing-value recovery.

Header mapping supports pipe, tab and aligned whitespace tables, with an explicit result column and common extra columns. Complex merged cells, date-only historical headers, reordered unaligned OCR columns and long wrapped names may require manual correction. Comma decimals are supported; ambiguous thousands separators are not automatically resolved. Reference ranges currently support two-ended numeric intervals, not demographic range matrices or all one-sided interval formats. Identical duplicates retain one source occurrence; conflicting rows remain visible. Qualifiers are preserved but downstream recommendation rules require exact results: remove the bound or enter a separately verified exact measurement.

Confidence is null because no calibrated score exists. Every extraction begins `needs_review`; conflicts are labelled separately. The confirmation checkbox records local workflow intent, not a clinical verification audit. Backend analysis continues accepting the existing exact-value API for compatibility.

## Manual verification

1. Install Python dependencies and Tesseract. Start `DEBUG=false uvicorn app.main:app --reload --port 8000` from `backend`.
2. Run `npm run dev` from `frontend`, or use the rebuilt production frontend through FastAPI.
3. Upload each bundled PDF; check values, units and printed ranges. Try the all-six and SI-unit reports.
4. Upload a clear printed report as PNG/JPG and as a scanned multi-page PDF. Confirm OCR labels and page numbers. Try a rotated image.
5. Paste `Vitamin D <12 ng/mL`, `Hb 12 g/dL\nHb 9 g/dL`, and `Calcium 9.2` separately. Check bounds/conflicts/unit warnings and blocked continuation until corrected or removed.
6. Correct an SI-unit value and unit, add a missing marker, remove a row, confirm review, and continue to recommendations. Values and ranges now use the edited unit consistently.
7. Retry a failed upload. Upload an empty/corrupted file, renamed image, mismatched MIME, locked PDF or file over the limit and check understandable errors.

## Acceptance status

- Satisfied in automated representative tests: native/scanned PDF and image extraction, pasted text, six existing biomarkers, page traces, patient/reference separation in tested layouts, explicit missing/uncertain results, strict unit conversion, duplicate/conflict visibility, invalid-file errors and existing backend functionality.
- Implemented and build-validated, browser checks pending: upload feedback, correction/removal/addition, warning review and explicit confirmation in the preserved UI.
- Partially satisfied: completeness and Gemini triggering are evidence-based, but fail-closed privacy/source validation limits independent AI recovery; complex tables and historical result selection still require human review.
- Pending deployment validation: real Gemini, broad camera-report accuracy, concurrency/load evaluation, reverse-proxy/container limits and browser end-to-end interaction.
