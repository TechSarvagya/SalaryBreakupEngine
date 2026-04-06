from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RULES_DIR = DATA_DIR / "rules"
TEMPLATES_DIR = DATA_DIR / "templates"
OUTPUT_DIR = DATA_DIR / "outputs"

RULES_WORKBOOK_PATH = RULES_DIR / "salary_rules.xlsx"
EMPLOYEE_TEMPLATE_PATH = TEMPLATES_DIR / "employee_input_template.xlsx"
