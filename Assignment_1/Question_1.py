import pandas as pd

# Q1 - Read the CSV File
sales_data = pd.read_csv("pandas_dataset.csv")
print(sales_data.head())

# Q2 - Rename Columns
sales_data.columns = sales_data.columns.str.lower().str.replace(" ", "_")

# Q3 - Drop Unnecessary Rows
sales_data = sales_data.dropna(how="all")
sales_data = sales_data.reset_index(drop=True)

# Q4 - Drop Columns
sales_data = sales_data.drop(columns=["product"])

# Q5 - Count Missing Values
print(sales_data.isnull().sum())

# Q6 - Handle Missing Values
sales_data = sales_data.dropna(subset=["sales"])
sales_data["profit"] = sales_data["profit"].fillna(sales_data["profit"].mean())
sales_data["discount"] = sales_data["discount"].fillna(sales_data["discount"].median())

# Q7 - Handle Missing Categorical Data
sales_data["customer_name"] = sales_data["customer_name"].fillna("Unknown")

# Q8 - Detect and Remove Duplicates
print(sales_data.duplicated(subset=["order_id"]).sum())
sales_data = sales_data.drop_duplicates(subset=["order_id"]).reset_index(drop=True)

# Q9 - Filtering and creating new columns
print(sales_data[sales_data["unit_price"] > 20000])
print(sales_data[(sales_data["unit_price"] > 10000) & (sales_data["status"] == "Completed")][["customer_name", "category", "status"]])

sales_data["total_amount"] = sales_data["quantity"] * sales_data["unit_price"]
sales_data["customer_type"] = sales_data["quantity"].apply(lambda qty: "Bulk Buyer" if qty >= 3 else "Regular Buyer")

# Q10 - Final Clean Dataset
print(sales_data.shape)
print(sales_data.head(10))