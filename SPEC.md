# NutriLens — Technical Specification & System Architecture
**Version:** 1.0.0  
**Authors:** NutriLens Engineering Team  
**System:** Clinical Nutrition & Biomarker Intelligence Platform  
**Architecture Track:** Production System Specification  

---

## 1. Executive Summary & Positioning

### 1.1 One-Line Positioning
**NutriLens:** *From laboratory insights to personalized nutrition.*  
An evidence-grounded nutrition-support platform that transforms laboratory blood biomarkers into practical, culturally relevant Indian food recommendations, strictly adhering to individual dietary preferences and allergies without making medical diagnoses.

### 1.2 Core Differentiation (The 4 Pillars)
1. **Report Intelligence:** Dual-layer extraction (`pdfplumber` layout-aware extraction + Gemini Flash structured JSON fallback) paired with **PII de-identification** and a **Human-in-the-Loop Confirmation Screen**.
2. **Biomarker Intelligence:** Strict unit normalization (e.g., `ng/mL` vs `nmol/L`) and deterministic classification prioritizing the laboratory's printed reference range, falling back to age/sex baseline intervals.
3. **Nutrition Intelligence:** Hand-curated Indian food database (60+ items) cross-referenced with nutrient density (ICMR-NIN guidelines) and absorption synergy/inhibitor rules (e.g., Vitamin C + Iron absorption, Calcium/Tannin inhibition).
4. **Personalization & Safety Guardrails:** Hard constraint satisfaction for dietary types (Vegetarian, Vegan, Eggetarian, Non-Vegetarian) and allergens (Dairy, Gluten, Nuts, Soy, Eggs, Seafood). Fully grounded, non-diagnostic language with clinical consult thresholds for severely abnormal readings.

---

## 2. System Architecture & Tech Stack

```
                          ┌─────────────────────────┐
                          │   Client Application    │
                          │ (React 19 + Vite + TW)  │
                          └───────────┬─────────────┘
                                      │ REST API / Multipart
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend Application                           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Ingestion & Privacy Layer                                          │  │
│  │    • PDF Plumber Text & Table Extraction                              │  │
│  │    • PII Sanitizer (Regex scrubbing of Name, Phone, Email, Lab IDs)   │  │
│  │    • Regex Matcher with Alias Map                                     │  │
│  │    • LLM Fallback (Gemini Flash with Strict Pydantic JSON Schema)     │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 2. Biomarker Intelligence Engine                                      │  │
│  │    • Unit Normalization (Vit D ng/mL ↔ nmol/L, etc.)                  │  │
│  │    • Range Resolution (Report Range > Age/Sex Default Interval)       │  │
│  │    • Status Classifier (Low | Borderline | Normal | High)             │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 3. Nutrition Recommendation Engine                                    │  │
│  │    • Hard Filter: Diet Category (Veg, Vegan, Non-Veg)                 │  │
│  │    • Hard Filter: Allergen Exclusion                                  │  │
│  │    • Scoring & Ranking: Nutrient Density per Serving                  │  │
│  │    • Synergy Injector: Pairing Tips (e.g., Iron + Citrus)             │  │
│  └──────────────────────────────────┬────────────────────────────────────┘  │
│                                     ▼                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 4. Grounded Explanation Layer                                         │  │
│  │    • Template + LLM Synthesis (strictly bounded by structured data)   │  │
│  │    • Clinical Disclaimer & High-Severity Advisory Injection           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Persistence: SQLite via SQLAlchemy (Reports, Extracted Markers, History)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Technology Stack Selection
- **Backend Framework:** FastAPI (Python 3.11+) — Async, high performance, native Pydantic typing, auto OpenAPI documentation.
- **Frontend Framework:** React 19 + Vite + Tailwind CSS + Lucide Icons — Ultra-responsive UI, visual range sliders, zero bloat.
- **Database:** SQLite with SQLAlchemy ORM — Zero external dependencies, self-contained for local viva demo.
- **PDF Extraction:** `pdfplumber` + Python `re` (regular expressions).
- **LLM Engine:** Gemini 2.5 Flash via official Google GenAI SDK (`google-genai`).
- **Data Validation:** Pydantic v2.
- **Test Framework:** `pytest` (rule engine unit tests, benchmark harness).
- **PDF Export:** `xhtml2pdf` or `reportlab` for downloadable client nutrition plans.

---

## 3. Data Schemas & Reference Standards

### 3.1 Target Biomarkers (6 Core Parameters)

| Biomarker | Canonical Unit | Alternate Units | Alias Variations | Standard Adult Interval |
| :--- | :---: | :---: | :--- | :--- |
| **Vitamin D (25-OH)** | `ng/mL` | `nmol/L` ($1\text{ ng/mL} = 2.5\text{ nmol/L}$) | Vit D, 25-OH Vitamin D, 25-Hydroxycalciferol, 25(OH)D | Normal: 30–100 ng/mL<br>Borderline: 20–29.9 ng/mL<br>Low: <20 ng/mL |
| **Vitamin B12** | `pg/mL` | `pmol/L` ($1\text{ pg/mL} = 0.738\text{ pmol/L}$) | Vit B12, Cobalamin, Cyanocobalamin | Normal: 211–911 pg/mL<br>Borderline: 150–210 pg/mL<br>Low: <150 pg/mL |
| **Folate (Vitamin B9)** | `ng/mL` | `nmol/L` ($1\text{ ng/mL} = 2.266\text{ nmol/L}$) | Folic Acid, Serum Folate, Vit B9 | Normal: 4.0–20.0 ng/mL<br>Borderline: 2.5–3.9 ng/mL<br>Low: <2.5 ng/mL |
| **Serum Ferritin** | `ng/mL` | `µg/L` ($1\text{ ng/mL} = 1\text{ µg/L}$) | Ferritin, S. Ferritin | Male: 24–336 ng/mL<br>Female: 11–307 ng/mL<br>Low: <11-24 ng/mL |
| **Hemoglobin** | `g/dL` | `g/L` ($1\text{ g/dL} = 10\text{ g/L}$) | Hb, Hgb, Hemoglobin Total | Male: 13.8–17.2 g/dL<br>Female: 12.1–15.1 g/dL<br>Low: <12-13.8 g/dL |
| **Serum Calcium** | `mg/dL` | `mmol/L` ($1\text{ mmol/L} = 4.008\text{ mg/dL}$) | Total Calcium, S. Calcium, Ca | Normal: 8.5–10.2 mg/dL<br>Borderline: 8.0–8.4 mg/dL<br>Low: <8.0 mg/dL |

---

### 3.2 Indian Food Knowledge Base Schema (`foods.json`)
Each food item contains verified nutritional data derived from ICMR-NIN (National Institute of Nutrition, Hyderabad) Indian Food Composition Tables:

```json
{
  "food_id": "moringa_leaves",
  "name": "Drumstick Leaves (Moringa / Murungai)",
  "hindi_name": "Sahjan ke Patte",
  "category": "vegetable",
  "diet_type": ["veg", "vegan"],
  "allergens": [],
  "serving_size": "100g (cooked)",
  "nutrients": {
    "iron_mg": 4.0,
    "calcium_mg": 440.0,
    "folate_mcg": 40.0,
    "vitamin_c_mg": 120.0
  },
  "synergies": [
    "Contains natural Vitamin C which maximizes plant-based non-heme iron absorption."
  ],
  "preparation_tip": "Sauté lightly as a dry sabzi, add to dal, or boil in soups."
}
```

#### Supported Dietary Preferences:
- `veg` (Vegetarian, includes dairy)
- `vegan` (Strict plant-based, no dairy, no eggs)
- `eggetarian` (Vegetarian + eggs)
- `non_veg` (All inclusive: poultry, fish, meat)

#### Supported Allergen Filters:
- `dairy` (Milk, paneer, curd, ghee)
- `gluten` (Wheat, maida, barley)
- `nuts` (Peanuts, almonds, walnuts, cashews)
- `soy` (Soybeans, tofu, soy milk)
- `eggs`
- `seafood` (Fish, prawns, shellfish)

---

## 4. API Specification & Endpoints

### 4.1 Base URL: `/api/v1`

#### `POST /api/v1/extract-report`
- **Description:** Upload PDF or text report. Strips PII, runs regex extraction, triggers Gemini JSON fallback if confidence is low, and returns extracted markers.
- **Request:** `multipart/form-data` with `file: UploadFile` or raw JSON `raw_text: str`.
- **Response:**
```json
{
  "session_id": "uuid-string",
  "sanitized_preview": "Patient: [REDACTED] ...",
  "extracted_biomarkers": [
    {
      "biomarker_key": "vitamin_d",
      "display_name": "Vitamin D (25-OH)",
      "detected_value": 14.2,
      "detected_unit": "ng/mL",
      "canonical_value": 14.2,
      "canonical_unit": "ng/mL",
      "report_reference_range": {"low": 30.0, "high": 100.0},
      "extraction_method": "regex",
      "confidence": 0.98
    }
  ],
  "unmatched_text_lines": []
}
```

#### `POST /api/v1/analyze-and-recommend`
- **Description:** Takes verified biomarker values + user profile, executes the deterministic rule engine, filters the Indian food database, injects absorption tips, and synthesizes a grounded summary.
- **Request:**
```json
{
  "user_profile": {
    "age": 24,
    "gender": "female",
    "diet_type": "veg",
    "allergens": ["dairy"]
  },
  "biomarkers": [
    {
      "biomarker_key": "vitamin_d",
      "value": 14.2,
      "unit": "ng/mL",
      "reference_low": 30.0,
      "reference_high": 100.0
    },
    {
      "biomarker_key": "ferritin",
      "value": 9.5,
      "unit": "ng/mL",
      "reference_low": 11.0,
      "reference_high": 307.0
    }
  ]
}
```
- **Response:**
```json
{
  "analysis_id": "uuid-string",
  "timestamp": "2026-11-11T12:00:00Z",
  "status_summary": {
    "total_analyzed": 2,
    "low_count": 2,
    "borderline_count": 0,
    "normal_count": 0,
    "high_count": 0
  },
  "marker_analyses": [
    {
      "biomarker_key": "vitamin_d",
      "display_name": "Vitamin D (25-OH)",
      "value": 14.2,
      "unit": "ng/mL",
      "status": "low",
      "severity": "moderate_deficiency",
      "range_low": 30.0,
      "range_high": 100.0,
      "percentage_of_optimal": 47.3,
      "clinical_disclaimer_triggered": false
    }
  ],
  "recommendations": [
    {
      "target_biomarker": "ferritin",
      "nutrient_name": "Iron",
      "recommended_foods": [
        {
          "food_id": "moringa_leaves",
          "name": "Drumstick Leaves (Moringa)",
          "hindi_name": "Sahjan ke Patte",
          "serving": "100g cooked",
          "key_nutrient_yield": "4.0 mg Iron (27% RDA)",
          "synergy_tip": "High in natural Vitamin C for enhanced plant-iron absorption."
        }
      ],
      "absorption_dos": [
        "Pair plant iron with Vitamin C sources like amla, lemon, or guava."
      ],
      "absorption_donts": [
        "Avoid tea, coffee, or calcium-rich milk within 1 hour of iron-rich meals (tannins and calcium block iron uptake)."
      ]
    }
  ],
  "grounded_explanation": "Your blood report indicates Vitamin D (14.2 ng/mL) and Ferritin (9.5 ng/mL) are below reference ranges...",
  "requires_physician_consult": true,
  "consult_reasons": ["Ferritin is significantly low (<10 ng/mL). Consult your physician to rule out chronic anemia."]
}
```

#### `GET /api/v1/history`
- Returns historical reports stored in SQLite for longitudinal progress tracking.

#### `POST /api/v1/export-plan-pdf`
- Generates a branded, downloadable A4 PDF of the dietary recommendation plan.

---

## 5. Privacy & De-Identification Protocol

To satisfy security criteria and clinical data privacy:
1. **PII Masking:** Before raw text or unparsed PDF snippets are routed to any external API (Gemini), a sanitization pass runs locally via regex to scrub:
   - Patient Names (`Name: [A-Za-z ]+`)
   - Contact Numbers (`(\+91|0)?[6-9]\d{9}`)
   - Email Addresses (`[\w\.-]+@[\w\.-]+\.\w+`)
   - Hospital / Clinic Registration & UHID IDs
2. **Local Storage:** SQLite stores only anonymized analysis sessions keyed by random UUIDs unless explicit local user accounts are created.

---

## 6. Evaluation Framework & Benchmark (For Day 9 & Viva)

### 6.1 Evaluation Dataset
- **Synthetic Report Pool:** 20 generated synthetic PDF blood reports covering:
  - 5 standard single-column reports (e.g., Dr. Lal PathLabs style)
  - 5 multi-column table reports (Metropolis / SRL style)
  - 5 irregular whitespace & varied alias reports
  - 5 noisy reports with edge-case units (`nmol/L`, `g/L`)

### 6.2 Metrics & Ablation Table
We will empirically measure and report:
1. **Biomarker Extraction Precision & Recall:** Target $\ge 95\%$ on canonical 6 markers.
2. **Unit Conversion Accuracy:** 100% adherence on conversion test suite.
3. **Allergen & Diet Safety Rate:** Target **100.0%** (Zero allergen violations across 100 test permutations).
4. **Ablation Comparison:**
   - Method A: Deterministic Regex-only parser.
   - Method B: Hybrid (Regex + Gemini JSON Fallback).
   - *Hypothesis to prove:* Method B maintains >95% accuracy on distorted layouts where Method A drops below 65%.

---

## 7. Directory Structure

```text
NutriLens/
├── SPEC.md                                 # Single Source of Truth
├── README.md                               # Project presentation & setup
├── backend/
│   ├── app/
│   │   ├── main.py                         # FastAPI App initialization & CORS
│   │   ├── config.py                       # Settings & environment variables
│   │   ├── data/
│   │   │   ├── biomarkers.json             # 6 Biomarker ranges, aliases, units
│   │   │   └── foods.json                  # 60+ Indian foods with ICMR nutrients
│   │   ├── models/
│   │   │   ├── schemas.py                  # Pydantic request/response models
│   │   │   └── database.py                 # SQLAlchemy SQLite models
│   │   ├── parsers/
│   │   │   ├── sanitizer.py                # PII Redaction module
│   │   │   ├── pdf_extractor.py            # pdfplumber table & text parsing
│   │   │   ├── regex_matcher.py            # Alias dictionary & regex parser
│   │   │   └── llm_fallback.py             # Gemini GenAI structured fallback
│   │   ├── engine/
│   │   │   ├── unit_converter.py           # Canonical unit conversions
│   │   │   ├── rule_engine.py              # Status & range classification
│   │   │   ├── recommender.py              # Food ranking, allergen & diet filters
│   │   │   └── explanation_generator.py    # Grounded synthesis
│   │   └── api/
│   │       ├── v1/
│   │       │   ├── router.py               # Combined API routers
│   │       │   ├── extract.py              # Upload & parse endpoints
│   │       │   ├── recommend.py            # Recommendation & analysis
│   │       │   └── history.py              # History & PDF export
│   └── tests/
│       ├── test_unit_converter.py          # Conversion tests
│       ├── test_rule_engine.py             # Deterministic status tests
│       ├── test_recommender.py             # Allergen safety constraint tests
│       └── test_sanitizer.py               # PII masking verification
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── Navbar.tsx
│       │   ├── UploadZone.tsx              # Drag-and-drop PDF upload
│       │   ├── VerificationTable.tsx       # Human-in-the-loop confirmation
│       │   ├── UserProfileForm.tsx         # Diet type, age, sex, allergens
│       │   ├── RangeSliderBar.tsx          # InsideTracker-style visual range
│       │   ├── FoodCard.tsx                # ZOE-style food & synergy card
│       │   ├── HistoryDashboard.tsx        # Longitudinal trends
│       │   └── DisclaimerModal.tsx         # Medical safety guardrail
│       └── services/api.ts                 # Axios / Fetch client
├── evaluation/
│   ├── synthetic_generator.py              # ReportLab synthetic PDF generator
│   ├── benchmark_runner.py                 # Extraction & ablation tester
│   └── ground_truth/                       # 20 ground truth JSON files
└── docs/                                   # Documentation chapters & technical artifacts
    ├── final_report_draft.docx
    ├── poster_A1_layout.pdf
    └── slide_deck.pptx
```

