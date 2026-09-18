import pandas as pd

# 1.Read the CSV File
sales_rec = pd.read_csv("pandas_dataset.csv")
original_shape = sales_rec.shape
print(sales_rec.head())

# 2.Rename Columns
sales_rec.columns = sales_rec.columns.str.lower().str.replace(" ", "_")

# 3.Drop Unnecessary Rows
sales_rec = sales_rec.iloc[1:].reset_index(drop=True)

# 4.Drop Columns
sales_rec =sales_rec.drop(columns=["product"])

# 5.Count Missing Values
print(sales_rec.isnull().sum())

# 6.Handle Missing Values

# a.Drop Rows Based on a Column
sales_rec = sales_rec.dropna(subset=["sales"])

# b.Fill Missing Values
sales_rec["profit"] =sales_rec["profit"].fillna(sales_rec["profit"].mean())
sales_rec["discount"] = sales_rec["discount"].fillna(sales_rec["discount"].median())

# 7.Handle Missing Categorical Data
sales_rec["customer_name"] =sales_rec["customer_name"].fillna("Unknown")

# 8.Detect and Remove Duplicates
duplicate_count =sales_rec.duplicated(subset=["order_id"]).sum()

print(duplicate_count)

before_count = len(sales_rec)
sales_rec = sales_rec.drop_duplicates(subset=["order_id"])
sales_rec =sales_rec.reset_index(drop=True)
removed_count =before_count - len(sales_rec)

print(removed_count)

# 9.Filtering and creating new columns
costly_orders =sales_rec[sales_rec["unit_price"]>20000]
print(costly_orders)

done_orders = sales_rec[(sales_rec["unit_price"]>10000) & (sales_rec["status"]=="Completed")]
print(done_orders[["customer_name","category","status"]])

sales_rec["total_amount"] = sales_rec["quantity"] *sales_rec["unit_price"] - sales_rec["discount"]
sales_rec["customer_type"] =sales_rec["quantity"].apply(lambda qty:"Bulk Buyer" if qty>=3 else "Regular Buyer")

# 10.Final Clean Dataset
print("Before:", original_shape, "After:", sales_rec.shape)
print(sales_rec.head(10))