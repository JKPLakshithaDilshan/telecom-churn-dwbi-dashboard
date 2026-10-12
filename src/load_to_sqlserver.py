"""
Load Step: SQLite warehouse -> SQL Server (DWBI_Assignment)
============================================================
Second stage of the pipeline. etl_pipeline.py builds the star schema in
telecom_dw.db (SQLite). This script copies the five dimensions and the fact
table into SQL Server so Power BI / SSMS use exactly the ETL output.

Run order:
    1. python etl_pipeline.py          -> telecom_dw.db (warehouse + mart + views), retention_mart.csv, etl_log.txt
    2. python load_to_sqlserver.py     -> SQL Server tables, sqlserver_load_log.txt

Requirements:
    pip install pandas pyodbc
    Microsoft ODBC Driver 17 or 18 for SQL Server
    retention_mart_sql.py must sit in the same folder (it defines the mart and views)

Connection settings can be overridden with environment variables:
    DW_SERVER   (default: localhost)      e.g. localhost\\SQLEXPRESS
    DW_DATABASE (default: DWBI_Assignment)
    DW_DRIVER   (default: ODBC Driver 17 for SQL Server)
    DW_USER / DW_PASSWORD  (optional; Windows authentication is used if unset)
"""

import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

import retention_mart_sql as mart_sql

ROOT_DIR = Path(__file__).resolve().parents[1]
SQLITE_PATH = ROOT_DIR / "data" / "warehouse" / "telecom_dw.db"
DDL_PATH = ROOT_DIR / "sql" / "star_schema_exports" / "ssms_star_schema.sql"
LOG_PATH = ROOT_DIR / "logs" / "sqlserver_load_log.txt"

SERVER = os.getenv("DW_SERVER", "localhost")
DATABASE = os.getenv("DW_DATABASE", "DWBI_Assignment")
DRIVER = os.getenv("DW_DRIVER", "ODBC Driver 17 for SQL Server")
USER = os.getenv("DW_USER")
PASSWORD = os.getenv("DW_PASSWORD")

# Dimensions first, fact last (foreign keys must exist before the fact is loaded).
LOAD_ORDER = [
    ("Dim_Customer", ["CustomerKey", "CustomerID", "Gender", "Senior_Citizen", "Partner", "Dependents"]),
    ("Dim_Location", ["LocationKey", "City", "Zip_Code", "Latitude", "Longitude"]),
    ("Dim_Service", ["ServiceKey", "Phone_Service", "Multiple_Lines", "Internet_Service", "Online_Security",
                     "Online_Backup", "Device_Protection", "Tech_Support", "Streaming_TV", "Streaming_Movies"]),
    ("Dim_Contract", ["ContractKey", "Contract", "Paperless_Billing", "Payment_Method"]),
    ("Dim_Date", ["DateKey", "FullDate", "Year", "Quarter", "MonthName", "MonthNumber", "QuarterName"]),
    ("Fact_CustomerAccount", ["CustomerAccountKey", "CustomerKey", "LocationKey", "ServiceKey", "ContractKey",
                              "DateKey", "Tenure_Months", "Monthly_Charges", "Total_Charges", "Avg_Monthly_Spend",
                              "Tenure_Years", "Churn_Value", "Churn_Score", "CLTV", "Risk_Segment"]),
]

FK_CHECKS = [
    ("CustomerKey", "Dim_Customer"), ("LocationKey", "Dim_Location"), ("ServiceKey", "Dim_Service"),
    ("ContractKey", "Dim_Contract"), ("DateKey", "Dim_Date"),
]

log = []


def step(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line)
    log.append(line)


def connection_string(database):
    base = f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={database};TrustServerCertificate=yes;"
    if USER:
        return base + f"UID={USER};PWD={PASSWORD};"
    return base + "Trusted_Connection=yes;"


def read_table(sqlite_conn, table, columns):
    """Read one warehouse table from SQLite in the exact column order of the SQL Server table."""
    df = pd.read_sql(f"SELECT {', '.join(columns)} FROM {table} ORDER BY {columns[0]}", sqlite_conn)
    if "FullDate" in df.columns:
        df["FullDate"] = pd.to_datetime(df["FullDate"]).dt.date
    # pyodbc needs plain Python values, with NaN converted to NULL
    return df.astype(object).where(df.notna(), None)


def run_script(cursor, script):
    """Execute a T-SQL script, splitting it on its GO batch separators."""
    batches = [b.strip() for b in re.split(r"^\s*GO\s*$", script, flags=re.MULTILINE | re.IGNORECASE) if b.strip()]
    for batch in batches:
        cursor.execute(batch)
    return len(batches)


def run_ddl(cursor):
    """Execute ssms_star_schema.sql (the star schema table definitions)."""
    with open(DDL_PATH, encoding="utf-8") as f:
        return run_script(cursor, f.read())


def main():
    import pyodbc  # imported here so the helper functions can be tested without a driver

    step(f"CONNECT: SQL Server '{SERVER}', database '{DATABASE}'")
    master = pyodbc.connect(connection_string("master"), autocommit=True)
    master.cursor().execute(f"IF DB_ID('{DATABASE}') IS NULL CREATE DATABASE [{DATABASE}]")
    master.close()

    conn = pyodbc.connect(connection_string(DATABASE))
    cur = conn.cursor()
    cur.fast_executemany = True
    sqlite_conn = sqlite3.connect(SQLITE_PATH)

    step("DDL: Dropping and recreating star schema tables from ssms_star_schema.sql")
    n = run_ddl(cur)
    conn.commit()
    step(f"  -> {n} batches executed")

    loaded = {}
    for table, cols in LOAD_ORDER:
        step(f"LOAD: {table}")
        df = read_table(sqlite_conn, table, cols)
        placeholders = ", ".join("?" for _ in cols)
        insert = f"INSERT INTO dbo.{table} ({', '.join(cols)}) VALUES ({placeholders})"
        cur.execute(f"SET IDENTITY_INSERT dbo.{table} ON")  # keep the ETL surrogate keys
        cur.executemany(insert, df.values.tolist())
        cur.execute(f"SET IDENTITY_INSERT dbo.{table} OFF")
        conn.commit()
        loaded[table] = len(df)
        step(f"  -> Loaded {len(df)} rows")

    step("MART: Building Mart_CustomerRetention from the SQL Server star schema and creating retention views")
    n = run_script(cur, mart_sql.sqlserver_script(DATABASE))
    conn.commit()
    step(f"  -> {n} batches executed ({len(mart_sql.VIEWS)} views created)")

    step("VALIDATION: Row counts, SQLite warehouse vs SQL Server")
    for table, _ in LOAD_ORDER:
        sql_count = cur.execute(f"SELECT COUNT(*) FROM dbo.{table}").fetchone()[0]
        src_count = sqlite_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        step(f"  -> {table}: SQLite {src_count} | SQL Server {sql_count} | Match: {src_count == sql_count}")

    mart_sql_rows = cur.execute("SELECT COUNT(*) FROM dbo.Mart_CustomerRetention").fetchone()[0]
    mart_src_rows = sqlite_conn.execute("SELECT COUNT(*) FROM Mart_CustomerRetention").fetchone()[0]
    step(f"  -> Mart_CustomerRetention: SQLite {mart_src_rows} | SQL Server {mart_sql_rows} | Match: {mart_src_rows == mart_sql_rows}")
    for v in mart_sql.VIEWS:
        step(f"  -> {v}: {cur.execute(f'SELECT COUNT(*) FROM dbo.{v}').fetchone()[0]} rows in SQL Server "
             f"(SQLite: {sqlite_conn.execute(f'SELECT COUNT(*) FROM {v}').fetchone()[0]})")

    step("VALIDATION: Orphan foreign key check (fact rows with no matching dimension row)")
    for fk, dim in FK_CHECKS:
        q = (f"SELECT COUNT(*) FROM dbo.Fact_CustomerAccount f "
             f"LEFT JOIN dbo.{dim} d ON f.{fk} = d.{fk} WHERE d.{fk} IS NULL")
        orphans = cur.execute(q).fetchone()[0]
        step(f"  -> {fk} -> {dim}: {orphans} orphan rows (expected: 0)")

    step("VALIDATION: Churn rate, SQLite vs SQL Server")
    sql_rate = cur.execute("SELECT AVG(CAST(Churn_Value AS FLOAT)) FROM dbo.Fact_CustomerAccount").fetchone()[0]
    src_rate = sqlite_conn.execute("SELECT AVG(Churn_Value) FROM Fact_CustomerAccount").fetchone()[0]
    step(f"  -> SQLite {src_rate:.4%} | SQL Server {sql_rate:.4%} | Match: {abs(src_rate - sql_rate) < 1e-9}")

    conn.close()
    sqlite_conn.close()
    step("SQL SERVER LOAD COMPLETE")
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "w") as f:
        f.write("\n".join(log))


if __name__ == "__main__":
    main()
