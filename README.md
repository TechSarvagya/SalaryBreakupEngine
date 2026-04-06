# Salary Rule Engine

FastAPI + GraphQL + `pyDMNrules` salary engine with a React + Vite HR interface and spreadsheet workflow.

## What it does

- HR uploads an employee input spreadsheet.
- The API processes each row through a `pyDMNrules` workbook.
- The response is an Excel file containing inputs plus calculated outputs.
- HR can download the salary rules workbook, change thresholds/percentages/caps, and upload it back.

## Run

Backend:

```bash
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

This project is now split cleanly:

- `app/` is backend only
- `frontend/` is React + Vite only

If you want a production frontend build:

```bash
cd frontend
npm run build
```

## Endpoints

- `GET /health`
- `GET /graphql`
- `GET /rules/download`
- `POST /rules/upload`
- `GET /employees/template`
- `POST /employees/process`

## Notes

- The editable rules workbook is stored at `data/rules/salary_rules.xlsx`.
- The employee template is stored at `data/templates/employee_input_template.xlsx`.
- The percentage, cap, threshold, and formula logic lives in the downloadable DMN workbook.
- Input validation rules are enforced in the API before DMN execution so invalid employee rows are returned in the output sheet with a `Validation Message`.
- The returned employee result workbook intentionally hides the internal `HalfSum` helper column.
