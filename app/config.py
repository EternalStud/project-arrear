# config.py - System Configurations, DA & HRA Rates, and Fitment Matrix

# DA Rate Schedule - Bihar Government
DA_RATES = [
    {"from": "2023-01", "to": "2023-12", "rate": 0.46},
    {"from": "2024-01", "to": "2024-06", "rate": 0.50},
    {"from": "2024-07", "to": "2024-12", "rate": 0.53},
    {"from": "2025-01", "to": "2025-06", "rate": 0.55},
    {"from": "2025-07", "to": "2025-12", "rate": 0.58},
    {"from": "2026-01", "to": "2026-06", "rate": 0.60},
]

# Common HRA presets offered in the frontend UI
HRA_PRESETS = {
    "4% → 5%": [
        {"from": "2020-01", "to": "2023-12", "rate_percent": 4.0},
        {"from": "2024-01", "to": "9999-12", "rate_percent": 5.0},
    ],
    "7.5% → 10%": [
        {"from": "2020-01", "to": "2023-12", "rate_percent": 7.5},
        {"from": "2024-01", "to": "9999-12", "rate_percent": 10.0},
    ],
    "4% → 7.5% → 10% (corrected joiner)": [
        {"from": "2020-01", "to": "2023-12", "rate_percent": 7.5},
        {"from": "2024-01", "to": "9999-12", "rate_percent": 10.0},
    ],
}

# Fixed values
MA_FIXED = 1000      # Medical Allowance
GIS_FIXED = 30       # GIS contribution
NPS_EMPLOYEE_RATE = 0.10  # 10% of (Basic + DA)

# Fitment Matrix for School Teachers
# Layout of values list per step:
# Index 0: Category I-V (Primary)
# Index 1: Category VI-VIII (Middle)
# Index 2: Category Senior VI-VIII (Senior Middle)
# Index 3: Category IX-X (Secondary)
# Index 4: Category XI-XII (Higher Secondary)
# Index 5: Category Senior XI-XII (Senior Higher Secondary)
FITMENT_MATRIX = {
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

# Designation mapping to fitment column index
DESIGNATION_COLUMN_MAP = {
    "Exclusive Teacher (1-5)": 0,
    "School Teacher(1-5)": 0,
    "School Teacher(6-8)": 1,
    "Senior School Teacher(6-8)": 2,
    "School Teacher(9-10)": 3,
    "School Teacher(11-12)": 4,
    "Senior School Teacher(11-12)": 5,
}

# Month ordering for a financial year (March to February)
FY_MONTH_ORDER = ["Mar", "Apr", "May", "Jun", "Jul", "Aug",
                   "Sep", "Oct", "Nov", "Dec", "Jan", "Feb"]

# Map of month abbreviations to calendar month numbers
MONTH_TO_NUM = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}
