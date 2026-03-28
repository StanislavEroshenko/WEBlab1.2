from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class StateUSA(db.Model):
    __tablename__ = "state_usa"
    state_id = db.Column(db.Integer, primary_key=True)
    state_name = db.Column(db.String(12), nullable=False, unique=True)
    cities = db.relationship("City", backref="state", lazy=True)

class City(db.Model):
    __tablename__ = "city"
    city_id = db.Column(db.Integer, primary_key=True)
    city_name = db.Column(db.String(16), nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey("state_usa.state_id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("city_name", "state_id", name="uq_city_name_state"),
    )
    sales = db.relationship("Sale", backref="city", lazy=True)

class Category(db.Model):
    __tablename__ = "category"
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(20), nullable=False, unique=True)
    sub_categories = db.relationship("SubCategory", backref="category", lazy=True)

class SubCategory(db.Model):
    __tablename__ = "sub_category"
    sub_category_id = db.Column(db.Integer, primary_key=True)
    sub_category_name = db.Column(db.String(20), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.category_id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("sub_category_name", "category_id", name="uq_sub_category_name_category"),
    )
    sales = db.relationship("Sale", backref="sub_category", lazy=True)

class Customer(db.Model):
    __tablename__ = "customer"
    customer_id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(30), nullable=False, unique=True)
    sales = db.relationship("Sale", backref="customer", lazy=True)

class PaymentMode(db.Model):
    __tablename__ = "payment_mode"
    payment_mode_id = db.Column(db.Integer, primary_key=True)
    payment_mode_name = db.Column(db.String(16), nullable=False, unique=True)
    sales = db.relationship("Sale", backref="payment_mode", lazy=True)

class OrderSale(db.Model):
    __tablename__ = "order_sale"
    order_id = db.Column(db.Integer, primary_key=True)
    order_name = db.Column(db.String(12), nullable=False, unique=True)
    sales = db.relationship("Sale", backref="order", lazy=True)

class Sale(db.Model):
    __tablename__ = "sale"
    sale_id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("order_sale.order_id", ondelete="SET NULL"), nullable=True)
    amount = db.Column(db.Integer, nullable=False)
    profit = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    sub_category_id = db.Column(db.Integer, db.ForeignKey("sub_category.sub_category_id", ondelete="SET NULL"), nullable=True)
    payment_mode_id = db.Column(db.Integer, db.ForeignKey("payment_mode.payment_mode_id", ondelete="SET NULL"), nullable=True)
    order_date = db.Column(db.Date, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.customer_id", ondelete="SET NULL"), nullable=True)
    city_id = db.Column(db.Integer, db.ForeignKey("city.city_id", ondelete="SET NULL"), nullable=True)

    def as_universal_dict(self):
        return {
            "order_name": self.order.order_name if self.order else None,
            "amount": self.amount,
            "profit": self.profit,
            "quantity": self.quantity,
            "category": self.sub_category.category.category_name if self.sub_category and self.sub_category.category else None,
            "sub_category": self.sub_category.sub_category_name if self.sub_category else None,
            "payment_mode": self.payment_mode.payment_mode_name if self.payment_mode else None,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "customer_name": self.customer.customer_name if self.customer else None,
            "state": self.city.state.state_name if self.city and self.city.state else None,
            "city": self.city.city_name if self.city else None,
        }
