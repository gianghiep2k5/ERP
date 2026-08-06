"""Inventory router: GET /api/inventory and GET /api/inventory/{inventory_id}."""
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.constants import DEMO_ANALYSIS_DATE
from app.database import get_db
from app.dependencies import READ_ALL_ROLES, require_role
from app.models.inventory_balance import InventoryBalance
from app.models.location import Location
from app.models.lot import Lot
from app.models.sku import SKU
from app.models.user import User
from app.schemas.inventory import InventoryDetail, InventoryItem, InventoryListResponse

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


def _calculate_days_to_expiry(expiry_date_str: str) -> int:
    exp_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
    return (exp_date - DEMO_ANALYSIS_DATE).days


@router.get(
    "",
    response_model=InventoryListResponse,
    summary="List inventory balances with filters, FEFO priority, and pagination",
)
def list_inventory(
    current_user: Annotated[User, Depends(require_role(READ_ALL_ROLES))],
    db: Annotated[Session, Depends(get_db)],
    sku_id: Optional[str] = Query(None, description="Filter by SKU ID"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    scenario: Optional[str] = Query(None, description="Filter by scenario (normal, stockout, expiry, transfer)"),
    location_id: Optional[str] = Query(None, description="Filter by Location ID"),
    expiry_bucket: Optional[str] = Query(
        None, description="Filter by expiry bucket: expired, <=30, 31-60, 61-90, >90"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
) -> InventoryListResponse:
    """
    Fetches inventory balances with joined Lot, SKU, and Location data.
    Calculates FEFO priority per SKU (rank 1 = earliest expiry date for that SKU).
    """
    query = (
        db.query(InventoryBalance, Lot, SKU, Location)
        .join(Lot, InventoryBalance.lot_id == Lot.lot_id)
        .join(SKU, Lot.sku_id == SKU.sku_id)
        .join(Location, InventoryBalance.location_id == Location.location_id)
    )

    if sku_id:
        query = query.filter(SKU.sku_id == sku_id)
    if category:
        query = query.filter(SKU.category == category)
    if scenario:
        query = query.filter(InventoryBalance.scenario == scenario)
    if location_id:
        query = query.filter(Location.location_id == location_id)

    raw_results = query.all()

    # Calculate days to expiry and filter by expiry_bucket if specified
    items: List[InventoryItem] = []
    
    # We need to calculate FEFO priority (rank of expiry_date per SKU)
    # Group lots by SKU to assign FEFO priority
    sku_lots: dict[str, list] = {}
    for inv, lot, sku, loc in raw_results:
        sku_lots.setdefault(sku.sku_id, []).append((lot.expiry_date, lot.lot_id))

    # Sort each SKU's lots by expiry_date asc, lot_id asc
    fefo_ranks: dict[str, int] = {}
    for s_id, lot_list in sku_lots.items():
        sorted_lots = sorted(lot_list, key=lambda x: (x[0], x[1]))
        for rank, (_, lot_id) in enumerate(sorted_lots, start=1):
            fefo_ranks[f"{s_id}:{lot_id}"] = rank

    for inv, lot, sku, loc in raw_results:
        days_left = _calculate_days_to_expiry(lot.expiry_date)

        # Expiry bucket filter check
        if expiry_bucket:
            if expiry_bucket == "expired" and days_left > 0:
                continue
            elif expiry_bucket == "<=30" and not (0 < days_left <= 30):
                continue
            elif expiry_bucket == "31-60" and not (30 < days_left <= 60):
                continue
            elif expiry_bucket == "61-90" and not (60 < days_left <= 90):
                continue
            elif expiry_bucket == ">90" and days_left <= 90:
                continue

        fefo = fefo_ranks.get(f"{sku.sku_id}:{lot.lot_id}", 1)

        items.append(
            InventoryItem(
                inventory_id=inv.inventory_id,
                lot_id=lot.lot_id,
                sku_id=sku.sku_id,
                sku_name=sku.sku_name,
                category=sku.category,
                pack_size=sku.pack_size,
                location_id=loc.location_id,
                location_name=loc.location_name,
                on_hand_qty=inv.on_hand_qty,
                available_qty=inv.available_qty,
                reserved_qty=inv.reserved_qty,
                quarantine_qty=inv.quarantine_qty,
                manufacturing_date=lot.manufacturing_date,
                expiry_date=lot.expiry_date,
                days_to_expiry=days_left,
                fefo_priority=fefo,
                scenario=inv.scenario,
                data_status=inv.data_status,
            )
        )

    # Sort items by FEFO (expiry_date asc) by default
    items.sort(key=lambda x: (x.expiry_date, x.lot_id))

    total = len(items)
    paginated_items = items[skip : skip + limit]

    return InventoryListResponse(
        items=paginated_items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{inventory_id}",
    response_model=InventoryDetail,
    summary="Get single inventory balance detail",
)
def get_inventory_detail(
    inventory_id: str,
    current_user: Annotated[User, Depends(require_role(READ_ALL_ROLES))],
    db: Annotated[Session, Depends(get_db)],
) -> InventoryDetail:
    """Returns detailed information for a single inventory record."""
    result = (
        db.query(InventoryBalance, Lot, SKU, Location)
        .join(Lot, InventoryBalance.lot_id == Lot.lot_id)
        .join(SKU, Lot.sku_id == SKU.sku_id)
        .join(Location, InventoryBalance.location_id == Location.location_id)
        .filter(InventoryBalance.inventory_id == inventory_id)
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory record '{inventory_id}' not found",
        )

    inv, lot, sku, loc = result
    days_left = _calculate_days_to_expiry(lot.expiry_date)

    # Compute FEFO priority for this lot among all lots for this SKU
    sku_lots = (
        db.query(Lot.lot_id, Lot.expiry_date)
        .filter(Lot.sku_id == sku.sku_id)
        .all()
    )
    sorted_lots = sorted(sku_lots, key=lambda x: (x.expiry_date, x.lot_id))
    fefo = 1
    for rank, (l_id, _) in enumerate(sorted_lots, start=1):
        if l_id == lot.lot_id:
            fefo = rank
            break

    return InventoryDetail(
        inventory_id=inv.inventory_id,
        lot_id=lot.lot_id,
        sku_id=sku.sku_id,
        sku_name=sku.sku_name,
        category=sku.category,
        pack_size=sku.pack_size,
        location_id=loc.location_id,
        location_name=loc.location_name,
        on_hand_qty=inv.on_hand_qty,
        available_qty=inv.available_qty,
        reserved_qty=inv.reserved_qty,
        quarantine_qty=inv.quarantine_qty,
        manufacturing_date=lot.manufacturing_date,
        expiry_date=lot.expiry_date,
        days_to_expiry=days_left,
        fefo_priority=fefo,
        scenario=inv.scenario,
        data_status=inv.data_status,
    )
