# Assignment Submission Contents

## Main deliverables
- Final report: [IT3101_DWBI_Report_Final.docx](IT3101_DWBI_Report_Final.docx)
- Final Power BI dashboard: [dashboard/Telecom_Churn_Dashboard_StarSchema.pbix](dashboard/Telecom_Churn_Dashboard_StarSchema.pbix)
- Populated warehouse and retention mart: [data/warehouse/telecom_dw.db](data/warehouse/telecom_dw.db)
- Retention mart export: [data/processed/retention_mart.csv](data/processed/retention_mart.csv)
- Source files: [data/source/customer_billing_source.csv](data/source/customer_billing_source.csv), [data/source/location_reference_source.csv](data/source/location_reference_source.csv), [data/source/service_subscription_source.json](data/source/service_subscription_source.json)
- Original source workbook: [data/raw/Telco_customer_churn.xlsx](data/raw/Telco_customer_churn.xlsx)
- ETL implementation and evidence: [etl_pipeline.py](etl_pipeline.py), [logs/etl_log.txt](logs/etl_log.txt), [assets/screenshots/etl_script_screenshot.png](assets/screenshots/etl_script_screenshot.png), [assets/screenshots/etl_log_screenshot.png](assets/screenshots/etl_log_screenshot.png)
- Task 4 SQL and Power BI exports: [sql/star_schema_exports](sql/star_schema_exports)
- Star-schema diagram: [star_schema_erd.png](star_schema_erd.png)
- Power BI semantic model screenshot: [semantic_model_star_schema.png](insights%20and%20dashboard%20pages/semantic_model_star_schema.png)
- SSMS table row-count validation: [ssms_row_counts.png](insights%20and%20dashboard%20pages/ssms_row_counts.png)
- Architecture, dashboard pages, and interaction evidence: [assets/dashboard_screenshots](insights%20and%20dashboard%20pages)
- Reproducibility scripts: [build_final_assignment_report.py](build_final_assignment_report.py), [generate_ssms_star_schema.py](generate_ssms_star_schema.py)

## Dashboard-supported findings
- Overall churn rate: 26.54% across 7,043 customer accounts.
- Risk segment distribution: 2,559 High Risk (36.33%), 2,805 Medium Risk (39.83%), and 1,679 Low Risk (23.84%).
- Largest treemap revenue category: Month-to-month Fiber optic, $185,181.10 in monthly charges.
- Customer count by join quarter rises from 419 in 2023Q2 to 1,062 in 2023Q3.
- Average monthly charges by join quarter: $78.09 in 2017Q4 and $53.32 in 2023Q3.
- Average churn score shown for San Francisco Month-to-month is 69.13; Bakersfield One year is 40.50.
- Displayed city customer counts: Los Angeles 305; San Diego 150.

## Database note
`data/warehouse/telecom_dw.db` contains the populated SQLite warehouse and retention mart. The SQL Server `DWBI_Assignment` fact and dimension tables were populated from the six CSV exports. Their row counts match the exports, and all five fact-to-dimension key checks returned zero orphan rows. `sql/star_schema_exports` includes the table-creation script, CSV exports, and relationship guide.

## Before submission
- Add the student-designed cover on page 1; page 2 contains all four student names and IDs.
- Confirm the final PBIX visuals and model relationships in Power BI Desktop.
- If the PBIX was changed after the included screenshots were captured, replace the dashboard and interaction images in `assets/dashboard_screenshots`.
