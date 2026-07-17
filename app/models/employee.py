# employee.py - Pydantic models for Employee data and configuration
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class Employee(BaseModel):
    employee_id: str
    name: str
    designation: str
    designation_category: str  # Column name in fitment matrix, e.g. "XI-XII"
    pran: str                  # GPF/PRAN Number
    pan: str                   # PAN Number
    doj: str                   # Date of Joining, e.g., "16-11-2023"
    bank_account: Optional[str] = None
    ifsc: Optional[str] = None
    school_name: Optional[str] = None
    block_name: Optional[str] = None
    increment_month: str       # "July" or "January"

class HRARateEntry(BaseModel):
    from_month: str            # format: "YYYY-MM"
    to_month: str              # format: "YYYY-MM" (or "9999-12" for ongoing)
    rate_percent: float        # e.g., 4.0, 5.0, 7.5, 10.0
