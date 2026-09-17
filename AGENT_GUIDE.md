# 🤖 AI Agent Engineering & Domain Handbook: Bihar Teacher Arrear Portal

This handbook provides indispensable context, statutory domain rules, architectural requirements, and operational protocols for any AI Agent (or human engineer) maintaining or extending this codebase.

---

## 🧭 1. Core Mission & Domain Overview

The **Bihar Teacher Arrear Portal** is an automated, audit-compliant financial calculator and official Excel spreadsheet generator for government teachers across **all 38 districts of Bihar** under the **District Programme Officer (Establishment), Education Department, Government of Bihar**.

It supports:
- **BPSC TRE 1** (Joined Nov 2023 onwards)
- **BPSC TRE 2** (Joined Feb/Mar 2024 onwards)
- **BPSC TRE 3**
- **Exclusive Teachers (विशिष्ट शिक्षक)**
- **Headmasters (प्रधानाध्यापक)**

The portal resolves retroactive salary and Dearness Allowance (DA) revisions by extracting drawn amounts from official Bihar HRMS PDF statements, computing statutory admissible amounts, and populating official multi-sheet DPO Excel forms.

---

## ⚡ 2. The Golden Rules for AI Agents (MANDATORY)

Any AI agent modifying this project must strictly comply with these rules:

### ⚠️ Rule 1: DUAL FILE SYNCHRONIZATION
The frontend exists in two locations in the repository:
1. `frontend/` (`frontend/index.html`, `frontend/style.css`, `frontend/script.js`)
2. Repository Root (`index.html`, `style.css`, `script.js`) — served directly by GitHub Pages with custom domain.

**Whenever you modify any frontend file in `frontend/`, you MUST immediately copy it to the root:**
```bash
cp frontend/index.html index.html && cp frontend/style.css style.css && cp frontend/script.js script.js
```
Always run `diff -u` to ensure zero drift between root and `frontend/`.

### ⚠️ Rule 2: CACHE BUSTING DISCIPLINE
Browsers and CDNs aggressively cache `style.css` and `script.js`.
Whenever modifying styling or client JavaScript:
- Increment the version query parameter (e.g. `?v=3.0` $\to$ `?v=3.1`) in **both** `index.html` and `frontend/index.html`:
  ```html
  <link rel="stylesheet" href="style.css?v=3.1">
  <script src="script.js?v=3.1" defer></script>
  ```

### ⚠️ Rule 3: PRESERVE OPENPYXL EXCEL FORMULAS & FORMATTING
- In `salary_arrear_writer.py` and `da_arrear_writer.py`, column formulas such as `=C8-K8` (Difference) and `=SUM(C8:C20)` **MUST NOT** be overwritten with raw values.
- Header rows 1–7 and summary rows must preserve font styling, cell borders, and alignments.

### ⚠️ Rule 4: CALENDAR DAYS ENGINE
- "No of Days" in output sheets must reflect the **actual calendar days** of each month (e.g., Jan=31, Feb=28/29, Mar=31, Apr=30, etc.).
- Leap years (like 2024 with Feb=29 days) must be correctly handled.
- Joining month pro-ration depends on Forenoon (FN) vs. Afternoon (AN) session selection.
- DA Arrear standalone adjustment rows use `0` days so net difference is added without inflating normal working days.

### ⚠️ Rule 5: FITMENT MATRIX INTEGRITY
- Admissible basic pay must strictly follow the official 6-column Fitment Matrix in `app/config.py`.
- Increments are exactly 3% rounded to the nearest index on the government grid (e.g., Level 1: 25000 $\to$ 25750 $\to$ 26520 $\to$ 27320 $\to$ 28140 $\to$ 28980 $\to$ 29850; Level 2: 28000 $\to$ 28840 $\to$ 29710).

---

## 🏛️ 3. Statutory Financial & Calculation Rules

### 3.1 All 38 Bihar Districts
The portal accepts any Bihar district. When a teacher selects or inputs a district:
- The district name is automatically capitalized (e.g., `SITAMARHI`, `PATNA`, `MUZAFFARPUR`).
- Row 1 of the official Excel sheets is dynamically formatted as:
  ```text
  OFFICE, DPO ESTABLISHMENT [DISTRICT_NAME]
  ```

### 3.2 Annual Increment Timing
Derived from the teacher's Date of Joining (DOJ):
- **January Cycle**: Teachers who join between **January 2 and July 1** receive their 3% increment annually in **January**.
- **July Cycle**: Teachers who join between **July 2 and January 1** receive their 3% increment annually in **July**.
- Increment requires completing a minimum qualifying period before the first increment is granted.

### 3.3 Dearness Allowance (DA) Schedule
Configured in `app/config.py` and customizable in the frontend DA schedule:
| Period | Standard DA Rate |
| :--- | :--- |
| Up to Dec 2023 | **46.0%** |
| Jan 2024 – Jun 2024 | **50.0%** |
| Jul 2024 – Dec 2024 | **53.0%** |
| Jan 2025 – Jun 2025 | **55.0%** |
| Jul 2025 – Dec 2025 | **58.0%** |
| Jan 2026 – Dec 2026 | **61.0%** |

### 3.4 House Rent Allowance (HRA) Rules
Bihar revised HRA rates effective from **January 1, 2024**:
- **Rural (Category A)**: 4% (before Jan 2024) $\to$ **5%** (from Jan 2024).
- **Sub-divisional / Urban (Category B)**: 7.5% (before Jan 2024) $\to$ **10%** (from Jan 2024).
- **Corrected Joiner**: Many teachers' HRMS originally defaulted to rural 4%, but their actual school entitlement was 7.5% $\to$ 10%.
- **Transfer Handling**: Multiple HRA date ranges can be added if a teacher transferred between schools with different HRA categories during the arrear scope.

### 3.5 Professional Tax (PT) Annual Motihari Slab
Applied annually in **September**:
| Annual Gross Income | Professional Tax (Deducted in Sep) |
| :--- | :--- |
| Up to ₹3,00,000 | **₹0** |
| ₹3,00,001 to ₹5,00,000 | **₹1,000** |
| ₹5,00,001 to ₹10,00,000 | **₹2,000** |
| Above ₹10,00,001 | **₹2,500** |

Deducted identically from Admissible and Drawn Net Pay to maintain mathematical consistency.

---

## 🎨 4. Frontend UI/UX System & Styling Architecture

The user interface follows a modern dark glassmorphism design system:

```text
┌─────────────────────────────────────────────────────────────┐
│                      HEADER & GUIDE                         │
├──────────────────────────────┬──────────────────────────────┤
│         LEFT CARD            │          RIGHT CARD          │
│ 1. Arrear Scope Selector     │ 4. Arrear Type Selection     │
│ 2. HRMS Upload Grid (Dynamic)│ 5. HRA Rate Rules (Native)   │
│ 3. School & Employee Details │ 6. DA Schedule (Native)      │
├──────────────────────────────┴──────────────────────────────┤
│               CENTRIC MASTER ACTION CONTAINER               │
│        [ 📥 Generate & Download Arrear Forms ]              │
│                                                             │
│         TOP-TIER INTERACTIVE PROGRESS CENTER                │
│ 🔘 [Pulse Radar] Generating Arrear Spreadsheet      [ 88% ] │
│ [============================== Light Streak Track ========]│
│ [1. HRMS Data]  [2. Pay Slips]  [3. Matrix]  [4. Export]    │
├─────────────────────────────────────────────────────────────┤
│                      SITE FOOTER                            │
└─────────────────────────────────────────────────────────────┘
```

### Key UI Features:
1. **Centric Master Action Container**:
   - Uses `grid-column: 1 / -1;` to span across both grid columns.
   - Centers `#btn-submit` horizontally on the page.
2. **Interactive Progress Center (`#progress-container`)**:
   - Deep slate container (`#0b1329`) with glowing indigo border (`2px solid #6366f1`).
   - Animated pulsing radar ring (`.progress-pulse-ring`).
   - 16px high-contrast glowing track with a moving light reflection streak.
   - Dynamic 4-step chips (`#step-1` to `#step-4`) updating live from 0% to 100% with checkmarks (`✓`).
3. **Native Month Pickers**:
   - `color-scheme: dark;` enables dark calendar popups.
   - `showPicker()` click listener on entire input surface.

---

## 🛠️ 5. Development & Testing Commands

### Local Backend Execution:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Verification Commands:
```bash
# Verify file synchronization
diff -u frontend/index.html index.html
diff -u frontend/style.css style.css
diff -u frontend/script.js script.js

# Test Python modules
python3 -c "import app.main; print('FastAPI loaded successfully')"
```

---

## 📌 6. Maintenance & Extension Protocol

When adding new features (e.g. 7th Pay Commission DA hikes, new Cadres):
1. Update `app/config.py` for backend matrix and schedules.
2. Update default tables in `frontend/index.html` and `index.html`.
3. Update presets in `frontend/script.js` and `script.js`.
4. Bump cache-busting query parameter `?v=X.X` in both HTML files.
5. Synchronize files and verify with `diff -u`.
6. Document changes in `progress.md`.
