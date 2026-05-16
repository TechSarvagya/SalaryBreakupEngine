# Salary Rule Engine

A FastAPI + Strawberry GraphQL backend with a React + Vite frontend for processing employee salary workbooks through editable DMN rules. HR users can download the rules workbook, edit payroll formulas in Excel, upload employee data, and receive a calculated salary output workbook.

## What It Does

- Uses `pyDMNrules` to calculate salary components from `data/rules/salary_rules.xlsx`.
- Creates the default rules workbook on startup if it is missing.
- Creates the employee input template on startup if it is missing.
- Processes employee Excel files row by row.
- Returns calculated salary components, validation messages, and processing status in an Excel output file.
- Uses GraphQL for all frontend/backend communication.

## Employee Input Columns

The employee workbook uses these columns:

- `Employee ID`
- `Employee Name`
- `CTC`
- `CCA`
- `PF Option`
- `Professional Tax`
- `Employee PF Override`

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

Frontend runs at `http://localhost:5173`. Backend runs at `http://localhost:8000`.

## Workflow

1. Start the backend and frontend.
2. Download the employee template from the frontend.
3. Download the salary rules workbook if rule changes are needed.
4. Fill employee rows in the template.
5. Upload edited salary rules if required.
6. Upload the employee workbook.
7. Download the processed salary result workbook.

## GraphQL API

All operations go through:

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

Excel files are transferred as base64 strings in GraphQL payloads.

## Validation

Rows are validated before DMN calculation:

- `CTC` must be numeric and greater than 0.
- `CCA` must be numeric and cannot be negative.
- `Professional Tax` must be numeric and cannot be negative.
- If `CTC` is 30000 or below, `PF Option` must be `P4`.
- If `CTC` is above 30000, `PF Option` must be `P1`, `P2`, `P3`, or `P5`.
- If `PF Option` is `P5`, `Employee PF Override` is required and must be at least 1800.

Invalid rows are still returned in the output workbook with a `Validation Message` and `Processing Status`.

## Project Structure

```text
.
├── app/
│   ├── main.py              # FastAPI app with GraphQL router only
│   ├── graphql_schema.py    # GraphQL queries and mutations
│   ├── engine.py            # SalaryRuleEngine and row processing
│   ├── excel.py             # Employee template and Excel helpers
│   ├── rules_workbook.py    # Default DMN rules workbook builder
│   ├── models.py            # Shared dataclasses
│   └── config.py            # Project paths
├── data/
│   ├── rules/               # salary_rules.xlsx
│   ├── templates/           # employee_input_template.xlsx
│   └── outputs/             # Generated result workbooks
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── requirements.txt
└── README.md
```

## Tech Stack

Backend:

- FastAPI 0.128.0
- Strawberry GraphQL 0.312.3
- pyDMNrules 1.4.4
- Pandas 2.2.2
- openpyxl 3.1.5
- Uvicorn 0.35.0

Frontend:

- React 19.1.0
- Vite 7.0.0
- Vite React Plugin 5.0.0
