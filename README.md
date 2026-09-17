# 📑 DPO Muzaffarpur — Teacher Arrear Form Generator

An automated, bulletproof Salary and DA Arrear calculator and official spreadsheet generator designed for teachers under the **District Programme Officer (Establishment), Muzaffarpur (Bihar Education Department)**.

It parses Bihar HRMS PDF payment statements and payslips, calculates statutory admissible pay based on the official Bihar Government Fitment Matrix and Dearness Allowance schedules, and automatically populates the official multi-sheet Excel arrear forms.

---

## 🌟 Key Features

- **Automated HRMS PDF Parsing**:
  - Automatically parses single-page HRMS Pay-Slips (extracting Employee Code, Name, Designation, Date of Joining, PRAN, Bank Account, IFSC, PAN).
  - Robust multi-page parsing of Yearly Payment Statements (FY 2023–24, 2024–25, 2025–26), extracting monthly drawn components including DA Arrear adjustments from Other Payment Details.
- **Accurate Admissible Salary Computation**:
  - Official 6-column Fitment Matrix progression for all teacher cadres (Class 1–5, 6–8, 9–10, 11–12, Senior grades).
  - Accurate 3% annual increment timing based on Date of Joining (January / July cycle).
  - Dynamic configurable DA rates (46%, 50%, 53%, 55%, 58%, 60%) and user-defined HRA date-range rules (4% → 5%, 7.5% → 10%, or custom).
  - Joining month pro-ration with Forenoon (FN) and Afternoon (AN) session handling.
  - Professional Tax (PT) annual Motihari slab deduction applied in September.
- **Official Excel Output**:
  - Generates official `DPO_Muzaffarpur_Arrear_Forms.xlsx` containing:
    - **Salary Arrear Format** (26-column format: Admissible, Drawn, Difference).
    - **DA Arrear Format** (17-column format).
  - Dynamic row adjustment with preserved Excel formatting and formulas (`=C8-K8`, etc.).
  - Automatic Net Arrear conversion into Indian currency words.
- **Modern Responsive Web UI**:
  - Drag-and-drop PDF upload with instant validation.
  - Quick-preset HRA rate selector with custom date-range builder.
  - Interactive on-screen preview before generation.
  - Integrated UPI QR scanner for voluntary developer appreciation.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
- **PDF Extraction**: [pdfplumber](https://github.com/jsvine/pdfplumber)
- **Spreadsheet Generation**: [openpyxl](https://openpyxl.readthedocs.io/)
- **Frontend**: Vanilla JavaScript, CSS3, HTML5 (zero heavyweight dependencies)
- **Deployment**:
  - Frontend: GitHub Pages with custom domain
  - Backend: Render Web Service

---

## 📁 Repository Structure

```text
├── app/
│   ├── main.py                     # FastAPI entrypoint and API routes
│   ├── config.py                   # Fitment Matrix, DA schedules, HRA presets
│   ├── models/                     # Data models (Employee, MonthlySalary)
│   ├── parsers/                    # HRMS PDF parsers (yearly payment & payslip)
│   ├── engine/                     # Calculation engine (admissible, difference, increments)
│   ├── generators/                 # Excel writers (Salary Arrear & DA Arrear)
│   └── utils/                      # Helper utilities (number to words, date formatting)
├── templates/
│   └── DPO_Muzaffarpur_Arrear_Forms.xlsx  # Clean base Excel template
├── frontend/                       # Web UI static assets
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── upi_qr.png
├── index.html                      # GitHub Pages root entrypoint
├── style.css
├── script.js
├── CNAME                           # GitHub Pages custom domain
├── requirements.txt                # Python backend dependencies
└── README.md
```

---

## 🚀 Getting Started Locally

### Prerequisites

- Python 3.10 or higher
- `pip` (Python package manager)

### Installation

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

5. **Open the application:**
   Navigate to `http://localhost:8000` in your web browser.

---

## 📄 License

This project is developed for educational and administrative assistance purposes for government teachers in Bihar.
