from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.config import RULES_WORKBOOK_PATH

THIN = Side(style="thin", color="000000")
DOUBLE = Side(style="double", color="000000")
TITLE_FILL = PatternFill("solid", fgColor="203A43")
GLOSSARY_FILL = PatternFill("solid", fgColor="FFF4D6")
HEADER_FILL = PatternFill("solid", fgColor="9AD1D4")
INPUT_FILL = PatternFill("solid", fgColor="E8F3F1")
OUTPUT_FILL = PatternFill("solid", fgColor="FFF0E1")
RULE_ODD_FILL = PatternFill("solid", fgColor="FFFFFF")
RULE_EVEN_FILL = PatternFill("solid", fgColor="F7FAFC")
TITLE_FONT = Font(bold=True, color="FFFFFF", size=12)
HEADER_FONT = Font(bold=True, color="16324F")
BODY_ALIGNMENT = Alignment(vertical="center", wrap_text=True)
TITLE_ALIGNMENT = Alignment(vertical="center", horizontal="left")


def _apply_table_border(cell, *, left: Side | None = None, right: Side | None = None, top: Side | None = None, bottom: Side | None = None) -> None:
    current = cell.border
    cell.border = Border(
        left=left or current.left,
        right=right or current.right,
        top=top or current.top,
        bottom=bottom or current.bottom,
    )


def _write_table(sheet, start_row: int, title: str, inputs: list[str], outputs: list[str], rules: list[list[object]]) -> int:
    start_col = 1
    title_cell = sheet.cell(row=start_row, column=start_col, value=title)
    title_cell.font = TITLE_FONT
    title_cell.fill = TITLE_FILL
    title_cell.alignment = TITLE_ALIGNMENT

    header_row = start_row + 1
    headings = ["U", *inputs, *outputs]
    divider_col = 1 + len(inputs)

    for index, heading in enumerate(headings, start=start_col):
        cell = sheet.cell(row=header_row, column=index, value=heading)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL if index == start_col else (INPUT_FILL if index <= divider_col else OUTPUT_FILL)
        cell.alignment = BODY_ALIGNMENT
        _apply_table_border(cell, top=THIN, bottom=DOUBLE)
        if index == divider_col:
            _apply_table_border(cell, right=DOUBLE)
        if index == divider_col + 1:
            _apply_table_border(cell, left=DOUBLE)

    for row_offset, rule in enumerate(rules, start=2):
        for col_offset, value in enumerate(rule, start=0):
            cell = sheet.cell(row=start_row + row_offset, column=start_col + col_offset, value=value)
            cell.fill = RULE_ODD_FILL if row_offset % 2 == 0 else RULE_EVEN_FILL
            cell.alignment = BODY_ALIGNMENT
            _apply_table_border(cell, top=THIN, bottom=THIN, left=THIN, right=THIN)
            if start_col + col_offset == divider_col:
                _apply_table_border(cell, right=DOUBLE)
            if start_col + col_offset == divider_col + 1:
                _apply_table_border(cell, left=DOUBLE)
    return start_row + len(rules) + 3


def _build_glossary(sheet) -> None:
    rows = [
        ("Glossary Salary Engine", "Business Concept", "Attribute"),
        ("Variable", "Business Concept", "Attribute"),
        ("Employee ID", "Employee", "employee_id"),
        ("Employee Name", None, "employee_name"),
        ("CTC", None, "ctc"),
        ("CCA", None, "cca"),
        ("PF Option", None, "pf_option"),
        ("Professional Tax", None, "professional_tax"),
        ("Employee PF Override", None, "employee_pf_override"),
        ("Validation Message", "Validation", "message"),
        ("Basic", "Salary", "basic"),
        ("HalfSum", None, "half_sum"),
        ("Basic for Statutory", None, "basic_for_statutory"),
        ("HRA", None, "hra"),
        ("Bonus", None, "bonus"),
        ("Employee PF", None, "employee_pf"),
        ("Employer PF", None, "employer_pf"),
        ("Employee ESI", None, "employee_esi"),
        ("Employer ESI", None, "employer_esi"),
        ("Medical Insurance", None, "medical_insurance"),
        ("Gratuity", None, "gratuity"),
        ("Gross", None, "gross"),
        ("Tax Before Rebate", "Tax", "tax_before_rebate"),
        ("Tax After Rebate", None, "tax_after_rebate"),
        ("Surcharge Multiplier", None, "surcharge_multiplier"),
        ("TDS", None, "tds"),
        ("Special", "Final", "special"),
        ("Take Home", None, "take_home"),
        ("CTC with CCA", None, "ctc_with_cca"),
        ("Gross with CCA", None, "gross_with_cca"),
    ]

    for row_index, row in enumerate(rows, start=1):
        for col_index, value in enumerate(row, start=1):
            cell = sheet.cell(row=row_index, column=col_index, value=value)
            cell.alignment = BODY_ALIGNMENT
            if row_index == 1:
                cell.fill = TITLE_FILL
                cell.font = TITLE_FONT
            elif row_index == 2:
                cell.fill = GLOSSARY_FILL
                cell.font = HEADER_FONT
            else:
                cell.fill = RULE_ODD_FILL if row_index % 2 else RULE_EVEN_FILL
    for cell in sheet[2]:
        cell.font = HEADER_FONT


def _autosize_sheet(sheet) -> None:
    for column in sheet.columns:
        values = [str(cell.value) for cell in column if cell.value is not None]
        if not values:
            continue
        width = min(max(len(value) for value in values) + 4, 38)
        sheet.column_dimensions[get_column_letter(column[0].column)].width = width
    sheet.freeze_panes = "A2"


def build_rules_workbook(path: Path = RULES_WORKBOOK_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()

    glossary = workbook.active
    glossary.title = "Glossary"
    _build_glossary(glossary)
    glossary.sheet_view.showGridLines = False
    glossary.sheet_properties.tabColor = "203A43"

    validations = workbook.create_sheet("01 Validation")
    validations.sheet_view.showGridLines = False
    validations.sheet_properties.tabColor = "8ECAE6"
    row = 1
    row = _write_table(
        validations,
        row,
        "Validation Checks",
        ["CTC", "CCA", "Professional Tax", "PF Option", "Employee PF Override"],
        ["Validation Message"],
        [
            ["1", "-", "-", "-", "-", "-", '""'],
            ["2", "-", "-", "-", "-", "-", '""'],
        ],
    )

    components = workbook.create_sheet("02 Components")
    components.sheet_view.showGridLines = False
    components.sheet_properties.tabColor = "2A9D8F"
    row = 1
    row = _write_table(
        components,
        row,
        "Basic Salary",
        ["CTC"],
        ["Basic"],
        [
            ["1", "[15000..25000]", "decimal(Employee.ctc * 0.5, 0)"],
            ["2", "[25001..35000]", "22000"],
            ["3", "[35001..45000]", "22500"],
            ["4", "-", "decimal(Employee.ctc * 0.5, 0)"],
        ],
    )
    row = _write_table(
        components,
        row,
        "Statutory Basic",
        ["Basic", "CTC", "CCA"],
        ["HalfSum", "Basic for Statutory"],
        [
            ["1", "-", "-", "-", "decimal((Employee.ctc + Employee.cca) / 2, 0)", "decimal(max(Salary.basic, Salary.half_sum), 0)"],
            ["2", "-", "-", "-", "decimal((Employee.ctc + Employee.cca) / 2, 0)", "decimal(max(Salary.basic, Salary.half_sum), 0)"],
        ],
    )
    row = _write_table(
        components,
        row,
        "HRA Rule",
        ["CTC", "Basic"],
        ["HRA"],
        [
            ["1", "[25001..45000]", "-", "0"],
            ["2", "-", "-", "decimal(Salary.basic * 0.5, 0)"],
        ],
    )
    row = _write_table(
        components,
        row,
        "Bonus Rule",
        ["Basic for Statutory"],
        ["Bonus"],
        [
            ["1", "<= 21000", "decimal(Salary.basic_for_statutory * 0.0833, 0)"],
            ["2", "> 21000", "0"],
        ],
    )
    row = _write_table(
        components,
        row,
        "PF Rule",
        ["PF Option", "Basic for Statutory", "Employee PF Override"],
        ["Employee PF", "Employer PF"],
        [
            ["1", '"P1"', "-", "-", "0", "0"],
            ["2", '"P2"', "-", "-", "1800", "1800"],
            ["3", '"P3"', "-", "-", "decimal(Salary.basic_for_statutory * 0.12, 0)", "decimal(Salary.basic_for_statutory * 0.12, 0)"],
            ["4", '"P4"', "-", "-", "decimal(min(Salary.basic_for_statutory * 0.12, 1800), 0)", "decimal(min(Salary.basic_for_statutory * 0.12, 1800), 0)"],
            ["5", '"P5"', "-", "-", "decimal(Employee.employee_pf_override, 0)", "1800"],
        ],
    )
    row = _write_table(
        components,
        row,
        "ESI Rule",
        ["Basic for Statutory"],
        ["Employee ESI", "Employer ESI"],
        [
            ["1", "<= 21000", "decimal(Salary.basic_for_statutory * 0.0075, 0)", "decimal(Salary.basic_for_statutory * 0.0325, 0)"],
            ["2", "> 21000", "0", "0"],
        ],
    )
    row = _write_table(
        components,
        row,
        "Medical Insurance Rule",
        ["Basic for Statutory"],
        ["Medical Insurance"],
        [
            ["1", "<= 21000", "0"],
            ["2", "> 21000", "250"],
        ],
    )
    row = _write_table(
        components,
        row,
        "Gratuity Rule",
        ["Basic"],
        ["Gratuity"],
        [
            ["1", "-", "decimal(Salary.basic * 0.05, 0)"],
            ["2", "-", "decimal(Salary.basic * 0.05, 0)"],
        ],
    )
    row = _write_table(
        components,
        row,
        "Gross Rule",
        ["CTC", "Employer PF", "Employer ESI", "Gratuity"],
        ["Gross"],
        [
            ["1", "-", "-", "-", "-", "decimal(Employee.ctc - Salary.employer_pf - Salary.employer_esi - Salary.gratuity, 0)"],
            ["2", "-", "-", "-", "-", "decimal(Employee.ctc - Salary.employer_pf - Salary.employer_esi - Salary.gratuity, 0)"],
        ],
    )

    tax = workbook.create_sheet("03 Tax")
    tax.sheet_view.showGridLines = False
    tax.sheet_properties.tabColor = "E76F51"
    row = 1
    row = _write_table(
        tax,
        row,
        "Tax Slab",
        ["Gross"],
        ["Tax Before Rebate"],
        [
            ["1", "< 33333", "0"],
            ["2", "[33333..66666]", "decimal(Salary.gross * 0.05, 0)"],
            ["3", "(66666..100000]", "decimal(Salary.gross * 0.10, 0)"],
            ["4", "(100000..133333]", "decimal(Salary.gross * 0.15, 0)"],
            ["5", "(133333..166666]", "decimal(Salary.gross * 0.20, 0)"],
            ["6", "(166666..200000]", "decimal(Salary.gross * 0.25, 0)"],
            ["7", "> 200000", "decimal(Salary.gross * 0.30, 0)"],
        ],
    )
    row = _write_table(
        tax,
        row,
        "Tax Rebate",
        ["Gross", "Tax Before Rebate"],
        ["Tax After Rebate"],
        [
            ["1", "<= 100000", "-", "decimal(max(Tax.tax_before_rebate - 5000, 0), 0)"],
            ["2", "> 100000", "-", "decimal(Tax.tax_before_rebate, 0)"],
        ],
    )
    row = _write_table(
        tax,
        row,
        "Tax Surcharge",
        ["Gross"],
        ["Surcharge Multiplier"],
        [
            ["1", "< 416667", "1"],
            ["2", "[416667..833333]", "1.1"],
            ["3", "(833333..1666667]", "1.15"],
            ["4", "> 1666667", "1.25"],
        ],
    )
    row = _write_table(
        tax,
        row,
        "Final TDS",
        ["Tax After Rebate", "Surcharge Multiplier"],
        ["TDS"],
        [
            ["1", "-", "-", "decimal(Tax.tax_after_rebate * Tax.surcharge_multiplier * 1.04, 0)"],
            ["2", "-", "-", "decimal(Tax.tax_after_rebate * Tax.surcharge_multiplier * 1.04, 0)"],
        ],
    )

    finals = workbook.create_sheet("04 Final")
    finals.sheet_view.showGridLines = False
    finals.sheet_properties.tabColor = "F4A261"
    row = 1
    row = _write_table(
        finals,
        row,
        "Final Salary Outputs",
        [
            "Gross",
            "Basic",
            "HRA",
            "Bonus",
            "Employee PF",
            "Employee ESI",
            "Professional Tax",
            "TDS",
            "CCA",
            "Medical Insurance",
            "CTC",
        ],
        ["Special", "Take Home", "CTC with CCA", "Gross with CCA"],
        [
            [
                "1",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                "decimal(Salary.gross - Salary.basic - Salary.hra - Salary.bonus, 0)",
                "decimal(Salary.gross - Salary.employee_pf - Salary.employee_esi - Employee.professional_tax - Tax.tds + Employee.cca - Salary.medical_insurance, 0)",
                "decimal(Employee.ctc + Employee.cca, 0)",
                "decimal(Salary.gross + Employee.cca, 0)",
            ],
            [
                "2",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
                "decimal(Salary.gross - Salary.basic - Salary.hra - Salary.bonus, 0)",
                "decimal(Salary.gross - Salary.employee_pf - Salary.employee_esi - Employee.professional_tax - Tax.tds + Employee.cca - Salary.medical_insurance, 0)",
                "decimal(Employee.ctc + Employee.cca, 0)",
                "decimal(Salary.gross + Employee.cca, 0)",
            ],
        ],
    )

    for sheet in workbook.worksheets:
        _autosize_sheet(sheet)

    workbook.save(path)
    return path
