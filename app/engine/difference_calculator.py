# difference_calculator.py - Logic for computing the difference (ADMISSIBLE - DRAWN)
from typing import Dict, List, Any, Optional
from app.models.monthly_salary import MonthlySalary
from app.config import FITMENT_MATRIX
from app.engine.increment_calculator import get_admissible_basic, get_designation_column_index, find_starting_step
from app.engine.admissible_calculator import calculate_admissible_for_month, post_process_professional_tax
from app.utils.number_to_words import convert_number_to_words


def compute_arrears(
    drawn_data: Dict[str, Dict[str, Any]],
    employee_info: Dict[str, Any],
    hra_rules: List[Dict[str, Any]],
    skip_joining_month: bool = True,
    da_rates: Optional[List[Dict[str, Any]]] = None,
    scope_start: Optional[str] = None,
    scope_end: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes differences for all months in drawn_data, detects months needing arrears,
    and returns a structured response with differences, totals, and words.
    """
    doj_str = employee_info.get("doj") or ""
    designation = employee_info.get("designation") or ""
    
    # 1. Map designation to column index
    column_idx = get_designation_column_index(designation)
    
    # 2. Extract drawn basic values to find starting step
    joining_basic_str = employee_info.get("joining_basic")
    joining_basic = int(joining_basic_str) if joining_basic_str and str(joining_basic_str).isdigit() else None
    
    drawn_basics = [m["basic"] for m in drawn_data.values() if m["basic"] > 0]
    starting_step = find_starting_step(drawn_basics, column_idx, joining_basic)
    
    # 3. Skip joining month if required
    # Extract month and year from DOJ
    joining_month_lbl = None
    if skip_joining_month and doj_str:
        try:
            # DOJ format DD-MM-YYYY
            parts = doj_str.split("-")
            month_num = int(parts[1])
            year_suffix = parts[2][-2:]
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            joining_month_lbl = f"{month_names[month_num-1]}-{year_suffix}"
        except Exception:
            pass
            
    # 4. Calculate standard admissible salary for each month first (without PT)
    admissible_months = {}
    
    for month_lbl, drawn in drawn_data.items():
        if skip_joining_month and month_lbl == joining_month_lbl:
            continue # skip joining month entirely
            
        # Parse month/year
        parts = month_lbl.split("-")
        month_name = parts[0]
        year = 2000 + int(parts[1])
        month_num = MONTH_TO_NUM_MAP[month_name]
        
        # Check scope filter (format: YYYY-MM)
        if scope_start and scope_end:
            month_str = f"{year}-{month_num:02d}"
            if not (scope_start <= month_str <= scope_end):
                continue
        
        # Calculate what the standard basic pay rate should have been for this calendar month
        std_basic_rate = get_admissible_basic(
            starting_step, column_idx, doj_str, year, month_num, joining_basic=joining_basic
        )
        
        # Check for LWP pro-ration ratio
        # Standard drawn basic pay rate for that month:
        # We can find what the drawn basic pay rate was supposed to be.
        # Usually it is drawn["basic"] but if pro-rated, we can get standard rate from fitment matrix
        # using the drawn basic as guide.
        # But wait! The simplest pro-ration ratio is:
        # Ratio = drawn["basic"] / standard_drawn_basic
        # Let's find which step the drawn basic matches.
        # If drawn["basic"] matches a step exactly, Ratio = 1.0
        # If it doesn't match any step exactly, we find the closest step in that column
        # and Ratio = drawn["basic"] / closest_step_basic
        column_values = [FITMENT_MATRIX_VALS[step][column_idx] for step in sorted(FITMENT_MATRIX_VALS.keys())]
        closest_std_basic = min(column_values, key=lambda x: abs(x - drawn["basic"]))
        
        # Avoid division by zero
        ratio = 1.0
        if drawn["basic"] > 0 and closest_std_basic > 0:
            if drawn["basic"] < closest_std_basic:
                # Pro-ration detected (LWP or partial month)
                ratio = drawn["basic"] / closest_std_basic
                
        # Calculate admissible values
        admissible_months[month_lbl] = calculate_admissible_for_month(
            month_lbl=month_lbl,
            financial_year=drawn["financial_year"],
            standard_basic_rate=std_basic_rate,
            hra_rules=hra_rules,
            pro_ration_ratio=ratio,
            da_rates=da_rates
        )
        
    # 5. Post-process PT for September
    admissible_months = post_process_professional_tax(admissible_months)
    
    # Also post-process PT for September in drawn data if not already present or if we want to be exact
    # The drawn data already contains the actual PT deducted as parsed from the PDF.
    
    # 6. Calculate differences
    arrear_months = []
    totals = {
        "basic": 0, "da": 0, "hra": 0, "ma": 0, "gross": 0,
        "nps": 0, "gis": 0, "net": 0
    }
    
    # Sort chronologically by calendar year and month
    def month_sort_key(month_lbl):
        parts = month_lbl.split("-")
        month_name = parts[0]
        year = 2000 + int(parts[1])
        month_num = MONTH_TO_NUM_MAP[month_name]
        return (year, month_num)
        
    sorted_months = sorted(admissible_months.keys(), key=month_sort_key)
    
    for month_lbl in sorted_months:
        adm = admissible_months[month_lbl]
        drn = drawn_data[month_lbl]
        
        diff = {
            "basic": adm["basic"] - drn["basic"],
            "da": adm["da"] - drn["da"],
            "hra": adm["hra"] - drn["hra"],
            "ma": adm["ma"] - drn["ma"],
            "gross": adm["gross"] - drn["gross"],
            "nps": adm["nps"] - drn["nps"],
            "gis": adm["gis"] - drn["gis"],
            "professional_tax": adm["professional_tax"] - drn["professional_tax"],
            "net": adm["net"] - drn["net"]
        }
        
        # If there's any difference, keep this regular month row
        if any(abs(v) > 0 for v in [diff["basic"], diff["da"], diff["hra"], diff["net"]]):
            arrear_months.append({
                "month_label": month_lbl,
                "admissible": adm,
                "drawn": drn,
                "difference": diff,
                "is_arrear_row": False
            })
            
            for key in totals.keys():
                totals[key] += diff[key]
                
        # If the employee drew an arrear bill in this month, add a dedicated Arrear Row right after
        arrear_val = drn.get("arrear_drawn", 0) or drn.get("arrear_net", 0)
        if arrear_val > 0:
            arr_gross = drn.get("arrear_gross", arrear_val)
            arr_nps = drn.get("arrear_nps", 0)
            arr_net = drn.get("arrear_net", arrear_val)
            
            arr_adm = {
                "days": 0, "basic": 0, "da": 0, "hra": 0, "ma": 0,
                "gross": 0, "nps": 0, "gis": 0, "professional_tax": 0, "net": 0
            }
            arr_drn = {
                "days": 0, "basic": arr_gross, "da": 0, "hra": 0, "ma": 0,
                "gross": arr_gross, "nps": arr_nps, "gis": 0, "professional_tax": 0, "net": arr_net
            }
            arr_diff = {
                "basic": -arr_gross, "da": 0, "hra": 0, "ma": 0,
                "gross": -arr_gross, "nps": -arr_nps, "gis": 0, "professional_tax": 0, "net": -arr_net
            }
            
            arrear_months.append({
                "month_label": f"{month_lbl} (Arrear)",
                "admissible": arr_adm,
                "drawn": arr_drn,
                "difference": arr_diff,
                "is_arrear_row": True
            })
            
            for key in totals.keys():
                totals[key] += arr_diff[key]
                
    # 7. Convert total net difference to words
    in_words = convert_number_to_words(totals["net"])
    
    return {
        "employee": employee_info,
        "starting_step": starting_step,
        "designation_category": get_designation_category_name(column_idx),
        "fitment_info": {
            "starting_step": starting_step,
            "designation_category": get_designation_category_name(column_idx),
            "basic_at_step": FITMENT_MATRIX[starting_step][column_idx]
        },
        "arrear_months": arrear_months,
        "totals": totals,
        "in_words": in_words
    }

# Helper mappings duplicated/imported from config for speed/safety
MONTH_TO_NUM_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

FITMENT_MATRIX_VALS = FITMENT_MATRIX

def get_designation_category_name(column_idx: int) -> str:
    categories = ["I-V", "VI-VIII", "Sr. VI-VIII", "IX-X", "XI-XII", "Sr. XI-XII"]
    return categories[column_idx] if column_idx < len(categories) else "I-V"
