"""Lots router: GET /api/lots and GET /api/lots/{lot_id}."""
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
from app.models.public_product import PublicProduct
from app.models.recommendation import Recommendation
from app.models.sku import SKU
from app.models.user import User
from app.schemas.lot import (
    LinkedRecommendation,
    LotDetail,
    LotListItem,
    LotListResponse,
)

router = APIRouter(prefix="/api/lots", tags=["lots"])


def _calculate_days_to_expiry(expiry_date_str: str) -> int:
    exp_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
    return (exp_date - DEMO_ANALYSIS_DATE).days


@router.get(
    "",
    response_model=LotListResponse,
    summary="List lots with FEFO position, search/filters, and pagination",
)
def list_lots(
    current_user: Annotated[User, Depends(require_role(READ_ALL_ROLES))],
    db: Annotated[Session, Depends(get_db)],
    sku_id: Optional[str] = Query(None, description="Filter by SKU ID"),
    category: Optional[str] = Query(None, description="Filter by Category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
) -> LotListResponse:
    """Returns all lots with calculated FEFO rank and inventory balance."""
    query = (
        db.query(Lot, SKU, InventoryBalance, Location)
        .join(SKU, Lot.sku_id == SKU.sku_id)
        .join(InventoryBalance, Lot.lot_id == InventoryBalance.lot_id)
        .join(Location, InventoryBalance.location_id == Location.location_id)
    )

    if sku_id:
        query = query.filter(SKU.sku_id == sku_id)
    if category:
        query = query.filter(SKU.category == category)

    raw_results = query.all()

    # Pre-calculate FEFO ranking per SKU
    sku_lots_map: dict[str, list] = {}
    for lot, sku, inv, loc in raw_results:
        sku_lots_map.setdefault(sku.sku_id, []).append((lot.expiry_date, lot.lot_id))

    fefo_map: dict[str, tuple[int, int]] = {}
    for s_id, lot_list in sku_lots_map.items():
        sorted_lots = sorted(lot_list, key=lambda x: (x[0], x[1]))
        total_for_sku = len(sorted_lots)
        for rank, (_, l_id) in enumerate(sorted_lots, start=1):
            fefo_map[l_id] = (rank, total_for_sku)

    items: List[LotListItem] = []
    for lot, sku, inv, loc in raw_results:
        days_left = _calculate_days_to_expiry(lot.expiry_date)
        rank, total_sku_lots = fefo_map.get(lot.lot_id, (1, 1))

        items.append(
            LotListItem(
                lot_id=lot.lot_id,
                sku_id=sku.sku_id,
                sku_name=sku.sku_name,
                category=sku.category,
                manufacturing_date=lot.manufacturing_date,
                expiry_date=lot.expiry_date,
                days_to_expiry=days_left,
                fefo_position=rank,
                fefo_total=total_sku_lots,
                on_hand_qty=inv.on_hand_qty,
                scenario=inv.scenario,
                location_name=loc.location_name,
            )
        )

    # Sort FEFO order by default (expiry_date asc)
    items.sort(key=lambda x: (x.expiry_date, x.lot_id))

    total = len(items)
    paginated_items = items[skip : skip + limit]

    return LotListResponse(
        items=paginated_items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{lot_id}",
    response_model=LotDetail,
    summary="Get full lot detail including Public Product reference and linked recommendations",
)
def get_lot_detail(
    lot_id: str,
    current_user: Annotated[User, Depends(require_role(READ_ALL_ROLES))],
    db: Annotated[Session, Depends(get_db)],
) -> LotDetail:
    """Returns complete lot details with SKU, Public Product, Inventory Balance, and linked recommendations."""
    result = (
        db.query(Lot, SKU, PublicProduct, InventoryBalance, Location)
        .join(SKU, Lot.sku_id == SKU.sku_id)
        .join(PublicProduct, SKU.public_product_id == PublicProduct.public_product_id)
        .join(InventoryBalance, Lot.lot_id == InventoryBalance.lot_id)
        .join(Location, InventoryBalance.location_id == Location.location_id)
        .filter(Lot.lot_id == lot_id)
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lot '{lot_id}' not found",
        )

    lot, sku, pub_prod, inv, loc = result
    days_left = _calculate_days_to_expiry(lot.expiry_date)

    # Compute FEFO position among all lots for this SKU
    sku_lots = (
        db.query(Lot.lot_id, Lot.expiry_date)
        .filter(Lot.sku_id == sku.sku_id)
        .all()
    )
    sorted_lots = sorted(sku_lots, key=lambda x: (x.expiry_date, x.lot_id))
    fefo_pos = 1
    for rank, (l_id, _) in enumerate(sorted_lots, start=1):
        if l_id == lot.lot_id:
            fefo_pos = rank
            break

    # Linked recommendations for this lot
    recs = (
        db.query(Recommendation)
        .filter(Recommendation.lot_id == lot.lot_id)
        .order_by(Recommendation.created_at.desc())
        .all()
    )

    linked_recs: List[LinkedRecommendation] = []
    for r in recs:
        effective_qty = r.adjusted_qty if r.adjusted_qty is not None else r.proposed_qty
        linked_recs.append(
            LinkedRecommendation(
                recommendation_id=r.recommendation_id,
                recommendation_type=r.recommendation_type,
                proposed_qty=r.proposed_qty,
                adjusted_qty=r.adjusted_qty,
                effective_qty=effective_qty,
                status=r.status,
                reason=r.reason,
                created_at=r.created_at,
            )
        )

    return LotDetail(
        lot_id=lot.lot_id,
        manufacturing_date=lot.manufacturing_date,
        expiry_date=lot.expiry_date,
        days_to_expiry=days_left,
        fefo_position=fefo_pos,
        fefo_total=len(sorted_lots),
        lot_data_status=lot.data_status,
        sku_id=sku.sku_id,
        sku_name=sku.sku_name,
        category=sku.category,
        pack_size=sku.pack_size,
        default_shelf_life_days=sku.default_shelf_life_days,
        unit_cost_vnd=sku.unit_cost_vnd,
        variant_status=sku.variant_status,
        source_status=sku.source_status,
        public_product_id=pub_prod.public_product_id,
        product_name=pub_prod.product_name,
        public_pack_size=pub_prod.public_pack_size,
        source_url=pub_prod.source_url,
        inventory_id=inv.inventory_id,
        location_id=loc.location_id,
        location_name=loc.location_name,
        location_type=loc.location_type,
        on_hand_qty=inv.on_hand_qty,
        available_qty=inv.available_qty,
        reserved_qty=inv.reserved_qty,
        quarantine_qty=inv.quarantine_qty,
        last_updated=inv.last_updated,
        scenario=inv.scenario,
        recommendations=linked_recs,
        analysis_date=DEMO_ANALYSIS_DATE.isoformat(),
    )
