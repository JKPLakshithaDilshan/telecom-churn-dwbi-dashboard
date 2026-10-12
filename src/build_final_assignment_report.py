from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Report factory
report_path = os.path.join(root, "IT3101_DWBI_Report_Final.docx")
summary_md_path = os.path.join(root, "assignment_completion_summary.md")

doc = Document()

# Leave page 1 blank for the student's cover page.
section = doc.sections[0]
section.top_margin = Inches(0.7)
section.bottom_margin = Inches(0.7)
section.left_margin = Inches(0.9)
section.right_margin = Inches(0.9)

# Student details page (page 2)
doc.add_page_break()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("SLIIT\n")
run.bold = True
run.font.size = 18
p.add_run("BSc (Hons) in Data Science\n")
p.add_run("IT3101 – Data Warehousing and Business Intelligence\n")
p.add_run("Design and Implementation of a Data Warehouse and Business Intelligence Solution\n")
p.add_run("Domain: Telecommunications – Customer Churn Analysis\n\n")
doc.add_heading("Student Details", level=1)
students = [
    ("Lakshitha Dilshan J K P", "IT24102621"),
    ("Nirmani K.H.D.T", "IT24103380"),
    ("Palliyaguruge C.T", "IT24103655"),
    ("Senaratne P.A.R.T", "IT24103526"),
]
student_table = doc.add_table(rows=1, cols=2)
student_table.style = "Table Grid"
student_table.rows[0].cells[0].text = "Student Name"
student_table.rows[0].cells[1].text = "Student ID"
for name, student_id in students:
    cells = student_table.add_row().cells
    cells[0].text = name
    cells[1].text = student_id
doc.add_paragraph("Submission Date: ___________________________")

doc.add_page_break()
doc.add_heading("Table of Contents", level=1)
contents = [
    "Executive Summary",
    "1. Task 1 – Dataset Selection and Business Scenario Identification",
    "2. Task 2 – Data Source Identification and Preparation",
    "3. Task 3 – Data Warehouse Architecture Design",
    "4. Task 4 – Dimensional Data Warehouse Design and Implementation",
    "5. Task 5 – ETL Process Development",
    "6. Task 6 – Data Mart Development",
    "7. Task 7 – OLAP Analysis and Business Intelligence Dashboard Development",
    "8. Task 8 – Business Insights and Recommendations",
    "9. AI Usage Disclosure",
    "10. References",
    "Appendix A – Technical Evidence",
    "Appendix B – Project File Inventory",
]
for item in contents:
    doc.add_paragraph(item)

doc.add_page_break()

# Executive summary

doc.add_heading("Executive Summary", level=1)
doc.add_paragraph("This project develops a telecom customer churn and retention analytics solution using 7,043 customer accounts. Python integrates customer/billing CSV, location-reference CSV, and service-subscription JSON sources, performs data preparation and derived-field creation, and loads a SQLite warehouse. The dimensional design uses Fact_CustomerAccount with Customer, Location, Service, Contract, and Date dimensions, with a separate SQL Server/Power BI export for the 73-row join-date dimension. The populated Mart_CustomerRetention table supports retention analysis. The three-page Power BI dashboard presents executive KPIs, risk segments, contract/service charges, join-quarter comparisons, city/contract churn scores, and interactive customer analysis. Dashboard-supported results include 26.54% overall churn, 2,559 High Risk customers, and $185,181.10 in summed monthly charges for the Month-to-month/Fiber optic treemap category.")

doc.add_page_break()

# Task 1

doc.add_heading("1. Task 1 – Dataset Selection and Business Scenario Identification", level=1)
doc.add_paragraph("The selected dataset is a telecom customer churn dataset representing an OLTP-style customer-account environment. Each row stores customer account, contract, billing, service, and churn outcome details, which is suitable for a dimensional data warehouse and analytical dashboard.")
doc.add_paragraph("Business domain: Telecommunications / customer retention")
doc.add_paragraph("Business problem addressed: identifying churn drivers, measuring revenue exposure, segmenting risky customers, and designing retention strategies.")
doc.add_paragraph("Dataset source: IBM Telco Customer Churn dataset (extended version), sourced from Kaggle.")
doc.add_paragraph("Dataset format: CSV / Excel-based operational data transformed into a warehouse-ready analytical dataset.")
doc.add_paragraph("Number of records: 7,043 customer records.")
doc.add_paragraph("The dataset is suitable for a DW/BI solution because it contains both factual measures such as Monthly Charges, Total Charges, Tenure Months, Churn Score, and CLTV, and descriptive attributes such as Gender, Contract, Payment Method, Technology Service, and City, which map naturally to dimension tables.")

def add_table(rows, headers):
    table = doc.add_table(rows=len(rows)+1, cols=len(headers))
    table.style = 'Table Grid'
    for i, h in enumerate(headers):
        table.cell(0, i).text = h
    for r_idx, row in enumerate(rows, start=1):
        for c_idx, value in enumerate(row):
            table.cell(r_idx, c_idx).text = str(value)
    return table

source_rows = [
    ("Customer and billing system", "CSV", "7,043", "Customer profile, billing, churn status, tenure, contract"),
    ("Geographic reference system", "CSV", "1,652 unique ZIP codes", "City, State, Country, latitude, longitude"),
    ("Service provisioning system", "JSON", "7,043", "Phone service, internet service, device protection, streaming, tech support")
]
add_table(source_rows, ["Source", "Format", "Records", "Main content"])

doc.add_heading("Detailed Attribute Dictionary", level=2)
attribute_rows = [
    ("CustomerID", "Text / NVARCHAR(255)", "Natural key", "Source customer identifier; business key in Dim_Customer."),
    ("CustomerKey", "Integer / INT IDENTITY", "Surrogate key", "Dim_Customer primary key; fact foreign key."),
    ("CustomerAccountKey", "Integer / INT IDENTITY", "Fact key", "Identifies one account-grain row in the Task 4 fact export."),
    ("Gender, Senior_Citizen, Partner, Dependents", "Text", "Attributes", "Customer demographic and household categories."),
    ("Tenure_Months", "Integer", "Measure", "Account tenure in months."),
    ("Tenure_Years", "Decimal", "Derived measure", "Tenure_Months divided by 12, rounded to one decimal place."),
    ("Contract", "Text / NVARCHAR(100)", "Attribute", "Contract term category."),
    ("Paperless_Billing", "Text", "Attribute", "Paperless billing status."),
    ("Payment_Method", "Text / NVARCHAR(100)", "Attribute", "Payment method category."),
    ("Monthly_Charges", "Decimal / DECIMAL(10,2)", "Measure", "Current monthly account charges."),
    ("Total_Charges", "Decimal / DECIMAL(10,2)", "Measure", "Accumulated customer charges."),
    ("Avg_Monthly_Spend", "Decimal / DECIMAL(10,2)", "Derived measure", "Total_Charges divided by tenure months; zero tenure is treated as one."),
    ("Churn_Label", "Text", "Outcome label", "Text churn outcome in the customer/billing source."),
    ("Churn_Value", "Integer / INT", "Outcome / measure", "Binary churn indicator; its average is used as a churn rate."),
    ("Churn_Score", "Integer / INT", "Risk score", "Dataset-provided churn score; not a churn-rate percentage."),
    ("CLTV", "Integer / INT", "Measure / estimate", "Customer lifetime value estimate."),
    ("Churn_Reason", "Text", "Outcome explanation", "Recorded churn reason; ETL fills nulls with a not-applicable label."),
    ("Zip_Code", "Integer in source; NVARCHAR(50) in SQL Server", "Location attribute", "ZIP identifier used to join the location reference."),
    ("City, State, Country", "Text", "Location attributes", "Geographic categories from the location reference source."),
    ("Latitude, Longitude", "Decimal / FLOAT", "Location attributes", "Geographic coordinates."),
    ("Phone_Service, Multiple_Lines", "Text / NVARCHAR(20)", "Service attributes", "Phone and multiple-line service categories."),
    ("Internet_Service", "Text / NVARCHAR(50)", "Service attribute", "Internet category such as DSL, Fiber optic, or No."),
    ("Online_Security, Online_Backup, Device_Protection, Tech_Support, Streaming_TV, Streaming_Movies", "Text / NVARCHAR(20)", "Service attributes", "Service subscription categories."),
    ("LocationKey, ServiceKey, ContractKey, DateKey", "Integer / INT IDENTITY", "Surrogate keys", "Dimension primary keys referenced by Fact_CustomerAccount."),
    ("FullDate", "Date / DATE in SQL Server", "Date attribute", "Full join/snapshot date, depending on the generated output."),
    ("Year, MonthNumber", "Integer", "Date attributes", "Numeric calendar hierarchy fields."),
    ("Quarter, MonthName, QuarterName", "Text", "Date attributes", "Descriptive calendar hierarchy fields."),
    ("Risk_Segment", "Text / NVARCHAR(50)", "Risk attribute", "High Risk, Medium Risk, or Low Risk value carried from retention_mart into the Task 4 export."),
    ("Join_Date, Join_Year, Join_Quarter", "Date text, integer, text", "Cohort attributes", "Retention-mart cohort fields used to derive the separate 73-row Dim_Date export."),
]
add_table(attribute_rows, ["Attribute(s)", "Data Type", "DWBI Role", "Description"])

doc.add_heading("DWBI Suitability", level=2)
for item in [
    "The 7,043 account-grain records provide a clear unit of analysis for churn and charge metrics.",
    "Numerical fields such as Monthly_Charges, Total_Charges, Tenure_Months, Churn_Value, Churn_Score, and CLTV support aggregation and comparison.",
    "Customer, contract, service, payment, and geographic attributes support dimensional slicing and grouping.",
    "The three source formats (CSV, CSV reference data, and JSON) demonstrate integration from multiple operational-style sources.",
    "The records support a fact-and-dimension model and a retention-focused mart for operational decision support.",
]:
    doc.add_paragraph(item, style="List Bullet")

# Task 2

doc.add_heading("2. Task 2 – Data Source Identification and Preparation", level=1)
doc.add_paragraph("The implementation uses three operational-style source systems that represent a realistic architecture for reporting and analytical processing.")

doc.add_paragraph("Source 1: Customer & Billing System (data/source/customer_billing_source.csv)")
doc.add_paragraph("This source stores demographic and account data such as CustomerID, Gender, Senior_Citizen, Partner, Dependents, Tenure_Months, Contract, Paperless_Billing, Payment_Method, Monthly_Charges, Total_Charges, Churn_Value, Churn_Score, CLTV, and Churn_Reason.")

doc.add_paragraph("Source 2: Location Reference System (data/source/location_reference_source.csv)")
doc.add_paragraph("This lookup table stores ZIP-code-level geographic details including City, State, Country, Latitude, and Longitude. It enables dimensional analysis by location and supports geographical churn comparisons.")

doc.add_paragraph("Source 3: Service Provisioning System (data/source/service_subscription_source.json)")
doc.add_paragraph("This source contains service subscription features including Phone_Service, Multiple_Lines, Internet_Service, Online_Security, Online_Backup, Device_Protection, Tech_Support, Streaming_TV, and Streaming_Movies. It maps to the service dimension in the data warehouse.")

doc.add_paragraph("Data preparation steps included loading each source into a staged analytical environment, trimming text values, filling blank Total_Charges values with 0, standardising fields, removing duplicates where needed, and creating derived fields such as Avg_Monthly_Spend and Tenure_Years. This ensured that the files could be merged into a unified analytical model without losing business meaning.")

doc.add_heading("Data Quality and Edge Cases", level=2)
doc.add_paragraph("The ETL code replaces blank Total_Charges strings with 0 before numeric conversion. Its recorded run found 0 remaining blanks, indicating the input CSV had no blank values at execution time. Churn_Reason nulls are filled with 'Not Applicable - Active Customer'; the run found 0 remaining nulls. Duplicate CustomerID values are checked; 0 duplicates were found, so the pipeline removed no rows in that run. Text/object values are stripped of leading and trailing whitespace (22 columns in the logged run). Churn_Value, Churn_Score, and CLTV are cast to integers. Avg_Monthly_Spend and Tenure_Years are derived. The cleaned merged dataframe is saved as cleaned_master.pkl; this is a file-based staging artifact, not a staging database schema.")

doc.add_picture(os.path.join(root, "assets", "dashboard_screenshots", "Source Integration and Relationship Diagram.png"), width=Inches(6.0))

# Task 3

doc.add_heading("3. Task 3 – Data Warehouse Architecture Design", level=1)
doc.add_paragraph("The solution follows an operational-to-analytical architecture with four major layers: Data Source Layer, Data Integration Layer, Storage Layer, and Presentation Layer.")

doc.add_paragraph("Data Source Layer: operational sources including billing, location, and service systems.")
doc.add_paragraph("Data Integration Layer: ETL pipeline built in Python that extracted, transformed, cleaned, standardised, and loaded the source data.")
doc.add_paragraph("Storage Layer: staging data, normalized warehouse tables, and a retention-focused data mart for business analysis.")
doc.add_paragraph("Presentation Layer: Power BI dashboard with executive summary, trend analysis, and interactive drill-down views.")

doc.add_picture(os.path.join(root, "assets", "dashboard_screenshots", "architecture_diagram.png"), width=Inches(6.5))

doc.add_paragraph("This architecture is suitable because it separates transactional systems from analytical reporting, allows data quality handling before load, and supports repeatable BI reporting with a single analytical source of truth.")

# Task 4

doc.add_heading("4. Task 4 – Dimensional Data Warehouse Design and Implementation", level=1)
doc.add_paragraph("The implementation uses a star schema with one fact table and multiple dimensions.")
doc.add_paragraph("Fact table: Fact_CustomerAccount")
doc.add_paragraph("Dimension tables: Dim_Customer, Dim_Location, Dim_Service, Dim_Contract, and Dim_Date")
doc.add_paragraph("Business grain: one row per customer account record. The generated fact export contains 7,043 rows and one row per customer account, supporting churn and revenue analysis at customer-account level.")
doc.add_paragraph("Fact key roles: CustomerAccountKey is the fact table primary key. CustomerKey, LocationKey, ServiceKey, ContractKey, and DateKey are foreign keys to their matching dimensions.")
doc.add_paragraph("Measures and analysis attributes: Tenure_Months, Monthly_Charges, Total_Charges, Avg_Monthly_Spend, Tenure_Years, Churn_Value, Churn_Score, CLTV, and Risk_Segment. Churn_Value is a 0/1 indicator; its average represents the churn rate.")
doc.add_paragraph("Dimension primary keys are CustomerKey, LocationKey, ServiceKey, ContractKey, and DateKey. The relationships are from each dimension key to its matching fact foreign key. The date hierarchy is Year > Quarter > Month, with MonthName sorted by MonthNumber. The customer key is unique in both the current fact and customer dimension because this dataset contains one account row per customer.")
doc.add_paragraph("Date implementation note: the SQLite ETL prototype uses one snapshot date (DateKey 1, 2023-09-30). The separate Task 4 SQL/Power BI star-schema export derives 73 date rows from customer Join_Date values for quarterly analysis. These are separate generated outputs and should not be described as one synchronized database model.")

doc.add_picture(os.path.join(root, "assets", "images", "star_schema_erd.png"), width=Inches(6.5))
doc.add_paragraph("Power BI Model view evidence: the six fact and dimension tables are connected in the semantic model. Dim_Customer to Fact_CustomerAccount is an active one-to-one relationship because the dataset has one account row per customer.")
doc.add_picture(os.path.join(root, "assets", "dashboard_screenshots", "semantic_model_star_schema.png"), width=Inches(6.5))
doc.add_paragraph("SQL Server load validation: SSMS row counts match the exported tables: Dim_Customer 7,043; Dim_Location 1,652; Dim_Service 322; Dim_Contract 24; Dim_Date 73; and Fact_CustomerAccount 7,043. A foreign-key validation query returned zero orphan fact rows for CustomerKey, LocationKey, ServiceKey, ContractKey, and DateKey.")
doc.add_picture(os.path.join(root, "assets", "dashboard_screenshots", "ssms_row_counts.png"), width=Inches(6.5))

dim_table = [
    ("Fact_CustomerAccount", "One row per customer account; PK CustomerAccountKey", "FKs CustomerKey, LocationKey, ServiceKey, ContractKey, DateKey; Tenure_Months, Monthly_Charges, Total_Charges, Avg_Monthly_Spend, Tenure_Years, Churn_Value, Churn_Score, CLTV, Risk_Segment"),
    ("Dim_Customer", "Customer dimension; PK CustomerKey", "CustomerID, Gender, Senior_Citizen, Partner, Dependents"),
    ("Dim_Location", "Location dimension; PK LocationKey", "City, Zip_Code, Latitude, Longitude"),
    ("Dim_Service", "Service feature dimension; PK ServiceKey", "Phone_Service, Multiple_Lines, Internet_Service, Online_Security, Online_Backup, Device_Protection, Tech_Support, Streaming_TV, Streaming_Movies"),
    ("Dim_Contract", "Contract and billing dimension; PK ContractKey", "Contract, Paperless_Billing, Payment_Method"),
    ("Dim_Date", "Date reference dimension; PK DateKey", "FullDate, Year, Quarter, MonthName, MonthNumber, QuarterName"),
]
add_table(dim_table, ["Table", "Purpose", "Key attributes"])

doc.add_paragraph("The schema supports customer, service, location, and contract-based intelligence and provides a strong basis for executive summary, trend analysis, and segmentation reporting.")

doc.add_heading("Design Decision Matrix", level=2)
design_rows = [
    ("Business process", "Customer-account churn, retention, and charges analysis"),
    ("Fact table", "Fact_CustomerAccount"),
    ("Grain", "One row per customer account; 7,043 rows in the Task 4 export"),
    ("Measures", "Tenure_Months, Monthly_Charges, Total_Charges, Avg_Monthly_Spend, Tenure_Years, Churn_Value, Churn_Score, CLTV"),
    ("Dimensions", "Dim_Customer, Dim_Location, Dim_Service, Dim_Contract, Dim_Date"),
]
add_table(design_rows, ["Decision", "Implementation"])

doc.add_heading("Surrogate and Foreign Key Map", level=2)
key_rows = [
    ("Dim_Customer.CustomerKey", "Fact_CustomerAccount.CustomerKey", "Customer account profile"),
    ("Dim_Location.LocationKey", "Fact_CustomerAccount.LocationKey", "City and ZIP geography"),
    ("Dim_Service.ServiceKey", "Fact_CustomerAccount.ServiceKey", "Subscribed service combination"),
    ("Dim_Contract.ContractKey", "Fact_CustomerAccount.ContractKey", "Contract and payment attributes"),
    ("Dim_Date.DateKey", "Fact_CustomerAccount.DateKey", "Snapshot date in SQLite; join date in the separate Task 4 export"),
]
add_table(key_rows, ["Dimension Primary Key", "Fact Foreign Key", "Relationship Meaning"])
doc.add_paragraph("The dimension keys are warehouse surrogate keys generated for the exports and declared as IDENTITY primary keys in the SQL Server DDL. CustomerID remains the natural/business identifier in Dim_Customer. In the current dataset CustomerKey is unique on both the dimension and fact sides because the grain is one account per customer.")

doc.add_heading("Future Slowly Changing Dimensions", level=2)
doc.add_paragraph("SCD processing is not implemented. If customer, location, service, or contract attributes change over time, a Type 2 design could add effective-start and effective-end dates plus a current-row indicator, create a new surrogate-key version for each change, and retain historical fact-to-dimension links.")

# Task 5

doc.add_heading("5. Task 5 – ETL Process Development", level=1)
doc.add_paragraph("The ETL process was implemented in Python using the pandas and sqlite3 libraries. It follows a reproducible workflow: Extract → Transform → Load.")

doc.add_paragraph("Extract: the data was read from CSV and JSON sources, including the customer billing data, location reference table, and service subscriptions.")
doc.add_paragraph("Transform: blank values were handled, text columns were standardised, duplicates were checked, numeric data types were validated, and derived attributes such as Avg_Monthly_Spend and Tenure_Years were created.")
doc.add_paragraph("Load: transformed records were inserted into fact and dimension tables in SQLite, using surrogate keys to maintain relationship integrity and warehouse consistency.")

doc.add_paragraph("The ETL log file documents each step and confirms the pipeline was run successfully. This provides evidence of orderly transformation and warehouse population.")

doc.add_picture(os.path.join(root, "assets", "screenshots", "assets/screenshots/etl_log_screenshot.png"), width=Inches(6.0))

doc.add_paragraph("ETL validation checks included null foreign key validation, churn-rate matching before and after the load, and row-count reconciliation between the source data and the fact table.")

doc.add_heading("Complete ETL Execution Sequence", level=2)
etl_steps = [
    "Extract customer/billing CSV (7,043 rows), location-reference CSV (1,652 rows), and service-subscription JSON (7,043 rows).",
    "Left-join location on Zip_Code and service subscriptions on CustomerID; clean blanks, trim text, check duplicate CustomerID values, convert numeric types, and derive Avg_Monthly_Spend and Tenure_Years.",
    "Stage the cleaned merged dataframe in cleaned_master.pkl. The code does not create a separate staging database schema.",
    "Build dimensions and assign sequential surrogate keys to distinct dimension rows.",
    "Load SQLite dimensions in this order: Dim_Customer, Dim_Location, Dim_Service, Dim_Contract, Dim_Date; then attach keys and load Fact_CustomerAccount.",
    "For the separate Task 4 CSV/SQL Server export, use the 73 Join_Date-derived rows in Dim_Date, import all dimensions first, and import Fact_CustomerAccount last.",
    "Validate null foreign keys, compare churn rate before/after load, reconcile source/fact counts, and check SQL Server for unmatched fact keys.",
]
for step in etl_steps:
    doc.add_paragraph(step, style="List Number")
doc.add_paragraph("The SQLite ETL writes to telecom_dw_new.db and uses a one-row snapshot Dim_Date. data/warehouse/telecom_dw.db is a separate populated warehouse database that contains Mart_CustomerRetention. These database outputs are not one synchronized load target.")

# Task 6

doc.add_heading("6. Task 6 – Data Mart Development", level=1)
doc.add_paragraph("A department-specific data mart was created to support retention and churn analysis for business users. The mart is centred on customer risk and churn exposure and is designed for decision-makers in customer retention and commercial strategy.")
doc.add_paragraph("Purpose: support proactive risk management and customer retention planning.")
doc.add_paragraph("Target users: customer success managers, sales and retention managers, executive leadership, and telecom operations teams.")
doc.add_paragraph("Analytical benefits: the data mart enables churn segmentation, contract-risk analysis, service sensitivity analysis, and monthly revenue exposure reviews.")
doc.add_paragraph("The final retention mart includes fields such as CustomerID, Contract, Internet_Service, Payment_Method, Monthly_Charges, Churn_Value, Risk_Segment, and Join_Quarter, which make it directly useful for BI dashboards and retention planning.")
doc.add_heading("Mart Object, Views, and Governance", level=2)
doc.add_paragraph("The implemented mart object is the physical table Mart_CustomerRetention in data/warehouse/telecom_dw.db, with 7,043 rows; data/processed/retention_mart.csv is its flat-file export. No retention-focused SQL views were found in the inspected SQLite objects or SQL Server DDL. The mart's curated, denormalized fields reduce query complexity for retention analysis. A dedicated mart can simplify user access and support consistent definitions, but this project does not implement SQL roles, row-level security, or view-based security; those are deployment considerations rather than completed controls.")

# Task 7

doc.add_heading("7. Task 7 – OLAP Analysis and Business Intelligence Dashboard Development", level=1)
doc.add_paragraph("The solution uses Microsoft Power BI to present an interactive warehouse-based dashboard with three report pages. The final star-schema report is saved as dashboard/Telecom_Churn_Dashboard_StarSchema.pbix; its visual field bindings reference Fact_CustomerAccount and the applicable dimensions rather than retention_mart.")

doc.add_paragraph("Report Page 1: Executive Summary")
doc.add_paragraph("This page contains KPI cards for 7,043 customers, 26.54% overall churn, $64.76 average monthly charges, and $4,400 average customer lifetime value. A donut chart shows the customer distribution by Risk_Segment, and a treemap shows summed monthly charges by Contract and Internet_Service.")
doc.add_picture(os.path.join(root, "assets", "dashboard_screenshots", "page1_executive_summary.png"), width=Inches(6.2))

doc.add_paragraph("Report Page 2: Trend Analysis")
doc.add_paragraph("This page compares customer counts by Join_Quarter and average Monthly_Charges by Join_Quarter. A city-by-contract matrix compares average Churn_Score for the displayed cities; the Top N city filter ranks cities by customer count. Churn_Score is a score, not a churn-rate percentage.")
doc.add_picture(os.path.join(root, "assets", "dashboard_screenshots", "page2_trend_analysis.png"), width=Inches(6.2))

doc.add_paragraph("Report Page 3: Interactive Analysis")
doc.add_paragraph("This page provides Contract, Internet_Service, Risk_Segment, and Year slicers, a clear-all-slicers control, a city/contract matrix with customer counts and average Churn_Score, and a customer-level scatter plot of Tenure_Months against Monthly_Charges, sized by CLTV and colored by Risk_Segment. The city/contract matrix supports drill-down and roll-up between city and contract levels.")
doc.add_picture(os.path.join(root, "assets", "dashboard_screenshots", "page3_interactive_analysis.png"), width=Inches(6.2))

doc.add_heading("Power BI Aggregations and OLAP Operations Matrix", level=2)
doc.add_paragraph("No named custom DAX measures were found in the PBIX visual query metadata. The visuals use implicit aggregations; the relationship guide's sample formulas are recommendations, not evidence of measures stored in this PBIX.")
dax_rows = [
    ("Total customers", "Fact_CustomerAccount[CustomerAccountKey]", "Count of nonblank values; implicit visual aggregation, no stored DAX formula"),
    ("Overall churn rate", "Fact_CustomerAccount[Churn_Value]", "Average of the 0/1 outcome; no stored DAX formula"),
    ("Average monthly charges", "Fact_CustomerAccount[Monthly_Charges]", "Average; no stored DAX formula"),
    ("Average CLTV", "Fact_CustomerAccount[CLTV]", "Average; no stored DAX formula"),
    ("Customers by risk segment", "Fact_CustomerAccount[Risk_Segment] and [CustomerAccountKey]", "Category by count of nonblank account keys"),
    ("Treemap charges", "Fact_CustomerAccount[Monthly_Charges]", "Sum by Dim_Contract[Contract] and Dim_Service[Internet_Service]; Average Churn_Value tooltip"),
    ("Join-quarter customers", "Fact_CustomerAccount[CustomerAccountKey] by Dim_Date[Quarter]", "Count of nonblank account keys"),
    ("Join-quarter charges", "Fact_CustomerAccount[Monthly_Charges] by Dim_Date[Quarter]", "Average"),
    ("City/contract score", "Fact_CustomerAccount[Churn_Score] by City and Contract", "Average; City Top 10 is ranked by account count"),
    ("Customer scatter", "Tenure_Months, Monthly_Charges, CLTV, Risk_Segment, CustomerAccountKey", "Average X/Y/Size, Risk_Segment series, account key identifies customer-level points"),
]
add_table(dax_rows, ["Visual Metric", "PBIX Field(s)", "Actual PBIX Aggregation"])
olap_rows = [
    ("Slice", "Select one Contract, Internet_Service, Risk_Segment, or Year slicer value."),
    ("Dice", "Combine two or more slicers to filter a multi-attribute subset."),
    ("Drill-down", "Expand the Interactive Analysis matrix from City to Contract rows."),
    ("Roll-up", "Collapse the matrix from Contract level back to City."),
    ("Cross-filter", "Slicer and visual selections filter or highlight related report visuals."),
]
add_table(olap_rows, ["OLAP Operation", "Existing Dashboard Control"])

doc.add_paragraph("The dashboard demonstrates OLAP-style analysis by enabling business users to compare dimensions and fact measures efficiently, which is a key objective of the assignment.")

# Task 8

doc.add_heading("8. Task 8 – Business Insights and Recommendations", level=1)
high_risk_customers = 2559
high_risk_share = 36.33
medium_risk_customers = 2805
medium_risk_share = 39.83
low_risk_customers = 1679
low_risk_share = 23.84
average_charges_2023q3 = 53.32
average_charges_2017q4 = 78.09
charges_change_pct = (average_charges_2023q3 / average_charges_2017q4 - 1) * 100

insights = [
    ("Overall churn exposure", "1,869 of 7,043 accounts have Churn_Value = 1, giving an overall churn rate of 26.54%.", "Use the Executive Summary churn KPI as the baseline for monitoring retention initiatives."),
    ("Risk-segment mix", f"The risk donut shows {high_risk_customers:,} High Risk customers ({high_risk_share:.2f}%), {medium_risk_customers:,} Medium Risk customers ({medium_risk_share:.2f}%), and {low_risk_customers:,} Low Risk customers ({low_risk_share:.2f}%).", "Prioritize review of High Risk accounts and monitor the larger Medium Risk segment."),
    ("Largest contract/service charge category", "The treemap's Month-to-month/Fiber optic category has $185,181.10 in summed monthly charges, the largest displayed category.", "Review retention offers and service experience for this high-charge cohort; the visual shows revenue exposure, not proof of churn causality."),
    ("Join-quarter customer counts", "The cohort chart shows 419 accounts in 2023Q2 and 1,062 in 2023Q3. Join_Date is derived from tenure/snapshot data, so this is not a verified acquisition time series.", "Validate the apparent Q3 cohort increase against acquisition records before using it for staffing or growth decisions."),
    ("Average charges by join cohort", f"Average Monthly_Charges are ${average_charges_2017q4:.2f} for 2017Q4 and ${average_charges_2023q3:.2f} for 2023Q3 join cohorts, a {abs(charges_change_pct):.2f}% difference. This compares cohorts, not customer prices over time.", "Compare plan mix and customer value across cohorts before changing pricing or offers."),
    ("City/contract churn-score contrast", "The displayed matrix reports average Churn_Score 69.13 for San Francisco/Month-to-month and 40.50 for Bakersfield/One year; the Bakersfield cell has six accounts. Churn_Score is not a churn-rate percentage.", "Review higher-scoring combinations and validate them against actual churn outcomes before targeting interventions."),
    ("Customer concentration by city", "The displayed city matrix shows 305 Los Angeles accounts and 150 San Diego accounts.", "Prioritize investigation of customer experience and retention patterns in the largest displayed city cohorts."),
]

for index, (name, evidence, recommendation) in enumerate(insights, start=1):
    doc.add_heading(f"Insight {index}: {name}", level=2)
    doc.add_paragraph(f"Technical Evidence: {evidence}")
    doc.add_paragraph(f"Actionable Recommendation: {recommendation}")

# AI usage disclosure

doc.add_heading("9. AI Usage Disclosure", level=1)
doc.add_paragraph("AI tools were used as a supporting aid for brainstorming, report wording improvement, and refinement of analytical explanations. All final technical work, ETL logic, and business interpretations were reviewed and validated by the author against the project data and assignment requirements. The final submission reflects the author’s own understanding and implementation decisions.")

# References

doc.add_heading("10. References", level=1)
refs = [
    "IBM Telco Customer Churn Dataset (extended version), Kaggle.",
    "Power BI Dashboard implementation for customer retention and churn analysis.",
    "Python ETL pipeline for data extraction, cleaning, and warehouse loading.",
    "Assignment brief: IT3101 – Data Warehousing and Business Intelligence.",
]
for ref in refs:
    doc.add_paragraph(ref)

# Appendices

doc.add_heading("Appendix A – Technical Evidence", level=1)
appendix_a_rows = [
    ("assets/screenshots/etl_script_screenshot.png", "Python ETL implementation."),
    ("assets/screenshots/etl_log_screenshot.png; logs/etl_log.txt", "ETL execution stages and logged row-count/churn validation."),
    ("star_schema_erd.png", "Designed star schema for Task 4."),
    ("assets/dashboard_screenshots/semantic_model_star_schema.png", "Power BI Model view with the fact and five dimension tables and active relationships."),
    ("assets/dashboard_screenshots/ssms_row_counts.png", "SSMS table counts: 7,043 customer, 1,652 location, 322 service, 24 contract, 73 date, and 7,043 fact rows."),
    ("assets/dashboard_screenshots/page1_executive_summary.png; page2_trend_analysis.png; page3_interactive_analysis.png", "The three Power BI report pages."),
    ("assets/dashboard_screenshots/filtering_before.png; filtering_after.png", "Filter interaction evidence."),
    ("assets/dashboard_screenshots/drilldown_before.png; drilldown_after.png", "Drill-down interaction evidence."),
    ("assets/dashboard_screenshots/brushing_before.png; brushing_after.png", "Visual-selection/brushing evidence."),
    ("assets/dashboard_screenshots/architecture_diagram.png; Source Integration and Relationship Diagram.png", "Architecture and source-integration diagrams."),
]
add_table(appendix_a_rows, ["Evidence File(s)", "Description"])
doc.add_paragraph("A separate screenshot of the zero-orphan foreign-key query is not included in the current package; add it if screenshot evidence of that validation is required.")

doc.add_heading("Appendix B – Project File Inventory", level=1)
appendix_b_rows = [
    ("IT3101_DWBI_Report_Final.docx", "Final report; blank page one reserved for the student cover, student roster on page two."),
    ("dashboard/Telecom_Churn_Dashboard_StarSchema.pbix", "Final three-page Power BI report using the fact and dimension tables."),
    ("data/warehouse/telecom_dw.db", "Populated SQLite warehouse and Mart_CustomerRetention table."),
    ("data/processed/retention_mart.csv", "7,043-row retention mart export."),
    ("data/source/customer_billing_source.csv", "Customer and billing source data."),
    ("data/source/location_reference_source.csv", "ZIP-code location reference source."),
    ("data/source/service_subscription_source.json", "Service subscription source data."),
    ("data/raw/Telco_customer_churn.xlsx", "Original customer churn workbook."),
    ("etl_pipeline.py", "Python/pandas/SQLite extraction, transformation, and load implementation."),
    ("logs/etl_log.txt", "ETL run and validation log."),
    ("assets/screenshots/etl_script_screenshot.png; assets/screenshots/etl_log_screenshot.png", "ETL implementation and execution screenshots."),
    ("build_final_assignment_report.py", "Reproducible report and summary generator."),
    ("generate_ssms_star_schema.py", "Generates Task 4 star-schema SQL and CSV exports."),
    ("assignment_completion_summary.md", "Submission contents and implementation notes."),
    ("star_schema_erd.png", "Star-schema diagram."),
    ("assets/dashboard_screenshots/architecture_diagram.png", "High-level DW/BI architecture."),
    ("assets/dashboard_screenshots/Source Integration and Relationship Diagram.png", "Source integration diagram."),
    ("assets/dashboard_screenshots/page1_executive_summary.png; page2_trend_analysis.png; page3_interactive_analysis.png", "Dashboard page screenshots."),
    ("assets/dashboard_screenshots/filtering_before.png; filtering_after.png; drilldown_before.png; drilldown_after.png; brushing_before.png; brushing_after.png", "Interactive filtering, drill, and brushing evidence."),
    ("assets/dashboard_screenshots/semantic_model_star_schema.png", "Power BI semantic model screenshot."),
    ("assets/dashboard_screenshots/ssms_row_counts.png", "SSMS imported row-count evidence."),
    ("sql/star_schema_exports/ssms_star_schema.sql", "SQL Server star-schema DDL with primary and foreign keys."),
    ("sql/star_schema_exports/Fact_CustomerAccount.csv", "Task 4 account-grain fact export."),
    ("sql/star_schema_exports/Dim_Customer.csv; Dim_Location.csv; Dim_Service.csv; Dim_Contract.csv; Dim_Date.csv", "Task 4 dimension exports."),
    ("sql/star_schema_exports/powerbi_relationship_guide.md", "Power BI relationship and import guidance."),
]
add_table(appendix_b_rows, ["File or Folder", "Description"])

# Save docx
try:
    doc.save(report_path)
    print(f"Saved final report to: {report_path}")
except Exception as e:
    print('Error saving report', e)

# Save markdown summary
md = """# Assignment Submission Contents

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
"""
with open(summary_md_path, "w", encoding="utf-8") as f:
    f.write(md)
print(f"Saved summary markdown to: {summary_md_path}")
