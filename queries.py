from sqlalchemy import func, desc, case, select
from models import db, Sale, City, StateUSA, Category, SubCategory, Customer, PaymentMode, OrderSale

def q1_related_filtered_sorted():
    # Related tables with filtering and sorting
    return (
        db.session.query(
            Sale.sale_id,
            OrderSale.order_name,
            Sale.amount,
            Sale.profit,
            Sale.quantity,
            Customer.customer_name,
            City.city_name,
            StateUSA.state_name,
            PaymentMode.payment_mode_name,
        )
        .join(OrderSale, Sale.order_id == OrderSale.order_id)
        .join(Customer, Sale.customer_id == Customer.customer_id)
        .join(City, Sale.city_id == City.city_id)
        .join(StateUSA, City.state_id == StateUSA.state_id)
        .join(PaymentMode, Sale.payment_mode_id == PaymentMode.payment_mode_id)
        .filter(StateUSA.state_name == "California")
        .order_by(desc(Sale.amount), desc(Sale.profit))
        .limit(20)
    )

def q2_related_computed_rows():
    # Computed columns per row
    return (
        db.session.query(
            Sale.sale_id,
            OrderSale.order_name,
            Sale.amount,
            Sale.quantity,
            (Sale.amount / func.nullif(Sale.quantity, 0)).label("avg_price_per_item"),
            (Sale.profit / func.nullif(Sale.amount, 0) * 100).label("profit_margin_pct"),
            Category.category_name,
            SubCategory.sub_category_name,
        )
        .join(OrderSale, Sale.order_id == OrderSale.order_id)
        .join(SubCategory, Sale.sub_category_id == SubCategory.sub_category_id)
        .join(Category, SubCategory.category_id == Category.category_id)
        .order_by(desc((Sale.profit / func.nullif(Sale.amount, 0) * 100)))
        .limit(20)
    )

def q3_group_aggregates():
    return (
        db.session.query(
            Category.category_name,
            func.count(Sale.sale_id).label("sales_count"),
            func.sum(Sale.amount).label("total_amount"),
            func.avg(Sale.amount).label("avg_amount"),
            func.sum(Sale.profit).label("total_profit"),
        )
        .join(SubCategory, Sale.sub_category_id == SubCategory.sub_category_id)
        .join(Category, SubCategory.category_id == Category.category_id)
        .group_by(Category.category_name)
        .order_by(desc("total_amount"))
    )

def q4_group_filter_source_and_grouped():
    # Filter original records + grouped values with HAVING
    return (
        db.session.query(
            StateUSA.state_name,
            func.count(Sale.sale_id).label("sales_count"),
            func.sum(Sale.amount).label("total_amount"),
            func.sum(Sale.profit).label("total_profit"),
        )
        .join(City, Sale.city_id == City.city_id)
        .join(StateUSA, City.state_id == StateUSA.state_id)
        .filter(Sale.quantity >= 10)
        .group_by(StateUSA.state_name)
        .having(func.sum(Sale.amount) > 20000)
        .order_by(desc("total_profit"))
    )

def q5_nested_query():
    # Customers whose total amount is above the average customer total amount
    customer_totals = (
        db.session.query(
            Sale.customer_id.label("customer_id"),
            func.sum(Sale.amount).label("total_amount"),
        )
        .group_by(Sale.customer_id)
        .subquery()
    )

    avg_total = db.session.query(func.avg(customer_totals.c.total_amount)).scalar_subquery()

    return (
        db.session.query(
            Customer.customer_name,
            customer_totals.c.total_amount,
        )
        .join(customer_totals, Customer.customer_id == customer_totals.c.customer_id)
        .filter(customer_totals.c.total_amount > avg_total)
        .order_by(desc(customer_totals.c.total_amount))
    )
