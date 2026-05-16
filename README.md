# Salary Rule Engine

A FastAPI + Strawberry GraphQL backend with a React + Vite frontend for processing employee salary workbooks through editable DMN rules.

## What It Does

- Downloads the current salary rules workbook through GraphQL.
- Downloads the employee input template through GraphQL.
- Uploads edited salary rules through GraphQL.
- Uploads employee workbooks through GraphQL and returns a processed Excel result.
- Uses `pyDMNrules` to apply the rules in `data/rules/salary_rules.xlsx`.

## Employee Input Columns

- `Employee ID`
- `Employee Name`
- `Monthly CTC`
- `CCA`
- `PF Enabled`
- `State`
- `Other Deductions`

## Run

Backend:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

Backend: `http://localhost:8000`

## GraphQL API

All app operations use:

```text
POST /graphql
POST /graphql/
```

Queries:

- `health`
- `rulesWorkbook`
- `downloadRules`
- `downloadEmployeeTemplate`

Mutations:

- `reloadRules`
- `uploadRules(fileContent: String!, fileName: String!)`
- `processEmployees(fileContent: String!, fileName: String!)`

Excel files are transferred as base64 strings.

## Project Structure

```text
.
├── app/
│   ├── main.py
│   ├── graphql_schema.py
│   ├── engine.py
│   ├── excel.py
│   ├── rules_workbook.py
│   ├── models.py
│   └── config.py
├── data/
│   ├── rules/
│   ├── templates/
│   └── outputs/
├── frontend/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── requirements.txt
└── README.md
```

## Notes

- The backend creates the rules workbook on startup if it is missing.
- The backend creates or refreshes the employee template if it is missing or has stale columns.
- FastAPI REST endpoints and API docs are disabled; the frontend talks to GraphQL only.
- Generated result files are saved under `data/outputs/`.
