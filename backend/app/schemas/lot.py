"""Pydantic schemas for lot endpoints."""
from typing import List, Optional
from pydantic import BaseModel


class LinkedRecommendation(BaseModel):
    recommendation_id: str
    recommendation_type: str
    proposed_qty: int
    adjusted_qty: Optional[int]
    effective_qty: int          # COALESCE(adjusted_qty, proposed_qty)
    status: str
    reason: str
    created_at: str


class LotDetail(BaseModel):
    # ── Lot ──────────────────────────────────────────────────────────────
    lot_id: str
    manufacturing_date: str
    expiry_date: str
    days_to_expiry: int
    fefo_position: int          # rank of this lot among all lots for its SKU
    fefo_total: int             # total lots for this SKU
    lot_data_status: str

    # ── SKU ──────────────────────────────────────────────────────────────
    sku_id: str
    sku_name: str
    category: str
    pack_size: Optional[str]
    default_shelf_life_days: int
    unit_cost_vnd: int
    variant_status: str
    source_status: str

    # ── Public product ────────────────────────────────────────────────────
    public_product_id: str
    product_name: str
    public_pack_size: Optional[str]
    source_url: str

    # ── Inventory balance ─────────────────────────────────────────────────
    inventory_id: str
    location_id: str
    location_name: str
    location_type: str
    on_hand_qty: int
    available_qty: int
    reserved_qty: int
    quarantine_qty: int
    last_updated: str
    scenario: str

    # ── Linked recommendations ────────────────────────────────────────────
    recommendations: List[LinkedRecommendation]

    # ── Meta ─────────────────────────────────────────────────────────────
    analysis_date: str


class LotListItem(BaseModel):
    lot_id: str
    sku_id: str
    sku_name: str
    category: str
    manufacturing_date: str
    expiry_date: str
    days_to_expiry: int
    fefo_position: int
    fefo_total: int
    on_hand_qty: int
    scenario: str
    location_name: str


class LotListResponse(BaseModel):
    items: List[LotListItem]
    total: int
    skip: int
    limit: int
