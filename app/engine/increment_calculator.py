# increment_calculator.py - Logic for Basic Pay increments and fitment matrix lookup
from datetime import datetime, date
from typing import Dict, Any, List
from app.config import FITMENT_MATRIX, DESIGNATION_COLUMN_MAP

def get_designation_column_index(designation: str) -> int:
    """
    Returns the fitment matrix column index for a given designation.
    Defaults to 0 (I-V) if designation not found.
    """
    # Clean designation string to make match robust
    cleaned = (designation or "").strip()
    # Check exact match
    if cleaned in DESIGNATION_COLUMN_MAP:
        return DESIGNATION_COLUMN_MAP[cleaned]
    
    # Check partial match
    for desc, idx in DESIGNATION_COLUMN_MAP.items():
        if desc.lower() in cleaned.lower() or cleaned.lower() in desc.lower():
            return idx
            
    # Default fallback
    return 0

def find_starting_step(drawn_basic_values: List[int], column_idx: int, joining_basic: int = None) -> int:
    """
    Finds the starting step (1-20) in the fitment matrix by matching drawn basic values
    or the explicitly provided joining basic with the values in the specified column index.
    """
    column_values = [FITMENT_MATRIX[step][column_idx] for step in sorted(FITMENT_MATRIX.keys())]
    
    if joining_basic:
        # Check exact match for the provided joining basic
        if joining_basic in column_values:
            return column_values.index(joining_basic) + 1
        # Fallback to closest match if not exact
        closest_val = min(column_values, key=lambda x: abs(x - joining_basic))
        return column_values.index(closest_val) + 1
    
    # Try to find a exact match in drawn basics
    for val in drawn_basic_values:
        if val in column_values:
            return column_values.index(val) + 1
            
    # Fallback: check if any drawn basic is close to a step
    for val in drawn_basic_values:
        # Avoid zero or very small values (like partial months)
        if val < 10000:
            continue
        for step, step_vals in FITMENT_MATRIX.items():
            step_val = step_vals[column_idx]
            # If within 2%, it's likely this step
            if abs(val - step_val) / step_val < 0.02:
                return step
                
    return 1 # default to Step 1

def determine_increment_month(doj_str: str) -> str:
    """
    Determines if increment is in July or January based on DOJ.
    - DOJ between July 1 and Dec 31: July increment.
    - DOJ between Jan 1 and June 30: January increment.
    """
    try:
        # DOJ format is usually DD-MM-YYYY
        doj_date = datetime.strptime(doj_str, "%d-%m-%Y").date()
    except Exception:
        try:
            # Try YYYY-MM-DD
            doj_date = datetime.strptime(doj_str, "%Y-%m-%d").date()
        except Exception:
            # Fallback
            return "July"
            
    if 7 <= doj_date.month <= 12:
        return "July"
    else:
        return "January"

def get_admissible_basic(
    starting_step: int,
    column_idx: int,
    doj_str: str,
    target_year: int,
    target_month: int,
    joining_basic: int = None
) -> int:
    """
    Calculates the correct admissible Basic Pay rate for a target month and year,
    applying the annual 3% increment rule using the fitment matrix steps.
    """
    try:
        doj_date = datetime.strptime(doj_str, "%d-%m-%Y").date()
    except Exception:
        try:
            doj_date = datetime.strptime(doj_str, "%Y-%m-%d").date()
        except Exception:
            doj_date = date(2023, 11, 16) # Fallback to default
            
    increment_month_num = 7 if 7 <= doj_date.month <= 12 else 1
    
    # Calculate how many increments have passed since joining
    # Increment happens on July/January of each year after joining.
    # For example, if DOJ is Nov 2023, increments happen on:
    # - July 2024 (Step 2)
    # - July 2025 (Step 3)
    # - July 2026 (Step 4)
    # etc.
    
    current_step = starting_step
    target_date = date(target_year, target_month, 1)
    
    # Traverse year by year from DOJ year to target year
    current_year = doj_date.year
    while True:
        # Date of next increment
        # If DOJ is Nov 2023, next increment is July 2024
        # If DOJ is March 2024, next increment is Jan 2025 (actually next year Jan)
        # Wait, if DOJ is Jan-Jun, the increment is in January of next year?
        # Let's clarify: does the increment happen in the very next January/July,
        # or after 1 year of service?
        # Typically, a teacher gets their first increment after completing 6 months or in the next cycle.
        # In Bihar, new joiners get their first increment in the next July (for Jul-Dec group)
        # or next January (for Jan-Jun group).
        # Let's verify for Zafar Ali: Joined Nov 2023. First increment drawn in July 2024. That is next July!
        # So yes, the increment happens on July/Jan of the next calendar year.
        
        inc_year = current_year
        # If DOJ is in Nov (increment July), the next increment is in July of the following year
        if increment_month_num == 7 and doj_date.month >= 7:
            inc_year = current_year + 1
        elif increment_month_num == 1:
            inc_year = current_year + 1
            
        next_increment_date = date(inc_year, increment_month_num, 1)
        
        if next_increment_date > target_date:
            break
            
        current_step += 1
        current_year = inc_year
        
    if joining_basic:
        # Dynamically calculate by adding 3% each increment, rounded to nearest 10
        basic = joining_basic
        num_increments = current_step - starting_step
        for _ in range(num_increments):
            basic = round((basic * 1.03) / 10) * 10
        return basic
    else:
        # Cap step at max (20)
        current_step = min(current_step, 20)
        
        # Lookup in fitment matrix
        return FITMENT_MATRIX[current_step][column_idx]
