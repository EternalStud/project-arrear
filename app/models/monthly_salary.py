# monthly_salary.py - Monthly salary data structures
from pydantic import BaseModel

class MonthlySalary(BaseModel):
    month_label: str       # format: "Mar-24", "Apr-24", etc.
    financial_year: str    # format: "2024-25"
    days: int              # Number of paid days
    basic: int
    da: int
    hra: int
    ma: int
    gross: int
    nps: int
    gis: int
    professional_tax: int = 0
    net: int
