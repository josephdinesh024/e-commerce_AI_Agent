from typing import Optional, Dict, Any
from app.db import SessionLocal
from app import models
import json


def enrich_context_from_route(session_id: str, route: Optional[str]) -> Dict[str, Any]:
    """
    Given a route and session_id, fetch the relevant entity data from the DB.
    Returns a dict that gets injected into the agent's system context.

    This replaces request_page_context_tool and get_page_context_tool entirely.
    The agent no longer needs to request context — it's always provided.

    Examples:
        /product/12        → fetch product 12 details
        /cart              → fetch cart summary for session
        /orders            → fetch recent orders for session
        /orders/5          → fetch order 5 for session
        /checkout          → fetch cart + saved addresses
        /                  → no entity data needed
    """
    if not route:
        return {}

    db = SessionLocal()
    try:
        context: Dict[str, Any] = {}

        # Product detail page
        if route.startswith("/product/"):
            parts = route.rstrip("/").split("/")
            if len(parts) >= 3 and parts[2].isdigit():
                product_id = int(parts[2])
                product = db.query(models.Product).filter(
                    models.Product.id == product_id,
                    models.Product.is_listed == True
                ).first()
                if product:
                    context["product"] = {
                        "id": product.id,
                        "name": product.name,
                        "price": product.price,
                        "stock": product.stock,
                        "availability": "In Stock" if product.stock > 0 else "Out of Stock"
                    }

        # Cart page
        elif route == "/cart":
            cart = db.query(models.Cart).filter(
                models.Cart.session_id == session_id
            ).first()
            if cart and cart.items:
                context["cart"] = {
                    "item_count": len(cart.items),
                    "items": [
                        {"product_id": i.product_id, "name": i.product.name, "quantity": i.quantity}
                        for i in cart.items if i.product
                    ]
                }
            else:
                context["cart"] = {"item_count": 0, "items": []}

        # Checkout page
        elif route == "/checkout":
            cart = db.query(models.Cart).filter(
                models.Cart.session_id == session_id
            ).first()
            total = 0.0
            items = []
            if cart and cart.items:
                for item in cart.items:
                    if item.product:
                        item_total = item.product.price * item.quantity
                        total += item_total
                        items.append({
                            "product_id": item.product_id,
                            "name": item.product.name,
                            "quantity": item.quantity,
                            "subtotal": round(item_total, 2)
                        })
            addresses = db.query(models.Address).filter(
                models.Address.session_id == session_id
            ).order_by(models.Address.created_at.desc()).limit(3).all()
            context["checkout"] = {
                "cart_items": items,
                "cart_total": round(total, 2),
                "saved_addresses": [
                    {"id": a.id, "name": a.name, "city": a.city, "state": a.state, "pincode": a.pincode}
                    for a in addresses
                ]
            }

        # Order list page
        elif route == "/orders":
            orders = db.query(models.Order).filter(
                models.Order.session_id == session_id
            ).order_by(models.Order.created_at.desc()).limit(5).all()
            context["orders"] = [
                {
                    "order_id": o.id,
                    "status": o.status,
                    "total": o.total_amount,
                    "date": o.created_at.strftime("%Y-%m-%d")
                }
                for o in orders
            ]

        # Specific order page  /orders/5
        elif route.startswith("/orders/"):
            parts = route.rstrip("/").split("/")
            if len(parts) >= 3 and parts[2].isdigit():
                order_id = int(parts[2])
                order = db.query(models.Order).filter(
                    models.Order.id == order_id,
                    models.Order.session_id == session_id
                ).first()
                if order:
                    context["order"] = {
                        "order_id": order.id,
                        "status": order.status,
                        "total": order.total_amount,
                        "items": [
                            f"{i.quantity}x {i.product.name}" for i in order.items if i.product
                        ]
                    }

        return context

    finally:
        db.close()


def format_enriched_context(context: Dict[str, Any]) -> str:
    """
    Serialise enriched context into a compact string for the system block.
    Empty context returns empty string — no noise injected.
    """
    if not context:
        return ""
    return f"(SYSTEM) Page data: {json.dumps(context, separators=(',', ':'))}\n"