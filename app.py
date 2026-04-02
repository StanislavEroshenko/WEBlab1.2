from __future__ import annotations
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from sqlalchemy import func
from config import Config
from models import db, StateUSA, City, Category, SubCategory, Customer, PaymentMode, OrderSale, Sale
from data_utils import ensure_demo_source_db, get_source_rows, init_normalized_database, recreate_universal_relation_query
from queries import q1_related_filtered_sorted, q2_related_computed_rows, q3_group_aggregates, q4_group_filter_source_and_grouped, q5_nested_query
from datetime import datetime

TABLE_MODEL_MAP = [
    ("state_usa", "Штаты", StateUSA),
    ("city", "Города", City),
    ("category", "Категории", Category),
    ("sub_category", "Подкатегории", SubCategory),
    ("customer", "Покупатели", Customer),
    ("payment_mode", "Способы оплаты", PaymentMode),
    ("order_sale", "Заказы", OrderSale),
    ("sale", "Продажи", Sale),
]

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        ensure_demo_source_db(app.config["SOURCE_DB_PATH"], min_rows=150)
        source_rows = get_source_rows(app.config["SOURCE_DB_PATH"], app.config["SOURCE_TABLE_NAME"])
        init_normalized_database(source_rows)

    @app.context_processor
    def inject_nav():
        return {"nav_tables": TABLE_MODEL_MAP}

    @app.route("/")
    def index():
        all_tables = []
        for slug, title, model in TABLE_MODEL_MAP:
            columns = [c.key for c in model.__table__.columns]

            query = model.query
            if slug == "sale":
                query = query.order_by(model.sale_id.desc())

            rows = [{col: getattr(obj, col) for col in columns} for obj in query.limit(50).all()]
            all_tables.append({"title": title, "columns": columns, "rows": rows})

        results = {
            "q1": [dict(row._asdict()) for row in q1_related_filtered_sorted().all()],
            "q2": [dict(row._asdict()) for row in q2_related_computed_rows().all()],
            "q3": [dict(row._asdict()) for row in q3_group_aggregates().all()],
            "q4": [dict(row._asdict()) for row in q4_group_filter_source_and_grouped().all()],
            "q5": [dict(row._asdict()) for row in q5_nested_query().all()],
        }

        universal_rows = [dict(row._asdict()) for row in recreate_universal_relation_query().limit(50).all()]

        return render_template(
            "index.html",
            all_tables=all_tables,
            results=results,
            universal_rows=universal_rows,
        )

    @app.route("/reimport", methods=["POST"])
    def reimport():
        with app.app_context():
            source_rows = get_source_rows(app.config["SOURCE_DB_PATH"], app.config["SOURCE_TABLE_NAME"])
            stats = init_normalized_database(source_rows)
        flash(f"База пересобрана. Загружено записей sale: {stats['sales']}", "success")
        return redirect(url_for("index"))

    # ---------- API CRUD для Sale (доступно по /api/orders) ----------
    @app.route("/api/orders", methods=["GET"])
    def api_get_sales():
        columns = [c.key for c in Sale.__table__.columns]
        sales = Sale.query.limit(100).all()
        return jsonify([{col: getattr(s, col) for col in columns} for s in sales])

    @app.route("/api/orders/<int:sale_id>", methods=["GET"])
    def api_get_sale(sale_id):
        sale = Sale.query.get_or_404(sale_id)
        columns = [c.key for c in Sale.__table__.columns]
        return jsonify({col: getattr(sale, col) for col in columns})


    from datetime import datetime
    @app.route('/api/orders', methods=['POST'])
    def api_create_sale():
        data = request.get_json()

        if "order_date" in data:
            data["order_date"] = datetime.strptime(data["order_date"], "%Y-%m-%d").date()

        sale = Sale(**data)
        db.session.add(sale)
        db.session.commit()
        return jsonify({"message": "Sale created", "id": sale.sale_id})

    @app.route("/api/orders/<int:sale_id>", methods=["PUT"])
    def api_update_sale(sale_id):
        sale = Sale.query.get_or_404(sale_id)
        data = request.get_json()
        for key, value in data.items():
            if hasattr(sale, key):
                setattr(sale, key, value)
        db.session.commit()
        return jsonify({"message": "Sale updated"})

    @app.route("/api/orders/<int:sale_id>", methods=["DELETE"])
    def api_delete_sale(sale_id):
        sale = Sale.query.get_or_404(sale_id)
        db.session.delete(sale)
        db.session.commit()
        return jsonify({"message": "Sale deleted"})

    # ---------- API вложенный JSON ----------
    @app.route("/api/orders_nested", methods=["GET"])
    def api_sales_nested():
        rows = (
            db.session.query(Sale, Customer, SubCategory)
            .join(Customer, Sale.customer_id == Customer.customer_id)
            .join(SubCategory, Sale.sub_category_id == SubCategory.sub_category_id)
            .all()
        )

        nested = []
        for sale, customer, subcategory in rows:
            nested.append({
                "sale_id": sale.sale_id,
                "amount": sale.amount,
                "customer": {
                    "id": customer.customer_id,
                    "name": customer.customer_name,
                },
                "category": {
                    "id": subcategory.sub_category_id,
                    "name": subcategory.sub_category_name,
                },
            })
        return jsonify(nested)

    # ---------- API агрегаты ----------
    @app.route("/api/aggregates/city", methods=["GET"])
    def api_stats_city():
        stats = db.session.query(
            City.city_name.label("city"),
            func.max(Sale.amount).label("max_sale"),
            func.min(Sale.amount).label("min_sale"),
            func.avg(Sale.amount).label("avg_sale")
        ).join(Customer, Customer.city_id == City.city_id)\
         .join(Sale, Sale.customer_id == Customer.customer_id)\
         .group_by(City.city_id).all()
        return jsonify([dict(row._asdict()) for row in stats])

    @app.route("/api/aggregates/category", methods=["GET"])
    def api_stats_category():
        stats = db.session.query(
            SubCategory.sub_category_name.label("subcategory"),
            func.max(Sale.amount).label("max_sale"),
            func.min(Sale.amount).label("min_sale"),
            func.avg(Sale.amount).label("avg_sale")
        ).join(Sale, Sale.sub_category_id == SubCategory.sub_category_id)\
         .group_by(SubCategory.sub_category_id).all()
        return jsonify([dict(row._asdict()) for row in stats])

    @app.route("/api/aggregates/payment_mode", methods=["GET"])
    def api_stats_payment_mode():
        stats = db.session.query(
            PaymentMode.payment_mode_name.label("payment_mode"),
            func.max(Sale.amount).label("max_sale"),
            func.min(Sale.amount).label("min_sale"),
            func.avg(Sale.amount).label("avg_sale")
        ).join(Sale, Sale.payment_mode_id == PaymentMode.payment_mode_id)\
         .group_by(PaymentMode.payment_mode_id).all()
        return jsonify([dict(row._asdict()) for row in stats])

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)