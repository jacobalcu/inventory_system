from sqlalchemy import Column, String, Boolean, Integer, Numeric

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    # Primary Key: Auto-Increment integers
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Product Name: Indexed for fast lookups
    name = Column(String, index=True, nullable=False)

    # Project SKU: Unique identifier for inventory management
    sku = Column(String, unique=True, index=True, nullable=False)

    # Price: Not float as they are imprecise
    # 10 digits total, 2 after the decimal point (e.g. 99999999.99)
    price = Column(Numeric(10, 2), nullable=False)

    # Inventory
    stock_quantity = Column(Integer, default=0, nullable=False)

    # Locking for Concurrency
    # Optimistic Locking
    #   - Every time we update the product, increment this number
    #   - If version in DB doesn't match version we have, know someone else modified it
    version = Column(Integer, default=0, nullable=False)
