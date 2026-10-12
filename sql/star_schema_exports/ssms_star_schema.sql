USE DWBI_Assignment;
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
