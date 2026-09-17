# 📑 Bihar Teacher Arrear Portal — DPO Establishment (All 38 Districts)

An automated, audit-compliant Salary and DA Arrear calculator and official spreadsheet generator designed for teachers across all **38 Districts of Bihar** under the **District Programme Officer (Establishment), Education Department, Government of Bihar**.

The system parses Bihar HRMS PDF payment statements and payslips, calculates statutory admissible pay based on the official Bihar Government 6-column Fitment Matrix and Dearness Allowance schedules, and automatically generates official multi-sheet Excel arrear forms tailored to any selected district.

Supports **BPSC TRE 1, TRE 2, TRE 3, Exclusive Teachers (विशिष्ट शिक्षक), and Headmasters**.

---

## 🌟 Key Features

- **Universal Bihar District Support (All 38 Districts)**:
  - Supports **Muzaffarpur, Patna, Gaya, Bhagalpur, Darbhanga, Sitamarhi, Motihari, Purnea**, and all other Bihar districts.
  - Selecting "Other District" allows teachers to specify their district, which is automatically converted to uppercase and dynamically stamped onto Row 1 of the official Excel sheets (`OFFICE, DPO ESTABLISHMENT [DISTRICT]`).
- **Dynamic Arrear Scope Selector**:
  - Flexible **From (Month)** and **To (Month)** picker with native month selectors.
  - Automatically calculates the elapsed duration (in months) and maps all affected Financial Years (e.g. FY 2023-24, 2024-25, 2025-26, 2026-27).
  - Dynamically renders the exact HRMS statement upload slots required for that period with zero manual configuration.
- **Automated HRMS PDF Parsing (`pdfplumber`)**:
  - **Pay-Slip Parser**: Extracts Employee Code, Name, Designation, Date of Joining (DOJ), PRAN, Bank Account, IFSC, and PAN.
  - **Yearly Statement Parser**: Extracts multi-page tables (March to February) of drawn components (Basic Pay, DA, HRA, MA, NPS, GIS, PT), including DA Arrears from Other Payment Details.
- **Accurate Statutory Pay Engine**:
  - **Bihar Fitment Matrix (6-column scale)**: Progression for Class 1–5, 6–8, 9–10, 11–12, and Headmasters.
  - **Annual Increment Cycle**: Accurate 3% annual increment cycle determination (January vs. July) derived from Date of Joining.
  - **Accurate Calendar Days Engine**: Exact calendar days calculated for each month (Jan=31, Feb=28/29, Mar=31, Apr=30, etc.) with joining month session pro-ration (Forenoon / Afternoon) and LWP adjustments.
  - **Dynamic HRA & DA Schedules**: Native month pickers with presets (Cat A: 4%→5%, Cat B: 7.5%→10%, Corrected Joiners) and custom date-range builder.
  - **Professional Tax (PT)**: Automatic application of the Motihari annual PT slab in September.
- **Official DPO Excel Generation (`openpyxl`)**:
  - Populates official `DPO_Muzaffarpur_Arrear_Forms.xlsx` sheets:
    - **Salary Arrear Format** (26 columns: Admissible, Drawn, Difference).
    - **DA Arrear Format** (17 columns).
  - Preserves Excel dynamic formulas (`=C8-K8`, `=SUM(...)`) and cell styling.
  - Converts net arrear totals into Indian currency words.
- **Top-Tier Centric UI & Interactive Progress Center**:
  - **Centric Action Layout**: Master "Generate & Download" hero button centered across the entire screen layout (`grid-column: 1 / -1;`).
  - **Interactive Progress Center**: Glassmorphic `#0b1329` card with an animated pulsing radar ring, a 16px high-contrast glowing progress track with moving light-reflection streaks, and dynamic 4-step chips (`1. HRMS Data` → `2. Salary Slips` → `3. HRA/DA Matrix` → `4. Excel Generation`).
  - **Comprehensive Hindi User Guide**: In-app modal with clear step-by-step guidance and common troubleshooting tips in Hindi.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
- **PDF Extraction**: [pdfplumber](https://github.com/jsvine/pdfplumber)
- **Spreadsheet Engine**: [openpyxl](https://openpyxl.readthedocs.io/)
- **Frontend**: Vanilla JavaScript (ES6+), CSS3 (Modern Glassmorphism & Custom Properties), HTML5
- **Deployment**:
  - Frontend: GitHub Pages with Custom Domain (`uhskaparpurakanti.in` / `arrear.uhskaparpurakanti.in`)
  - Backend: Render Web Service (`arrear-api.uhskaparpurakanti.in`)

---

## 📁 Repository Structure

```text
├── app/
│   ├── main.py                     # FastAPI routes, CORS, file endpoints
│   ├── config.py                   # Fitment Matrix, DA schedules, HRA presets
│   ├── models/                     # Pydantic schemas (Employee, MonthlySalary)
│   ├── parsers/                    # HRMS PDF parsers (yearly payment & payslip)
│   ├── engine/                     # Calculation engine (admissible, difference, increments)
│   ├── generators/                 # Excel writers (Salary Arrear & DA Arrear)
│   └── utils/                      # Helper utilities (number to words, date formatting)
├── templates/
│   └── DPO_Muzaffarpur_Arrear_Forms.xlsx  # Clean base Excel template
├── frontend/                       # Web UI static assets (source of truth)
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── upi_qr.png
├── index.html                      # GitHub Pages root entrypoint (must sync with frontend/)
├── style.css                       # GitHub Pages root stylesheet (must sync with frontend/)
├── script.js                       # GitHub Pages root script (must sync with frontend/)
├── AGENT_GUIDE.md                  # Comprehensive manual & golden rules for AI Agents
├── design.md                       # Comprehensive design specifications
├── progress.md                     # Implementation progress and phase history
├── deployment.md                   # Free-tier production deployment guide
├── requirements.txt                # Python backend dependencies
└── README.md
```

---

## 🤖 Guide for AI Agents & Developers

If you are an AI assistant or developer modifying this repository, please review [`AGENT_GUIDE.md`](AGENT_GUIDE.md) before making changes.

### Golden Rules:
1. **Dual File Synchronization**: Any change to `frontend/index.html`, `frontend/style.css`, or `frontend/script.js` **MUST** be copied identically to root `index.html`, `style.css`, and `script.js`.
2. **Browser Cache Busting**: Always increment the version query parameter (e.g., `?v=3.0` $\to$ `?v=3.1`) on stylesheet and script links in both `index.html` files whenever styling or client script changes are made.
3. **Excel Formulas Integrity**: Never replace dynamic openpyxl Excel formulas (such as `=C8-K8` or `=SUM(C8:C20)`) with hardcoded numbers.
4. **Calendar Days Accuracy**: Month day counts must reflect real calendar month lengths (Feb=28/29, Mar=31, Apr=30, etc.) and accurately pro-rate joining months.

---

## 🚀 Getting Started Locally

### Prerequisites

- Python 3.10 or higher
- `pip` (Python package manager)

### Installation & Run

1. **Clone the repository:**
   ```bash
   git clone https://github.com/EternalStud/project-arrear.git
   cd project-arrear
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the FastAPI server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Access the application:**
   Open `http://localhost:8000` in your web browser.

---

## 📄 License

Developed for public administrative assistance, transparency, and audit compliance for government teachers across Bihar. Made with ❤️ by Eternal Student.

