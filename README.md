# Salary Rule Engine

A FastAPI backend with React + Vite frontend for processing employee salary calculations using DMN (Decision Model Notation) rules. HR teams upload employee data, the engine applies configurable salary rules, and returns calculated salary components.

## What it does

- HR uploads an employee input spreadsheet (Employee ID, Name, CTC, CCA, PF Option, Professional Tax, Employee PF Override).
- The API processes each row through a `pyDMNrules` DMN workbook containing salary calculation logic.
- The engine calculates salary components: Basic, HRA, Bonus, Employee PF, Employer PF, ESI, Medical Insurance, Gratuity, Income Tax (TDS), and Take Home pay.
- Response is an Excel file with inputs, all calculated outputs, and validation messages for any errors.
- HR can download the editable rules workbook, modify thresholds/percentages/caps/formulas, and upload it back to reload the engine.

## Run

Backend:

```bash
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000` with API docs at `/docs`.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:5173`.

This project is now split cleanly:

- `app/` is backend only
- `frontend/` is React + Vite only

If you want a production frontend build:

```bash
cd frontend
npm run build
```

## Project Structure

```
.
├── app/                          # FastAPI backend
│   ├── main.py                   # FastAPI app, route handlers
│   ├── engine.py                 # SalaryRuleEngine (DMN processor)
│   ├── graphql_schema.py         # GraphQL query/mutation definitions
│   ├── excel.py                  # Excel read/write utilities
│   ├── rules_workbook.py         # DMN workbook builder
│   ├── models.py                 # Data models (ProcessingSummary, EmployeeRow)
│   └── config.py                 # Paths and configuration
├── frontend/                     # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx               # Main React component
│   │   ├── main.jsx              # React entry point
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── rules/                    # DMN salary rules workbook
│   ├── templates/                # Employee input template
│   └── outputs/                  # Processed results (generated)
├── requirements.txt              # Python dependencies
└── README.md

```

## Tech Stack

**Backend:**
- FastAPI 0.128.0 — REST API framework
- Strawberry GraphQL 0.312.3 — GraphQL support
- pyDMNrules 1.4.4 — DMN (Decision Model Notation) rule engine
- Pandas 2.2.2 — Data processing
- openpyxl 3.1.5 — Excel file handling
- Uvicorn 0.35.0 — ASGI server

**Frontend:**
- React 19.1.0
- Vite 7.0.0 — Build tool
- Vite React Plugin 5.0.0

## Workflow

1. **Initialize**: Backend loads `salary_rules.xlsx` (DMN workbook) on startup. If missing, creates default workbook.
2. **Download Template**: HR downloads employee input template to understand required columns.
3. **Populate Data**: HR fills in employee rows: ID, Name, CTC, CCA, PF Option, Professional Tax, PF Override.
4. **Upload & Process**: HR uploads spreadsheet → API validates each row → DMN engine calculates salary → Excel response generated with results + validation messages.
5. **Review Results**: HR downloads results with all calculated salary components.
6. **Update Rules** (optional): HR downloads current `salary_rules.xlsx` → modifies thresholds/percentages/formulas → uploads updated workbook → engine reloads.

## Architecture

- **Separation of Concerns**: Backend API handles business logic; React frontend handles UI.
- **DMN-Driven**: All salary calculation logic lives in the editable Excel workbook, not hardcoded.
- **Row-Level Validation**: Each employee row is validated (numeric fields, required fields) before DMN execution.
- **Stateless API**: Each request is independent; no session state.
- **CORS Enabled**: Frontend (localhost:5173) can call backend (localhost:8000).

## Endpoints

REST API:
- `GET /health` — Health check
- `GET /status` — System status (health + rules workbook state)
- `GET /rules/download` — Download the editable rules workbook (salary_rules.xlsx)
- `POST /rules/upload` — Upload a modified rules workbook to reload the engine
- `GET /employees/template` — Download the employee input template
- `POST /employees/process` — Process an uploaded employee spreadsheet and return results

GraphQL API (at `GET /graphql`):
- `Query.health` — Returns "ok"
- `Query.rules_workbook` — Returns rules workbook path and existence status
- `Mutation.reload_rules` — Manually reload the salary calculation engine

## Notes

- **Salary Components Calculated**: Basic, Basic for Statutory, HRA, Bonus, Employee PF, Employer PF, Employee ESI, Employer ESI, Medical Insurance, Gratuity, Gross Salary, Tax Before Rebate, Tax After Rebate, TDS, Special Allowance, Take Home, CTC with CCA, Gross with CCA.
- **Employee Input Fields**: Employee ID, Employee Name, CTC (Cost to Company), CCA (Cost to Company Add-ons), PF Option, Professional Tax, Employee PF Override.
- **Rules Workbook**: Stored at `data/rules/salary_rules.xlsx` — contains DMN rules for all percentage, cap, threshold, and formula logic. This is downloadable and editable by HR.
- **Employee Template**: Stored at `data/templates/employee_input_template.xlsx` — provides the structure for employee data uploads.
- **Output Storage**: Processed results are saved to `data/outputs/`.
- **Validation**: Input validation rules are enforced in the API before DMN execution. Invalid rows are returned in the output sheet with a `Validation Message`.
- **Hidden Columns**: The returned employee result workbook intentionally hides the internal `HalfSum` helper column.
- **Numeric Columns**: CTC, CCA, Professional Tax, and Employee PF Override are validated as numeric values.
- **Processing Summary**: The API returns headers with row counts: `X-Processed-Rows`, `X-Success-Rows`, `X-Error-Rows`.
