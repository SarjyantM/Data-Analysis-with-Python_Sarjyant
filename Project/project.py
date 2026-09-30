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


# =================================================================
# WEEK 2 - split into customers / products / orders
# =================================================================

# some stock codes have more than one description over time (typos, updates etc)
# just pick whichever description shows up most for that stock code
most_common_desc = (
    df.groupby(["stock_code", "description"]).size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
    .drop_duplicates(subset="stock_code")
)
products = most_common_desc[["stock_code", "description"]].sort_values("stock_code").reset_index(drop=True)

# price for the same product isn't fixed, it changes across the year
# so keep min/avg/max as reference info on the product itself
price_stats = df.groupby("stock_code")["unit_price"].agg(
    min_price="min", avg_price="mean", max_price="max"
).round(2).reset_index()

products = products.merge(price_stats, on="stock_code", how="left")
products.insert(0, "product_id", range(1, len(products) + 1))
products = products.rename(columns={"stock_code": "sku"})

print("\nproducts:", len(products))

# same idea for customers - pick their most common country
most_common_country = (
    df.groupby(["customer_id", "country"]).size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
    .drop_duplicates(subset="customer_id")
)
customers = most_common_country[["customer_id", "country"]].sort_values("customer_id").reset_index(drop=True)
customers["is_guest"] = customers["customer_id"] == -1
# -1 covers a bunch of different unknown customers from different countries
# so "most common country" doesn't really mean anything for that row
customers.loc[customers["is_guest"], "country"] = "Unknown"

# basic customer profile stats, based on completed orders only
completed = df[~df["is_cancelled"]]
customer_stats = completed.groupby("customer_id").agg(
    first_purchase=("invoice_date", "min"),
    last_purchase=("invoice_date", "max"),
    num_orders=("invoice_no", "nunique"),
    total_spent=("line_total", "sum"),
).reset_index()
customer_stats["total_spent"] = customer_stats["total_spent"].round(2)

customers = customers.merge(customer_stats, on="customer_id", how="left")
customers["num_orders"] = customers["num_orders"].fillna(0).astype(int)
customers["total_spent"] = customers["total_spent"].fillna(0)

print("customers:", len(customers))

# orders table, swapping stock_code for product_id
sku_to_id = dict(zip(products["sku"], products["product_id"]))
df["product_id"] = df["stock_code"].map(sku_to_id)

orders = df[["invoice_no", "invoice_date", "is_cancelled", "customer_id",
             "product_id", "quantity", "unit_price", "line_total"]].reset_index(drop=True)
orders.insert(0, "order_line_id", range(1, len(orders) + 1))

print("order lines:", len(orders))

# quick sanity check - every order should point to a real customer and product
assert orders["product_id"].notna().all(), "some order rows have no matching product"
assert orders["customer_id"].isin(customers["customer_id"]).all(), "some order rows have no matching customer"
print("foreign key check passed")

customers.to_csv("customers.csv", index=False)
products.to_csv("products.csv", index=False)
orders.to_csv("orders.csv", index=False)

print("\nsaved customers.csv, products.csv, orders.csv")
print("\ntop 5 real customers by total spent (excluding the guest bucket):")
real_customers = customers[~customers["is_guest"]]
print(real_customers.sort_values("total_spent", ascending=False).head()[["customer_id", "country", "num_orders", "total_spent"]])