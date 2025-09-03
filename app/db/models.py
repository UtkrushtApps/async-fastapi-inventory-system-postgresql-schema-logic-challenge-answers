from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column, Integer, String, Numeric, ForeignKey, DateTime, Boolean, func, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship

Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    products = relationship('Product', back_populates='category')


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    sku = Column(String(40), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True)
    price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, nullable=False, server_default='1')

    category = relationship('Category', back_populates='products')
    inventory_items = relationship('Inventory', back_populates='product')
    price_history = relationship('PriceHistory', back_populates='product', order_by='desc(PriceHistory.changed_at)')
    inventory_history = relationship('InventoryHistory', back_populates='product', order_by='desc(InventoryHistory.changed_at)')


Index('ix_product_name_sku', Product.name, Product.sku)

class Inventory(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False, unique=True)
    quantity = Column(Integer, nullable=False, default=0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship('Product', back_populates='inventory_items')


class PriceHistory(Base):
    __tablename__ = 'price_history'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    old_price = Column(Numeric(12, 2), nullable=True)
    new_price = Column(Numeric(12, 2), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship('Product', back_populates='price_history')

class InventoryHistory(Base):
    __tablename__ = 'inventory_history'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    old_quantity = Column(Integer, nullable=True)
    new_quantity = Column(Integer, nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    reason = Column(String(255), nullable=True)

    product = relationship('Product', back_populates='inventory_history')

