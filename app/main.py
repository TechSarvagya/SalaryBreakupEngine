from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from app.config import EMPLOYEE_TEMPLATE_PATH, RULES_WORKBOOK_PATH
from app.engine import SalaryRuleEngine
from app.excel import ensure_employee_template
from app.graphql_schema import schema
from app.rules_workbook import build_rules_workbook

app = FastAPI(
    title="Salary Rule Engine",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
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
app.include_router(
    GraphQLRouter(
        schema,
        graphql_ide=None,
        allow_queries_via_get=False,
    ),
    prefix="/graphql",
)

engine = SalaryRuleEngine()


@app.on_event("startup")
def startup() -> None:
    if not RULES_WORKBOOK_PATH.exists():
        build_rules_workbook()
    ensure_employee_template()
    engine.reload()
