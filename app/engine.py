from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from uuid import uuid4

import pandas as pd
from pyDMNrules import DMN

from app.config import OUTPUT_DIR, RULES_WORKBOOK_PATH
from app.models import ProcessingSummary

NUMERIC_COLUMNS = [
    "Monthly CTC",
    "CTC",
    "CCA",
    "Other Deductions",
]
REQUIRED_COLUMNS = ["Monthly CTC", "CCA", "PF Enabled", "State"]
OUTPUT_COLUMNS = [
    "Validation Message",
    "Basic",
    "HRA",
    "Transport Allowance",
    "Medical Allowance",
    "Bonus",
    "Special",
    "Gross",
    "Employer PF",
    "Employer ESI",
    "Employer Insurance",
    "Gratuity",
    "Employee PF",
    "Employee ESI",
    "Professional Tax",
    "Taxable Annual",
    "Tax Before Rebate",
    "Tax After Rebate",
    "TDS",
    "Take Home",
    "CTC (Total)",
]
FINAL_COLUMN_ORDER = [
    "Employee ID",
    "Employee Name",
    "Monthly CTC",
    "CTC",
    "CCA",
    "PF Enabled",
    "State",
    "Other Deductions",
    *OUTPUT_COLUMNS,
    "Processing Status",
]
ROUNDED_OUTPUT_COLUMNS = [
    "Basic",
    "HRA",
    "Transport Allowance",
    "Medical Allowance",
    "Bonus",
    "Special",
    "Gross",
    "Employer PF",
    "Employer ESI",
    "Employer Insurance",
    "Gratuity",
    "Employee PF",
    "Employee ESI",
    "Professional Tax",
    "Taxable Annual",
    "Tax Before Rebate",
    "Tax After Rebate",
    "TDS",
    "Take Home",
    "CTC (Total)",
]


class SalaryRuleEngine:
    def __init__(self, rules_path: Path = RULES_WORKBOOK_PATH) -> None:
        self.rules_path = rules_path
        self._dmn: DMN | None = None

    def ensure_loaded(self) -> None:
        dmn = DMN()
        status = dmn.load(str(self.rules_path))
        if "errors" in status:
            raise ValueError("; ".join(status["errors"]))
        self._dmn = dmn

    def reload(self) -> None:
        self.ensure_loaded()

    def _round_half_up(self, value: object) -> object:
        if value is None or pd.isna(value):
            return value
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return value

    def _validate_row(self, row: dict[str, object]) -> list[str]:
        errors: list[str] = []
        monthly_ctc = row.get("Monthly CTC")
        cca = row.get("CCA")
        pf_enabled = row.get("PF Enabled")
        state = row.get("State")

        if monthly_ctc is None or pd.isna(monthly_ctc):
            errors.append("Monthly CTC must be numeric")
        elif float(monthly_ctc) <= 0:
            errors.append("Monthly CTC must be greater than 0")

        if pd.isna(cca) or cca is None:
            errors.append("CCA must be numeric")
        elif float(cca) < 0:
            errors.append("CCA cannot be negative")

        if pf_enabled is None or pd.isna(pf_enabled):
            errors.append("PF Enabled must be provided as Yes or No")
        elif isinstance(pf_enabled, str):
            normalized = pf_enabled.strip().lower()
            if normalized not in {"yes", "no"}:
                errors.append("PF Enabled must be 'Yes' or 'No'")
        else:
            errors.append("PF Enabled must be provided as text 'Yes' or 'No'")

        if state is None or pd.isna(state) or not str(state).strip():
            errors.append("State must be provided")

        return errors

    def process_dataframe(self, dataframe: pd.DataFrame) -> tuple[pd.DataFrame, ProcessingSummary]:
        if self._dmn is None:
            self.ensure_loaded()

        prepared = dataframe.copy()
        for column in REQUIRED_COLUMNS:
            if column not in prepared.columns:
                prepared[column] = None
        # Support either Monthly CTC or CTC as input
        if "Monthly CTC" in prepared.columns:
            prepared["Monthly CTC"] = pd.to_numeric(prepared["Monthly CTC"], errors="coerce")
        if "CTC" in prepared.columns:
            prepared["CTC"] = pd.to_numeric(prepared["CTC"], errors="coerce")
        if "CCA" in prepared.columns:
            prepared["CCA"] = pd.to_numeric(prepared["CCA"], errors="coerce")
        if "Other Deductions" in prepared.columns:
            prepared["Other Deductions"] = pd.to_numeric(prepared["Other Deductions"], errors="coerce").fillna(0)
        for column in ["Monthly CTC", "CTC", "CCA", "Other Deductions"]:
            if column not in prepared.columns:
                prepared[column] = 0
        if "PF Enabled" not in prepared.columns:
            prepared["PF Enabled"] = "Yes"
        if "State" not in prepared.columns:
            prepared["State"] = "Delhi"

        # Map Monthly CTC to CTC for the rules engine
        prepared["CTC"] = prepared["Monthly CTC"]

        prepared["PF Enabled"] = (
            prepared["PF Enabled"]
            .fillna("Yes")
            .astype(str)
            .str.strip()
            .str.lower()
            .replace({"true": "yes", "false": "no", "y": "yes", "n": "no"})
            .str.capitalize()
        )
        prepared["State"] = prepared["State"].fillna("Delhi").astype(str).str.strip()

        result_rows: list[dict[str, object]] = []
        success_rows = 0

        for _, record in prepared.iterrows():
            row = {
                key: (None if pd.isna(value) else value)
                for key, value in record.to_dict().items()
            }
            errors = self._validate_row(row)
            if errors:
                result_row = {**row}
                for output in OUTPUT_COLUMNS:
                    result_row.setdefault(output, None)
                result_row["Validation Message"] = " | ".join(errors)
                result_row["Processing Status"] = "validation errors"
                result_rows.append(result_row)
                continue

            status, decisions = self._dmn.decide(row)
            if "errors" in status:
                result_row = {**row}
                for output in OUTPUT_COLUMNS:
                    result_row.setdefault(output, None)
                result_row["Validation Message"] = " | ".join(status["errors"])
                result_row["Processing Status"] = "dmn errors"
                result_rows.append(result_row)
                continue

            if not decisions:
                result_row = {**row}
                for output in OUTPUT_COLUMNS:
                    result_row.setdefault(output, None)
                result_row["Validation Message"] = "No DMN decisions were returned"
                result_row["Processing Status"] = "dmn errors"
                result_rows.append(result_row)
                continue

            final_result = decisions[-1]["Result"]
            final_result.pop("HalfSum", None)
            final_result["Validation Message"] = ""
            final_result["Processing Status"] = "no errors"
            result_rows.append(final_result)
            success_rows += 1

        merged = pd.DataFrame(result_rows)
        for column in FINAL_COLUMN_ORDER:
            if column not in merged.columns:
                merged[column] = None
        for column in ROUNDED_OUTPUT_COLUMNS:
            if column in merged.columns:
                merged[column] = merged[column].apply(self._round_half_up)
        merged = merged[FINAL_COLUMN_ORDER]

        summary = ProcessingSummary(
            file_name="",
            processed_rows=len(merged.index),
            success_rows=success_rows,
            error_rows=len(merged.index) - success_rows,
        )
        return merged, summary

    def save_results(self, dataframe: pd.DataFrame, source_name: str) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        target = OUTPUT_DIR / f"{Path(source_name).stem}_salary_results_{timestamp}_{uuid4().hex[:8]}.xlsx"
        dataframe.to_excel(target, index=False)
        return target
