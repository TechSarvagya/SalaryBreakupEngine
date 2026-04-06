from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ProcessingSummary:
    file_name: str
    processed_rows: int
    success_rows: int
    error_rows: int


EmployeeRow = dict[str, Any]
