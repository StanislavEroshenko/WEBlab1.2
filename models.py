from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class StateUSA(db.Model):
    state_id = db.Column(db.Integer, primary_key=True)
    state_name = db.Column(db.String, nullable=False)
    cities = db.relationship("City", back_populates="state")

class City(db.Model):
    city_id = db.Column(db.Integer, primary_key=True)
    city_name = db.Column(db.String, nullable=False)
    state_id = db.Column(db.Integer, db.ForeignKey("state_usa.state_id"))
    state = db.relationship("StateUSA", back_populates="cities")
    customers = db.relationship("Customer", back_populates="city")

class Category(db.Model):
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String, nullable=False)
    sub_categories = db.relationship("SubCategory", back_populates="category")

class SubCategory(db.Model):
    sub_category_id = db.Column(db.Integer, primary_key=True)
    sub_category_name = db.Column(db.String, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.category_id"))
    category = db.relationship("Category", back_populates="sub_categories")
    sales = db.relationship("Sale", back_populates="sub_category")

class Customer(db.Model):
    customer_id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String, nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey("city.city_id"))
    city = db.relationship("City", back_populates="customers")
    sales = db.relationship("Sale", back_populates="customer")

class PaymentMode(db.Model):
    payment_mode_id = db.Column(db.Integer, primary_key=True)
    payment_mode_name = db.Column(db.String, nullable=False)
    sales = db.relationship("Sale", back_populates="payment_mode")

class OrderSale(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    order_name = db.Column(db.String, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.customer_id"))
    customer = db.relationship("Customer")
    date = db.Column(db.Date)
    total_amount = db.Column(db.Float)

class Sale(db.Model):
    sale_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order_sale.order_id"))
    amount = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.customer_id"))
    sub_category_id = db.Column(db.Integer, db.ForeignKey("sub_category.sub_category_id"))
    payment_mode_id = db.Column(db.Integer, db.ForeignKey("payment_mode.payment_mode_id"))
    city_id = db.Column(db.Integer, db.ForeignKey("city.city_id"))
    order_date = db.Column(db.Date, nullable=False)  # <- добавлено

    customer = db.relationship("Customer", back_populates="sales")
    sub_category = db.relationship("SubCategory", back_populates="sales")
    payment_mode = db.relationship("PaymentMode", back_populates="sales")
    city = db.relationship("City")