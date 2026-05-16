# Salary Rule Engine

A FastAPI + Strawberry GraphQL backend with a React + Vite frontend for processing employee salary workbooks. HR users can download the current salary rules workbook, edit payroll rules in Excel, upload employee data, and download a processed salary sheet with calculated earnings, deductions, tax, and validation messages.

## What It Does

- Downloads an editable DMN salary rules workbook from `data/rules/salary_rules.xlsx`.
- Downloads an employee input template from `data/templates/employee_input_template.xlsx`.
- Accepts employee workbooks with these columns:
  - `Employee ID`
  - `Employee Name`
  - `Monthly CTC`
  - `CCA`
  - `PF Enabled`
  - `State`
  - `Other Deductions`
- Validates each employee row before calculation.
- Runs each valid row through `pyDMNrules`.
- Returns a processed Excel file with calculated salary components and row-level status.
- Stores generated output files in `data/outputs/`.

## Current Calculation Rules

The calculation logic is defined in the DMN Excel workbook, not hardcoded into the API route. If `data/rules/salary_rules.xlsx` is missing, the backend creates a default workbook on startup.

Default rules include:

- `Basic` = 40% of monthly CTC.
- `HRA` = 40% of Basic.
- `Transport Allowance` = 1600.
- `Medical Allowance` = 1250.
- `Bonus` = 8.33% of Basic.
- `Employer PF` = 12% of Basic capped at 15000 when PF is enabled, otherwise 0.
- `Employee PF` = 12% of Basic capped at 15000 when PF is enabled, otherwise 0.
- `Gratuity` = 4.81% of Basic.
- `Employer Insurance` = 1000.
- `Gross Before ESI` = Monthly CTC - Employer PF - Gratuity - Employer Insurance.
- `Employer ESI` = 3.25% adjusted from Gross Before ESI when Gross Before ESI is 21000 or below, otherwise 0.
- `Gross` = Gross Before ESI - Employer ESI.
- `Employee ESI` = 0.75% of Gross when Gross is 21000 or below, otherwise 0.
- `Professional Tax` = 200 for Delhi when Gross is above 15000, otherwise 0.
- `Special` = Gross - Basic - HRA - Transport Allowance - Medical Allowance - Bonus.
- `Taxable Annual` = max(0, Gross * 12 - 75000 - Other Deductions).
- `Tax Before Rebate` is calculated with the New Regime slab table.
- `Tax After Rebate` = 0 when taxable annual income is 1200000 or below, otherwise Tax Before Rebate.
- `TDS` = monthly tax after 4% cess.
- `Take Home` = Gross - Employee PF - Employee ESI - Professional Tax - TDS.
- `CTC (Total)` = Gross + Employer PF + Employer ESI + Gratuity + Employer Insurance.

The final output values are rounded using half-up rounding.

## Run The Project

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

The backend runs at `http://localhost:8000`.

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

If the backend is not running on the same origin as the frontend expects, set `VITE_API_BASE_URL` before starting Vite.

## How To Use

1. Start the backend.
2. Start the frontend.
3. Click **Download salary rules** to get the current editable rules workbook.
4. Click **Download employee template** and fill employee rows.
5. Optionally edit the salary rules workbook and upload it with **Upload updated rules**.
6. Upload the employee workbook with **Process employee workbook**.
7. The processed result workbook downloads automatically.

## Validation

Rows are validated before DMN processing:

- `Monthly CTC` must be numeric and greater than 0.
- `CCA` must be numeric and cannot be negative.
- `PF Enabled` must be `Yes` or `No`.
- `State` must be provided.
- `Other Deductions` is converted to numeric and defaults to 0 when blank.

Rows with validation or DMN errors are included in the output workbook with a `Validation Message` and `Processing Status`.

## GraphQL API

GraphQL is available at:

```text
POST /graphql
POST /graphql/
```

Available queries:

- `health`
- `rulesWorkbook`
- `downloadRules`
- `downloadEmployeeTemplate`

Available mutations:

- `reloadRules`
- `uploadRules(fileContent: String!, fileName: String!)`
- `processEmployees(fileContent: String!, fileName: String!)`

File upload and download payloads are base64-encoded `.xlsx` files.

## Project Structure

```text
.
├── app/
│   ├── main.py              # FastAPI app and GraphQL router
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
│   │   ├── App.jsx          # Main React UI
│   │   ├── main.jsx         # React entry point
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

## Notes

- FastAPI documentation routes are disabled in this app.
- The backend creates the default rules workbook and employee template during startup if they do not already exist.
- The rules workbook has instruction, glossary, salary component, tax, and final salary sheets.
- Edited rules are validated by reloading them through `pyDMNrules`; invalid uploads restore the previous rules workbook when possible.
