from __future__ import annotations

import base64
from pathlib import Path
from tempfile import NamedTemporaryFile

import strawberry

from app.config import EMPLOYEE_TEMPLATE_PATH, RULES_WORKBOOK_PATH
from app.engine import SalaryRuleEngine
from app.excel import ensure_employee_template, read_employee_workbook
from app.rules_workbook import build_rules_workbook


@strawberry.type
class RuleWorkbookInfo:
    path: str
    exists: bool


@strawberry.type
class FileDownload:
    file_name: str
    file_content: str


@strawberry.type
class ProcessingSummary:
    processed_rows: int
    success_rows: int
    error_rows: int
    file_name: str
    file_content: str


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> str:
        return "ok"

    @strawberry.field
    def rules_workbook(self) -> RuleWorkbookInfo:
        return RuleWorkbookInfo(path=str(RULES_WORKBOOK_PATH), exists=RULES_WORKBOOK_PATH.exists())

    @strawberry.field
    def download_rules(self) -> FileDownload:
        if not RULES_WORKBOOK_PATH.exists():
            build_rules_workbook()
        return FileDownload(
            file_name="salary_rules.xlsx",
            file_content=base64.b64encode(RULES_WORKBOOK_PATH.read_bytes()).decode("utf-8"),
        )

    @strawberry.field
    def download_employee_template(self) -> FileDownload:
        ensure_employee_template()
        return FileDownload(
            file_name="employee_input_template.xlsx",
            file_content=base64.b64encode(EMPLOYEE_TEMPLATE_PATH.read_bytes()).decode("utf-8"),
        )


@strawberry.type
class Mutation:
    @strawberry.mutation
    def reload_rules(self) -> str:
        SalaryRuleEngine().reload()
        return "Rules reloaded successfully"

    @strawberry.mutation
    def upload_rules(self, file_content: str, file_name: str) -> str:
        if not file_name.lower().endswith(".xlsx"):
            raise ValueError("Only .xlsx files are supported")

        engine = SalaryRuleEngine()
        RULES_WORKBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
        existing_bytes = RULES_WORKBOOK_PATH.read_bytes() if RULES_WORKBOOK_PATH.exists() else None

        try:
            RULES_WORKBOOK_PATH.write_bytes(base64.b64decode(file_content))
            engine.reload()
        except Exception as exc:
            if existing_bytes is not None:
                RULES_WORKBOOK_PATH.write_bytes(existing_bytes)
                engine.reload()
            raise ValueError(f"Invalid rules workbook: {exc}") from exc

        return "Rules workbook uploaded and reloaded"

    @strawberry.mutation
    def process_employees(self, file_content: str, file_name: str) -> ProcessingSummary:
        if not file_name.lower().endswith(".xlsx"):
            raise ValueError("Only .xlsx files are supported")

        engine = SalaryRuleEngine()
        with NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            temp_file.write(base64.b64decode(file_content))
            temp_path = Path(temp_file.name)

        try:
            dataframe = read_employee_workbook(temp_path)
            results, summary = engine.process_dataframe(dataframe)
            output_path = engine.save_results(results, file_name)
            result_content = base64.b64encode(output_path.read_bytes()).decode("utf-8")

            return ProcessingSummary(
                processed_rows=summary.processed_rows,
                success_rows=summary.success_rows,
                error_rows=summary.error_rows,
                file_name=output_path.name,
                file_content=result_content,
            )
        except Exception as exc:
            raise ValueError(str(exc)) from exc
        finally:
            temp_path.unlink(missing_ok=True)


schema = strawberry.Schema(query=Query, mutation=Mutation)
