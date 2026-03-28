from __future__ import annotations
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

from sqlalchemy import text

from models import db, StateUSA, City, Category, SubCategory, Customer, PaymentMode, OrderSale, Sale

RNG = random.Random(42)

STATE_CITIES = {
    "Florida": ["Miami", "Orlando", "Tampa"],
    "Illinois": ["Chicago", "Springfield", "Peoria"],
    "New York": ["Buffalo", "New York City", "Rochester"],
    "California": ["Los Angeles", "San Diego", "San Francisco"],
    "Texas": ["Dallas", "Austin", "Houston"],
    "Ohio": ["Columbus", "Cincinnati", "Cleveland"],
}

CATEGORY_SUBS = {
    "Electronics": ["Electronic Games", "Printers", "Laptops", "Phones"],
    "Office Supplies": ["Pens", "Markers", "Paper", "Binders"],
    "Furniture": ["Tables", "Chairs", "Sofas", "Bookcases"],
}

PAYMENT_MODES = ["UPI", "Debit Card", "EMI", "Credit Card", "COD"]

FIRST_NAMES = [
    "David", "Connor", "Robert", "John", "Clayton", "Andrea", "Olivia", "Emma",
    "Noah", "Liam", "Mia", "Sophia", "Ethan", "Lucas", "Ava", "Isabella",
]
LAST_NAMES = [
    "Padilla", "Morgan", "Stone", "Fields", "Smith", "Hill", "Taylor", "Brown",
    "Martin", "Jackson", "White", "Harris", "Clark", "Lewis", "Walker", "Hall",
]

def ensure_demo_source_db(path: Path, min_rows: int = 120) -> None:
    """Create a demo sales_dump.db if no source DB is present.
    This is only a fallback for local testing.
    """
    if path.exists():
        try:
            with sqlite3.connect(path) as conn:
                conn.execute("SELECT 1 FROM sales LIMIT 1")
            return
        except sqlite3.Error:
            pass

    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS sales")
        cur.execute("""
            CREATE TABLE sales(
                order_name CHAR(12) NOT NULL,
                amount INTEGER NOT NULL,
                profit INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                category VARCHAR(15) NOT NULL,
                sub_category VARCHAR(16) NOT NULL,
                payment_mode VARCHAR(11) NOT NULL,
                order_date DATE NOT NULL,
                customer_name VARCHAR(23) NOT NULL,
                state CHAR(10) NOT NULL,
                city CHAR(13) NOT NULL
            )
        """)
        rows = []
        order_no = 25000
        customers = [f"{fn} {ln}" for fn in FIRST_NAMES for ln in LAST_NAMES]
        dates = [date(2021,1,1) + timedelta(days=i) for i in range(1600)]
        all_city_state = [(city, state) for state, cities in STATE_CITIES.items() for city in cities]
        for i in range(min_rows):
            state, cities = RNG.choice(list(STATE_CITIES.items()))
            city = RNG.choice(cities)
            category = RNG.choice(list(CATEGORY_SUBS.keys()))
            sub_category = RNG.choice(CATEGORY_SUBS[category])
            payment_mode = RNG.choice(PAYMENT_MODES)
            customer_name = RNG.choice(customers)
            order_name = f"B-{order_no + i:05d}"
            quantity = RNG.randint(1, 20)
            amount = RNG.randint(100, 15000)
            profit = max(0, int(amount * RNG.uniform(0.05, 0.45)))
            order_date = RNG.choice(dates).isoformat()
            rows.append((order_name, amount, profit, quantity, category, sub_category, payment_mode, order_date, customer_name, state, city))
        cur.executemany("INSERT INTO sales VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
        conn.commit()

def get_source_rows(source_db_path: Path, table_name: str = "sales"):
    with sqlite3.connect(source_db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
        return [dict(r) for r in rows]

def init_normalized_database(source_rows: list[dict]) -> dict[str, int]:
    """Populate normalized tables from the universal relation rows."""
    db.drop_all()
    db.create_all()

    # Unique dictionaries
    states = sorted({r["state"].strip() for r in source_rows})
    categories = sorted({r["category"].strip() for r in source_rows})
    payment_modes = sorted({r["payment_mode"].strip() for r in source_rows})
    customers = sorted({r["customer_name"].strip() for r in source_rows})
    orders = sorted({r["order_name"].strip() for r in source_rows})
    # preserve city/state uniqueness
    city_pairs = sorted({(r["city"].strip(), r["state"].strip()) for r in source_rows})
    subcat_pairs = sorted({(r["sub_category"].strip(), r["category"].strip()) for r in source_rows})

    state_map = {}
    for name in states:
        obj = StateUSA(state_name=name)
        db.session.add(obj)
        db.session.flush()
        state_map[name] = obj.state_id

    category_map = {}
    for name in categories:
        obj = Category(category_name=name)
        db.session.add(obj)
        db.session.flush()
        category_map[name] = obj.category_id

    payment_map = {}
    for name in payment_modes:
        obj = PaymentMode(payment_mode_name=name)
        db.session.add(obj)
        db.session.flush()
        payment_map[name] = obj.payment_mode_id

    customer_map = {}
    for name in customers:
        obj = Customer(customer_name=name)
        db.session.add(obj)
        db.session.flush()
        customer_map[name] = obj.customer_id

    order_map = {}
    for name in orders:
        obj = OrderSale(order_name=name)
        db.session.add(obj)
        db.session.flush()
        order_map[name] = obj.order_id

    city_map = {}
    for city_name, state_name in city_pairs:
        obj = City(city_name=city_name, state_id=state_map[state_name])
        db.session.add(obj)
        db.session.flush()
        city_map[(city_name, state_name)] = obj.city_id

    subcat_map = {}
    for subcat_name, cat_name in subcat_pairs:
        obj = SubCategory(sub_category_name=subcat_name, category_id=category_map[cat_name])
        db.session.add(obj)
        db.session.flush()
        subcat_map[(subcat_name, cat_name)] = obj.sub_category_id

    db.session.commit()

    # Insert sales
    sale_objects = []
    for r in source_rows:
        sale_objects.append(
            Sale(
                order_id=order_map[r["order_name"].strip()],
                amount=int(r["amount"]),
                profit=int(r["profit"]),
                quantity=int(r["quantity"]),
                sub_category_id=subcat_map[(r["sub_category"].strip(), r["category"].strip())],
                payment_mode_id=payment_map[r["payment_mode"].strip()],
                order_date=_parse_date(r["order_date"]),
                customer_id=customer_map[r["customer_name"].strip()],
                city_id=city_map[(r["city"].strip(), r["state"].strip())],
            )
        )
    db.session.bulk_save_objects(sale_objects)
    db.session.commit()

    return {
        "states": len(states),
        "cities": len(city_pairs),
        "categories": len(categories),
        "sub_categories": len(subcat_pairs),
        "customers": len(customers),
        "payment_modes": len(payment_modes),
        "orders": len(orders),
        "sales": len(sale_objects),
    }

def _parse_date(value):
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return date.fromisoformat(value.isoformat())
    s = str(value)
    return date.fromisoformat(s[:10])

def recreate_universal_relation_query():
    """Return rows from normalized tables in the original universal structure."""
    return (
        db.session.query(
            OrderSale.order_name.label("order_name"),
            Sale.amount.label("amount"),
            Sale.profit.label("profit"),
            Sale.quantity.label("quantity"),
            Category.category_name.label("category"),
            SubCategory.sub_category_name.label("sub_category"),
            PaymentMode.payment_mode_name.label("payment_mode"),
            Sale.order_date.label("order_date"),
            Customer.customer_name.label("customer_name"),
            StateUSA.state_name.label("state"),
            City.city_name.label("city"),
        )
        .join(OrderSale, Sale.order_id == OrderSale.order_id)
        .join(SubCategory, Sale.sub_category_id == SubCategory.sub_category_id)
        .join(Category, SubCategory.category_id == Category.category_id)
        .join(PaymentMode, Sale.payment_mode_id == PaymentMode.payment_mode_id)
        .join(Customer, Sale.customer_id == Customer.customer_id)
        .join(City, Sale.city_id == City.city_id)
        .join(StateUSA, City.state_id == StateUSA.state_id)
        .order_by(Sale.sale_id)
    )
