import pandas as pd

# Q1 - read csv
sales_data = pd.read_csv("pandas_dataset.csv")
print(sales_data.head())

# Q2 - rename columns
sales_data.columns = sales_data.columns.str.lower().str.replace(" ", "_")

# Q3 - drop blank row, reset index
sales_data = sales_data.dropna(how="all")
sales_data = sales_data.reset_index(drop=True)

# Q4 - drop product column
sales_data = sales_data.drop(columns=["product"])

# Q5 - count missing values
print(sales_data.isnull().sum())

# Q6 - handle missing values
sales_data = sales_data.dropna(subset=["sales"])
sales_data["profit"] = sales_data["profit"].fillna(sales_data["profit"].mean())
sales_data["discount"] = sales_data["discount"].fillna(sales_data["discount"].median())

# Q7 - fill missing customer name
sales_data["customer_name"] = sales_data["customer_name"].fillna("Unknown")

# Q8 - remove duplicates
print(sales_data.duplicated(subset=["order_id"]).sum())
sales_data = sales_data.drop_duplicates(subset=["order_id"]).reset_index(drop=True)

# Q9 - filtering and new columns
print(sales_data[sales_data["unit_price"] > 20000])
print(sales_data[(sales_data["unit_price"] > 10000) & (sales_data["status"] == "Completed")][["customer_name", "category", "status"]])

sales_data["total_amount"] = sales_data["quantity"] * sales_data["unit_price"]
sales_data["customer_type"] = sales_data["quantity"].apply(lambda qty: "Bulk Buyer" if qty >= 3 else "Regular Buyer")

# Q10 - final dataset
print(sales_data.shape)
print(sales_data.head(10))