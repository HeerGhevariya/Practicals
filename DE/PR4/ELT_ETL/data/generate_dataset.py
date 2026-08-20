"""
Synthetic Unnormalized Retail Sales Data Generator
Generates a realistic unnormalized CSV dataset with typical data quality flaws
(inconsistent casing, whitespace, currency formatting, date variations, nulls/invalid records).
"""

import os
import csv
import random
from datetime import datetime, timedelta

def generate_retail_data(output_path: str, num_records: int = 200000, seed: int = 42):
    random.seed(seed)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    categories = ["Electronics", "Clothing", "Home & Kitchen", "Books", "Sports & Outdoors", "Beauty & Care"]
    products_pool = [
        ("PROD-101", "Wireless Noise-Canceling Headphones", "Electronics", 149.99),
        ("PROD-102", "Ergonomic Mechanical Keyboard", "Electronics", 89.50),
        ("PROD-103", "4K Ultra HD Monitor 27-inch", "Electronics", 299.00),
        ("PROD-104", "Cotton Crewneck T-Shirt", "Clothing", 19.99),
        ("PROD-105", "Slim Fit Denim Jeans", "Clothing", 49.95),
        ("PROD-106", "All-Weather Running Jacket", "Clothing", 79.00),
        ("PROD-107", "Stainless Steel French Press", "Home & Kitchen", 34.50),
        ("PROD-108", "Non-Stick Ceramic Frying Pan", "Home & Kitchen", 42.00),
        ("PROD-109", "Robot Vacuum Cleaner", "Home & Kitchen", 219.99),
        ("PROD-110", "Designing Data-Intensive Applications", "Books", 55.00),
        ("PROD-111", "Clean Code Developer Guide", "Books", 44.95),
        ("PROD-112", "Yoga Mat Eco-Friendly 6mm", "Sports & Outdoors", 29.99),
        ("PROD-113", "Insulated Water Bottle 32oz", "Sports & Outdoors", 22.50),
        ("PROD-114", "Hydrating Facial Cleanser", "Beauty & Care", 18.00),
        ("PROD-115", "Organic Argan Oil Hair Serum", "Beauty & Care", 26.50),
    ]
    
    customers_pool = [
        (f"CUST-{100 + i}", f"Customer {i}", f"user_{i}@example.com")
        for i in range(1, 1001)
    ]
    
    stores_pool = [
        ("STR-01", "New York, NY"),
        ("STR-02", "San Francisco, CA"),
        ("STR-03", "Chicago, IL"),
        ("STR-04", "Austin, TX"),
        ("STR-05", "Seattle, WA"),
        ("STR-06", "Boston, MA"),
    ]
    
    payment_methods = ["Credit Card", "Debit Card", "PayPal", "Cash", "Apple Pay"]
    
    start_date = datetime(2024, 1, 1)
    
    fieldnames = [
        "transaction_id",
        "transaction_date",
        "customer_id",
        "customer_name",
        "customer_email",
        "store_id",
        "store_location",
        "product_id",
        "product_name",
        "product_category",
        "quantity",
        "unit_price",
        "discount_amount",
        "payment_method"
    ]
    
    print(f"Generating {num_records} unnormalized retail transaction records...")
    
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for i in range(1, num_records + 1):
            txn_id = f"TXN-{1000000 + i}"
            
            # Random date within 180 days
            seconds_offset = random.randint(0, 180 * 24 * 3600)
            dt = start_date + timedelta(seconds=seconds_offset)
            
            # Date format variation & noise injection
            date_rand = random.random()
            if date_rand < 0.85:
                dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            elif date_rand < 0.95:
                dt_str = dt.strftime("%Y/%m/%d %H:%M:%S")
            elif date_rand < 0.99:
                dt_str = dt.strftime("%d-%m-%Y %H:%M:%S")
            else:
                dt_str = "INVALID_DATE"  # Dirty data
                
            cust_id, cust_name, cust_email = random.choice(customers_pool)
            # Casing & whitespace noise
            if random.random() < 0.15:
                cust_name = f"  {cust_name.lower()} "
                cust_email = f" {cust_email.upper()}  "
                
            store_id, store_loc = random.choice(stores_pool)
            if random.random() < 0.10:
                store_loc = f" {store_loc} "
                
            prod_id, prod_name, prod_cat, base_price = random.choice(products_pool)
            if random.random() < 0.10:
                prod_name = f" {prod_name.upper()} "
                prod_cat = f" {prod_cat.lower()} "
                
            # Quantity noise
            qty_rand = random.random()
            if qty_rand < 0.95:
                quantity_val = str(random.randint(1, 10))
            elif qty_rand < 0.98:
                quantity_val = f" {random.randint(1, 5)} "
            else:
                quantity_val = "-1"  # Invalid quantity
                
            # Price string formatting noise
            if random.random() < 0.20:
                unit_price_val = f"$ {base_price:.2f} "
            else:
                unit_price_val = f"{base_price:.2f}"
                
            # Discount noise
            discount_rand = random.random()
            if discount_rand < 0.70:
                discount_val = "0.00"
            elif discount_rand < 0.95:
                disc_amt = round(base_price * random.uniform(0.05, 0.25), 2)
                discount_val = f"$ {disc_amt:.2f}" if random.random() < 0.3 else f"{disc_amt:.2f}"
            else:
                discount_val = ""  # Null/missing discount
                
            pm = random.choice(payment_methods)
            if random.random() < 0.15:
                pm = f"  {pm.lower()}  "
                
            writer.writerow({
                "transaction_id": txn_id,
                "transaction_date": dt_str,
                "customer_id": cust_id,
                "customer_name": cust_name,
                "customer_email": cust_email,
                "store_id": store_id,
                "store_location": store_loc,
                "product_id": prod_id,
                "product_name": prod_name,
                "product_category": prod_cat,
                "quantity": quantity_val,
                "unit_price": unit_price_val,
                "discount_amount": discount_val,
                "payment_method": pm
            })
            
    print(f"Dataset generated successfully: {output_path} ({os.path.getsize(output_path) / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    target_path = os.path.join(os.path.dirname(__file__), "raw_retail_sales.csv")
    generate_retail_data(target_path, num_records=200000)
