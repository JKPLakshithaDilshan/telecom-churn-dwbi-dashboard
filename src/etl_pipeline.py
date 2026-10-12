"""
ETL Pipeline: Telecom Customer Churn Data Warehouse
=====================================================
Extracts data from three source systems, transforms it (cleaning,
standardisation, derived attributes), and loads it into a star-schema
data warehouse (SQLite).

Sources:
  1. customer_billing_source.csv   - Customer & Billing System (CSV)
  2. location_reference_source.csv - Geographic Reference System (CSV)
  3. service_subscription_source.json - Service Provisioning System (JSON)
  4. Telco_customer_churn.xlsx         - original raw export (Excel), used only to
                                         audit/reconcile the prepared sources

Target: telecom_dw.db (SQLite) containing 1 fact table + 5 dimension tables,
the Stg_CustomerMaster staging table, the Mart_CustomerRetention data mart and its views
(Dim_Date is built from the derived Join_Date: 73 rows, Year > Quarter > Month > Date)
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

import retention_mart_sql as mart_sql

ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "data" / "source"
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
WAREHOUSE_DIR = ROOT_DIR / "data" / "warehouse"
LOG_DIR = ROOT_DIR / "logs"
DB_PATH = WAREHOUSE_DIR / "telecom_dw.db"
SNAPSHOT_DATE = pd.Timestamp("2023-09-30")   # date the source extract was taken (assumption)
DAYS_PER_TENURE_MONTH = 30                  # tenure month approximated as 30 days

log = []
def step(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    log.append(f"[{ts}] {msg}")


# =====================================================================
# EXTRACT
# =====================================================================
step("EXTRACT: Reading Source 1 - Customer & Billing System (CSV)")
source1 = pd.read_csv(SOURCE_DIR / "customer_billing_source.csv")
step(f"  -> {source1.shape[0]} rows, {source1.shape[1]} columns extracted")

step("EXTRACT: Reading Source 2 - Location Reference System (CSV)")
source2 = pd.read_csv(SOURCE_DIR / "location_reference_source.csv")
step(f"  -> {source2.shape[0]} rows, {source2.shape[1]} columns extracted")

step("EXTRACT: Reading Source 3 - Service Provisioning System (JSON)")
with open(SOURCE_DIR / "service_subscription_source.json") as f:
    source3 = pd.DataFrame(json.load(f))
step(f"  -> {source3.shape[0]} rows, {source3.shape[1]} columns extracted")

# Source-preparation audit: the three prepared sources above were derived from the
# original raw Excel export. Reading the raw file lets the pipeline prove what the
# preparation step fixed and that no records were lost.
RAW_XLSX = RAW_DIR / "Telco_customer_churn.xlsx"
step("EXTRACT: Reading Source 4 - original raw export (Excel) for source-preparation audit")
raw = None
if os.path.exists(RAW_XLSX):
    raw = pd.read_excel(RAW_XLSX)
    step(f"  -> {raw.shape[0]} rows, {raw.shape[1]} columns extracted")
    raw_blank_tc = int((raw['Total Charges'].astype(str).str.strip() == '').sum())
    raw_null_reason = int(raw['Churn Reason'].isnull().sum())
    step(f"  -> Raw issues found: {raw_blank_tc} blank Total Charges, {raw_null_reason} empty Churn Reason (active customers)")
    step(f"  -> Raw categories kept as-is by design: {int((raw['Multiple Lines'] == 'No phone service').sum())} 'No phone service', "
         f"{int((raw['Internet Service'] == 'No').sum())} accounts with no internet service")
    ids_raw = set(raw['CustomerID'])
    step(f"  -> Reconciliation: CustomerID sets identical across raw, billing CSV and service JSON: "
         f"{ids_raw == set(source1['CustomerID']) == set(source3['CustomerID'])}")
    step(f"  -> Reconciliation: prepared sources hold {int((source1['Tenure_Months'] == 0).sum())} tenure-0 accounts "
         f"(raw blank Total Charges = {raw_blank_tc}; all blanks belong to tenure-0 accounts: "
         f"{bool((raw.loc[raw['Total Charges'].astype(str).str.strip() == '', 'Tenure Months'] == 0).all())})")
else:
    step("  -> Raw Excel not found - audit skipped")


# =====================================================================
# TRANSFORM
# =====================================================================
step("TRANSFORM: Joining sources on Zip_Code and CustomerID")
merged = source1.merge(source2, on="Zip_Code", how="left")
merged = merged.merge(source3, on="CustomerID", how="left")
unmatched_zip = int(merged['City'].isnull().sum())   # checked here, before text trimming
step(f"  -> Merged dataset: {merged.shape[0]} rows, {merged.shape[1]} columns")

step("TRANSFORM: Missing value handling")
blank_before = (merged['Total_Charges'].astype(str).str.strip() == '').sum()
merged['Total_Charges'] = merged['Total_Charges'].astype(str).str.strip().replace('', '0').astype(float)
step(f"  -> Blank Total_Charges remaining in prepared source: {blank_before} (set to 0 and cast to float; "
     f"raw export had {raw_blank_tc if raw is not None else 'n/a'}, already fixed during source preparation)")

null_reason_before = merged['Churn_Reason'].isnull().sum()
merged['Churn_Reason'] = merged['Churn_Reason'].fillna('Not Applicable - Active Customer')
step(f"  -> Null Churn_Reason remaining in prepared source: {null_reason_before} "
     f"(raw export had {raw_null_reason if raw is not None else 'n/a'}, labelled 'Not Applicable - Active Customer' during preparation)")

step("TRANSFORM: Deduplication check")
dupes = merged['CustomerID'].duplicated().sum()
step(f"  -> Duplicate CustomerIDs found: {dupes}")
if dupes:
    merged = merged.drop_duplicates(subset='CustomerID', keep='first').reset_index(drop=True)
    step(f"  -> Removed {dupes} duplicate rows (kept first occurrence)")

step("TRANSFORM: Standardisation - trimming whitespace on text columns")
text_cols = merged.select_dtypes(include=['object','str']).columns
for c in text_cols:
    merged[c] = merged[c].astype(str).str.strip()
step(f"  -> Trimmed {len(text_cols)} text columns")

step("TRANSFORM: Derived attribute creation")
merged['Avg_Monthly_Spend'] = (merged['Total_Charges'] / merged['Tenure_Months'].replace(0, 1)).round(2)
merged['Tenure_Years'] = (merged['Tenure_Months'] / 12).round(1)
step("  -> Created Avg_Monthly_Spend and Tenure_Years derived columns")

# Join date is not stored in the source system, so it is derived from tenure.
# Join_Date = snapshot date - (Tenure_Months x 30 days). This gives the Date
# dimension a real calendar hierarchy (Year > Quarter > Month > Date).
merged['Join_Date'] = (SNAPSHOT_DATE - pd.to_timedelta(merged['Tenure_Months'] * DAYS_PER_TENURE_MONTH, unit='D')).dt.strftime('%Y-%m-%d')
step(f"  -> Created Join_Date derived column (snapshot {SNAPSHOT_DATE.date()} minus tenure x {DAYS_PER_TENURE_MONTH} days); "
     f"{merged['Join_Date'].nunique()} distinct join dates")

# Risk segment banding from the churn score (High >= 70, Medium 40-69, Low < 40).
merged['Risk_Segment'] = pd.cut(merged['Churn_Score'], bins=[-1, 39, 69, 100],
                                labels=['Low Risk', 'Medium Risk', 'High Risk']).astype(str)
step(f"  -> Created Risk_Segment (Low <40, Medium 40-69, High >=70): {merged['Risk_Segment'].value_counts().to_dict()}")

step("TRANSFORM: Data type conversion check")
merged['Churn_Value'] = merged['Churn_Value'].astype(int)
merged['Churn_Score'] = merged['Churn_Score'].astype(int)
merged['CLTV'] = merged['CLTV'].astype(int)
step("  -> Confirmed Churn_Value, Churn_Score, CLTV as integer types")


step("TRANSFORM: Data quality rules (critical rules stop the pipeline)")
dq_failures = []
def dq_rule(name, violations, critical=True):
    violations = int(violations)
    status = "PASS" if violations == 0 else ("FAIL" if critical else "FLAGGED - retained")
    step(f"  -> {name}: {violations} violations [{status}]")
    if violations and critical:
        dq_failures.append(name)

expected = merged['Tenure_Months'] * merged['Monthly_Charges']
dq_rule("R1 Every customer Zip_Code exists in the location reference", unmatched_zip)
dq_rule("R2 Churn_Label agrees with Churn_Value", ((merged['Churn_Label'] == 'Yes') != (merged['Churn_Value'] == 1)).sum())
dq_rule("R3 Churn_Score within 0-100", (~merged['Churn_Score'].between(0, 100)).sum())
dq_rule("R4 Monthly_Charges > 0 and Tenure_Months >= 0", ((merged['Monthly_Charges'] <= 0) | (merged['Tenure_Months'] < 0)).sum())
dq_rule("R5 Total_Charges is 0 only for tenure-0 accounts",
        (((merged['Total_Charges'] <= 0) & (merged['Tenure_Months'] > 0)) | ((merged['Total_Charges'] > 0) & (merged['Tenure_Months'] == 0))).sum())
na_reason = 'Not Applicable - Active Customer'
dq_rule("R6 Churn_Reason present for churned customers only",
        (((merged['Churn_Value'] == 0) & (merged['Churn_Reason'] != na_reason)) | ((merged['Churn_Value'] == 1) & (merged['Churn_Reason'] == na_reason))).sum())
dq_rule("R7 CLTV > 0", (merged['CLTV'] <= 0).sum())
dq_rule("R8 Total_Charges within 50% of Tenure x Monthly_Charges",
        ((merged['Total_Charges'] - expected).abs() > 0.5 * (expected + 1)).sum(), critical=False)
if dq_failures:
    raise ValueError(f"ETL stopped - critical data quality rules failed: {dq_failures}")

step(f"TRANSFORM COMPLETE: Final cleaned dataset {merged.shape[0]} rows x {merged.shape[1]} columns")


# =====================================================================
# LOAD
# =====================================================================
step("LOAD: Connecting to target warehouse (SQLite)")
WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB_PATH)

step("LOAD: Writing staging table Stg_CustomerMaster (cleaned, integrated, pre-dimensional)")
merged.to_sql('Stg_CustomerMaster', conn, if_exists='replace', index=False)
stg_rows = conn.execute("SELECT COUNT(*) FROM Stg_CustomerMaster").fetchone()[0]
step(f"  -> Staged {stg_rows} rows x {merged.shape[1]} columns")

step("LOAD: Building Dim_Customer")
dim_customer = merged[['CustomerID','Gender','Senior_Citizen','Partner','Dependents']].drop_duplicates().reset_index(drop=True)
dim_customer.insert(0, 'CustomerKey', range(1, len(dim_customer)+1))
dim_customer.to_sql('Dim_Customer', conn, if_exists='replace', index=False)
step(f"  -> Loaded {len(dim_customer)} rows")

step("LOAD: Building Dim_Location")
dim_location = merged[['City','Zip_Code','Latitude','Longitude']].drop_duplicates(subset='Zip_Code').reset_index(drop=True)
dim_location.insert(0, 'LocationKey', range(1, len(dim_location)+1))
dim_location.to_sql('Dim_Location', conn, if_exists='replace', index=False)
step(f"  -> Loaded {len(dim_location)} rows")

step("LOAD: Building Dim_Service (junk dimension)")
service_cols = ['Phone_Service','Multiple_Lines','Internet_Service','Online_Security',
                'Online_Backup','Device_Protection','Tech_Support','Streaming_TV','Streaming_Movies']
dim_service = merged[service_cols].drop_duplicates().reset_index(drop=True)
dim_service.insert(0, 'ServiceKey', range(1, len(dim_service)+1))
dim_service.to_sql('Dim_Service', conn, if_exists='replace', index=False)
step(f"  -> Loaded {len(dim_service)} rows")

step("LOAD: Building Dim_Contract")
dim_contract = merged[['Contract','Paperless_Billing','Payment_Method']].drop_duplicates().reset_index(drop=True)
dim_contract.insert(0, 'ContractKey', range(1, len(dim_contract)+1))
dim_contract.to_sql('Dim_Contract', conn, if_exists='replace', index=False)
step(f"  -> Loaded {len(dim_contract)} rows")

step("LOAD: Building Dim_Date (derived from Join_Date)")
dim_date = pd.DataFrame({'FullDate': sorted(merged['Join_Date'].unique())})
_d = pd.to_datetime(dim_date['FullDate'])
dim_date['Year'] = _d.dt.year
dim_date['Quarter'] = _d.dt.year.astype(str) + 'Q' + _d.dt.quarter.astype(str)
dim_date['MonthName'] = _d.dt.strftime('%B')
dim_date['MonthNumber'] = _d.dt.month
dim_date['QuarterName'] = dim_date['Quarter']
dim_date.insert(0, 'DateKey', range(1, len(dim_date)+1))
dim_date.to_sql('Dim_Date', conn, if_exists='replace', index=False)
step(f"  -> Loaded {len(dim_date)} rows ({dim_date['FullDate'].min()} to {dim_date['FullDate'].max()})")

step("LOAD: Building Fact_CustomerAccount (attaching surrogate keys)")
fact = merged.merge(dim_customer, on=['CustomerID','Gender','Senior_Citizen','Partner','Dependents'], how='left')
fact = fact.merge(dim_location, on=['City','Zip_Code','Latitude','Longitude'], how='left')
fact = fact.merge(dim_service, on=service_cols, how='left')
fact = fact.merge(dim_contract, on=['Contract','Paperless_Billing','Payment_Method'], how='left')
fact = fact.merge(dim_date[['FullDate','DateKey']], left_on='Join_Date', right_on='FullDate', how='left')

fact_table = fact[['CustomerKey','LocationKey','ServiceKey','ContractKey','DateKey',
                    'Tenure_Months','Monthly_Charges','Total_Charges','Avg_Monthly_Spend',
                    'Tenure_Years','Churn_Value','Churn_Score','CLTV','Risk_Segment']].copy()
fact_table.insert(0, 'CustomerAccountKey', range(1, len(fact_table)+1))
fact_table.to_sql('Fact_CustomerAccount', conn, if_exists='replace', index=False)
step(f"  -> Loaded {len(fact_table)} rows into Fact_CustomerAccount")

# ---------------------------------------------------------------------
# DATA MART: Mart_CustomerRetention is derived from the warehouse (fact + dimensions),
# not from the staging data, then analytical views are layered on top of it.
# SQL lives in retention_mart_sql.py so SQLite and SQL Server use identical logic.
# ---------------------------------------------------------------------
step("LOAD: Building data mart Mart_CustomerRetention from the star schema")
for v in mart_sql.VIEWS:
    conn.execute(f"DROP VIEW IF EXISTS {v}")
conn.execute("DROP TABLE IF EXISTS Mart_CustomerRetention")
conn.execute("CREATE TABLE Mart_CustomerRetention AS " + mart_sql.MART_SELECT + " ORDER BY f.CustomerAccountKey")
mart_rows = conn.execute("SELECT COUNT(*) FROM Mart_CustomerRetention").fetchone()[0]
step(f"  -> Loaded {mart_rows} rows x {len(mart_sql.MART_COLUMNS)} columns")

step("LOAD: Creating retention analytical views on the mart")
for v, (question, select) in mart_sql.VIEWS.items():
    conn.execute(f"CREATE VIEW {v} AS {select}")
    n = conn.execute(f"SELECT COUNT(*) FROM {v}").fetchone()[0]
    step(f"  -> {v}: {n} rows - {question}")

pd.read_sql("SELECT * FROM Mart_CustomerRetention", conn).to_csv(PROCESSED_DIR / "retention_mart.csv", index=False)
step("LOAD: Exported mart to data/processed/retention_mart.csv")
conn.commit()


# =====================================================================
# VALIDATION
# =====================================================================
step("VALIDATION: Checking for null foreign keys")
null_fks = fact_table[['CustomerKey','LocationKey','ServiceKey','ContractKey','DateKey']].isnull().sum().sum()
step(f"  -> Null foreign keys found: {null_fks} (expected: 0)")

step("VALIDATION: Checking every fact foreign key exists in its dimension (orphan check)")
for fk, dim, name in [('CustomerKey', dim_customer, 'Dim_Customer'), ('LocationKey', dim_location, 'Dim_Location'),
                      ('ServiceKey', dim_service, 'Dim_Service'), ('ContractKey', dim_contract, 'Dim_Contract'),
                      ('DateKey', dim_date, 'Dim_Date')]:
    orphans = (~fact_table[fk].isin(dim[fk])).sum()
    step(f"  -> {fk} -> {name}: {orphans} orphan rows (expected: 0)")

step("VALIDATION: Comparing churn rate before vs after load")
rate_before = merged['Churn_Value'].mean()
rate_after = fact_table['Churn_Value'].mean()
step(f"  -> Source churn rate: {rate_before:.4%} | Warehouse churn rate: {rate_after:.4%} | Match: {rate_before == rate_after}")

step("VALIDATION: Row count reconciliation")
step(f"  -> Staging rows: {stg_rows} | Fact table rows: {fact_table.shape[0]} | Match: {stg_rows == fact_table.shape[0]}")
step(f"  -> Source rows: {source1.shape[0]} | Fact table rows: {fact_table.shape[0]} | Match: {source1.shape[0] == fact_table.shape[0]}")

step("VALIDATION: Data mart reconciliation")
step(f"  -> Mart rows: {mart_rows} | Fact table rows: {fact_table.shape[0]} | Match: {mart_rows == fact_table.shape[0]}")
mart_rate = conn.execute("SELECT AVG(Churn_Value) FROM Mart_CustomerRetention").fetchone()[0]
step(f"  -> Mart churn rate: {mart_rate:.4%} | Warehouse churn rate: {rate_after:.4%} | Match: {abs(mart_rate - rate_after) < 1e-12}")
seg_total = conn.execute("SELECT SUM(Customers) FROM vw_Retention_ByRiskSegment").fetchone()[0]
con_total = conn.execute("SELECT SUM(Customers) FROM vw_Retention_ByContract").fetchone()[0]
ten_total = conn.execute("SELECT SUM(Customers) FROM vw_Retention_ByTenureBand").fetchone()[0]
qtr_total = conn.execute("SELECT SUM(Customers) FROM vw_Retention_ByJoinQuarter").fetchone()[0]
step(f"  -> View totals reconcile to {mart_rows} customers: risk {seg_total}, contract {con_total}, tenure {ten_total}, join quarter {qtr_total} | "
     f"Match: {seg_total == con_total == ten_total == qtr_total == mart_rows}")

conn.close()
step("ETL PIPELINE COMPLETE")

with open(LOG_DIR / "etl_log.txt", "w") as f:
    f.write("\n".join(log))
