from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from uuid import uuid4

import pandas as pd
from pyDMNrules import DMN

from app.config import OUTPUT_DIR, RULES_WORKBOOK_PATH
from app.models import ProcessingSummary

NUMERIC_COLUMNS = ["CTC", "CCA", "Professional Tax", "Employee PF Override"]
REQUIRED_COLUMNS = ["CTC", "CCA", "PF Option", "Professional Tax"]
OUTPUT_COLUMNS = [
    "Validation Message",
    "Basic",
    "Basic for Statutory",
    "HRA",
    "Bonus",
    "Employee PF",
    "Employer PF",
    "Employee ESI",
    "Employer ESI",
    "Medical Insurance",
    "Gratuity",
    "Gross",
    "Tax Before Rebate",
    "Tax After Rebate",
    "Surcharge Multiplier",
    "TDS",
    "Special",
    "Take Home",
    "CTC with CCA",
    "Gross with CCA",
]
FINAL_COLUMN_ORDER = [
    "Employee ID",
    "Employee Name",
    "CTC",
    "CCA",
    "PF Option",
    "Professional Tax",
    "Employee PF Override",
    *OUTPUT_COLUMNS,
    "Processing Status",
]
ROUNDED_OUTPUT_COLUMNS = [
    "Basic",
    "Basic for Statutory",
    "HRA",
    "Bonus",
    "Employee PF",
    "Employer PF",
    "Employee ESI",
    "Employer ESI",
    "Medical Insurance",
    "Gratuity",
    "Gross",
    "Tax Before Rebate",
    "Tax After Rebate",
    "TDS",
    "Special",
    "Take Home",
    "CTC with CCA",
    "Gross with CCA",
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
        ctc = row.get("CTC")
        cca = row.get("CCA")
        professional_tax = row.get("Professional Tax")
        pf_option = row.get("PF Option")
        pf_override = row.get("Employee PF Override")

        if pd.isna(ctc) or ctc is None:
            errors.append("CTC must be numeric")
        elif float(ctc) <= 0:
            errors.append("CTC must be greater than 0")

        if pd.isna(cca) or cca is None:
            errors.append("CCA must be numeric")
        elif float(cca) < 0:
            errors.append("CCA cannot be negative")

        if pd.isna(professional_tax) or professional_tax is None:
            errors.append("Professional Tax must be numeric")
        elif float(professional_tax) < 0:
            errors.append("Professional Tax cannot be negative")

        if not isinstance(pf_option, str):
            errors.append("PF Option must be provided")
        elif not pd.isna(ctc) and ctc is not None:
            if float(ctc) <= 30000 and pf_option != "P4":
                errors.append("If CTC is 30000 or below, PF Option must be P4")
            if float(ctc) > 30000 and pf_option not in {"P1", "P2", "P3", "P5"}:
                errors.append("If CTC is above 30000, PF Option must be P1, P2, P3, or P5")

        if pf_option == "P5":
            if pd.isna(pf_override) or pf_override is None:
                errors.append("Employee PF Override is required for P5")
            elif float(pf_override) < 1800:
                errors.append("Employee PF Override must be at least 1800 for P5")

        return errors

    def process_dataframe(self, dataframe: pd.DataFrame) -> tuple[pd.DataFrame, ProcessingSummary]:
        if self._dmn is None:
            self.ensure_loaded()

        prepared = dataframe.copy()
        for column in REQUIRED_COLUMNS:
            if column not in prepared.columns:
                prepared[column] = None
        for column in NUMERIC_COLUMNS:
            if column in prepared.columns:
                prepared[column] = pd.to_numeric(prepared[column], errors="coerce")

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
