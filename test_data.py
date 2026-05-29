import pandas as pd
import random
import uuid
from datetime import datetime, timedelta

# ── orders ──────────────────────────────────────────────
orders = pd.read_csv("dataset/olist_orders_dataset.csv")
new_orders = []
for i in range(50):
    purchase_time = datetime.now() - timedelta(days=random.randint(0, 6))
    new_orders.append({
        "order_id": uuid.uuid4().hex,
        "customer_id": uuid.uuid4().hex,
        "order_status": random.choice(["delivered", "shipped", "processing"]),
        "order_purchase_timestamp": purchase_time.strftime("%Y-%m-%d %H:%M:%S"),
        "order_approved_at": (purchase_time + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "order_delivered_carrier_date": (purchase_time + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "order_delivered_customer_date": (purchase_time + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
        "order_estimated_delivery_date": (purchase_time + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),
    })
orders = pd.concat([orders, pd.DataFrame(new_orders)], ignore_index=True)
orders.to_csv("dataset/olist_orders_dataset.csv", index=False)
print(f"Orders: {len(orders)} rows")

# ── order items ─────────────────────────────────────────
items = pd.read_csv("dataset/olist_order_items_dataset.csv")
new_items = []
for o in new_orders:
    new_items.append({
        "order_id": o["order_id"],
        "order_item_id": 1,
        "product_id": uuid.uuid4().hex,
        "seller_id": uuid.uuid4().hex,
        "shipping_limit_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
        "price": round(random.uniform(20, 500), 2),
        "freight_value": round(random.uniform(5, 50), 2),
    })
items = pd.concat([items, pd.DataFrame(new_items)], ignore_index=True)
items.to_csv("dataset/olist_order_items_dataset.csv", index=False)
print(f"Items: {len(items)} rows")

# ── order payments ───────────────────────────────────────
payments = pd.read_csv("dataset/olist_order_payments_dataset.csv")
new_payments = []
for o in new_orders:
    new_payments.append({
        "order_id": o["order_id"],
        "payment_sequential": 1,
        "payment_type": random.choice(["credit_card", "boleto", "debit_card"]),
        "payment_installments": random.randint(1, 12),
        "payment_value": round(random.uniform(20, 600), 2),
    })
payments = pd.concat([payments, pd.DataFrame(new_payments)], ignore_index=True)
payments.to_csv("dataset/olist_order_payments_dataset.csv", index=False)
print(f"Payments: {len(payments)} rows")

# ── order reviews ────────────────────────────────────────
reviews = pd.read_csv("dataset/olist_order_reviews_dataset.csv")
new_reviews = []
for o in new_orders:
    new_reviews.append({
        "review_id": uuid.uuid4().hex,
        "order_id": o["order_id"],
        "review_score": random.randint(1, 5),
        "review_comment_title": "",
        "review_comment_message": random.choice([
            "Great product!", "Fast delivery", "Good quality",
            "As expected", "Would buy again"
        ]),
        "review_creation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "review_answer_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
reviews = pd.concat([reviews, pd.DataFrame(new_reviews)], ignore_index=True)
reviews.to_csv("dataset/olist_order_reviews_dataset.csv", index=False)
print(f"Reviews: {len(reviews)} rows")

print("\nAll files updated.")