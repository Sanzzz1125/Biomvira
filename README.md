# NutriLens — From Laboratory Insights to Personalized Nutrition

**Evidence-Based Nutrition Support Platform**  
AI & Clinical Biomarker Intelligence System  

---

## 🌿 Overview
**NutriLens** is an evidence-grounded nutrition-support platform that transforms laboratory blood biomarkers into practical, culturally relevant Indian food recommendations. It strictly adheres to individual dietary preferences and allergies without making clinical diagnoses.

### The 4 Core Pillars
1. **Report Intelligence:** Dual-layer extraction (`pdfplumber` layout-aware extraction + Gemini Flash structured JSON fallback) paired with local **PII de-identification** and a **Human-in-the-Loop Confirmation Screen**.
2. **Biomarker Intelligence:** Strict unit normalization (e.g., `ng/mL` vs `nmol/L`, `pg/mL` vs `pmol/L`) and deterministic classification prioritizing the laboratory's printed reference range.
3. **Nutrition Intelligence:** 65+ hand-curated Indian food items cross-referenced with ICMR-NIN nutritional composition and absorption synergy/inhibitor rules (e.g., Vitamin C + Iron absorption, Calcium/Tannin inhibition).
4. **Personalization & Safety Guardrails:** Hard constraint satisfaction for dietary types (`Vegetarian`, `Vegan`, `Eggetarian`, `Non-Vegetarian`) and allergens (`Dairy`, `Gluten`, `Nuts`, `Soy`, `Eggs`, `Seafood`). Severely low readings trigger clinical consult advisories.

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│     Client UI (React 19 + Vite + Tailwind CSS)         │
│  • Drag & Drop PDF Ingestion                           │
│  • Human-in-the-Loop Verification Table                │
│  • InsideTracker-style Visual Range Gauges             │
│  • ZOE-style Food Cards & Synergy Tips                 │
└───────────────────────────┬────────────────────────────┘
                            │ REST API / Multipart
                            ▼
┌────────────────────────────────────────────────────────┐
│               FastAPI Backend Pipeline                 │
│                                                        │
│  1. Ingestion & Privacy Layer                          │
│     • pdfplumber layout & table parser                 │
│     • Local PII Sanitizer (Regex scrubbing)            │
│     • Regex Matcher with alias resolution              │
│     • Gemini 2.5 Flash JSON fallback                   │
│                                                        │
│  2. Biomarker Intelligence Engine                      │
│     • Unit Normalization (Canonical conversions)       │
│     • Range Resolution (Report Range > Demographics)   │
│     • Status Classifier (Low | Borderline | Normal)    │
│                                                        │
│  3. Nutrition Recommendation Engine                    │
│     • Hard Filter: Diet Category (Veg/Vegan/Non-Veg)   │
│     • Hard Filter: Allergen Exclusion (Zero-tolerance) │
│     • Ranking: ICMR-NIN Nutrient Density per serving   │
│     • Synergy Injector (Absorption Dos & Don'ts)       │
│                                                        │
│  4. Delivery & Export Layer                            │
│     • Deterministic Grounded Narrative Generator       │
│     • ReportLab Downloadable Branded A4 PDF            │
│     • Private per-user history (Neon PostgreSQL)       │
│     • Accounts, roles & audit log (owner/admin/user)   │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.11+
- Node.js 20.19+, 22.13+ or 24+ (includes DOM test support)

### 1. Backend Setup
```bash
# from the project root
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # then paste your Neon DATABASE_URL into backend/.env
```
Without a `DATABASE_URL`, the backend uses a local SQLite file (`backend/nutrilens.db`) for offline development.
Database tables are created and upgraded automatically (Alembic migrations) when the server starts.

Create the single **owner** account (once per database):
```bash
cd backend
python -m app.cli create-owner --email you@example.com --name "Your Name"
```

Run the app (API + built frontend on one port):
```bash
python run.py
```
- Interactive UI: [http://localhost:8000/](http://localhost:8000/) *(serves the production build in `frontend/dist`)*
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Development Setup
```bash
cd frontend
npm install
npm run dev
```
- Frontend Dev Server: [http://localhost:5173/](http://localhost:5173/) *(proxies `/api` to port 8000)*

### 3. Build Frontend for Production
```bash
cd frontend
npm run build
```
The compiled SPA is output to `frontend/dist/` and automatically served by FastAPI at `http://localhost:8000/`.

---

## 🧪 Running Tests

```bash
.venv/bin/python -m pytest -q          # backend: extraction, rules, auth, roles, ownership, admin
cd frontend && npm test                # frontend: profile form, login, role-based navigation, full flow
```
Backend tests always use a throwaway in-memory database, never the real one.

---

## 📡 API Endpoints

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/v1/extract-report` | Anyone | Upload PDF/image or paste text; scrubs PII and extracts biomarkers. |
| `POST` | `/api/v1/analyze-and-recommend` | Anyone | Returns the personalised plan. **Saved to history only when signed in.** |
| `POST` | `/api/v1/export-plan-pdf` | Anyone | Renders the supplied analysis as a PDF; never reads stored reports. |
| `POST` | `/api/v1/auth/register` · `/login` · `/logout` | Anyone | Account sign-up and sessions (HttpOnly cookie). |
| `GET` | `/api/v1/auth/session` · `/auth/me` | Anyone / signed in | Who is signed in. |
| `PATCH`/`POST` | `/api/v1/auth/me` · `/change-password` · `/delete-account` | Signed in | Self-service account management. |
| `GET`/`POST` | `/api/v1/auth/invites/{token}` · `/auth/reset/{token}` | Link holder | One-time invitation and password-reset links. |
| `GET`/`DELETE` | `/api/v1/history` · `/history/{id}` | Signed in | Your own saved reports only (others' return 404). |
| `GET`/`PATCH`/`POST`/`DELETE` | `/api/v1/admin/users…` · `/admin/invites…` · `/admin/stats` · `/admin/audit-logs` | Admin, owner | User management, invitations, dashboard, audit log. |
| `POST`/`DELETE` | `/api/v1/admin/access…` · `/admin/transfer-ownership` | Owner | Grant/remove admin access, hand over ownership. |
| `GET` | `/api/health` | Anyone | Health check (never touches the database). |
| `GET` | `/docs` | Anyone | Interactive Swagger UI. |

---

## 📄 License & Safety
NutriLens is an educational nutrition-support tool and does not provide clinical diagnoses or prescription drug advice.


## Report formats and OCR

The existing upload flow accepts printed PDF, JPG/JPEG and PNG reports, plus pasted text. Native PDF extraction remains local with pdfplumber; insufficient pages use local Tesseract OCR. Install `tesseract` (macOS: `brew install tesseract`; Debian/Ubuntu: `apt-get install tesseract-ocr`) with English data, then install `backend/requirements.txt`.

Default limits are 10 MiB, 20 PDF pages, 20 million image pixels and 90 seconds per report. All are configurable in `backend/app/config.py` through uppercase environment settings. Deploy with proxy body-size and container memory limits. Handwriting and universal mobile-camera compatibility are not supported claims.

Review every extracted value and unit, resolve duplicates, and confirm the verification checkbox before continuing. Missing units, qualified bounds and conflicts are surfaced rather than silently corrected. Gemini receives only allowlisted clinical tokens, never raw images; this intentionally limits recovery of ambiguous rows.

See [implementation details, actual test results and manual verification](EXTRACTION_CHANGES.md) for the complete change inventory, limitations and acceptance checklist.


## Age input

Age starts at 25, can be cleared during editing, and must be a whole number from 1–120 before submission.
Frontend regression tests: `cd frontend && npm test`.

## Accounts, roles & saved history

| Role | Who | Can do |
|---|---|---|
| **Guest** | Not signed in | Analyze a report, download the PDF. Nothing is saved. |
| **User** | Anyone who signs up | Everything a guest can, plus a private history of their analyses, account settings, delete account. |
| **Admin** | Invited or promoted by the owner | Everything a user can, plus the admin portal: dashboard, manage *users* (edit, disable, unlock, sign out, reset link, delete), invite users, audit log. Cannot change other admins or the owner. |
| **Owner** | Exactly one, created with `python -m app.cli create-owner` | Everything an admin can, plus add admins by email (promote or one-time invite link), edit/disable/remove admins, issue their reset links, and transfer ownership. |

- **Only one owner** is enforced by the database itself (a partial unique index), not just the code.
- **Nobody, including admins and the owner, can read another person's medical reports.** Admin views show account metadata and counts only.
- Passwords are hashed with Argon2id. Sessions are random tokens in an HttpOnly, SameSite cookie (7 days), revoked on logout, password change, disable or reset. Changes require a CSRF header. 5 failed logins lock an account for 15 minutes.
- Invitation and password-reset links are single-use, expire after 48 hours and are stored only as hashes. No email service is needed: admins copy the link and send it themselves.
- Every security-relevant action (sign-ins, failed logins, role changes, invites, resets, deletions) is written to the audit log.
- Lost owner password: `python -m app.cli set-password --email you@example.com` (run with the production `DATABASE_URL`).

## Deployment (Vercel + Render + Neon, all free tiers)

| Part | Host | Notes |
|---|---|---|
| Database | **Neon** Postgres, Singapore | Use the *pooled* connection string as `DATABASE_URL`. |
| API | **Render** web service (Docker, `backend/Dockerfile`), Singapore | Env vars: `DATABASE_URL`, `COOKIE_SECURE=true`, optional `GEMINI_API_KEY`. Sleeps after 15 min idle (first request ~30–60 s). |
| Frontend | **Vercel**, root directory `frontend` | `frontend/vercel.json` forwards `/api/*` to the Render URL, so the browser sees one domain and login cookies stay first-party. |

After the first deploy, create the owner from your laptop against the production database:
`cd backend && DATABASE_URL="<neon url>" python -m app.cli create-owner --email you@example.com --name "Your Name"`.

See [extraction changes](EXTRACTION_CHANGES.md) and the earlier [privacy containment report](SECURITY_FIXES.md) for history.
