# Documnetation

## Bronze Layer Documentation

This layer serves as the raw ingestion point for all source data. Data here is immutable and reflects the data exactly as it was received from the
source system. No transformations or cleaning are performed at this stage.

Key Components:
Source: Kaggle Olist Brazillian ecommerce data

In this step raw data remains unchanged

## Silver Layer Documentation

This is the step for data cleaning and preprocesing

Steps undertaken:

1. Load all files into tables
2. Make a list of tables with null values and a list of table siwth duplicates
3. in order_reviews table, drop duplicates and drop rows where review_score is 0 . Replace nulls in title and message field
4. in order_products datset drop rows where porduct name is null and replce nulls where dimensions are misiing
5. save cleaned tables
6. enforce data type constraints:
    a. cast review score as Int
    b. cast dates as Timestamp

## Gold Layer Documentation

This is the step for Dashboard Creation

This report consists of a 3-page dashboard

1. Revenue Details
2. Customers Satisfaction
3. Product Trends

### Revenue Details

This page provides an overview of total revenue performance across sellers, customers, and product categories.

**Key Metrics (KPI Cards):**

- **Total Revenue** – 15.84M: Aggregate revenue from all completed orders
- **Revenue Lost from Cancelled Orders** – 105.89K: Revenue impact of cancellations
- **Freight % of Revenue** – 0.14: Freight cost as a proportion of total revenue

**Visuals on this page:**

| Visual | Chart Type | Description |
|--------|-----------|-------------|
| Revenue by Seller by seller_id | Bar Chart | Compares revenue contribution per seller |
| Total Revenue by customer_state | Bar Chart | Geographic breakdown of revenue by Brazilian state |
| Total Revenue by customer_city | Map | Spatial distribution of revenue across cities |
| Total Revenue by product_category_name_english | Bar Chart | Revenue split across product categories |
| Freight % by Category by product_category_name_english | Bar Chart | Freight cost burden per product category |
| Total Freight by product_category_name_english | Bar Chart | Absolute freight cost per product category |

**Filters available:** (list any slicers you have — e.g., date range, category, state)

**Data sources used:** order_payments, orders, order_items, sellers, customers, products tables (Silver layer cleaned data)

### Customers Satisfaction

This page analyzes customer experience metrics including review scores, 
delivery performance, and payment behavior.

**Key Metrics (KPI Cards):**

- **Total Customers** – 96K: Total unique customers who placed orders
- **Avg Review Score** – 4.09: Average rating across all order reviews (scale 1–5)
- **Reviews 1 Star %** – 0.12: Proportion of customers who gave a 1-star review
- **Reviews 5 Star %** – 0.58: Proportion of customers who gave a 5-star review
- **Avg Delivery Days** – 12.50: Average number of days from order to delivery

**Visuals on this page:**

| Visual | Chart Type | Description |
|--------|------------|-------------|
| Total Customers by customer_state | Bar Chart | Distribution of customers across Brazilian states |
| Late Delivery Rate % by customer_state | Bar Chart | % of orders delivered late per state |
| Reviews 2★, 1★, 3★, 4★, 5★ breakdown | Pie Chart | Share of each review score across all orders |
| Avg Revenue by Installments by payment_installments | Bar Chart | Average order revenue grouped by number of payment installments |

**Data sources used:** order_reviews, orders, customers, order_payments 
tables (Silver layer cleaned data)

**Notes:**

- Late delivery rate is highest in northern and remote states due to logistics distance
- High 1-star % (11K) despite low Reviews 1 Star % KPI (0.12) —  KPI reflects proportion, pie chart shows absolute count
- Installment analysis helps identify if higher installment counts
  correlate with higher-value purchases
**Delivery Days Insight:**

- Median (10 days) < Average (12.50 days)
- A tail of late deliveries in remote northern states inflates the average by ~2.5 days
- Cross-reference with Late Delivery Rate % by state to identify problem regions

### Product Trends

This page analyzes product pricing, order value, cancellation behavior, 
and fulfillment speed across product categories.

**Visuals on this page:**

| Visual | Chart Type | Description |
|--------|------------|-------------|
| Min Price, Max Price and Avg Price by product_category_name_english | Clustered Bar Chart | Price range and average per category — identifies premium vs budget categories |
| High Price Orders, Low Price Orders and Mid Price Orders | Pie Chart | Order volume split by price tier |
| Cancellation Rate % by product_category_name_english | Bar Chart | Which categories have highest order cancellations |
| Price Variance by product_category_name_english | Bar Chart | Spread between min and max price per category — high variance = inconsistent pricing |
| Avg Approval Time Days, Avg Ship Time Days and Avg Transit Time Days | Bar Chart | Fulfillment pipeline breakdown per stage |
| Avg Order Value by Category by product_category_name_english | Bar Chart | Average spend per order across categories |

**Fulfillment Pipeline (overall averages):**
| Stage | Days |
|-------|------|
| Avg Approval Time | ~0.52 days |
| Avg Ship Time | 2.71 days |
| Avg Transit Time | 9.28 days |
| **Total** | **~12.51 days** ← matches Avg Delivery Days on Customers page |

**Key Insights to Note:**

- Transit time (9.28 days) dominates the pipeline at ~74% of total delivery time — logistics is the primary bottleneck, not seller processing
- dvds_blu_ray and fixed_telephony have the highest cancellation rates — 
  investigate pricing or stock issues in these categories
- Computers have the highest Avg Order Value (~1K) and highest Max Price —
  premium category driving disproportionate revenue
- High price variance categories (computers, furniture) suggest 
  inconsistent seller pricing — candidate for price standardization

**Data sources used:** olist_products_dataset, olist_order_items_da,
olist_orders_dataset, olist_order_payments (Gold layer aggregations)

## Refresh Pipeline Documentation

### Purpose and Scope
Orchestrates moving data from source CSV files through Bronze, Silver, and Gold layers automatically when new data arrives. The watcher detects file changes, uploads to OneLake, triggers the Fabric notebook, and polls until completion.

---

### Key Components

| Component | File | Role |
|-----------|------|------|
| File Watcher | `pipeline_watcher.py` | Monitors `./dataset` for CSV changes every 10 seconds using watchdog |
| OneLake Uploader | `upload_to_onelake()` | Uploads changed CSVs via ADLSg2 REST API (create → append → flush) |
| Notebook Trigger | `trigger_fabric_pipeline()` | Triggers Fabric notebook job and polls for completion every 30s |
| Test Data Generator | `test_data.py` | Appends 50 synthetic rows to orders, items, payments, reviews CSVs |
| Fabric Notebook | `Notebook_1.ipynb` | Bronze reload → Silver cleaning → type casting → Power BI refresh |

---

### Execution Flow

1. CSV in `./dataset` is modified (e.g. by `test_data.py`)
2. Watcher wakes every 10 seconds, checks `CHANGED_FILES` set
3. Acquires Azure Storage token (`scope: storage.azure.com`)
4. Uploads all changed CSVs to OneLake — 3-step ADLSg2: create file → append bytes → flush
5. OneLake file modification event automatically triggers **Pipeline_1** via a Fabric Data Activator rule
6. Pipeline_1 runs Notebook1, executing: Bronze reload → Silver cleaning → type casting → Power BI dataset refresh

---

### Fabric Trigger Rule 
| Setting | Value |
|---------|-------|
| Rule name | Refresh |
| Rule status | Running |
| Source | OneLake events |
| Action | Run Pipeline |
| Fabric item | Pipeline_1 (Project) |
| Parameters | `__type` (String), `__subject` (String) |

> Once files are uploaded to OneLake, the trigger rule fires Pipeline_1 automatically.
> Monitor run history via **Pipeline_1 → View run history** in Fabric.

---

### Authentication

OAuth 2.0 client credentials flow. Set these environment variables before running:

| Variable | Description |
|----------|-------------|
| `FABRIC_WORKSPACE_ID` | Microsoft Fabric workspace GUID |
| `FABRIC_PIPELINE_ID` | Fabric notebook item ID |
| `TENANT_ID` | Azure AD tenant ID |
| `CLIENT_ID` | Service principal application ID |
| `CLIENT_SECRET` | Service principal secret — never commit to source control |

> Two separate tokens are acquired per run: one for OneLake (storage scope) and one for the Fabric API (fabric scope), as they use different OAuth audiences.

---

### Error Handling

| Failure | Behaviour | Action |
|---------|-----------|--------|
| OneLake upload fails | Pipeline not triggered; error printed | Check `CLIENT_SECRET` expiry and OneLake path |
| Notebook job fails | Prints `Failed` + `failureReason` from API | Check Fabric notebook run logs |
| Job exceeds 7-min poll window | Polling stops silently | Increase `range(14)` for larger datasets |
| Token acquisition fails | `KeyError` on `resp.json()` | Verify all 5 env vars are set |

---

### SLA

| Stage | Expected Duration |
|-------|------------------|
| File detection | < 10 seconds |
| OneLake upload | < 30 seconds per file |
| Notebook execution | 2–5 minutes (includes Spark cold start) |
| Power BI refresh | 1–3 minutes |
| **Total end-to-end** | **6–10 minutes** |

