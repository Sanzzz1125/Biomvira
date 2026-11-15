# Age input and shared history security fixes

> **Update (Nov 2026):** the temporary measures below have been superseded. NutriLens now has real accounts with
> server-enforced report ownership, roles (guest, user, admin, single owner) and an audit log, so saved history is
> re-enabled privately per user. See *Accounts, roles & saved history* in the [README](README.md). This document is
> kept as the record of the original containment fix.

## Age input

Root cause: `UserProfileForm.tsx` ran `parseInt(e.target.value) || 25` on every keystroke. Clearing the final digit produced `NaN`, immediately restoring 25. The application initial profile separately used 26, despite the intended default being 25.

The form now retains a local string draft (including an empty string), validates a whole number from 1 through 120 on submission, displays an accessible error, and only then updates the numeric profile. The validated profile is passed directly into the analysis callback, avoiding a stale value from React's asynchronous state update. The initial application default is now 25, matching the existing backend default. Styling and the main flow remain intact.

Files:

- `frontend/src/components/UserProfileForm.tsx`: editable string, age validation and explicit validated-profile submission.
- `frontend/src/App.tsx`: default 25 and submit the supplied validated profile to the API.
- `frontend/tests/profile-history.test.mjs`: DOM interaction tests for default, deletion, empty-state retention across another profile edit, numeric submission (1, 18, 21, 30, 65, 120), invalid values, corrections and the React flow to the results screen. Network responses in the React flow test are mocked; the real backend flow is tested separately.

## History access

No authentication, account model, authenticated session or report ownership field exists. The report model has a UUID, demographics and clinical data, but no owner. `/api/v1/history` previously queried the newest 20 records globally and returned them to every caller. Browser identity, localStorage, caller-supplied IDs and fabricated authorization headers cannot establish ownership.

The minimal safe solution is to disable saved history until verified authentication and ownership are implemented:

- `GET /api/v1/history` always returns **403**, without querying medical records. Its response has `Cache-Control: no-store`.
- The existing History tab displays an explanatory card. It makes no history request and never shows shared rows.
- New analysis requests still return results and recommendations, but no longer persist unowned medical records.
- Existing records and the database schema are untouched. No legacy rows are deleted, migrated or assigned to users.
- There were no individual saved-report retrieval, deletion or saved-report PDF routes. These remain unavailable (`404`/`405`); unknown API GETs now return `404` instead of the SPA's successful HTML response.
- The existing PDF endpoint is a stateless renderer, not a stored-report download. It remains available for the current workflow, requires the full analysis response body, never queries the database, and rejects ID-only requests (`422`). Caller-supplied IDs are filename labels only. PDF responses are marked `no-store`; errors no longer include internal exception details.
- The frontend fallback file handler now resolves requested paths and requires containment inside `frontend/dist`. This closes a related encoded path traversal route that could otherwise expose private files, including the database. The assets mount already uses Starlette's containment checks.

Files:

- `backend/app/api/v1/history.py`: deny listing, validate full export payload, preserve current-result PDF export without database access, safe errors/filename and no-store headers.
- `backend/app/api/v1/recommend.py`: stop writing shared unowned records, remove save-error logging.
- `backend/app/main.py`: constrain frontend files to the public build directory and return actual API 404s.
- `frontend/src/components/HistoryDashboard.tsx`: preserve page/card styling and explain the disabled history feature.
- `frontend/src/services/api.ts`: retain a useful server error if history is requested by another caller.
- `backend/tests/test_api.py`: replace the obsolete shared-history expectation with a denial assertion; retain recommendation checks.
- `backend/tests/test_history_security.py`: independent clients, fake identities, legacy preservation, direct access/deletion/download denial, traversal, age API validation and real upload → extraction → reviewed values → analysis → recommendations → PDF regression.
- `frontend/tests/profile-history.test.mjs`: history UI does not request shared records.
- `frontend/package.json`, `frontend/package-lock.json`: add `npm test` and the development-only `jsdom` DOM environment. No runtime dependency was added. Tests use Node's built-in runner and existing Vite/React tooling.
- `frontend/dist/index.html`, `frontend/dist/assets/*`, `frontend/tsconfig.tsbuildinfo`: regenerated production output; Vite removes obsolete bundled assets. Source styling was not redesigned.
- `README.md`, `EXTRACTION_CHANGES.md`, `SECURITY_FIXES.md`: current behavior, limits, run/test instructions and historical-document clarification.

## Actual validation

Executed from the repository root:

```
DEBUG=false DATABASE_URL=sqlite:////private/tmp/nutrilens-security-tests.db /private/tmp/nutrilens-venv/bin/python -m pytest -q
```

Result: **95 passed, 2 warnings in 4.29s**. No failures or skips. The warnings are existing FastAPI `on_event` startup deprecations. Tests use temporary/in-memory databases, not the real medical database.

Executed from `frontend`:

```
npm test
npm run build
```

Frontend tests: **15 passed**, no failed, cancelled or skipped tests. Tests cover React DOM interaction using jsdom, not a real browser. The integration test verifies the application starts at 25, passes edited age 65 to the analysis request, and renders results. Shared-history UI is checked without any history fetch.

Build: TypeScript and Vite **passed**, 1,606 modules transformed. The dependency installation reported **0 vulnerabilities**. A first frontend test run passed but Vite attempted an unnecessary HMR socket; the test harness now disables WebSockets/HMR and reruns cleanly. A misplaced npm invocation from the repository root failed before tests ran; the actual frontend tests/build were run in `frontend` as shown above.

Authorization tests use two independent anonymous clients; they do **not** demonstrate authenticated per-user isolation. They demonstrate that private saved data is unavailable to every unauthenticated caller, including callers pretending to be users A or B. Legacy rows are seeded only in isolated test databases, and assertions verify they remain unchanged after analysis and attempted access/deletion.

Unexecuted: real-device browser testing, production deployment verification and login/ownership tests (there is no login system). No real Gemini requests were made.

## Start the demo

The already-installed test/demo environment on this machine:

```
cd /Users/akki/Downloads/NutriLens
DEBUG=false /private/tmp/nutrilens-venv/bin/python run.py
```

Open `http://127.0.0.1:8000` for the rebuilt production frontend. Restart any backend already running an older version and reload open browser tabs. The backend change is essential; replacing the frontend alone does not fix the vulnerability.

For a persistent local virtual environment instead:

```
cd /Users/akki/Downloads/NutriLens
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build
DEBUG=false python run.py
```

OCR requires Tesseract, already installed on this machine. Frontend development (optional separate terminal): `cd /Users/akki/Downloads/NutriLens/frontend && npm run dev`.

## Manual verification

1. Upload `sample_reports/report_01_lal_pathlabs_low_vit_d_and_iron.pdf`. Review biomarkers and check the confirmation box; continue to the profile.
2. Confirm age is 25. Backspace twice and pause: it should stay empty. Click Generate my plan: expect “Please enter your age.”
3. Try 0, -1, 121 and 18.5: expect the whole-number/range error and no submission. Try 18, 21, 30 or 65: recommendations should render. Check the analysis network request contains the age you entered.
4. Download the current plan. It should still produce a PDF.
5. In two separate browser profiles or devices, analyze different synthetic reports. Each History tab should display the privacy explanation, with no saved records shown. New analyses are intentionally not saved.
6. Call `curl -i http://127.0.0.1:8000/api/v1/history`: expect 403. Add `?user_id=someone` or `-H 'Authorization: Bearer invented'`: still 403.
7. Try `curl -i http://127.0.0.1:8000/api/v1/history/any-id` and `curl -i -X DELETE http://127.0.0.1:8000/api/v1/history/any-id`: expect 404/405 and no records changed.
8. Try `curl -i -H 'Content-Type: application/json' -d '{"analysis_id":"any-id"}' http://127.0.0.1:8000/api/v1/export-plan-pdf`: expect 422, never a saved report.
9. Try `curl --path-as-is -i 'http://127.0.0.1:8000/..%2f..%2fbackend%2fnutrilens.db'`: expect 404.

## Remaining limitations

This is a privacy containment fix, not an authentication implementation. Saved history must stay disabled until a real authenticated identity, server-enforced ownership and an explicit legacy-data migration policy are implemented and tested. Server administrators still have filesystem access to the retained database; it must not be placed in a public directory or separately exposed by hosting configuration. Data already viewed or downloaded before this fix cannot be revoked by a code change. Current results live in the browser's in-memory state until reset/reload; clients remain responsible for protecting downloaded PDFs. Original OCR/extraction limitations remain as documented in `EXTRACTION_CHANGES.md`.
