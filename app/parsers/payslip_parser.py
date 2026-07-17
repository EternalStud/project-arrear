# payslip_parser.py - Parser for HRMS single-page Pay Slip PDF
import pdfplumber
import re
from typing import Dict, Any

def parse_payslip(pdf_path: str) -> Dict[str, Any]:
    """
    Parses a single-page HRMS Pay Slip PDF.
    Extracts employee identification, DOJ, bank details, designation, and current rates.
    """
    extracted_data = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            raise ValueError("The PDF has no pages.")
        
        text = pdf.pages[0].extract_text()
        if not text:
            raise ValueError("Could not extract text from the pay slip PDF.")
        
        # Regex mappings for employee metadata
        patterns = {
            "employee_id": [r"Employee Code\s*:\s*(\d+)", r"Employee ID\s*:\s*(\d+)"],
            "doj": [r"DOJ\s*:\s*([\d-]+)"],
            "name": [r"Employee Name\s*:\s*(.*?)(?=\s+(?:GPF/PRAN|GPF|PAN|DOJ|Bank|$))"],
            "pran": [r"(?:GPF/PRAN|GPF|PRAN)\s*:\s*(\d+)"],
            "bank_account": [r"Bank A/C\s*:\s*(\d+)", r"Account No\s*:\s*(\d+)"],
            "ifsc": [r"IFSC Code\s*:\s*([A-Z0-9]+)", r"IFSC\s*:\s*([A-Z0-9]+)"],
            "pan": [r"PAN\s*:\s*([A-Z0-9]+)"],
            "basic_rate": [r"Basic Rate\s*:\s*(\d+)"],
            "designation": [r"Designation\s*:\s*(.*?)(?=\s*(?:Teachers|Grade|Type|Current|$))"],
        }
        
        for key, regexes in patterns.items():
            value = None
            for r in regexes:
                match = re.search(r, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    break
            extracted_data[key] = value

        # In case Designation spans multiple lines or has extra characters, clean it up
        if extracted_data.get("designation"):
            # strip trailing/leading spaces and newlines
            extracted_data["designation"] = re.sub(r'\s+', ' ', extracted_data["designation"]).strip()
            
    return extracted_data

if __name__ == "__main__":
    # Test on the local file
    import sys
    test_path = "/Volumes/Eternal T7/Project ARREAR/ Input of 1 teacher/Pay-slip.pdf"
    try:
        res = parse_payslip(test_path)
        print("Success:")
        for k, v in res.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print("Failed:", e)
