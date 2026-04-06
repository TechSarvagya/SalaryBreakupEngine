from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from strawberry.fastapi import GraphQLRouter

from app.config import EMPLOYEE_TEMPLATE_PATH, RULES_WORKBOOK_PATH
from app.engine import SalaryRuleEngine
from app.excel import ensure_employee_template, read_employee_workbook
from app.graphql_schema import schema
from app.rules_workbook import build_rules_workbook

app = FastAPI(title="Salary Rule Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(GraphQLRouter(schema), prefix="/graphql")

engine = SalaryRuleEngine()


@app.on_event("startup")
def startup() -> None:
    if not RULES_WORKBOOK_PATH.exists():
        build_rules_workbook()
    ensure_employee_template()
    engine.reload()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/status")
def status() -> dict[str, object]:
    return {
        "health": "ok",
        "rulesWorkbook": {
            "path": str(RULES_WORKBOOK_PATH),
            "exists": RULES_WORKBOOK_PATH.exists(),
        },
    }


@app.get("/rules/download")
def download_rules() -> FileResponse:
    if not RULES_WORKBOOK_PATH.exists():
        build_rules_workbook()
    return FileResponse(
        RULES_WORKBOOK_PATH,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="salary_rules.xlsx",
    )


@app.post("/rules/upload")
async def upload_rules(file: UploadFile = File(...)) -> JSONResponse:
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    RULES_WORKBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing_bytes = RULES_WORKBOOK_PATH.read_bytes() if RULES_WORKBOOK_PATH.exists() else None
    with RULES_WORKBOOK_PATH.open("wb") as target:
        shutil.copyfileobj(file.file, target)
    try:
        engine.reload()
    except Exception as exc:
        if existing_bytes is not None:
            RULES_WORKBOOK_PATH.write_bytes(existing_bytes)
            engine.reload()
        raise HTTPException(status_code=400, detail=f"Invalid rules workbook: {exc}") from exc
    return JSONResponse({"message": "Rules workbook uploaded and reloaded"})


@app.get("/employees/template")
def download_employee_template() -> FileResponse:
    ensure_employee_template()
    return FileResponse(
        EMPLOYEE_TEMPLATE_PATH,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="employee_input_template.xlsx",
    )


@app.post("/employees/process")
async def process_employees(file: UploadFile = File(...)) -> FileResponse:
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")

    with NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = Path(temp_file.name)

    try:
        dataframe = read_employee_workbook(temp_path)
        results, summary = engine.process_dataframe(dataframe)
        output_path = engine.save_results(results, file.filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)

    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=output_path.name,
        headers={
            "X-Processed-Rows": str(summary.processed_rows),
            "X-Success-Rows": str(summary.success_rows),
            "X-Error-Rows": str(summary.error_rows),
        },
    )
