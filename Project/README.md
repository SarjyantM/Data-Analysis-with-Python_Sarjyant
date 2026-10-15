# Supermarket Sales: End-to-End ETL Pipeline

Dataset: Kaggle "Supermarket sales" (`SuperMarket Analysis.csv`, 1,000 rows, January to March 2019).

Pipeline: Raw CSV -> EDA -> Clean/Transform (Pandas) -> Analysis -> Load into MySQL -> SQL reports.

## Requirements
- Python 3.9+
- A running MySQL server (a user that can create databases)
- Python packages: `pip install -r requirements.txt`

## Run
1. Start MySQL.
2. Set the connection if it differs from the defaults.
   Defaults: user `root`, password empty, host `localhost`, port `3306`.

   Mac / Linux:
   ```
   export DB_USER="root"
   export DB_PASSWORD=""
   export DB_HOST="127.0.0.1"
   export DB_PORT="3306"
   ```

   Windows PowerShell:
   ```
   $env:DB_USER="root"; $env:DB_PASSWORD=""; $env:DB_HOST="127.0.0.1"; $env:DB_PORT="3306"
   ```
3. Run `python project.py`

The script creates `supermarket_db`, builds the tables, loads the data and checks the row counts.

## Files
| File | Purpose |
|---|---|
| `project.py` | Full pipeline: extract, EDA, clean, analyse, load, SQL reports |
| `SuperMarket Analysis.csv` | Raw dataset (never modified) |
| `cleaned_sales.csv`, `branches.csv`, `customers.csv`, `products.csv`, `orders.csv` | Cleaned and split tables |
| `supermarket_mysql.sql` | Database/table DDL (PKs, FKs, constraints) and the 12 report queries |
| `sql_reports.txt` | Output of the 12 SQL reports |
| `insights.txt` | The 6 questions and data-driven insights |
| `erd.png` | Entity Relationship Diagram |
| `eda_*.png`, `sales_by_*.png` | EDA and analysis charts |
| `requirements.txt` | Python package dependencies |

## Database design
`branches`, `customers`, `products` (parents) -> `orders` (child, 3 foreign keys). See `erd.png`.

## Notes
- The dataset has no real customer ID, so `customers` groups rows by (`customer_type`, `gender`). Customer-level insights compare groups, not individuals.
- The dataset has no product ID, so `products` is derived from `product_line`.
- The data covers only three months (January to March 2019), so monthly trends are limited to that period.
