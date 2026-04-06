from __future__ import annotations

from pathlib import Path

import strawberry

from app.config import RULES_WORKBOOK_PATH
from app.engine import SalaryRuleEngine


@strawberry.type
class RuleWorkbookInfo:
    path: str
    exists: bool


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> str:
        return "ok"

    @strawberry.field
    def rules_workbook(self) -> RuleWorkbookInfo:
        return RuleWorkbookInfo(path=str(RULES_WORKBOOK_PATH), exists=RULES_WORKBOOK_PATH.exists())


@strawberry.type
class Mutation:
    @strawberry.mutation
    def reload_rules(self) -> str:
        SalaryRuleEngine().reload()
        return "Rules reloaded successfully"


schema = strawberry.Schema(query=Query, mutation=Mutation)
