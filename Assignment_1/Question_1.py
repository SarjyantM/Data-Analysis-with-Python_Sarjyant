import pandas as pd

# Q1 
df = pd.read_csv("pandas_dataset.csv")
print(df.head())

# Q2
df.columns = df.columns.str.lower().str.replace(" ", "_")

# Q3 
df = df.dropna(how="all")
df = df.reset_index(drop=True)

# Q4 
df = df.drop(columns=["product"])

# Q5 
print(df.isnull().sum())

# Q6
df = df.dropna(subset=["sales"])
df["profit"] = df["profit"].fillna(df["profit"].mean())
df["discount"] = df["discount"].fillna(df["discount"].median())

# Q7 
df["customer_name"] = df["customer_name"].fillna("Unknown")

# Q8 
print(df.duplicated(subset=["order_id"]).sum())
df = df.drop_duplicates(subset=["order_id"]).reset_index(drop=True)

# Q9 
print(df[df["unit_price"] > 20000])
print(df[(df["unit_price"] > 10000) & (df["status"] == "Completed")][["customer_name", "category", "status"]])

df["total_amount"] = df["quantity"] * df["unit_price"]
df["customer_type"] = df["quantity"].apply(lambda q: "Bulk Buyer" if q >= 3 else "Regular Buyer")

# Q10 
print(df.shape)
print(df.head(10))