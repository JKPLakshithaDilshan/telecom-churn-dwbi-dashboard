# Telecom Customer Churn Data Warehouse and BI Dashboard

Portfolio-ready data warehousing and business intelligence project for telecom customer churn analysis. The solution integrates CSV, JSON, and Excel-based source data, builds a star-schema warehouse, creates a customer-retention data mart, and presents churn insights through a Power BI dashboard.

## Project Highlights

- Integrated 7,043 telecom customer records from customer billing, location reference, and service subscription sources.
- Built a SQLite data warehouse with one account-grain fact table and five dimensions: customer, location, service, contract, and date.
- Created a retention-focused data mart with analytical SQL views for churn, risk segment, contract, tenure, cohort, and high-risk active customer analysis.
- Prepared SQL Server DDL and CSV exports for SSMS and Power BI star-schema modelling.
- Designed a three-page Power BI dashboard for executive KPIs, trend analysis, and interactive churn exploration.

## Repository Structure

```text
.
├── assets/
│   ├── dashboard_screenshots/   # Dashboard, model, architecture, and interaction evidence
│   ├── images/                  # Star schema ERD and visual assets
│   └── screenshots/             # ETL execution screenshots
├── dashboard/                   # Power BI .pbix dashboard
├── data/
│   ├── raw/                     # Original source workbook
│   ├── source/                  # Prepared operational source files
│   ├── processed/               # Generated retention mart export
│   └── warehouse/               # SQLite warehouse database
├── docs/                        # Submission notes and supporting documentation
├── logs/                        # ETL and load logs
├── reports/                     # Final assignment report PDF
├── sql/
│   ├── star_schema_exports/     # SQL Server DDL plus fact/dimension CSV exports
│   └── retention_mart_sqlserver.sql
└── src/                         # Python ETL, SQL generation, and report scripts
```

## Tech Stack

- Python
- pandas
- SQLite
- SQL Server / SSMS
- Power BI
- python-docx

## How To Run

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Rebuild the SQLite warehouse and retention mart:

```bash
python src/etl_pipeline.py
```

3. Regenerate SQL Server / Power BI star-schema exports:

```bash
python src/generate_ssms_star_schema.py
```

4. Optional: load the SQLite warehouse into SQL Server:

```bash
python src/load_to_sqlserver.py
```

SQL Server connection settings can be overridden with `DW_SERVER`, `DW_DATABASE`, `DW_DRIVER`, `DW_USER`, and `DW_PASSWORD`.

## Key Outputs

- Final dashboard: `dashboard/Telecom_Churn_Dashboard_StarSchema.pbix`
- Final report: `reports/final_report/IT3101_DWBI_Report_Final_(2026-DS-10).pdf`
- SQLite warehouse: `data/warehouse/telecom_dw.db`
- Retention mart export: `data/processed/retention_mart.csv`
- SQL Server star schema: `sql/star_schema_exports/ssms_star_schema.sql`
- Power BI relationship guide: `sql/star_schema_exports/powerbi_relationship_guide.md`

## Dashboard Findings

- Overall churn rate: 26.54% across 7,043 customer accounts.
- High-risk segment: 2,559 customers, representing 36.33% of the base.
- Largest monthly revenue category: month-to-month fiber optic customers, with 185,181.10 in monthly charges.
- Join-quarter customer counts rise from 419 in 2023 Q2 to 1,062 in 2023 Q3.

## Suggested Repository Details

- Repository name: `telecom-churn-dwbi-dashboard`
- Description: `Telecom customer churn data warehouse, retention mart, SQL Server star schema, and Power BI dashboard.`

## Team

- Lakshitha Dilshan J K P
- Nirmani K.H.D.T
- Palliyaguruge C.T
- Senaratne P.A.R.T

