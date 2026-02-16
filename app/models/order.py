import uuid  # For generating unique IDs
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, Enum, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship  # For defining relationships between tables
import enum

from app.core.database import Base
from .product import Product
from .user import User


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    # Primary Key: UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User ID for this order
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)

    # Total Amount
    # Store sum here so no need to query OrderItems every time
    total_amount = Column(Numeric(10, 2), default=0.00)

    # Timestamps (Audit Trail)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # The Relationship
    #   back_populates: Tells ORM "The 'order' field on OrderItem points back here."
    #   lazy="selectin": Critical for Async. Tells ORM to load items efficiently
    #   in separate query rather than trying to join massive tables
    items = relationship("OrderItem", back_populates="order", lazy="selectin")


class OrderItem(Base):
    __tablename__ = "order_items"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Order ID
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)

    # Product ID
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # Quantity
    quantity = Column(Integer, default=1, nullable=False)

    # Unit Price (Snapshot)
    unit_price = Column(Numeric(10, 2), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")  # allows us to access item.product.name
