from __future__ import annotations
from flask import Flask, render_template, redirect, url_for, flash
from sqlalchemy import inspect
from config import Config
from models import db, StateUSA, City, Category, SubCategory, Customer, PaymentMode, OrderSale, Sale
from data_utils import ensure_demo_source_db, get_source_rows, init_normalized_database, recreate_universal_relation_query
from queries import q1_related_filtered_sorted, q2_related_computed_rows, q3_group_aggregates, q4_group_filter_source_and_grouped, q5_nested_query

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
        # Подготавливаем все таблицы
        all_tables = []
        for slug, title, model in TABLE_MODEL_MAP:
            columns = [c.key for c in model.__table__.columns]
            rows = [{col: getattr(obj, col) for col in columns} for obj in model.query.limit(50).all()]
            all_tables.append({"title": title, "columns": columns, "rows": rows})

        # Подготавливаем все запросы (преобразуем строки в словари)
        results = {
            "q1": [dict(row._asdict()) if hasattr(row, "_asdict") else dict(row) for row in q1_related_filtered_sorted().all()],
            "q2": [dict(row._asdict()) if hasattr(row, "_asdict") else dict(row) for row in q2_related_computed_rows().all()],
            "q3": [dict(row._asdict()) if hasattr(row, "_asdict") else dict(row) for row in q3_group_aggregates().all()],
            "q4": [dict(row._asdict()) if hasattr(row, "_asdict") else dict(row) for row in q4_group_filter_source_and_grouped().all()],
            "q5": [dict(row._asdict()) if hasattr(row, "_asdict") else dict(row) for row in q5_nested_query().all()],
        }

        # Универсальная таблица
        universal_rows = [
            dict(row._asdict()) if hasattr(row, "_asdict") else dict(row)
            for row in recreate_universal_relation_query().limit(50).all()
        ]

        return render_template(
            "index.html",
            all_tables=all_tables,
            results=results,
            universal_rows=universal_rows,
        )

    @app.route("/table/<slug>")
    def table_view(slug):
        matched = next((x for x in TABLE_MODEL_MAP if x[0] == slug), None)
        if not matched:
            flash("Таблица не найдена", "error")
            return redirect(url_for("index"))
        _, title, model = matched
        objects = model.query.limit(200).all()
        columns = [c.key for c in inspect(model).mapper.column_attrs]
        rows = [{col: getattr(obj, col) for col in columns} for obj in objects]
        return render_template("table.html", title=title, rows=rows, columns=columns, slug=slug)

    @app.route("/queries")
    def queries():
        results = {
            "q1": q1_related_filtered_sorted().all(),
            "q2": q2_related_computed_rows().all(),
            "q3": q3_group_aggregates().all(),
            "q4": q4_group_filter_source_and_grouped().all(),
            "q5": q5_nested_query().all(),
        }
        universal_rows = recreate_universal_relation_query().limit(200).all()
        return render_template("queries.html", results=results, universal_rows=universal_rows)

    @app.route("/reimport", methods=["POST"])
    def reimport():
        with app.app_context():
            source_rows = get_source_rows(app.config["SOURCE_DB_PATH"], app.config["SOURCE_TABLE_NAME"])
            stats = init_normalized_database(source_rows)
        flash(f"База пересобрана. Загружено записей sale: {stats['sales']}", "success")
        return redirect(url_for("index"))

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
