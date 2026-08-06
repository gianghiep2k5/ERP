"""Pydantic schemas for inventory endpoints."""
from typing import List, Optional
from pydantic import BaseModel


class InventoryItem(BaseModel):
    inventory_id: str
    lot_id: str
    sku_id: str
    sku_name: str
    category: str
    pack_size: Optional[str]
    location_id: str
    location_name: str
    on_hand_qty: int
    available_qty: int
    reserved_qty: int
    quarantine_qty: int
    manufacturing_date: str
    expiry_date: str
    days_to_expiry: int
    fefo_priority: int   # 1 = earliest expiry for this SKU
    scenario: str
    data_status: str


class InventoryListResponse(BaseModel):
    items: List[InventoryItem]
    total: int
    skip: int
    limit: int


class InventoryDetail(InventoryItem):
    """Single inventory balance — same fields as list item, no extra joins needed."""
    pass
