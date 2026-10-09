# End-to-End ETL & Data Analysis Pipeline
# Dataset: Kaggle "Supermarket sales"

import os

import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# MySQL connection settings
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")  
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "3306"))
DB_NAME     = "supermarket_db"

# CSV file extract
raw = pd.read_csv("SuperMarket Analysis.csv", encoding="utf-8-sig")

# EDA
print(raw.shape)
print(raw.columns.tolist())
print(raw.dtypes)
print(raw.head())
print(raw.describe())
print(raw.isnull().sum())
print("duplicates:", raw.duplicated().sum())
print(raw.nunique())
print(raw["Product line"].value_counts())
print(raw["Payment"].value_counts())

print("sales = cogs + tax:", ((raw["cogs"] + raw["Tax 5%"] - raw["Sales"]).abs() < 0.01).all())
print("gross income same as tax:", (raw["gross income"] == raw["Tax 5%"]).all())
print("cogs = price * qty:", ((raw["Unit price"] * raw["Quantity"] - raw["cogs"]).abs() < 0.01).all())

# Outlier check with the IQR rule
for col in ["Unit price", "Quantity", "Sales", "Rating"]:
    q1, q3 = raw[col].quantile([0.25, 0.75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    print(f"outliers in {col}:", int(((raw[col] < lo) | (raw[col] > hi)).sum()))

# Check that categories are what we expect
for col in ["Branch", "City", "Customer type", "Gender", "Product line", "Payment"]:
    print(f"{col}:", sorted(raw[col].unique()))

# Clean & Transform
sales = raw.drop_duplicates()
sales = sales.rename(columns={
    "Invoice ID": "invoice_id", "Branch": "branch", "City": "city",
    "Customer type": "customer_type", "Gender": "gender", "Product line": "product_line",
    "Unit price": "unit_price", "Quantity": "quantity", "Tax 5%": "tax", "Sales": "sales_amount",
    "Date": "date", "Time": "time", "Payment": "payment", "Rating": "rating",
})
sales = sales.drop(columns=["gross margin percentage", "gross income"])

for col in ["branch", "city", "customer_type", "gender", "product_line", "payment"]:
    sales[col] = sales[col].str.strip()

sales["order_date"] = pd.to_datetime(sales["date"], format="%m/%d/%Y")
sales["order_time"] = pd.to_datetime(sales["time"], format="%I:%M:%S %p").dt.strftime("%H:%M:%S")
sales["order_month"] = sales["order_date"].dt.strftime("%Y-%m")
sales = sales.drop(columns=["date", "time"])

print("rows:", len(raw), "->", len(sales))
sales.to_csv("cleaned_sales.csv", index=False)

branches = sales[["branch", "city"]].drop_duplicates().reset_index(drop=True)
branches.insert(0, "branch_id", range(1, len(branches) + 1))

customers = sales[["customer_type", "gender"]].drop_duplicates().reset_index(drop=True)
customers.insert(0, "customer_id", range(1, len(customers) + 1))

products = sales[["product_line"]].drop_duplicates().reset_index(drop=True)
products.insert(0, "product_id", range(1, len(products) + 1))

orders = sales.merge(branches, on=["branch", "city"])
orders = orders.merge(customers, on=["customer_type", "gender"])
orders = orders.merge(products, on="product_line")
orders["order_date"] = orders["order_date"].dt.strftime("%Y-%m-%d")
orders = orders[["invoice_id", "branch_id", "customer_id", "product_id", "order_date", "order_time",
                 "payment", "unit_price", "quantity", "tax", "sales_amount", "cogs", "rating"]]
orders.insert(0, "order_id", range(1, len(orders) + 1))

for name, table in [("branches", branches), ("customers", customers),
                    ("products", products), ("orders", orders)]:
    table.to_csv(name + ".csv", index=False)
    print(name, len(table))

# Analysis
by_product = sales.groupby("product_line")["sales_amount"].sum().sort_values(ascending=False)
by_month = sales.groupby("order_month")["sales_amount"].sum()
by_city = sales.groupby("city")["sales_amount"].sum().sort_values(ascending=False)
avg_sale = sales["sales_amount"].mean()
avg_by_type = sales.groupby("customer_type")["sales_amount"].mean()
payment_counts = sales["payment"].value_counts()
rating_by_product = sales.groupby("product_line")["rating"].mean().sort_values()

print(by_product)
print(by_month)
print(by_city)
print(rating_by_product)

insights = [
    f"{by_product.index[0]} brings in the most money ({by_product.iloc[0]:,.0f}, {by_product.iloc[0] / by_product.sum() * 100:.0f}% of total). {by_product.index[-1]} is lowest.",
    f"{by_month.idxmax()} was the best month with {by_month.max():,.0f}, {by_month.idxmin()} the weakest with {by_month.min():,.0f}.",
    f"{by_city.index[0]} is the top city, {by_city.iloc[0]:,.0f} in sales vs {by_city.iloc[-1]:,.0f} for {by_city.index[-1]}.",
    f"Average invoice is {avg_sale:,.0f}. Payment is split fairly evenly: {', '.join(f'{k} {v}' for k, v in payment_counts.items())}.",
    f"Members average {avg_by_type['Member']:,.0f} per invoice vs {avg_by_type['Normal']:,.0f} for normal customers, a gap of {abs(avg_by_type['Member'] - avg_by_type['Normal']) / avg_by_type['Normal'] * 100:.0f}%.",
    f"Lowest rated product line is {rating_by_product.index[0]} ({rating_by_product.iloc[0]:.2f}), highest is {rating_by_product.index[-1]} ({rating_by_product.iloc[-1]:.2f}).",
]

print("\ninsights")
for i, line in enumerate(insights, 1):
    print(f"{i}. {line}")

by_product.sort_values().plot(kind="barh", title="Sales by product line")
plt.xlabel("sales")
plt.tight_layout()
plt.savefig("sales_by_product_line.png")
plt.close()

# Load into MySQL
# Create the database if it doesn't exist, then connect to it
server_url = URL.create("mysql+pymysql", username=DB_USER, password=DB_PASSWORD,
                        host=DB_HOST, port=DB_PORT)
with create_engine(server_url).begin() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4"))

engine = create_engine(URL.create("mysql+pymysql", username=DB_USER, password=DB_PASSWORD,
                                  host=DB_HOST, port=DB_PORT, database=DB_NAME))

DDL = """
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS branches;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE branches (
    branch_id  INT          NOT NULL,
    branch     VARCHAR(20)  NOT NULL,
    city       VARCHAR(40)  NOT NULL,
    CONSTRAINT pk_branches PRIMARY KEY (branch_id),
    CONSTRAINT uq_branch UNIQUE (branch, city)
) ENGINE = InnoDB;

CREATE TABLE customers (
    customer_id    INT         NOT NULL,
    customer_type  VARCHAR(20) NOT NULL,
    gender         VARCHAR(10) NOT NULL,
    CONSTRAINT pk_customers PRIMARY KEY (customer_id),
    CONSTRAINT chk_customer_type CHECK (customer_type IN ('Member', 'Normal')),
    CONSTRAINT chk_gender CHECK (gender IN ('Male', 'Female'))
) ENGINE = InnoDB;

CREATE TABLE products (
    product_id    INT         NOT NULL,
    product_line  VARCHAR(40) NOT NULL,
    CONSTRAINT pk_products PRIMARY KEY (product_id),
    CONSTRAINT uq_product_line UNIQUE (product_line)
) ENGINE = InnoDB;

CREATE TABLE orders (
    order_id      INT           NOT NULL,
    invoice_id    VARCHAR(20)   NOT NULL,
    branch_id     INT           NOT NULL,
    customer_id   INT           NOT NULL,
    product_id    INT           NOT NULL,
    order_date    DATE          NOT NULL,
    order_time    TIME          NOT NULL,
    payment       VARCHAR(20)   NOT NULL,
    unit_price    DECIMAL(10,2) NOT NULL,
    quantity      INT           NOT NULL,
    tax           DECIMAL(10,4) NOT NULL,
    sales_amount  DECIMAL(12,4) NOT NULL,
    cogs          DECIMAL(12,4) NOT NULL,
    rating        DECIMAL(3,1),
    CONSTRAINT pk_orders PRIMARY KEY (order_id),
    CONSTRAINT uq_invoice UNIQUE (invoice_id),
    CONSTRAINT fk_orders_branch FOREIGN KEY (branch_id) REFERENCES branches (branch_id),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
    CONSTRAINT fk_orders_product FOREIGN KEY (product_id) REFERENCES products (product_id),
    CONSTRAINT chk_payment CHECK (payment IN ('Cash', 'Credit card', 'Ewallet')),
    CONSTRAINT chk_unit_price CHECK (unit_price > 0),
    CONSTRAINT chk_quantity CHECK (quantity > 0),
    CONSTRAINT chk_sales CHECK (sales_amount > 0),
    CONSTRAINT chk_rating CHECK (rating BETWEEN 1 AND 10)
) ENGINE = InnoDB;
"""

statements = [s.strip() for s in DDL.split(";") if s.strip()]
with engine.begin() as conn:
    for stmt in statements:
        conn.execute(text(stmt))
print("schema created")

# Load parent tables first, then orders
load_order = ["branches", "customers", "products", "orders"]
table_map = {"branches": branches, "customers": customers, "products": products, "orders": orders}

with engine.begin() as conn:
    for name in load_order:
        table_map[name].to_sql(name, conn, if_exists="append", index=False,
                               method="multi", chunksize=500)
        print("loaded", name, len(table_map[name]))

# Post-load check: row counts must match
with engine.connect() as conn:
    check = pd.DataFrame({
        "table": load_order,
        "dataframe_rows": [len(table_map[t]) for t in load_order],
        "mysql_rows": [conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() for t in load_order],
    })
    check["match"] = check["dataframe_rows"] == check["mysql_rows"]
    print(check.to_string(index=False))
    assert check["match"].all()

# SQL Reporting
print("\nsales by product line")
print(pd.read_sql(text("""
    SELECT p.product_line, COUNT(*) AS num_orders, ROUND(SUM(o.sales_amount), 2) AS revenue
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    GROUP BY p.product_line
    ORDER BY revenue DESC"""), engine))

print("\nmonthly revenue")
print(pd.read_sql(text("""
    SELECT DATE_FORMAT(order_date, '%Y-%m') AS month, ROUND(SUM(sales_amount), 2) AS revenue
    FROM orders
    GROUP BY month
    ORDER BY month"""), engine))

print("\nrevenue by branch and city")
print(pd.read_sql(text("""
    SELECT b.branch, b.city, ROUND(SUM(o.sales_amount), 2) AS revenue
    FROM orders o
    JOIN branches b ON o.branch_id = b.branch_id
    GROUP BY b.branch_id
    ORDER BY revenue DESC"""), engine))

print("\naverage order value by customer type and gender")
print(pd.read_sql(text("""
    SELECT c.customer_type, c.gender, COUNT(*) AS num_orders, ROUND(AVG(o.sales_amount), 2) AS avg_order_value
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    GROUP BY c.customer_id
    ORDER BY avg_order_value DESC"""), engine))

print("\npayment methods")
print(pd.read_sql(text("""
    SELECT payment, COUNT(*) AS num_orders, ROUND(SUM(sales_amount), 2) AS revenue
    FROM orders
    GROUP BY payment
    ORDER BY num_orders DESC"""), engine))

print("\nproduct lines earning more than the average product line")
print(pd.read_sql(text("""
    SELECT p.product_line, ROUND(SUM(o.sales_amount), 2) AS revenue
    FROM orders o
    JOIN products p ON o.product_id = p.product_id
    GROUP BY p.product_line
    HAVING SUM(o.sales_amount) > (
        SELECT AVG(total) FROM (
            SELECT SUM(sales_amount) AS total FROM orders GROUP BY product_id) AS sub)
    ORDER BY revenue DESC"""), engine))

print("\nbranches with more than 330 orders")
print(pd.read_sql(text("""
    SELECT b.branch, b.city, COUNT(*) AS num_orders
    FROM orders o
    JOIN branches b ON o.branch_id = b.branch_id
    GROUP BY b.branch_id
    HAVING COUNT(*) > 330
    ORDER BY num_orders DESC"""), engine))

print("\nratings grouped high / medium / low")
print(pd.read_sql(text("""
    SELECT CASE WHEN rating >= 9 THEN 'High (9+)'
                WHEN rating >= 7 THEN 'Medium (7-9)'
                ELSE 'Low (under 7)' END AS rating_group,
           COUNT(*) AS num_orders,
           ROUND(AVG(sales_amount), 2) AS avg_order_value
    FROM orders
    GROUP BY rating_group
    ORDER BY num_orders DESC"""), engine))

print("\nbusiest hours of the day")
print(pd.read_sql(text("""
    SELECT HOUR(order_time) AS hour, COUNT(*) AS num_orders
    FROM orders
    GROUP BY hour
    ORDER BY num_orders DESC
    LIMIT 5"""), engine))

print("\nbig invoices (over 800) per branch")
print(pd.read_sql(text("""
    SELECT b.branch, COUNT(*) AS big_invoices
    FROM orders o
    JOIN branches b ON o.branch_id = b.branch_id
    WHERE o.sales_amount > 800
    GROUP BY b.branch
    ORDER BY big_invoices DESC"""), engine))

print("\nhigh-value ewallet orders in Yangon")
print(pd.read_sql(text("""
    SELECT o.invoice_id, p.product_line, o.sales_amount, o.payment
    FROM orders o
    JOIN branches b ON o.branch_id = b.branch_id
    JOIN products p ON o.product_id = p.product_id
    WHERE o.payment = 'Ewallet' AND b.city = 'Yangon' AND o.sales_amount > 500
    ORDER BY o.sales_amount DESC"""), engine))

print("\nbranches with no big invoices")
print(pd.read_sql(text("""
    SELECT b.branch, b.city, COUNT(o.order_id) AS big_invoices
    FROM branches b
    LEFT JOIN orders o ON o.branch_id = b.branch_id AND o.sales_amount > 800
    GROUP BY b.branch_id
    ORDER BY big_invoices DESC"""), engine))

engine.dispose()