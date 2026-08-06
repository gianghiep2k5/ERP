"""Expiry risk calculation service for V-IMS AI.

Calculates explainable expiry-risk metrics for inventory lots using:
- DEMO_ANALYSIS_DATE (2026-08-05)
- 30-day historical sales demand (sales_history)
- 30-day AI forecast results (forecast_results)
- Deterministic risk band rules
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.constants import DEMO_ANALYSIS_DATE
from app.models.inventory_balance import InventoryBalance
from app.models.location import Location
from app.models.lot import Lot
from app.models.public_product import PublicProduct
from app.models.recommendation import Recommendation
from app.models.sku import SKU


@dataclass
class ExpiryRiskAssessment:
    inventory_id: str
    lot_id: str
    sku_id: str
    sku_name: str
    category: str
    location_id: str
    location_name: str
    available_qty: int
    on_hand_qty: int
    manufacturing_date: str
    expiry_date: str
    analysis_date: str
    days_to_expiry: int
    recent_30d_sales_qty: int
    recent_average_daily_demand: float
    forecast_consumption_before_expiry: float
    forecast_method: str
    projected_surplus: float
    projected_shortage: float
    surplus_ratio: float
    urgency_factor: float
    risk_score: float
    risk_band: str
    explanation: str
    proposed_actions: List[str] = field(default_factory=list)
    fefo_position: int = 1
    related_recommendation_ids: List[str] = field(default_factory=list)
    pack_size: Optional[str] = None
    public_product_id: Optional[str] = None
    product_name: Optional[str] = None
    source_url: Optional[str] = None


def calculate_days_to_expiry(expiry_date_str: str) -> int:
    exp_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
    return (exp_date - DEMO_ANALYSIS_DATE).days


def determine_risk_band(
    days_to_expiry: int,
    projected_surplus: float,
    surplus_ratio: float,
) -> str:
    """
    Applies deterministic risk band rules in exact priority order:
    1. Expired: days_to_expiry <= 0
    2. Critical: not expired AND (days_to_expiry <= 14 and projected_surplus > 0 OR surplus_ratio >= 0.50)
    3. High: not Expired/Critical AND (days_to_expiry <= 30 and projected_surplus > 0 OR surplus_ratio >= 0.30)
    4. Medium: not Expired/Critical/High AND (days_to_expiry <= 60 and projected_surplus > 0 OR surplus_ratio >= 0.10)
    5. Low: all remaining cases
    """
    if days_to_expiry <= 0:
        return "Expired"
    if (days_to_expiry <= 14 and projected_surplus > 0) or surplus_ratio >= 0.50:
        return "Critical"
    if (days_to_expiry <= 30 and projected_surplus > 0) or surplus_ratio >= 0.30:
        return "High"
    if (days_to_expiry <= 60 and projected_surplus > 0) or surplus_ratio >= 0.10:
        return "Medium"
    return "Low"


def get_proposed_actions(risk_band: str) -> List[str]:
    """Returns deterministic proposed actions for decision support."""
    if risk_band == "Expired":
        return [
            "Quarantine the lot immediately",
            "Escalate to Quality Manager",
            "Block normal FEFO dispatch pending quality decision",
        ]
    elif risk_band == "Critical":
        return [
            "Prioritise immediate FEFO dispatch",
            "Review transfer opportunity",
            "Escalate to Quality Manager",
            "Monitor daily",
        ]
    elif risk_band == "High":
        return [
            "Prioritise FEFO",
            "Review transfer opportunity",
            "Monitor at least twice weekly",
        ]
    elif risk_band == "Medium":
        return [
            "Increase monitoring frequency",
            "Review demand and promotion assumptions",
            "Maintain FEFO priority",
        ]
    else:  # Low
        return [
            "Continue normal monitoring",
            "Maintain FEFO processing",
        ]


def generate_explanation(
    risk_band: str,
    days_to_expiry: int,
    available_qty: int,
    projected_surplus: float,
    surplus_ratio: float,
    expiry_date: str,
) -> str:
    if risk_band == "Expired":
        days_past = abs(days_to_expiry)
        return (
            f"This lot expired on {expiry_date} ({days_past} days ago) with "
            f"{available_qty} units of available stock remaining."
        )
    percent = round(surplus_ratio * 100, 1)
    surplus_int = int(round(projected_surplus))
    return (
        f"This lot is classified as {risk_band} Risk because {percent}% of available stock "
        f"({surplus_int} units) is projected to remain unconsumed before expiry, "
        f"with {days_to_expiry} days remaining."
    )


def compute_lot_expiry_risk(
    lot_id: str,
    sku_id: str,
    sku_name: str,
    category: str,
    expiry_date_str: str,
    manufacturing_date_str: str,
    available_qty: int,
    on_hand_qty: int,
    inventory_id: str,
    location_id: str,
    location_name: str,
    recent_30d_sales_qty: int,
    sku_forecasts: List[tuple],  # list of (forecast_date_str, forecast_qty)
    related_recommendation_ids: Optional[List[str]] = None,
    fefo_position: int = 1,
    pack_size: Optional[str] = None,
    public_product_id: Optional[str] = None,
    product_name: Optional[str] = None,
    source_url: Optional[str] = None,
) -> ExpiryRiskAssessment:
    days_to_expiry = calculate_days_to_expiry(expiry_date_str)
    recent_avg_demand = round(recent_30d_sales_qty / 30.0, 2)

    # Calculate forecast consumption before expiry & determine method used
    if days_to_expiry <= 0:
        forecast_consumption = 0.0
        forecast_method = "Expired lot"
    elif not sku_forecasts:
        forecast_consumption = round(recent_avg_demand * max(days_to_expiry, 0), 2)
        forecast_method = "Recent daily demand fallback"
    elif 1 <= days_to_expiry <= 30:
        sum_fc = sum(qty for f_date, qty in sku_forecasts if f_date <= expiry_date_str)
        forecast_consumption = float(sum_fc)
        forecast_method = "30-day forecast"
    else:  # days_to_expiry > 30
        sum_30d = sum(qty for _, qty in sku_forecasts)
        extra_days = days_to_expiry - 30
        forecast_consumption = round(sum_30d + (recent_avg_demand * extra_days), 2)
        forecast_method = "30-day forecast + demand extrapolation"

    projected_surplus = max(round(available_qty - forecast_consumption, 2), 0.0)
    projected_shortage = max(round(forecast_consumption - available_qty, 2), 0.0)

    denom = max(available_qty, 1)
    surplus_ratio = round(projected_surplus / float(denom), 4)

    urgency_factor = round(max(0.0, min(1.0, (60.0 - days_to_expiry) / 60.0)), 4)

    if days_to_expiry <= 0:
        risk_score = 100.0
    else:
        raw_score = 100.0 * (0.65 * surplus_ratio + 0.35 * urgency_factor)
        risk_score = round(raw_score, 1)

    risk_band = determine_risk_band(days_to_expiry, projected_surplus, surplus_ratio)
    explanation = generate_explanation(
        risk_band, days_to_expiry, available_qty, projected_surplus, surplus_ratio, expiry_date_str
    )
    actions = get_proposed_actions(risk_band)

    return ExpiryRiskAssessment(
        inventory_id=inventory_id,
        lot_id=lot_id,
        sku_id=sku_id,
        sku_name=sku_name,
        category=category,
        location_id=location_id,
        location_name=location_name,
        available_qty=available_qty,
        on_hand_qty=on_hand_qty,
        manufacturing_date=manufacturing_date_str,
        expiry_date=expiry_date_str,
        analysis_date=DEMO_ANALYSIS_DATE.isoformat(),
        days_to_expiry=days_to_expiry,
        recent_30d_sales_qty=recent_30d_sales_qty,
        recent_average_daily_demand=recent_avg_demand,
        forecast_consumption_before_expiry=forecast_consumption,
        forecast_method=forecast_method,
        projected_surplus=projected_surplus,
        projected_shortage=projected_shortage,
        surplus_ratio=surplus_ratio,
        urgency_factor=urgency_factor,
        risk_score=risk_score,
        risk_band=risk_band,
        explanation=explanation,
        proposed_actions=actions,
        fefo_position=fefo_position,
        related_recommendation_ids=related_recommendation_ids or [],
        pack_size=pack_size,
        public_product_id=public_product_id,
        product_name=product_name,
        source_url=source_url,
    )


def fetch_all_expiry_assessments(db: Session) -> List[ExpiryRiskAssessment]:
    """Fetches all 120 inventory lots and computes expiry risk assessments."""
    # 1. Fetch raw lots with joins
    results = (
        db.query(
            Lot,
            SKU,
            InventoryBalance,
            Location,
            PublicProduct,
        )
        .join(SKU, Lot.sku_id == SKU.sku_id)
        .join(InventoryBalance, Lot.lot_id == InventoryBalance.lot_id)
        .join(Location, InventoryBalance.location_id == Location.location_id)
        .join(PublicProduct, SKU.public_product_id == PublicProduct.public_product_id)
        .all()
    )

    # 2. Fetch 30-day sales per SKU ending on 2026-08-05
    # Date range for 30d window: 2026-07-07 to 2026-08-05
    start_30d = (DEMO_ANALYSIS_DATE - timedelta(days=29)).isoformat()
    end_30d = DEMO_ANALYSIS_DATE.isoformat()

    from app.models.sales_history import SalesHistory
    from app.models.forecast_result import ForecastResult

    sales_rows = (
        db.query(SalesHistory.sku_id, func.sum(SalesHistory.quantity_sold))
        .filter(SalesHistory.sales_date >= start_30d)
        .filter(SalesHistory.sales_date <= end_30d)
        .group_by(SalesHistory.sku_id)
        .all()
    )
    sales_30d_map: Dict[str, int] = {sku_id: qty or 0 for sku_id, qty in sales_rows}

    # 3. Fetch forecast results after 2026-08-05
    forecast_rows = (
        db.query(ForecastResult.sku_id, ForecastResult.forecast_date, ForecastResult.forecast_qty)
        .filter(ForecastResult.forecast_date > end_30d)
        .all()
    )
    forecast_map: Dict[str, List[tuple]] = {}
    for s_id, f_date, qty in forecast_rows:
        forecast_map.setdefault(s_id, []).append((f_date, qty))

    # 4. Fetch linked recommendations map per lot
    rec_rows = db.query(Recommendation.lot_id, Recommendation.recommendation_id).filter(Recommendation.lot_id.isnot(None)).all()
    recs_map: Dict[str, List[str]] = {}
    for lot_id, rec_id in rec_rows:
        recs_map.setdefault(lot_id, []).append(rec_id)

    # 5. Compute FEFO rank per SKU
    sku_lots_map: Dict[str, list] = {}
    for lot, sku, inv, loc, pub in results:
        sku_lots_map.setdefault(sku.sku_id, []).append((lot.expiry_date, lot.lot_id))

    fefo_ranks: Dict[str, int] = {}
    for s_id, lot_list in sku_lots_map.items():
        sorted_lots = sorted(lot_list, key=lambda x: (x[0], x[1]))
        for rank, (_, l_id) in enumerate(sorted_lots, start=1):
            fefo_ranks[l_id] = rank

    # 6. Assess all lots
    assessments: List[ExpiryRiskAssessment] = []
    for lot, sku, inv, loc, pub in results:
        assessment = compute_lot_expiry_risk(
            lot_id=lot.lot_id,
            sku_id=sku.sku_id,
            sku_name=sku.sku_name,
            category=sku.category,
            expiry_date_str=lot.expiry_date,
            manufacturing_date_str=lot.manufacturing_date,
            available_qty=inv.available_qty,
            on_hand_qty=inv.on_hand_qty,
            inventory_id=inv.inventory_id,
            location_id=loc.location_id,
            location_name=loc.location_name,
            recent_30d_sales_qty=sales_30d_map.get(sku.sku_id, 0),
            sku_forecasts=forecast_map.get(sku.sku_id, []),
            related_recommendation_ids=recs_map.get(lot.lot_id, []),
            fefo_position=fefo_ranks.get(lot.lot_id, 1),
            pack_size=sku.pack_size,
            public_product_id=pub.public_product_id,
            product_name=pub.product_name,
            source_url=pub.source_url,
        )
        assessments.append(assessment)

    return assessments
