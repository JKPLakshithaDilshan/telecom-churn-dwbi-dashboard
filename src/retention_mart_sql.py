"""
Retention Data Mart - SQL definitions (shared by the SQLite ETL and the SQL Server loader)
===========================================================================================
Department served : Customer Retention / Commercial Strategy
Mart table        : Mart_CustomerRetention  (one row per customer account, denormalised)
Built from        : the star schema (Fact_CustomerAccount + the five dimensions)
Analytical views  : vw_Retention_* and vw_AtRisk_ActiveCustomers

The same SQL runs on SQLite and SQL Server (only the mart table DDL differs).
Run `python retention_mart_sql.py` to regenerate retention_mart_sqlserver.sql,
a stand-alone script that can be executed in SSMS.
"""

from pathlib import Path

MART_COLUMNS = [
    "CustomerAccountKey", "CustomerID", "Gender", "Senior_Citizen", "Partner", "Dependents",
    "City", "Zip_Code", "Internet_Service", "Phone_Service", "Online_Security", "Tech_Support",
    "Streaming_TV", "Streaming_Movies", "Contract", "Payment_Method", "Paperless_Billing",
    "Tenure_Months", "Tenure_Years", "Monthly_Charges", "Total_Charges", "Avg_Monthly_Spend",
    "Churn_Value", "Churn_Score", "CLTV", "Risk_Segment", "Join_Date", "Join_Year", "Join_Quarter",
]

# Mart = the fact table joined to every dimension, keeping the retention-relevant attributes.
MART_SELECT = """SELECT
    f.CustomerAccountKey, c.CustomerID, c.Gender, c.Senior_Citizen, c.Partner, c.Dependents,
    l.City, l.Zip_Code,
    s.Internet_Service, s.Phone_Service, s.Online_Security, s.Tech_Support, s.Streaming_TV, s.Streaming_Movies,
    k.Contract, k.Payment_Method, k.Paperless_Billing,
    f.Tenure_Months, f.Tenure_Years, f.Monthly_Charges, f.Total_Charges, f.Avg_Monthly_Spend,
    f.Churn_Value, f.Churn_Score, f.CLTV, f.Risk_Segment,
    d.FullDate AS Join_Date, d.Year AS Join_Year, d.Quarter AS Join_Quarter
FROM Fact_CustomerAccount f
JOIN Dim_Customer c ON f.CustomerKey = c.CustomerKey
JOIN Dim_Location l ON f.LocationKey = l.LocationKey
JOIN Dim_Service  s ON f.ServiceKey  = s.ServiceKey
JOIN Dim_Contract k ON f.ContractKey = k.ContractKey
JOIN Dim_Date     d ON f.DateKey     = d.DateKey"""

# SQL Server table definition (SQLite creates its table with CREATE TABLE ... AS SELECT)
MART_DDL_SQLSERVER = """CREATE TABLE dbo.Mart_CustomerRetention (
    CustomerAccountKey INT NOT NULL PRIMARY KEY,
    CustomerID NVARCHAR(255) NOT NULL,
    Gender NVARCHAR(50),
    Senior_Citizen NVARCHAR(20),
    Partner NVARCHAR(20),
    Dependents NVARCHAR(20),
    City NVARCHAR(255),
    Zip_Code NVARCHAR(50),
    Internet_Service NVARCHAR(50),
    Phone_Service NVARCHAR(20),
    Online_Security NVARCHAR(20),
    Tech_Support NVARCHAR(20),
    Streaming_TV NVARCHAR(20),
    Streaming_Movies NVARCHAR(20),
    Contract NVARCHAR(100),
    Payment_Method NVARCHAR(100),
    Paperless_Billing NVARCHAR(20),
    Tenure_Months INT,
    Tenure_Years DECIMAL(5,1),
    Monthly_Charges DECIMAL(10,2),
    Total_Charges DECIMAL(10,2),
    Avg_Monthly_Spend DECIMAL(10,2),
    Churn_Value INT,
    Churn_Score INT,
    CLTV INT,
    Risk_Segment NVARCHAR(50),
    Join_Date DATE,
    Join_Year INT,
    Join_Quarter NVARCHAR(10)
)"""

# name -> (business question, SELECT). No ORDER BY inside views (SQL Server does not allow it).
VIEWS = {
    "vw_Retention_Summary": (
        "Headline retention KPIs for the whole customer base (one row).",
        """SELECT
    COUNT(*)                                                   AS Total_Customers,
    SUM(Churn_Value)                                           AS Churned_Customers,
    ROUND(100.0 * SUM(Churn_Value) / COUNT(*), 2)              AS Churn_Rate_Pct,
    SUM(CASE WHEN Risk_Segment = 'High Risk' AND Churn_Value = 0 THEN 1 ELSE 0 END)
                                                               AS Active_High_Risk_Customers,
    ROUND(SUM(CASE WHEN Risk_Segment = 'High Risk' AND Churn_Value = 0 THEN Monthly_Charges ELSE 0 END), 2)
                                                               AS Monthly_Revenue_At_Risk,
    ROUND(SUM(CASE WHEN Churn_Value = 1 THEN Monthly_Charges ELSE 0 END), 2)
                                                               AS Monthly_Revenue_Lost,
    ROUND(AVG(Monthly_Charges), 2)                             AS Avg_Monthly_Charges,
    ROUND(AVG(1.0 * CLTV), 0)                                        AS Avg_CLTV
FROM Mart_CustomerRetention"""),
    "vw_Retention_ByRiskSegment": (
        "How customers, churn and revenue split across Low / Medium / High risk.",
        """SELECT
    Risk_Segment,
    COUNT(*)                                       AS Customers,
    SUM(Churn_Value)                               AS Churned_Customers,
    ROUND(100.0 * SUM(Churn_Value) / COUNT(*), 2)  AS Churn_Rate_Pct,
    ROUND(AVG(1.0 * Churn_Score), 1)                     AS Avg_Churn_Score,
    ROUND(AVG(Monthly_Charges), 2)                 AS Avg_Monthly_Charges,
    ROUND(SUM(Monthly_Charges), 2)                 AS Total_Monthly_Charges
FROM Mart_CustomerRetention
GROUP BY Risk_Segment"""),
    "vw_Retention_ByContract": (
        "Which contract type and internet service combinations churn most.",
        """SELECT
    Contract,
    Internet_Service,
    COUNT(*)                                       AS Customers,
    SUM(Churn_Value)                               AS Churned_Customers,
    ROUND(100.0 * SUM(Churn_Value) / COUNT(*), 2)  AS Churn_Rate_Pct,
    ROUND(AVG(1.0 * Churn_Score), 1)                     AS Avg_Churn_Score,
    ROUND(SUM(Monthly_Charges), 2)                 AS Total_Monthly_Charges
FROM Mart_CustomerRetention
GROUP BY Contract, Internet_Service"""),
    "vw_Retention_ByTenureBand": (
        "How churn changes as customers stay longer.",
        """SELECT
    CASE WHEN Tenure_Months <= 12 THEN '1) 0-12 months'
         WHEN Tenure_Months <= 24 THEN '2) 13-24 months'
         WHEN Tenure_Months <= 48 THEN '3) 25-48 months'
         ELSE '4) 49+ months' END                  AS Tenure_Band,
    COUNT(*)                                       AS Customers,
    SUM(Churn_Value)                               AS Churned_Customers,
    ROUND(100.0 * SUM(Churn_Value) / COUNT(*), 2)  AS Churn_Rate_Pct,
    ROUND(AVG(Monthly_Charges), 2)                 AS Avg_Monthly_Charges
FROM Mart_CustomerRetention
GROUP BY CASE WHEN Tenure_Months <= 12 THEN '1) 0-12 months'
              WHEN Tenure_Months <= 24 THEN '2) 13-24 months'
              WHEN Tenure_Months <= 48 THEN '3) 25-48 months'
              ELSE '4) 49+ months' END"""),
    "vw_Retention_ByJoinQuarter": (
        "Customer cohorts by join quarter: size, churn and average charges.",
        """SELECT
    Join_Year,
    Join_Quarter,
    COUNT(*)                                       AS Customers,
    SUM(Churn_Value)                               AS Churned_Customers,
    ROUND(100.0 * SUM(Churn_Value) / COUNT(*), 2)  AS Churn_Rate_Pct,
    ROUND(AVG(Monthly_Charges), 2)                 AS Avg_Monthly_Charges
FROM Mart_CustomerRetention
GROUP BY Join_Year, Join_Quarter"""),
    "vw_AtRisk_ActiveCustomers": (
        "Call list for the retention team: active customers currently scored High Risk.",
        """SELECT
    CustomerID, City, Contract, Internet_Service, Payment_Method,
    Tenure_Months, Monthly_Charges, Churn_Score, CLTV
FROM Mart_CustomerRetention
WHERE Risk_Segment = 'High Risk' AND Churn_Value = 0"""),
}


def sqlserver_script(database="DWBI_Assignment"):
    """Full SSMS script: create the mart from the star schema, then create the views."""
    cols = ", ".join(MART_COLUMNS)
    out = [
        "-- Retention Data Mart for SQL Server (generated by retention_mart_sql.py)",
        "-- Run AFTER the star schema tables are loaded (load_to_sqlserver.py).",
        f"USE {database};\nGO\n",
        "IF OBJECT_ID('dbo.vw_AtRisk_ActiveCustomers', 'V') IS NOT NULL DROP VIEW dbo.vw_AtRisk_ActiveCustomers;",
    ]
    for name in VIEWS:
        if name != "vw_AtRisk_ActiveCustomers":
            out.append(f"IF OBJECT_ID('dbo.{name}', 'V') IS NOT NULL DROP VIEW dbo.{name};")
    out += ["IF OBJECT_ID('dbo.Mart_CustomerRetention', 'U') IS NOT NULL DROP TABLE dbo.Mart_CustomerRetention;", "GO\n",
            MART_DDL_SQLSERVER + ";\nGO\n",
            f"INSERT INTO dbo.Mart_CustomerRetention ({cols})",
            MART_SELECT.replace("FROM Fact_CustomerAccount f", "FROM dbo.Fact_CustomerAccount f")
                       .replace("JOIN Dim_", "JOIN dbo.Dim_") + "\nORDER BY f.CustomerAccountKey;\nGO\n"]
    for name, (question, select) in VIEWS.items():
        out += [f"-- {question}", f"CREATE VIEW dbo.{name} AS\n{select.replace('FROM Mart_CustomerRetention', 'FROM dbo.Mart_CustomerRetention')};", "GO\n"]
    return "\n".join(out)


if __name__ == "__main__":
    out_path = Path(__file__).resolve().parents[1] / "sql" / "retention_mart_sqlserver.sql"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(sqlserver_script())
    print(f"Wrote {out_path}")
