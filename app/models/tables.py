from sqlalchemy import Column, Date, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True)
    product_name = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True)
    order_date = Column(Date, index=True, nullable=False)
    product_id = Column(String, index=True, nullable=False)
    channel = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    sales_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False)


class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ad_date = Column(Date, index=True, nullable=False)
    campaign_id = Column(String, index=True, nullable=False)
    campaign_name = Column(String, nullable=False)
    product_id = Column(String, index=True, nullable=False)
    spend = Column(Float, nullable=False)
    impressions = Column(Integer, nullable=False)
    clicks = Column(Integer, nullable=False)
    conversions = Column(Integer, nullable=False)
    attributed_sales = Column(Float, nullable=False)


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_date = Column(Date, index=True, nullable=False)
    product_id = Column(String, index=True, nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    safety_stock = Column(Integer, nullable=False)


class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(String, primary_key=True)
    review_date = Column(Date, index=True, nullable=False)
    product_id = Column(String, index=True, nullable=False)
    rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=False)


class CSMessage(Base):
    __tablename__ = "cs_messages"

    message_id = Column(String, primary_key=True)
    message_date = Column(Date, index=True, nullable=False)
    product_id = Column(String, index=True, nullable=False)
    category = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, nullable=False)
