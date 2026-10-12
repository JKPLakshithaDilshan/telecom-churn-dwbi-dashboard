import os
import json
from pathlib import Path

import pandas as pd

root = Path(__file__).resolve().parents[1]
source_dir = root / "data" / "source"
processed_dir = root / "data" / "processed"
out_dir = root / "sql" / "star_schema_exports"
os.makedirs(out_dir, exist_ok=True)

# Read the original operational sources and the final retention mart.
customer_df = pd.read_csv(source_dir / "customer_billing_source.csv")
location_df = pd.read_csv(source_dir / "location_reference_source.csv")
with open(source_dir / "service_subscription_source.json", "r", encoding="utf-8") as f:
    service_df = pd.DataFrame(json.load(f))
mart_df = pd.read_csv(processed_dir / "retention_mart.csv")

# Merge operational sources for a clean analytical base.
merged = customer_df.merge(location_df, on="Zip_Code", how="left")
merged = merged.merge(service_df, on="CustomerID", how="left")

# Standardize and clean the merged data
for col in ["Total_Charges", "Monthly_Charges"]:
    if col in merged.columns:
        merged[col] = merged[col].astype(str).str.strip().replace("", "0").astype(float)

for col in merged.select_dtypes(include=["object", "str"]).columns:
    merged[col] = merged[col].astype(str).str.strip()

merged["Avg_Monthly_Spend"] = (merged["Total_Charges"] / merged["Tenure_Months"].replace(0, 1)).round(2)
merged["Tenure_Years"] = (merged["Tenure_Months"] / 12).round(1)

# Dim_Customer
customer_cols = ["CustomerID", "Gender", "Senior_Citizen", "Partner", "Dependents"]
dim_customer = merged[customer_cols].drop_duplicates().reset_index(drop=True)
dim_customer.insert(0, "CustomerKey", list(range(1, len(dim_customer) + 1)))

# Dim_Location
location_cols = ["City", "Zip_Code", "Latitude", "Longitude"]
dim_location = merged[location_cols].drop_duplicates().reset_index(drop=True)
dim_location.insert(0, "LocationKey", list(range(1, len(dim_location) + 1)))

# Dim_Service
service_cols = [
    "Phone_Service", "Multiple_Lines", "Internet_Service", "Online_Security",
    "Online_Backup", "Device_Protection", "Tech_Support", "Streaming_TV", "Streaming_Movies"
]
dim_service = merged[service_cols].drop_duplicates().reset_index(drop=True)
dim_service.insert(0, "ServiceKey", list(range(1, len(dim_service) + 1)))

# Dim_Contract
contract_cols = ["Contract", "Paperless_Billing", "Payment_Method"]
dim_contract = merged[contract_cols].drop_duplicates().reset_index(drop=True)
dim_contract.insert(0, "ContractKey", list(range(1, len(dim_contract) + 1)))

# Dim_Date derived from the retention mart's join date field to create a real hierarchy.
dim_date = mart_df[["Join_Date", "Join_Year", "Join_Quarter"]].drop_duplicates().sort_values(["Join_Year", "Join_Date"]).reset_index(drop=True)
dim_date = dim_date.rename(columns={"Join_Date": "FullDate", "Join_Year": "Year", "Join_Quarter": "Quarter"})
dim_date.insert(0, "DateKey", list(range(1, len(dim_date) + 1)))
dim_date["MonthName"] = pd.to_datetime(dim_date["FullDate"]).dt.strftime("%B")
dim_date["MonthNumber"] = pd.to_datetime(dim_date["FullDate"]).dt.month
dim_date["QuarterName"] = dim_date["Quarter"]

# Fact_CustomerAccount built from the cleaned operational data and linked to the retention mart metadata.
metrics = mart_df[["CustomerID", "CustomerAccountKey", "Risk_Segment", "Join_Date", "Join_Year", "Join_Quarter"]].copy()
fact = merged.merge(metrics, on="CustomerID", how="left")

fact = fact.merge(dim_customer, on=["CustomerID", "Gender", "Senior_Citizen", "Partner", "Dependents"], how="left")
fact = fact.merge(dim_location, on=["City", "Zip_Code", "Latitude", "Longitude"], how="left")
fact = fact.merge(dim_service, on=service_cols, how="left")
fact = fact.merge(dim_contract, on=["Contract", "Paperless_Billing", "Payment_Method"], how="left")
fact = fact.merge(dim_date.rename(columns={"FullDate": "Join_Date"})[["Join_Date", "DateKey"]], on="Join_Date", how="left")

fact_table = fact[[
    "CustomerAccountKey", "CustomerKey", "LocationKey", "ServiceKey", "ContractKey", "DateKey",
    "Tenure_Months", "Monthly_Charges", "Total_Charges", "Avg_Monthly_Spend",
    "Tenure_Years", "Churn_Value", "Churn_Score", "CLTV", "Risk_Segment"
]].copy()

# Save all tables to CSV for Power BI connection.
for name, frame in {
    "Dim_Customer": dim_customer,
    "Dim_Location": dim_location,
    "Dim_Service": dim_service,
    "Dim_Contract": dim_contract,
    "Dim_Date": dim_date,
    "Fact_CustomerAccount": fact_table,
}.items():
    frame.to_csv(os.path.join(out_dir, f"{name}.csv"), index=False)

# SSMS / SQL Server DDL
sql = '''USE DWBI_Assignment;
GO

IF OBJECT_ID('dbo.Fact_CustomerAccount', 'U') IS NOT NULL DROP TABLE dbo.Fact_CustomerAccount;
IF OBJECT_ID('dbo.Dim_Customer', 'U') IS NOT NULL DROP TABLE dbo.Dim_Customer;
IF OBJECT_ID('dbo.Dim_Location', 'U') IS NOT NULL DROP TABLE dbo.Dim_Location;
IF OBJECT_ID('dbo.Dim_Service', 'U') IS NOT NULL DROP TABLE dbo.Dim_Service;
IF OBJECT_ID('dbo.Dim_Contract', 'U') IS NOT NULL DROP TABLE dbo.Dim_Contract;
IF OBJECT_ID('dbo.Dim_Date', 'U') IS NOT NULL DROP TABLE dbo.Dim_Date;
GO

CREATE TABLE dbo.Dim_Customer (
    CustomerKey INT IDENTITY(1,1) PRIMARY KEY,
    CustomerID NVARCHAR(255) NOT NULL,
    Gender NVARCHAR(50),
    Senior_Citizen NVARCHAR(20),
    Partner NVARCHAR(20),
    Dependents NVARCHAR(20)
);

CREATE TABLE dbo.Dim_Location (
    LocationKey INT IDENTITY(1,1) PRIMARY KEY,
    City NVARCHAR(255),
    Zip_Code NVARCHAR(50),
    Latitude FLOAT,
    Longitude FLOAT
);

CREATE TABLE dbo.Dim_Service (
    ServiceKey INT IDENTITY(1,1) PRIMARY KEY,
    Phone_Service NVARCHAR(20),
    Multiple_Lines NVARCHAR(20),
    Internet_Service NVARCHAR(50),
    Online_Security NVARCHAR(20),
    Online_Backup NVARCHAR(20),
    Device_Protection NVARCHAR(20),
    Tech_Support NVARCHAR(20),
    Streaming_TV NVARCHAR(20),
    Streaming_Movies NVARCHAR(20)
);

CREATE TABLE dbo.Dim_Contract (
    ContractKey INT IDENTITY(1,1) PRIMARY KEY,
    Contract NVARCHAR(100),
    Paperless_Billing NVARCHAR(20),
    Payment_Method NVARCHAR(100)
);

CREATE TABLE dbo.Dim_Date (
    DateKey INT IDENTITY(1,1) PRIMARY KEY,
    FullDate DATE,
    Year INT,
    Quarter NVARCHAR(10),
    MonthName NVARCHAR(50),
    MonthNumber INT,
    QuarterName NVARCHAR(10)
);

CREATE TABLE dbo.Fact_CustomerAccount (
    CustomerAccountKey INT IDENTITY(1,1) PRIMARY KEY,
    CustomerKey INT NOT NULL,
    LocationKey INT NOT NULL,
    ServiceKey INT NOT NULL,
    ContractKey INT NOT NULL,
    DateKey INT NOT NULL,
    Tenure_Months INT,
    Monthly_Charges DECIMAL(10,2),
    Total_Charges DECIMAL(10,2),
    Avg_Monthly_Spend DECIMAL(10,2),
    Tenure_Years DECIMAL(5,1),
    Churn_Value INT,
    Churn_Score INT,
    CLTV INT,
    Risk_Segment NVARCHAR(50),
    CONSTRAINT FK_Fact_CustomerAccount_Customer FOREIGN KEY (CustomerKey) REFERENCES dbo.Dim_Customer(CustomerKey),
    CONSTRAINT FK_Fact_CustomerAccount_Location FOREIGN KEY (LocationKey) REFERENCES dbo.Dim_Location(LocationKey),
    CONSTRAINT FK_Fact_CustomerAccount_Service FOREIGN KEY (ServiceKey) REFERENCES dbo.Dim_Service(ServiceKey),
    CONSTRAINT FK_Fact_CustomerAccount_Contract FOREIGN KEY (ContractKey) REFERENCES dbo.Dim_Contract(ContractKey),
    CONSTRAINT FK_Fact_CustomerAccount_Date FOREIGN KEY (DateKey) REFERENCES dbo.Dim_Date(DateKey)
);
GO
'''
with open(os.path.join(out_dir, "ssms_star_schema.sql"), "w", encoding="utf-8") as f:
    f.write(sql)

powerbi_guide = '''# Power BI star schema relationship mapping

Use the generated CSV files in the folder `sql/star_schema_exports` for Power BI import.

## Relationship design
- Fact_CustomerAccount[CustomerKey] -> Dim_Customer[CustomerKey]
- Fact_CustomerAccount[LocationKey] -> Dim_Location[LocationKey]
- Fact_CustomerAccount[ServiceKey] -> Dim_Service[ServiceKey]
- Fact_CustomerAccount[ContractKey] -> Dim_Contract[ContractKey]
- Fact_CustomerAccount[DateKey] -> Dim_Date[DateKey]

## Recommended Power BI steps
1. Open Power BI Desktop.
2. Go to Get Data > Text/CSV.
3. Import all six tables from the folder `sql/star_schema_exports`.
4. In Model view, create the relationships above.
5. Use Fact_CustomerAccount as the fact table and the dimensions as lookup tables.
6. Add measures such as:
   - Churn Rate = DIVIDE(SUM(Fact_CustomerAccount[Churn_Value]), COUNTROWS(Fact_CustomerAccount))
   - Total Revenue = SUM(Fact_CustomerAccount[Monthly_Charges])
   - Average Monthly Spend = AVERAGE(Fact_CustomerAccount[Avg_Monthly_Spend])
7. Use Dim_Date for Year/Quarter/Month slicers and drilldown.

## Why this matches the assignment
This is a classic star schema with one fact table and multiple dimension tables connected by surrogate keys, exactly as required in Task 4.
'''
with open(os.path.join(out_dir, "powerbi_relationship_guide.md"), "w", encoding="utf-8") as f:
    f.write(powerbi_guide)

print("Generated star schema files:")
for name in [
    "Dim_Customer.csv", "Dim_Location.csv", "Dim_Service.csv", "Dim_Contract.csv",
    "Dim_Date.csv", "Fact_CustomerAccount.csv", "ssms_star_schema.sql", "powerbi_relationship_guide.md"
]:
    print(" -", os.path.join(out_dir, name))
print("\nRow counts:")
for name, frame in {
    "Dim_Customer": dim_customer,
    "Dim_Location": dim_location,
    "Dim_Service": dim_service,
    "Dim_Contract": dim_contract,
    "Dim_Date": dim_date,
    "Fact_CustomerAccount": fact_table,
}.items():
    print(f"{name}: {len(frame)}")
