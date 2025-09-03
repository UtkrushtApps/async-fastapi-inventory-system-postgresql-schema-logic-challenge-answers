from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select as async_select

from app.db.models import Category, Product, Inventory, PriceHistory, InventoryHistory
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from fastapi import BackgroundTasks, HTTPException, status

########## CATEGORY CRUD ##########

async def create_category(session: AsyncSession, name: str, description: Optional[str] = None) -> Category:
    cat = Category(name=name, description=description)
    session.add(cat)
    await session.commit()
    await session.refresh(cat)
    return cat

async def get_category(session: AsyncSession, category_id: int) -> Category:
    q = select(Category).where(Category.id == category_id)
    result = await session.execute(q)
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

async def list_categories(session: AsyncSession) -> List[Category]:
    q = select(Category)
    result = await session.execute(q)
    return result.scalars().all()

async def update_category(session: AsyncSession, category_id: int, patch: Dict[str, Any]) -> Category:
    q = select(Category).where(Category.id == category_id)
    res = await session.execute(q)
    category = res.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    for k, v in patch.items():
        setattr(category, k, v)
    await session.commit()
    await session.refresh(category)
    return category

async def delete_category(session: AsyncSession, category_id: int):
    category = await get_category(session, category_id)
    await session.delete(category)
    await session.commit()


########## PRODUCT CRUD ##########

async def create_product(
    session: AsyncSession,
    name: str,
    sku: str,
    price: Decimal,
    category_id: Optional[int] = None,
    description: Optional[str] = None,
    initial_quantity: int = 0
) -> Product:
    product = Product(
        name=name,
        sku=sku,
        price=price,
        category_id=category_id,
        description=description
    )
    session.add(product)
    await session.flush()  # Assign product.id

    # Create Inventory entry
    inventory = Inventory(product_id=product.id, quantity=initial_quantity)
    session.add(inventory)
    # Create PriceHistory
    phist = PriceHistory(product_id=product.id, old_price=None, new_price=price)
    session.add(phist)
    # Create InventoryHistory
    ihist = InventoryHistory(product_id=product.id, old_quantity=None, new_quantity=initial_quantity, reason="Initial stock")
    session.add(ihist)
    await session.commit()
    await session.refresh(product)
    return product

async def get_product(session: AsyncSession, product_id: int) -> Product:
    q = select(Product).where(Product.id == product_id).options(joinedload(Product.category))
    result = await session.execute(q)
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

async def get_product_by_sku(session: AsyncSession, sku: str) -> Product:
    q = select(Product).where(Product.sku == sku)
    result = await session.execute(q)
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

async def list_products(
    session: AsyncSession,
    name: Optional[str] = None,
    sku: Optional[str] = None,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    price_min: Optional[Decimal] = None,
    price_max: Optional[Decimal] = None,
    offset: int = 0,
    limit: int = 50
) -> List[Product]:
    filters = []
    if name:
        filters.append(Product.name.ilike(f"%{name}%"))
    if sku:
        filters.append(Product.sku == sku)
    if category_id is not None:
        filters.append(Product.category_id == category_id)
    if is_active is not None:
        filters.append(Product.is_active == is_active)
    if price_min is not None:
        filters.append(Product.price >= price_min)
    if price_max is not None:
        filters.append(Product.price <= price_max)

    q = select(Product).where(and_(*filters)).offset(offset).limit(limit)
    result = await session.execute(q)
    return result.scalars().all()

async def update_product(session: AsyncSession, product_id: int, patch: Dict[str, Any], background_tasks: Optional[BackgroundTasks]=None) -> Product:
    product = await get_product(session, product_id)
    update_fields = set(patch.keys())
    price_changed = 'price' in update_fields and getattr(product, 'price') != patch['price']
    old_price = product.price if price_changed else None
    for k, v in patch.items():
        setattr(product, k, v)
    await session.flush()
    if price_changed:
        # Insert PriceHistory
        phist = PriceHistory(product_id=product.id, old_price=old_price, new_price=patch['price'])
        session.add(phist)
    await session.commit()
    await session.refresh(product)
    return product

async def delete_product(session: AsyncSession, product_id: int):
    product = await get_product(session, product_id)
    await session.delete(product)
    await session.commit()


########## INVENTORY & HISTORY ##########

async def get_inventory(session: AsyncSession, product_id: int) -> Inventory:
    q = select(Inventory).where(Inventory.product_id == product_id)
    result = await session.execute(q)
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return inv

async def list_inventory(session: AsyncSession, in_stock_only: bool = False, offset: int = 0, limit: int = 50):
    q = select(Inventory).join(Product)
    if in_stock_only:
        q = q.where(Inventory.quantity > 0)
    q = q.offset(offset).limit(limit)
    result = await session.execute(q)
    return result.scalars().all()

async def update_inventory(
    session: AsyncSession,
    product_id: int,
    new_quantity: int,
    reason: Optional[str] = None,
    background_tasks: Optional[BackgroundTasks]=None
):
    inventory = await get_inventory(session, product_id)
    old_quantity = inventory.quantity
    inventory.quantity = new_quantity
    await session.flush()

    hist = InventoryHistory(product_id=product_id, old_quantity=old_quantity, new_quantity=new_quantity, reason=reason)
    session.add(hist)
    await session.commit()
    if background_tasks:
        background_tasks.add_task(log_inventory_change, hist.id, product_id, old_quantity, new_quantity, reason)
    return inventory

async def adjust_inventory(
    session: AsyncSession,
    product_id: int,
    delta: int,
    reason: Optional[str] = None,
    background_tasks: Optional[BackgroundTasks]=None
):
    inventory = await get_inventory(session, product_id)
    old_quantity = inventory.quantity
    new_quantity = old_quantity + delta
    if new_quantity < 0:
        raise HTTPException(status_code=409, detail="Insufficient inventory")
    inventory.quantity = new_quantity
    await session.flush()
    hist = InventoryHistory(product_id=product_id, old_quantity=old_quantity, new_quantity=new_quantity, reason=reason)
    session.add(hist)
    await session.commit()
    if background_tasks:
        background_tasks.add_task(log_inventory_change, hist.id, product_id, old_quantity, new_quantity, reason)
    return inventory

async def list_inventory_history(session: AsyncSession, product_id: Optional[int]=None, offset: int=0, limit: int=50) -> List[InventoryHistory]:
    q = select(InventoryHistory)
    if product_id:
        q = q.where(InventoryHistory.product_id==product_id)
    q = q.order_by(InventoryHistory.changed_at.desc()).offset(offset).limit(limit)
    result = await session.execute(q)
    return result.scalars().all()

async def list_price_history(session: AsyncSession, product_id: int, offset: int=0, limit: int=50) -> List[PriceHistory]:
    q = select(PriceHistory).where(PriceHistory.product_id == product_id).order_by(PriceHistory.changed_at.desc()).offset(offset).limit(limit)
    result = await session.execute(q)
    return result.scalars().all()

# --------- BACKGROUND LOGGING TASK -----------
import logging

async def log_inventory_change(hist_id: int, product_id: int, old_quantity: int, new_quantity: int, reason: Optional[str] = None):
    logging.info(f"InventoryHistory #{hist_id} for product_id {product_id}: {old_quantity} -> {new_quantity}. Reason: {reason}")
