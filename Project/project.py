# Dataset: Online Retail (UK online store, Dec 2010 to Dec 2011)
# Raw columns: InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country

import pandas as pd

df = pd.read_csv("online_retail.csv")

print("rows and columns:", df.shape)
print()
print("missing values:")
print(df.isna().sum())
print()
print("duplicate rows:", df.duplicated().sum())
print()
print("date range:", df["InvoiceDate"].min(), "to", df["InvoiceDate"].max())
print("unique invoices:", df["InvoiceNo"].nunique())
print("unique products:", df["StockCode"].nunique())
print("unique customers:", df["CustomerID"].nunique())
print("countries:", df["Country"].nunique())

# drop exact duplicates
before = len(df)
df = df.drop_duplicates()
print(f"\ndropped {before - len(df)} duplicate rows")

# any invoice number starting with "C" is a cancelled order
# checked earlier - every cancelled row already has a negative quantity
df["invoice_no"] = df["InvoiceNo"].astype(str).str.strip()
df["is_cancelled"] = df["invoice_no"].str.startswith("C")
print("cancelled invoice rows:", df["is_cancelled"].sum())

# drop rows where we don't even know what product it was
before = len(df)
df = df[df["Description"].notna()]
print(f"dropped {before - len(df)} rows with no product description")

# price of 0 or less isn't a real sale, just some kind of adjustment entry
before = len(df)
df = df[df["UnitPrice"] > 0]
print(f"dropped {before - len(df)} rows with price <= 0")

# negative quantity only makes sense for cancelled orders
# if it's negative but not cancelled, that's just a bad row
before = len(df)
df = df[(df["Quantity"] > 0) | (df["is_cancelled"])]
print(f"dropped {before - len(df)} rows with negative quantity on a non-cancelled order")

# clean up text columns
df["Description"] = df["Description"].astype(str).str.strip()
df["Country"] = df["Country"].astype(str).str.strip()
df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()

# about a quarter of rows have no CustomerID (guest checkout basically)
# instead of dropping all of that data, just give them id -1 for now
missing_cust = df["CustomerID"].isna().sum()
print(f"\nrows with no CustomerID (treated as guest): {missing_cust}")
df["customer_id"] = df["CustomerID"].fillna(-1).astype(int)

df["invoice_date"] = pd.to_datetime(df["InvoiceDate"])

df = df.rename(columns={
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "UnitPrice": "unit_price",
    "Country": "country",
})
df["line_total"] = df["quantity"] * df["unit_price"]

df = df[["invoice_no", "invoice_date", "is_cancelled", "customer_id",
         "country", "stock_code", "description", "quantity",
         "unit_price", "line_total"]]

print("\nshape after cleaning:", df.shape)

df.to_csv("cleaned_retail.csv", index=False)
print("saved cleaned_retail.csv")