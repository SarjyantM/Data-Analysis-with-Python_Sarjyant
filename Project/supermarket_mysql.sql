CREATE DATABASE IF NOT EXISTS supermarket_db CHARACTER SET utf8mb4;
USE supermarket_db;

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

-- sales by product line
SELECT p.product_line, COUNT(*) AS num_orders, ROUND(SUM(o.sales_amount), 2) AS revenue
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY p.product_line
ORDER BY revenue DESC;

-- monthly revenue
SELECT DATE_FORMAT(order_date, '%Y-%m') AS month, ROUND(SUM(sales_amount), 2) AS revenue
FROM orders
GROUP BY month
ORDER BY month;

-- revenue by branch and city
SELECT b.branch, b.city, ROUND(SUM(o.sales_amount), 2) AS revenue
FROM orders o
JOIN branches b ON o.branch_id = b.branch_id
GROUP BY b.branch_id
ORDER BY revenue DESC;

-- average order value by customer type and gender
SELECT c.customer_type, c.gender, COUNT(*) AS num_orders, ROUND(AVG(o.sales_amount), 2) AS avg_order_value
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id
ORDER BY avg_order_value DESC;

-- payment methods
SELECT payment, COUNT(*) AS num_orders, ROUND(SUM(sales_amount), 2) AS revenue
FROM orders
GROUP BY payment
ORDER BY num_orders DESC;

-- product lines earning more than the average product line
SELECT p.product_line, ROUND(SUM(o.sales_amount), 2) AS revenue
FROM orders o
JOIN products p ON o.product_id = p.product_id
GROUP BY p.product_line
HAVING SUM(o.sales_amount) > (
    SELECT AVG(total) FROM (
        SELECT SUM(sales_amount) AS total FROM orders GROUP BY product_id) AS sub)
ORDER BY revenue DESC;

-- branches with more than 330 orders
SELECT b.branch, b.city, COUNT(*) AS num_orders
FROM orders o
JOIN branches b ON o.branch_id = b.branch_id
GROUP BY b.branch_id
HAVING COUNT(*) > 330
ORDER BY num_orders DESC;

-- ratings grouped high / medium / low
SELECT CASE WHEN rating >= 9 THEN 'High (9+)'
            WHEN rating >= 7 THEN 'Medium (7-9)'
            ELSE 'Low (under 7)' END AS rating_group,
       COUNT(*) AS num_orders,
       ROUND(AVG(sales_amount), 2) AS avg_order_value
FROM orders
GROUP BY rating_group
ORDER BY num_orders DESC;

-- busiest hours of the day
SELECT HOUR(order_time) AS hour, COUNT(*) AS num_orders
FROM orders
GROUP BY hour
ORDER BY num_orders DESC
LIMIT 5;

-- big invoices (over 800) per branch
SELECT b.branch, COUNT(*) AS big_invoices
FROM orders o
JOIN branches b ON o.branch_id = b.branch_id
WHERE o.sales_amount > 800
GROUP BY b.branch
ORDER BY big_invoices DESC;

-- high-value ewallet orders in Yangon
SELECT o.invoice_id, p.product_line, o.sales_amount, o.payment
FROM orders o
JOIN branches b ON o.branch_id = b.branch_id
JOIN products p ON o.product_id = p.product_id
WHERE o.payment = 'Ewallet' AND b.city = 'Yangon' AND o.sales_amount > 500
ORDER BY o.sales_amount DESC;

-- big invoice count for every branch, including ones with none
SELECT b.branch, b.city, COUNT(o.order_id) AS big_invoices
FROM branches b
LEFT JOIN orders o ON o.branch_id = b.branch_id AND o.sales_amount > 800
GROUP BY b.branch_id
ORDER BY big_invoices DESC;
