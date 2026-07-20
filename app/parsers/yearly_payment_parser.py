# yearly_payment_parser.py - Parser for HRMS yearly payment statement PDF
import pdfplumber
import re
from typing import Dict, List, Any
from app.config import MONTH_TO_NUM

def parse_financial_year_from_header(header: str) -> tuple:
    """
    Parses a header like '2025-Mar' or '2026-Jan' and returns (month_name, year, financial_year).
    Returns None if not a valid header.
    """
    # Pattern to match YYYY-Mon or Mon-YY or YYYY-Month
    match = re.search(r"(\d{4})[-/]([A-Za-z]{3,})", header)
    if not match:
        # Try Mon-YY or similar
        match = re.search(r"([A-Za-z]{3,})[-/](\d{2,4})", header)
        if not match:
            return None
        month_name = match.group(1)[:3].capitalize()
        year_str = match.group(2)
        if len(year_str) == 2:
            year = 2000 + int(year_str)
        else:
            year = int(year_str)
    else:
        year = int(match.group(1))
        month_name = match.group(2)[:3].capitalize()
        
    if month_name not in MONTH_TO_NUM:
        return None
        
    # Determine financial year (Bihar financial year is March to February)
    if month_name in ["Jan", "Feb"]:
        fy_start = year - 1
        fy_end = year % 100
    else:
        fy_start = year
        fy_end = (year + 1) % 100
        
    fy_str = f"{fy_start}-{fy_end:02d}"
    return month_name, year, fy_str

def parse_yearly_payment(pdf_path: str) -> Dict[str, Any]:
    """
    Parses HRMS yearly payment statement PDF and extracts employee metadata and 12-month salary tables.
    """
    employee_info = {}
    monthly_data = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            raise ValueError("The PDF has no pages.")
            
        # 1. Parse employee metadata from Page 1 text
        p1_text = pdf.pages[0].extract_text()
        metadata_patterns = {
            "employee_id": [r"Employee ID\s*:\s*(\d+)"],
            "name": [r"Employee Name\s*:\s*(.*?)(?=\s+Current|$)"],
            "pran": [r"GPF/PRAN No\s*:\s*(\d+)", r"GPF/PRAN\s*:\s*(\d+)"],
            "pan": [r"PAN No\s*:\s*([A-Z0-9]+)", r"PAN\s*:\s*([A-Z0-9]+)"],
            "designation": [r"Designation\s*:\s*(.*?)(?=\s+Current|$)"],
        }
        
        for key, regexes in metadata_patterns.items():
            for r in regexes:
                match = re.search(r, p1_text, re.IGNORECASE)
                if match:
                    employee_info[key] = match.group(1).strip()
                    break
        
        # 2. Parse all tables across the pages
        # First, find the headers from Page 2 Table 1 or Page 1 Table 1 (usually page 2 table 1 is the header row)
        headers = []
        month_mappings = {} # maps column index in tables to (month_label, fy)
        
        for page_idx, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                # Look for a header table (contains columns starting with years, like 2025-Mar)
                for row in table:
                    if len(row) >= 2:
                        # Check if columns are month headers
                        parsed_headers = []
                        valid_headers_count = 0
                        for col_idx, col in enumerate(row[1:], start=1):
                            if col and str(col).strip():
                                parsed = parse_financial_year_from_header(col.strip())
                                if parsed:
                                    parsed_headers.append((col_idx, parsed))
                                    valid_headers_count += 1
                        
                        if valid_headers_count >= 1: # Header row found (works even for partial/ongoing financial year)
                            for col_idx, (m_name, year, fy) in parsed_headers:
                                month_label = f"{m_name}-{str(year)[2:]}"
                                month_mappings[col_idx] = {
                                    "month_label": month_label,
                                    "fy": fy,
                                    "month_name": m_name,
                                    "year": year
                                }
                            break
            if month_mappings:
                break
                
        if not month_mappings:
            raise ValueError(f"Could not find month headers in the PDF {pdf_path}.")
            
        # Initialize monthly data dictionary
        for info in month_mappings.values():
            monthly_data[info["month_label"]] = {
                "month_label": info["month_label"],
                "financial_year": info["fy"],
                "days": 30, # default, will be overwritten by attendance if available, or calendar days
                "basic": 0,
                "da": 0,
                "hra": 0,
                "ma": 0,
                "gross": 0,
                "nps": 0,
                "gis": 0,
                "professional_tax": 0,
                "net": 0,
                "arrear_drawn": 0
            }
            
        # 3. Extract salary components from all tables
        # Map table row descriptions to components
        row_mappings = {
            "basic": ["basic pay", "basic"],
            "da": ["dearness allowance", "dearness"],
            "hra": ["house rent allowance", "house rent"],
            "ma": ["medical allowance", "medical"],
            "gross": ["total earning", "total gross", "grossamount"],
            "nps": ["nps contribution", "nps"],
            "gis": ["gis state", "gis"],
            "professional_tax": ["professional tax", "professiona", "prof tax"],
            "net": ["total net", "net amount", "netamount"]
        }
        
        # We will loop through all tables and search for rows matching these keys
        for page in pdf.pages:
            page_text = (page.extract_text() or "").lower()
            is_other_detail_page = "other payment detail" in page_text or "other bill" in page_text
            
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 2:
                        continue
                    row_name = row[0]
                    if not row_name:
                        continue
                    row_name_clean = re.sub(r'\s+', ' ', row_name).strip().lower()
                    
                    if is_other_detail_page:
                        # Detect arrear component (da, basic, hra) from table context
                        arr_comp = "da"
                        table_str = str(table).lower()
                        if "da" in table_str or "dearness" in table_str:
                            arr_comp = "da"
                        elif "salary" in table_str or "basic" in table_str:
                            arr_comp = "basic"
                        elif "hra" in table_str or "house rent" in table_str:
                            arr_comp = "hra"
                            
                        # Extract arrear drawn, gross, and nps from Other Payment Detail section
                        for col_idx, info in month_mappings.items():
                            if col_idx < len(row):
                                val_str = row[col_idx]
                                if val_str is not None:
                                    val_clean = re.sub(r'[^\d]', '', val_str)
                                    val = int(val_clean) if val_clean else 0
                                    if val > 0:
                                        monthly_data[info["month_label"]]["arrear_component"] = arr_comp
                                        if "gross" in row_name_clean:
                                            monthly_data[info["month_label"]]["arrear_gross"] = val
                                        elif "deduction" in row_name_clean or "nps" in row_name_clean:
                                            monthly_data[info["month_label"]]["arrear_nps"] = val
                                        elif "total other" in row_name_clean or "net" in row_name_clean:
                                            monthly_data[info["month_label"]]["arrear_net"] = val
                                            monthly_data[info["month_label"]]["arrear_drawn"] = val
                    else:
                        # Regular PayBill components
                        matched_key = None
                        for key, keywords in row_mappings.items():
                            if any(kw in row_name_clean for kw in keywords):
                                matched_key = key
                                break
                                
                        if matched_key:
                            for col_idx, info in month_mappings.items():
                                if col_idx < len(row):
                                    val_str = row[col_idx]
                                    if val_str is not None:
                                        # Remove commas or spaces, extract integer
                                        val_clean = re.sub(r'[^\d]', '', val_str)
                                        val = int(val_clean) if val_clean else 0
                                        monthly_data[info["month_label"]][matched_key] = val

    # Verify if gross or net is zero for some months, meaning they didn't get paid (we shouldn't process them)
    filtered_monthly_data = {}
    for month_lbl, data in monthly_data.items():
        if data["basic"] > 0 or data["gross"] > 0:
            filtered_monthly_data[month_lbl] = data
            
    return {
        "employee": employee_info,
        "monthly_data": filtered_monthly_data
    }

if __name__ == "__main__":
    import json
    import sys
    test_path = "/Volumes/Eternal T7/Project ARREAR/ Input of 1 teacher/employee_yearly_payment_detail (4).pdf"
    try:
        res = parse_yearly_payment(test_path)
        print("Success! Employee info:")
        print(json.dumps(res["employee"], indent=2))
        print(f"Extracted {len(res['monthly_data'])} months of data:")
        for m, data in sorted(res["monthly_data"].items()):
            print(f"  {m}: Basic={data['basic']}, DA={data['da']}, HRA={data['hra']}, Net={data['net']}")
    except Exception as e:
        print("Failed:", e)
        import traceback
        traceback.print_exc()
