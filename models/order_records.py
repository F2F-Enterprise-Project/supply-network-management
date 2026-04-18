# models/order_records.py
import uuid

from datetime import datetime, UTC
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase

from config import engine


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True)
    status = Column(String, nullable=False)
    ordered_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(String, nullable=True)


class AgnetOrderRecord(Base):
    __tablename__ = "agnet_order_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, ForeignKey("orders.order_id"), nullable=False)
    agnet_order_id = Column(String, nullable=True)   # orderId returned by AgNet
    vendor_id = Column(String, nullable=False)
    manifest_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class LocalOrderRecord(Base):
    __tablename__ = "local_order_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, ForeignKey("orders.order_id"), nullable=False)
    vendor_id = Column(String, nullable=False)
    manifest_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
