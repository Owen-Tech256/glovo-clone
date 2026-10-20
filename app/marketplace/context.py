"""Template context shared by every page: header cart count and delivery-area list.

Presentation helpers only. Both values are read-only, and any database problem falls back to
empty defaults so that error pages and the shell still render.
"""
from flask import current_app
from flask_login import current_user
from sqlalchemy import func, select

from app.extensions import db
from app.models.commerce import CartItem, ServiceZone

from . import bp


@bp.app_context_processor
def shell_context():
    cart_count = 0
    zones = []
    try:
        if current_user.is_authenticated:
            cart_count = db.session.scalar(
                select(func.coalesce(func.sum(CartItem.quantity), 0)).where(CartItem.user_id == current_user.id)
            ) or 0
        zones = db.session.scalars(
            select(ServiceZone).where(ServiceZone.is_active.is_(True)).order_by(ServiceZone.city, ServiceZone.name).limit(20)
        ).all()
    except Exception:  # noqa: BLE001 - the page shell must never fail because of a helper query
        db.session.rollback()
        current_app.logger.warning("shell context queries failed; rendering without cart count or areas")
    return {"cart_count": int(cart_count), "nav_zones": zones}
