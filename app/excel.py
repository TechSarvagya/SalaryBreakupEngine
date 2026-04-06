from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font

from app.config import EMPLOYEE_TEMPLATE_PATH

INPUT_COLUMNS = [
    "Employee ID",
    "Employee Name",
    "CTC",
    "CCA",
    "PF Option",
    "Professional Tax",
    "Employee PF Override",
]


def ensure_employee_template() -> None:
    EMPLOYEE_TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if EMPLOYEE_TEMPLATE_PATH.exists():
        return

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Employees"
    for col, heading in enumerate(INPUT_COLUMNS, start=1):
        cell = sheet.cell(row=1, column=col, value=heading)
        cell.font = Font(bold=True)
    workbook.save(EMPLOYEE_TEMPLATE_PATH)


def dataframe_to_workbook_bytes(dataframe: pd.DataFrame, sheet_name: str = "Results") -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name=sheet_name)
    buffer.seek(0)
    return buffer.getvalue()


def read_employee_workbook(path: Path) -> pd.DataFrame:
    return pd.read_excel(path)
