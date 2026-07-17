# admissible_calculator.py - Logic for calculating admissible salary details
import calendar
from typing import Dict, Any, List
from datetime import date
from app.config import DA_RATES, MA_FIXED, GIS_FIXED, MONTH_TO_NUM
from app.models.monthly_salary import MonthlySalary

def get_da_rate_for_date(year: int, month: int) -> float:
    """
    Looks up the DA rate for a given calendar month and year from the DA schedule.
    Defaults to the last rate in the schedule if date is beyond the schedule.
    """
    date_str = f"{year}-{month:02d}"
    for entry in DA_RATES:
        if entry["from"] <= date_str <= entry["to"]:
            return entry["rate"]
    
    # Fallback to the latest known rate
    return DA_RATES[-1]["rate"]

def get_hra_rate_for_date(hra_rules: List[Dict[str, Any]], year: int, month: int) -> float:
    """
    Looks up the user-defined HRA rate for a given calendar month and year.
    Defaults to 0.04 (4%) if not found in rules.
    """
    date_str = f"{year}-{month:02d}"
    for rule in hra_rules:
        # Support both 'from'/'to' and 'from_month'/'to_month' formats
        from_m = rule.get("from") or rule.get("from_month")
        to_m = rule.get("to") or rule.get("to_month") or "9999-12"
        rate = rule.get("rate") or rule.get("rate_percent") or 4.0
        
        # Convert percent to decimal (e.g. 7.5 -> 0.075)
        if rate > 1.0:
            rate = rate / 100.0
            
        if from_m <= date_str <= to_m:
            return rate
            
    # Default fallback
    return 0.04

def calculate_pt_for_gross(annual_gross: float) -> int:
    """
    Calculates Professional Tax (PT) based on annual gross income slab.
    """
    if annual_gross <= 300000:
        return 0
    elif annual_gross <= 500000:
        return 1000
    elif annual_gross <= 1000000:
        return 2000
    else:
        return 2500

def parse_month_year(month_lbl: str) -> tuple:
    """
    Parses 'Mar-24' into (year, month_num).
    """
    parts = month_lbl.split("-")
    month_name = parts[0]
    year_suffix = parts[1]
    month_num = MONTH_TO_NUM[month_name]
    year = 2000 + int(year_suffix)
    return year, month_num

def calculate_admissible_for_month(
    month_lbl: str,
    financial_year: str,
    standard_basic_rate: int,
    hra_rules: List[Dict[str, Any]],
    pro_ration_ratio: float = 1.0
) -> Dict[str, Any]:
    """
    Calculates admissible salary components for a given month.
    Does NOT calculate PT and Net yet (PT depends on annual gross pay).
    """
    year, month_num = parse_month_year(month_lbl)
    _, total_days = calendar.monthrange(year, month_num)
    
    # 1. Get rates
    da_rate = get_da_rate_for_date(year, month_num)
    hra_rate = get_hra_rate_for_date(hra_rules, year, month_num)
    
    # 2. Calculate standard rates
    basic_std = standard_basic_rate
    da_std = int(basic_std * da_rate)
    hra_std = int(basic_std * hra_rate)
    ma_std = MA_FIXED
    
    # 3. Apply pro-ration ratio (LWP)
    basic_adm = int(basic_std * pro_ration_ratio)
    da_adm = int(basic_adm * da_rate)
    hra_adm = int(basic_adm * hra_rate)
    ma_adm = int(ma_std * pro_ration_ratio)
    
    gross_adm = basic_adm + da_adm + hra_adm + ma_adm
    nps_adm = int((basic_adm + da_adm) * 0.10)
    gis_adm = GIS_FIXED
    
    paid_days = int(round(pro_ration_ratio * total_days))
    
    return {
        "month_label": month_lbl,
        "financial_year": financial_year,
        "days": paid_days,
        "basic": basic_adm,
        "da": da_adm,
        "hra": hra_adm,
        "ma": ma_adm,
        "gross": gross_adm,
        "nps": nps_adm,
        "gis": gis_adm,
        "professional_tax": 0,  # calculated later
        "net": gross_adm - nps_adm - gis_adm # calculated without PT first
    }

def post_process_professional_tax(
    monthly_salaries: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Groups months by financial year, calculates annual gross pay,
    determines PT for September, and subtracts it from September Net Pay.
    """
    # Group by financial year
    fy_groups = {}
    for month_lbl, data in monthly_salaries.items():
        fy = data["financial_year"]
        if fy not in fy_groups:
            fy_groups[fy] = []
        fy_groups[fy].append(data)
        
    for fy, months in fy_groups.items():
        # Calculate total annual gross pay for this FY
        annual_gross = sum(m["gross"] for m in months)
        pt_amount = calculate_pt_for_gross(annual_gross)
        
        # Apply PT to September month of this FY if it exists in the list
        for m in months:
            month_name = m["month_label"].split("-")[0]
            if month_name == "Sep":
                m["professional_tax"] = pt_amount
                m["net"] = m["gross"] - m["nps"] - m["gis"] - pt_amount
                
    return monthly_salaries
