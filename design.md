# 🏗️ Design Document: DPO Muzaffarpur Arrear Form Generator

## 1. Problem Statement

Teachers under DPO Establishment Muzaffarpur need **Salary Arrear** and **DA Arrear** forms filled out when there's a revision in pay (e.g., DA rate change, HRA revision, or annual increment not applied timely). Currently, this is done **manually** — comparing what was **actually drawn** vs. what **should have been admissible** after the revision, for each month.

**Goal:** Automate the generation of filled `DPO_Muzaffarpur_Arrear_Forms.xlsx` (both sheets: `Salary Arrear Format` and `DA Arrear Format`) from uploaded input documents.

---

## 2. Inputs

### 2.1 Employee Yearly Payment Details (PDFs) — 3 files

These are PDFs downloaded from **HRMS, Govt. of Bihar** for financial years:
- **2023-24** (Mar 2023 → Feb 2024)
- **2024-25** (Mar 2024 → Feb 2025)
- **2025-26** (Mar 2025 → Feb 2026)

Each PDF contains **4 pages** with:

| Page | Content |
|------|---------|
| 1 | **Summary** — Net Amount, Gross Amount, BT Amount per month |
| 2 | **Earning Details** — Basic Pay, HRA, DA, MA per month + Deduction Details (NPS, GIS) |
| 3 | **Deduction continuation** — Professional Tax, Recovery, Gross Deduction, Net Amount |
| 4 | **Other Payment Detail** |

**Key fields extracted per month:**
```
Employee ID, Employee Name, Designation, GPF/PRAN No, PAN No
Current Office, Current Department

Per Month (12 months: Mar → Feb):
├── Basic Pay
├── Dearness Allowance (DA)
├── House Rent Allowance (HRA)
├── Medical Allowance (MA)
├── Total Earning (Gross)
├── NPS contribution
├── GIS (State Govt. Employees)
├── Professional Tax
├── Total Deduction
└── Net Pay
```

### 2.2 Pay Slip (PDF) — 1 file

A single-page PDF from HRMS containing the **latest/any month's pay slip**. This provides:

```
Employee Code, Employee Name, DOJ (Date of Joining) ← CRITICAL
GPF/PRAN, PAN, Bank A/C, IFSC Code
Current Office, Designation, Grade
Basic Rate (current basic pay rate)

Earnings: Basic Pay, HRA, DA, MA
Deductions: NPS, GIS
```

**IMPORTANT:** The Pay Slip provides **critical info not in yearly statements**: `Date of Joining`, `Bank Account Number`, `IFSC Code`. DOJ is essential for determining increment timing.

---

## 3. Output

### 3.1 Filled `DPO_Muzaffarpur_Arrear_Forms.xlsx`

The output Excel file has **2 sheets**:

#### Sheet 1: Salary Arrear Format (Columns A-Z)

```
Row 1:  OFFICE, DPO ESTABLISHMENT MUZAFFARPUR
Row 2:  SALARY ARREAR FORMAT
Row 3:  NAME OF SCHOOL- [value]          | BLOCK NAME - [value]
Row 4:  NAME OF TEACHER- [value]         | DESIGNATION- [value]    | DATE OF JOINING- [value]
Row 5:  PRAN- [value]                    | ACCOUNT NO.- [value]    | IFSC - [value]

Row 6-7 (Headers):
       MONTH | Days | ---ADMISSIBLE (C-J)--- | ----DRAWN (K-R)---- | ---DIFFERENCE (S-Z)---
                     | Basic|DA|HRA|MA|GROSS|NPS|GIS|NET | (same) | (same)

Rows 8-20: Data rows (up to 13 months)
Row 21:   G.TOTAL
Row 22:   IN WORDS [total net arrear in words]
Row 24:   TEACHER'S SIGNATURE          |  SIGNATURE AND SEAL OF HEADMASTER
```

#### Sheet 2: DA Arrear Format (Columns A-Q)

```
Row 6-7 (Headers):
       MONTH | Days | --ADMISSIBLE (C-G)-- | ---DRAWN (H-L)--- | --DIFFERENCE (M-Q)--
                     | Basic|DA|GROSS|NPS|NET | (same) | (same)

(Same header info rows 1-5, data rows 8-20, total row 21)
```

**Sections:**
- **ADMISSIBLE** = What should have been paid (calculated from correct rates)
- **DRAWN** = What was actually paid (from yearly payment PDFs)
- **DIFFERENCE** = ADMISSIBLE − DRAWN (the arrear amount)

---

## 4. Core Business Logic (VERIFIED WITH ACTUAL DATA)

### 4.1 Understanding "Arrear"

Arrears arise when the government revises pay/DA/HRA **retroactively**. HRMS continues paying at old rates until the system is updated. The manual arrear form is needed to claim the difference.

### 4.2 DA Rate Schedule (Bihar Government)

| Period | DA Rate (% of Basic) |
|--------|---------------------|
| Up to Dec 2023 | 46% |
| Jan 2024 – Jun 2024 | 50% |
| Jul 2024 – Dec 2024 | 53% |
| Jan 2025 – Jun 2025 | 55% |
| Jul 2025 – Dec 2025 | 58% |
| Jan 2026 – Jun 2026 | 60% |

These DA rates must be **configurable** in the system.

### 4.3 HRA Rate — User-Defined

**Why user must set HRA:**
HRA varies per teacher and is NOT predictable from the PDF data alone. Here's the real scenario:

1. Teacher joins → HRMS defaults HRA to **4%** (rural school default)
2. But existing teachers at the same school already get **7.5%** HRA
3. Education Dept. issues a correction letter → teacher should get 7.5% all along
4. Meanwhile, Bihar Govt. revises HRA rates from **Jan 2024**: 4%→5% and 7.5%→10%
5. So the correct admissible HRA for this teacher was **7.5% until Dec-23**, then **10% from Jan-24**
6. But HRMS drew at 4% → eventually corrected to 5% → then 10%

**Standard HRA revision (Jan 2024):**

| Old Rate | New Rate (from Jan 2024) |
|----------|-------------------------|
| 4% of Basic | **5%** of Basic |
| 7.5% of Basic | **10%** of Basic |

**Because each teacher's situation is different, the frontend will let the user define HRA as a list of date ranges + rates:**

```
HRA Rates (user enters):
  ┌────────────────┬────────────────┬──────┐
  │ From           │ To             │ Rate │
  ├────────────────┼────────────────┼──────┤
  │ Nov 2023       │ Dec 2023       │ 7.5% │
  │ Jan 2024       │ onwards        │ 10%  │
  └────────────────┴────────────────┴──────┘
```

The system will auto-detect the **drawn HRA rate** from the pay slip (e.g., 1280/32000 = 4%) and suggest the correct rate, but the user has final control.

### 4.4 Basic Pay & Increment Logic

**Fitment Matrix Table:**

| Entry | I-V | VI-VIII | Sr. VI-VIII | IX-X | XI-XII | Sr. XI-XII |
|-------|-----|---------|-------------|------|--------|------------|
| 1 | 25000 | 28000 | 30000 | 31000 | 32000 | 34000 |
| 2 | 25750 | 28840 | 30900 | 31930 | 32960 | 35020 |
| 3 | 26520 | 29700 | 31830 | 32890 | 33950 | 36070 |
| 4 | 27320 | 30600 | 32780 | 33870 | 34970 | 37150 |
| 5 | 28140 | 31510 | 33760 | 34890 | 36020 | 38270 |
| ... | ... | ... | ... | ... | ... | ... |

**Increment Rules:**
1. **3% annual increment** of current Basic, rounded to nearest **multiple of 10**
2. The fitment matrix values match this exactly (e.g., 32000 × 1.03 = 32960)
3. **Increment month depends on DOJ:**
   - DOJ in **Jul 1 – Dec 31** → Increment effective from **July** each year
   - DOJ in **Jan 1 – Jun 30** → Increment effective from **January** each year
4. The fitment matrix is the **lookup table** — each row is a step

**Verified Example (MD ZAFAR ALI):**
```
DOJ: 16-Nov-2023 → Jul-Dec group → Increment in July
Designation: School Teacher(11-12) → Column 6 (XI-XII)
Fitment Row 1: 32000 (starting Basic from Nov 2023)
Fitment Row 2: 32960 (from Jul 2024 = 32000 × 1.03)
Fitment Row 3: 33950 (from Jul 2025 = 32960 × 1.03, rounded to 10)
Fitment Row 4: 34970 (from Jul 2026 = 33950 × 1.03, rounded to 10)
```

### 4.5 NPS Rate
- Employee contribution: **10%** of (Basic + DA)
- Verified from data: `4672 / (32000 + 14720) = 10.00%` ✓

### 4.6 Fixed Values
- **MA** (Medical Allowance): ₹1000/month (fixed)
- **GIS** (Group Insurance Scheme): ₹30/month (fixed)

### 4.7 Complete Calculation Example

**MD ZAFAR ALI — Arrear from Dec-23 to Feb-26**

This teacher's school was actually a 7.5% HRA school, but HRMS set it to 4% as default for new joiners. After Jan-2024 revision, the correct rate is 10%.

User enters HRA: `7.5% (Nov-23 to Dec-23)` → `10% (Jan-24 onwards)`

```
Month    | Admiss.Basic | Drawn Basic | Admiss.DA | Drawn DA | Admiss.HRA | Drawn HRA | Net Diff
---------|-------------|-------------|-----------|----------|------------|-----------|--------
Dec-23   |    32000    |    32000    |  14720(46%)|  14720  |  2400(7.5%)|  1280(4%) | +1072
Jan-24   |    32000    |    32000    |  16000(50%)|  14720  |  3200(10%) |  1280(4%) | +2952
Feb-24   |    32000    |    32000    |  16000(50%)|  14720  |  3200(10%) |  1280(4%) | +2952
Mar-24   |    32000    |    32000    |  16000(50%)|  16000  |  3200(10%) |  1280(4%) | +1920
...      |             |             |           |          |            |           |
Jul-24   |    32960    |    32000    |  17468(53%)|  16000  |  3296(10%) |  1280(4%) | +4202
...      |             |             |           |          |            |           |
Jan-25   |    32960    |    32000    |  18128(55%)|  16000  |  3296(10%) |  1280(4%) | +4862
...      |             |             |           |          |            |           |
Jul-25   |    33950    |    33950    |  19691(58%)|  16975  |  3395(10%) |  1358(4%) | +4482
...      |             |             |           |          |            |           |
Dec-25   |    33950    |    33950    |  19691(58%)|  19691  |  3395(10%) |  1698(5%) | +1627
Jan-26   |    33950    |    33950    |  20370(60%)|  19691  |  3395(10%) |  3395(10%)| +611
Feb-26   |    33950    |    33950    |  20370(60%)|  19691  |  3395(10%) |  3395(10%)| +611
```

(Note: Exact totals depend on the HRA rates the user enters.)

### 4.8 Calculation Flow (Per Month)

```python
# ADMISSIBLE
basic_adm = lookup_basic_from_fitment(month, doj, designation)
da_adm    = int(basic_adm * da_rate_for_month)
hra_adm   = int(basic_adm * hra_rate_for_month)
ma_adm    = 1000
gross_adm = basic_adm + da_adm + hra_adm + ma_adm
nps_adm   = int((basic_adm + da_adm) * 0.10)
gis_adm   = 30
net_adm   = gross_adm - nps_adm - gis_adm

# DRAWN (from PDF)
# directly extracted

# DIFFERENCE
diff = admissible - drawn  (per field)
```

---

## 5. System Architecture

### 5.1 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Backend API** | **FastAPI** (Python) | Async, auto-docs, great for file handling |
| **PDF Parsing** | `pdfplumber` | Best for extracting tabular HRMS data |
| **Excel Generation** | `openpyxl` | Full control over formatting, merged cells |
| **Frontend** | HTML + Vanilla JS + CSS | Simple upload UI, no framework needed |
| **Deployment** | Local | Runs on user's machine |

### 5.2 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Frontend (Browser)                         │
│   Upload 4 PDFs → Configure → Preview → Download Excel      │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP (multipart/form-data)
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                            │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │   PDF Parsers   │  │  Config Store   │                   │
│  │ • Yearly Payment│  │ • DA rates      │                   │
│  │ • Pay Slip      │  │ • HRA rates     │                   │
│  └────────┬────────┘  │ • Fitment table │                   │
│           │           └────────┬────────┘                    │
│           ▼                    │                              │
│  ┌─────────────────────────────▼───────┐                    │
│  │       Calculation Engine            │                    │
│  │ • Determine Basic from fitment      │                    │
│  │ • Calculate ADMISSIBLE per month    │                    │
│  │ • Extract DRAWN from parsed PDFs    │                    │
│  │ • Compute DIFFERENCE               │                    │
│  └────────────────┬────────────────────┘                    │
│                   ▼                                          │
│  ┌─────────────────────────────────────┐                    │
│  │       Excel Generator              │                     │
│  │ • Copy template                    │                     │
│  │ • Fill Salary Arrear sheet         │                     │
│  │ • Fill DA Arrear sheet             │                     │
│  │ • Amount in words                  │                     │
│  └─────────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────────┘
```

### 5.3 Directory Structure

```
Project ARREAR/
├── design.md
├── DPO_Muzaffarpur_Arrear_Forms.xlsx       # Template
├── fitment matrix for School Teachers.heic  # Reference
├── Input of 1 teacher/                      # Test data
│
├── app/
│   ├── main.py                        # FastAPI entry point, serves frontend
│   ├── config.py                      # DA rates, HRA rates, fitment matrix, constants
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── employee.py                # Employee data model
│   │   ├── monthly_salary.py          # Monthly salary breakdown
│   │   └── arrear_config.py           # Arrear configuration
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── yearly_payment_parser.py   # Parse HRMS yearly payment PDFs
│   │   └── payslip_parser.py          # Parse HRMS pay slip PDF
│   │
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── increment_calculator.py    # Basic pay from fitment + DOJ
│   │   ├── admissible_calculator.py   # Calculate admissible amounts
│   │   └── difference_calculator.py   # Compute ADMISSIBLE - DRAWN
│   │
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── salary_arrear_writer.py    # Fill Salary Arrear sheet
│   │   ├── da_arrear_writer.py        # Fill DA Arrear sheet
│   │   └── template_manager.py        # Load/manage Excel template
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                  # API endpoints
│   │
│   └── utils/
│       ├── __init__.py
│       ├── number_to_words.py         # Convert amount to words
│       └── date_utils.py             # FY parsing, month ordering
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── templates/
│   └── DPO_Muzaffarpur_Arrear_Forms.xlsx
│
├── output/
├── requirements.txt
└── README.md
```

---

## 6. API Design

### 6.1 Endpoints

#### `POST /api/generate-arrear`

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `yearly_pdf_1` | File (PDF) | Yes | FY 2023-24 yearly payment |
| `yearly_pdf_2` | File (PDF) | Yes | FY 2024-25 yearly payment |
| `yearly_pdf_3` | File (PDF) | Yes | FY 2025-26 yearly payment |
| `payslip_pdf` | File (PDF) | Yes | Any month pay slip |
| `school_name` | String | Yes | Name of school |
| `block_name` | String | Yes | Block name |
| `hra_rates` | JSON String | Yes | User-defined HRA rates with date ranges (see below) |
| `arrear_type` | String | No | `"salary"` / `"da"` / `"both"` (default: `"both"`) |

**`hra_rates` format:**
```json
[
  {"from": "2023-11", "to": "2023-12", "rate_percent": 7.5},
  {"from": "2024-01", "to": "2026-12", "rate_percent": 10.0}
]
```

**Response:** Downloaded Excel file

#### `POST /api/parse-preview`

Upload PDFs and return parsed data for user verification.

**Response:**
```json
{
  "employee": {
    "name": "MD ZAFAR ALI",
    "employee_id": "40113120",
    "designation": "School Teacher(11-12)",
    "pran": "110139747944",
    "pan": "BELPA2587Q",
    "doj": "16-11-2023",
    "bank_account": "00000036338668366",
    "ifsc": "SBIN0001485"
  },
  "increment_schedule": {
    "increment_month": "July",
    "starting_basic": 32000,
    "steps": [
      {"from": "Nov-23", "to": "Jun-24", "basic": 32000},
      {"from": "Jul-24", "to": "Jun-25", "basic": 32960},
      {"from": "Jul-25", "to": "Jun-26", "basic": 33950}
    ]
  },
  "drawn_summary": {
    "total_months": 28,
    "months_with_wrong_da": 24,
    "months_with_wrong_hra": 23,
    "months_with_wrong_basic": 8
  },
  "estimated_total_arrear": 48241
}
```

#### `GET /api/config`

Returns current configuration (DA rates, HRA rates, fitment matrix).

#### `PUT /api/config`

Update configuration.

---

## 7. Data Models

### 7.1 Employee

```python
class Employee(BaseModel):
    employee_id: str
    name: str
    designation: str          # e.g., "School Teacher(11-12)"
    designation_category: str  # e.g., "XI-XII" → fitment column 6
    pran: str
    pan: str
    doj: str                  # "16-11-2023"
    doj_parsed: date
    bank_account: Optional[str]
    ifsc: Optional[str]
    school_name: Optional[str]
    block_name: Optional[str]
    increment_month: str      # "July" or "January" (derived from DOJ)

class HRARateEntry(BaseModel):
    from_month: str       # "2023-11"
    to_month: str         # "2023-12" or "9999-12" for ongoing
    rate_percent: float   # e.g., 7.5 or 10.0
```

### 7.2 MonthlySalary

```python
class MonthlySalary(BaseModel):
    month_label: str    # "Jan-24", "Feb-24", etc.
    days: int           # 30 or 31
    basic: int
    da: int
    hra: int
    ma: int
    gross: int
    nps: int
    gis: int
    net: int            # gross - nps - gis
```

### 7.3 FitmentEntry

```python
class FitmentEntry(BaseModel):
    step: int           # 1-20
    cat_1_5: int        # I-V
    cat_6_8: int        # VI-VIII
    cat_sr_6_8: int     # Senior VI-VIII
    cat_9_10: int       # IX-X
    cat_11_12: int      # XI-XII
    cat_sr_11_12: int   # Senior XI-XII
```

---

## 8. Processing Pipeline

```
Step 1: PARSE PAY SLIP
        → Extract: Name, DOJ, PRAN, PAN, Bank A/C, IFSC, Designation, Basic Rate
        → Determine increment month from DOJ

Step 2: PARSE 3 YEARLY PDFs
        → Extract monthly: Basic, DA, HRA, MA, Gross, NPS, GIS, Net
        → This is the DRAWN data (up to 36 months)

Step 3: DETERMINE BASIC PAY PROGRESSION
        → From DOJ, find starting Basic from fitment matrix
        → Apply 3% annual increment at correct month
        → Verify against DRAWN data where available

Step 4: DETECT ARREAR MONTHS
        → For each month, compare:
          - Drawn DA rate vs Admissible DA rate
          - Drawn HRA rate vs Admissible HRA rate
          - Drawn Basic vs Admissible Basic
        → Months with ANY mismatch need arrear

Step 5: CALCULATE ADMISSIBLE
        → For each arrear month, compute correct values using:
          - Correct Basic (from fitment progression)
          - Correct DA rate (from DA schedule)
          - Correct HRA rate (from user-defined HRA rate entries)
          - Fixed MA=1000, GIS=30, NPS=10%

Step 6: COMPUTE DIFFERENCES
        → ADMISSIBLE - DRAWN for each field

Step 7: GENERATE EXCEL
        → Copy template
        → Fill employee header info
        → Fill data rows for arrear months
        → Calculate totals
        → Convert net total to words
```

### 8.1 PDF Parsing Strategy

#### Yearly Payment PDF (Page 2 — Main Data Source)

```python
# Lines to parse on Page 2:
# "Basic Pay    32000 32000 32000 ... 384000"
# "Dearness     16000 16000 16000 ... 192000"
# "Allowance"   (continuation of previous)
# "House Rent   1280  1280  1280  ... 15360"
# "Allowance"   (continuation)
# "Medical      1000  1000  1000  ... 12000"
# "Allowance"   (continuation)
# "Total        50280 50280 50280 ... 603360"
# "Earning"     (continuation)
# "NPS          4800  4800  4800  ... 57600"
# "contributio" (continuation)
# "n employee"  (continuation)
# "GIS State    30    30    30    ... 360"

# Strategy: 
# 1. Split text into lines
# 2. Find "Earning Details" marker
# 3. Parse each earning/deduction row by regex
# 4. Handle multi-line labels (e.g., "NPS\ncontributio\nn employee")
# 5. Month headers: "2024-Mar 2024-Apr ... 2025-Feb Total"
```

#### Pay Slip PDF

```python
# Key fields to extract via regex:
# "Employee Code : 40113120"
# "DOJ : 16-11-2023"
# "Employee Name : MD ZAFAR ALI"
# "GPF/PRAN : 110139747944"
# "PAN : BELPA2587Q"
# "Bank A/C : 00000036338668366"
# "IFSC Code : SBIN0001485"
# "Basic Rate : 33950"
# "Designation : School Teacher(11-12)"
#
# Tables: Earnings (Basic Pay, HRA, DA, MA) and Deductions (NPS, GIS)
```

### 8.2 Increment Auto-Detection

```python
def determine_increment_month(doj: str) -> str:
    """
    DOJ 16-11-2023 → month=11 (Nov) → Jul-Dec group → "July"
    DOJ 15-03-2024 → month=3  (Mar) → Jan-Jun group → "January"
    """
    doj_month = parse_date(doj).month
    if 7 <= doj_month <= 12:
        return "July"
    else:
        return "January"

def get_basic_for_month(starting_basic: int, doj: date, target_month: date) -> int:
    """
    Calculate the correct Basic Pay for any given month.
    Uses 3% increment rule with fitment matrix as reference.
    """
    increment_month = 7 if doj.month >= 7 else 1
    
    # Count how many increments have occurred
    current = starting_basic
    year = doj.year
    
    while True:
        next_increment = date(year + (1 if doj.month >= 7 else 0), increment_month, 1)
        if next_increment > target_month:
            break
        if next_increment > doj:
            current = round_to_10(current * 1.03)
        year += 1
    
    return current
```

---

## 9. Configuration (config.py)

```python
# DA Rate Schedule - Bihar Government
DA_RATES = [
    {"from": "2023-01", "to": "2023-12", "rate": 0.46},
    {"from": "2024-01", "to": "2024-06", "rate": 0.50},
    {"from": "2024-07", "to": "2024-12", "rate": 0.53},
    {"from": "2025-01", "to": "2025-06", "rate": 0.55},
    {"from": "2025-07", "to": "2025-12", "rate": 0.58},
    {"from": "2026-01", "to": "2026-06", "rate": 0.60},
]

# HRA Rates — USER-DEFINED per teacher (not stored in config)
# The frontend provides a UI where the user enters HRA rate entries.
# Common presets offered as quick-select:
HRA_PRESETS = {
    "4% → 5%": [
        {"from": "2020-01", "to": "2023-12", "rate": 0.04},
        {"from": "2024-01", "to": "9999-12", "rate": 0.05},
    ],
    "7.5% → 10%": [
        {"from": "2020-01", "to": "2023-12", "rate": 0.075},
        {"from": "2024-01", "to": "9999-12", "rate": 0.10},
    ],
    "4% → 7.5% → 10% (corrected joiner)": [
        # For new joiners who were wrongly set to 4% but school is 7.5%
        # The admissible was always 7.5%, then 10% after revision
        {"from": "2020-01", "to": "2023-12", "rate": 0.075},
        {"from": "2024-01", "to": "9999-12", "rate": 0.10},
    ],
    "Custom": []  # User enters manually
}

# Fixed values
MA_FIXED = 1000
GIS_FIXED = 30
NPS_EMPLOYEE_RATE = 0.10  # 10% of (Basic + DA)

# Fitment Matrix for School Teachers
FITMENT_MATRIX = {
    # step: [I-V, VI-VIII, Sr.VI-VIII, IX-X, XI-XII, Sr.XI-XII]
    1:  [25000, 28000, 30000, 31000, 32000, 34000],
    2:  [25750, 28840, 30900, 31930, 32960, 35020],
    3:  [26520, 29700, 31830, 32890, 33950, 36070],
    4:  [27320, 30600, 32780, 33870, 34970, 37150],
    5:  [28140, 31510, 33760, 34890, 36020, 38270],
    6:  [28980, 32460, 34770, 35940, 37100, 39410],
    7:  [29850, 33430, 35810, 37020, 38210, 40600],
    8:  [30750, 34440, 36880, 38130, 39360, 41820],
    9:  [31670, 35470, 37990, 39270, 40540, 43070],
    10: [32620, 36530, 39130, 40450, 41750, 44360],
    11: [33600, 37630, 40300, 41660, 43000, 45690],
    12: [34610, 38760, 41510, 42910, 44290, 47060],
    13: [35640, 39920, 42750, 44200, 45620, 48480],
    14: [36710, 41120, 44030, 45520, 46990, 49930],
    15: [37810, 42350, 45350, 46890, 48400, 51430],
    16: [38940, 43620, 46710, 48300, 49850, 52970],
    17: [40110, 44930, 48110, 49750, 51350, 54560],
    18: [41320, 46280, 49550, 51240, 52890, 56200],
    19: [42550, 47660, 51040, 52770, 54470, 57880],
    20: [43830, 49090, 52570, 54360, 56110, 59620],
}

# Designation to fitment column mapping
DESIGNATION_COLUMN_MAP = {
    "Exclusive Teacher (1-5)": 0,   # I-V
    "School Teacher(1-5)": 0,
    "School Teacher(6-8)": 1,       # VI-VIII
    "Senior School Teacher(6-8)": 2, # Sr. VI-VIII
    "School Teacher(9-10)": 3,      # IX-X
    "School Teacher(11-12)": 4,     # XI-XII
    "Senior School Teacher(11-12)": 5, # Sr. XI-XII
}

FY_MONTH_ORDER = ["Mar", "Apr", "May", "Jun", "Jul", "Aug",
                   "Sep", "Oct", "Nov", "Dec", "Jan", "Feb"]
```

---

## 10. Frontend Design

```
┌──────────────────────────────────────────────────────────────┐
│  📋 DPO Muzaffarpur - Arrear Form Generator                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: Upload Documents                                    │
│  ┌──────────────────────┐ ┌──────────────────────┐          │
│  │ 📄 Yearly 2023-24    │ │ 📄 Yearly 2024-25    │          │
│  │ [Drop PDF here]      │ │ [Drop PDF here]      │          │
│  └──────────────────────┘ └──────────────────────┘          │
│  ┌──────────────────────┐ ┌──────────────────────┐          │
│  │ 📄 Yearly 2025-26    │ │ 📄 Pay Slip          │          │
│  │ [Drop PDF here]      │ │ [Drop PDF here]      │          │
│  └──────────────────────┘ └──────────────────────┘          │
│                                                              │
│  Step 2: School Details                                      │
│  School Name:  [________________________]                    │
│  Block Name:   [________________________]                    │
│                                                              │
│  Step 3: HRA Rate Configuration                              │
│  Quick Preset: [▼ Select...]                                │
│    ○ 4% → 5% (from Jan 2024)                                │
│    ○ 7.5% → 10% (from Jan 2024)                             │
│    ○ Corrected joiner (was 4%, school is 7.5% → 10%)        │
│    ● Custom                                                  │
│                                                              │
│  ┌────────────────┬────────────────┬──────┬─────┐           │
│  │ From           │ To             │ Rate │     │           │
│  ├────────────────┼────────────────┼──────┼─────┤           │
│  │ [Nov 2023  ▼]  │ [Dec 2023  ▼]  │ 7.5% │ [✕] │           │
│  │ [Jan 2024  ▼]  │ [Jun 2026  ▼]  │  10% │ [✕] │           │
│  └────────────────┴────────────────┴──────┴─────┘           │
│  [ + Add Row ]                                               │
│  Detected from pay slip: drawn HRA = 4% (likely wrong)      │
│                                                              │
│  Step 4: Preview (after upload + config)                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Employee: MD ZAFAR ALI  |  PRAN: 110139747944       │    │
│  │ DOJ: 16-11-2023  |  Increment: July                 │    │
│  │ Designation: School Teacher(11-12)                   │    │
│  │ Basic Progression: 32000→32960→33950                 │    │
│  │ HRA: 7.5% (Nov-Dec 23) → 10% (Jan 24+)             │    │
│  │ Arrear months: 27 | Estimated: ₹XX,XXX              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│           [ 🔄 Preview ]    [ 📥 Generate & Download ]       │
└──────────────────────────────────────────────────────────────┘
```

### Features:
- **Drag & Drop** PDF upload with file type validation
- **Auto-detection** of employee info, designation, increment timing
- **HRA rate builder** — presets for common scenarios + custom date-range editor
- **Preview** parsed data + estimated arrear before generating
- **Drawn HRA detection** — shows what HRMS set vs. what user says is correct
- **Download** generated Excel directly

---

## 11. Error Handling

| Error Scenario | Handling |
|----------------|----------|
| Invalid PDF (not HRMS format) | Clear error message |
| Months with ₹0 drawn (no salary) | Skip those months, don't include in arrear |
| Partial month (like Nov-23 with 14933) | Include but handle proportionally |
| Negative difference (overpaid) | Allow — these are valid |
| Basic not found in fitment matrix | Warn user, allow manual entry |
| PDFs from different employees | Cross-validate PRAN across all files |

---

## 12. Implementation Phases

### Phase 1: PDF Parsers + Config (3-4 days)
- [ ] `yearly_payment_parser.py` — parse all 4 pages
- [ ] `payslip_parser.py` — parse single page
- [ ] `config.py` — DA rates, HRA rates, fitment matrix
- [ ] Test with provided sample data

### Phase 2: Calculation Engine (2-3 days)
- [ ] `increment_calculator.py` — Basic from fitment + DOJ
- [ ] `admissible_calculator.py` — correct amounts per month
- [ ] `difference_calculator.py` — admissible - drawn
- [ ] Verify against manually calculated values

### Phase 3: Excel Generator (2 days)
- [ ] `template_manager.py` — copy and manage template
- [ ] `salary_arrear_writer.py` — fill Sheet 1
- [ ] `da_arrear_writer.py` — fill Sheet 2
- [ ] `number_to_words.py` — amount in words

### Phase 4: API + Frontend (2-3 days)
- [ ] FastAPI routes
- [ ] HTML/CSS/JS upload UI
- [ ] Preview functionality
- [ ] Download endpoint

### Phase 5: Testing & Polish (1-2 days)
- [ ] End-to-end test with MD ZAFAR ALI data
- [ ] Edge cases
- [ ] Error handling

---

## 13. Dependencies (requirements.txt)

```
fastapi>=0.104.0
uvicorn>=0.24.0
python-multipart>=0.0.6
pdfplumber>=0.10.0
openpyxl>=3.1.0
pydantic>=2.0.0
num2words>=0.5.13
```

---

## 14. Finalized Business Rules & Decisions

The remaining design decisions have been finalized as follows:

1. **Arrear Period Boundaries**: The system will **auto-detect** all months where drawn ≠ admissible.
2. **Professional Tax (PT)**: PT is calculated annually and deducted in September. The deduction is based on the annual gross income slab (from the DEO Motihari order):
   - Annual Gross Income up to ₹3,00,000: ₹0 PT
   - Annual Gross Income from ₹3,00,001 to ₹5,00,000: ₹1,000 PT
   - Annual Gross Income from ₹5,00,001 to ₹10,00,000: ₹2,000 PT
   - Annual Gross Income above ₹10,00,001: ₹2,500 PT
   This PT amount is deducted from the Net Pay for September in both Admissible and Drawn columns to maintain exact mathematical consistency.
3. **Partial First Month**: The joining month is **skipped entirely** from the arrear sheet.
4. **Number of Days & LWP**:
   - Total Days of Month is computed dynamically using calendar month/year limits (handling February in leap years correctly).
   - LWP (Leave Without Pay) is detected dynamically: if the drawn Basic Pay in any month is less than the standard basic pay rate, the LWP fraction is computed as `Ratio = Drawn Basic / Standard Basic Rate`.
   - Paid Days = `round(Ratio * Total Days of Month)`.
   - All admissible components for that month (Basic, DA, HRA, MA) are pro-rated by multiplying the standard admissible value by this `Ratio`.
   - The "No of Days" column in the output Excel sheet will be set to `Paid Days`.
