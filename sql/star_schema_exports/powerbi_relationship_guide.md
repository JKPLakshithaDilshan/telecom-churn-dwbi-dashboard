# Power BI star schema relationship mapping

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
