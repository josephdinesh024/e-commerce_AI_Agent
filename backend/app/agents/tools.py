from sqlalchemy import func, and_, or_
from app import models
from app.db import SessionLocal
from typing import Optional
import json
from app.services.user import UserService
from app import schemas


# ---------------------------------------------------------------------------
# READ TOOLS  (unchanged in logic, kept for completeness)
# ---------------------------------------------------------------------------

def search_products_tool(
    keyword: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    color: Optional[str] = None
) -> str:
    """
    Search for products based on keyword, price range, or color.
    Returns a list of matching products with their details.

    Args:
        keyword: Search term for product name or description
        min_price: Minimum price filter (numeric value)
        max_price: Maximum price filter (numeric value)
        color: Color filter (searches in name and description)
    """
    db = SessionLocal()
    try:
        if min_price and isinstance(min_price, str):
            try: min_price = float(min_price)
            except: min_price = None
        if max_price and isinstance(max_price, str):
            try: max_price = float(max_price)
            except: max_price = None

        query = db.query(models.Product).filter(models.Product.is_listed == True)

        if keyword:
            term = f"%{keyword.lower()}%"
            query = query.filter(or_(
                func.lower(models.Product.name).like(term),
                func.lower(models.Product.description).like(term)
            ))
        if color:
            term = f"%{color.lower()}%"
            query = query.filter(or_(
                func.lower(models.Product.name).like(term),
                func.lower(models.Product.description).like(term)
            ))
        if min_price is not None:
            query = query.filter(models.Product.price >= min_price)
        if max_price is not None:
            query = query.filter(models.Product.price <= max_price)

        products = query.limit(10).all()

        if not products:
            return "No products found matching your criteria."

        results = []
        for product in products:
            stats = db.query(
                func.avg(models.Review.rating).label('avg_rating'),
                func.count(models.Review.id).label('review_count')
            ).filter(models.Review.product_id == product.id).first()

            avg_rating = round(float(stats.avg_rating), 1) if stats.avg_rating else 0
            review_count = stats.review_count or 0

            results.append({
                "id": product.id,
                "name": product.name,
                "price": f"${product.price:.2f}",
                "image_url": product.image_url,
                "stock": product.stock,
                "rating": f"{avg_rating}/5.0 ({review_count} reviews)" if review_count > 0 else "No reviews yet",
                "description": product.description[:100] + "..." if len(product.description) > 100 else product.description
            })

        return json.dumps(results, indent=2)
    finally:
        db.close()


def get_product_details_tool(
    product_id: Optional[int] = None,
    product_name: Optional[str] = None
) -> str:
    """
    Get detailed information about a specific product.
    Provide either product_id or product_name.

    Args:
        product_id: The ID of the product
        product_name: The name of the product to search for
    """
    db = SessionLocal()
    try:
        if not product_id and not product_name:
            return "Please provide either product_id or product_name."

        if product_id:
            product = db.query(models.Product).filter(
                models.Product.id == product_id,
                models.Product.is_listed == True
            ).first()
        else:
            product = db.query(models.Product).filter(
                func.lower(models.Product.name).like(f"%{product_name.lower()}%"),
                models.Product.is_listed == True
            ).first()

        if not product:
            return "Product not found."

        stats = db.query(
            func.avg(models.Review.rating).label('avg_rating'),
            func.count(models.Review.id).label('review_count')
        ).filter(models.Review.product_id == product.id).first()

        avg_rating = round(float(stats.avg_rating), 1) if stats.avg_rating else 0
        review_count = stats.review_count or 0

        reviews = db.query(models.Review).filter(
            models.Review.product_id == product.id
        ).order_by(models.Review.created_at.desc()).limit(3).all()

        result = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "image_url": product.image_url,
            "price": f"${product.price:.2f}",
            "price_raw": product.price,
            "stock": product.stock,
            "availability": "In Stock" if product.stock > 0 else "Out of Stock",
            "average_rating": f"{avg_rating}/5.0",
            "total_reviews": review_count,
            "recent_reviews": [
                {"rating": r.rating, "comment": r.comment[:100] if r.comment else ""}
                for r in reviews
            ] if reviews else "No reviews yet"
        }

        return json.dumps(result, indent=2)
    finally:
        db.close()


def check_stock_tool(product_id: int) -> str:
    """
    Check the current stock availability for a product.

    Args:
        product_id: The ID of the product to check
    """
    db = SessionLocal()
    try:
        product = db.query(models.Product).filter(
            models.Product.id == product_id
        ).first()

        if not product:
            return f"Product with ID {product_id} not found."

        status = "Available" if product.stock > 0 else "Out of Stock"
        note = ""
        if product.stock == 0:
            note = "Currently out of stock. Check back soon!"
        elif product.stock < 5:
            note = f"Low stock! Only {product.stock} left."
        else:
            note = "Good availability."

        return json.dumps({
            "product_id": product.id,
            "name": product.name,
            "status": status,
            "stock": product.stock,
            "note": note
        })
    finally:
        db.close()


def cart_summary_tool(session_id: str) -> str:
    """
    Get the current cart summary for a user session.

    Args:
        session_id: The user's session ID
    """
    db = SessionLocal()
    try:
        cart = db.query(models.Cart).filter(
            models.Cart.session_id == session_id
        ).first()

        if not cart or not cart.items:
            return json.dumps({
                "items": [],
                "total_items": 0,
                "total_amount": "$0.00",
                "message": "Your cart is empty."
            })

        items = []
        total = 0.0
        for item in cart.items:
            if item.product and item.product.is_listed:
                item_total = item.product.price * item.quantity
                total += item_total
                items.append({
                    "id": item.product.id,
                    "product": item.product.name,
                    "image_url": item.product.image_url,
                    "quantity": item.quantity,
                    "price_per_item": f"${item.product.price:.2f}",
                    "subtotal": f"${item_total:.2f}"
                })

        return json.dumps({
            "items": items,
            "total_items": len(items),
            "total_amount": f"${total:.2f}",
            "message": f"You have {len(items)} item(s) in your cart totalling ${total:.2f}."
        }, indent=2)
    finally:
        db.close()


def order_status_tool(session_id: str, order_id: Optional[int] = None) -> str:
    """
    Check the status of an order. If order_id not provided, returns the most recent order.

    Args:
        session_id: The user's session ID (used to verify ownership)
        order_id: Optional specific order ID
    """
    db = SessionLocal()
    try:
        query = db.query(models.Order).filter(models.Order.session_id == session_id)
        if order_id:
            query = query.filter(models.Order.id == order_id)
        order = query.order_by(models.Order.created_at.desc()).first()

        if not order:
            return "No order found for this session."

        result = {
            "order_id": order.id,
            "status": order.status,
            "total_amount": f"${order.total_amount:.2f}",
            "items": [f"{item.quantity}x {item.product.name}" for item in order.items],
            "order_date": order.created_at.strftime("%Y-%m-%d %H:%M"),
            "shipping_address": {
                "name": order.address.name,
                "address": order.address.address,
                "city": order.address.city,
                "state": order.address.state,
                "pincode": order.address.pincode
            },
            "message": {
                "Pending": "Your order is being processed. Estimated delivery: 5-7 business days.",
                "Confirmed": "Your order is confirmed and will ship soon. Estimated delivery: 3-5 business days."
            }.get(order.status, f"Order status: {order.status}")
        }

        return json.dumps(result, indent=2)
    finally:
        db.close()


def list_orders_tool(session_id: str) -> str:
    """
    List all orders for the current session user.

    Args:
        session_id: The user's session ID
    """
    db = SessionLocal()
    try:
        orders = db.query(models.Order).filter(
            models.Order.session_id == session_id
        ).order_by(models.Order.created_at.desc()).all()

        if not orders:
            return json.dumps({"orders": [], "message": "No orders found."})

        result = []
        for order in orders:
            result.append({
                "order_id": order.id,
                "status": order.status,
                "total_amount": f"${order.total_amount:.2f}",
                "item_count": len(order.items),
                "order_date": order.created_at.strftime("%Y-%m-%d %H:%M")
            })

        return json.dumps({"orders": result, "total": len(result)}, indent=2)
    finally:
        db.close()


def faq_tool(question: str) -> str:
    """
    Answer questions about store policies, shipping, returns, refunds, and general FAQs.

    Args:
        question: The user's question about policies or general information
    """
    faq_database = {
        "shipping": "We offer free shipping on all orders. Delivery typically takes 5-7 business days. Express shipping is available for an additional fee with 2-3 day delivery.",
        "return": "We accept returns within 30 days of delivery. Items must be unused with original tags. Refund processed within 7-10 business days after receiving the item.",
        "refund": "Refunds are processed within 7-10 business days after we receive your return. Credited to your original payment method.",
        "payment": "We accept all major credit cards, debit cards, and UPI payments.",
        "sizing": "Refer to the size guide on each product page. We provide detailed measurements. If between sizes, we recommend sizing up.",
        "exchange": "We offer exchanges within 30 days. Contact support with your order number.",
        "cancellation": "Orders can be cancelled within 24 hours of placing. After that, you'll need to return the item.",
        "contact": "Reach us at support@dressstore.com or 1-800-DRESS-SHOP. Hours: 9AM–6PM EST, Mon–Fri."
    }

    question_lower = question.lower()
    for key, answer in faq_database.items():
        if key in question_lower:
            return answer

    return "Free shipping on all orders · 30-day returns · Refunds in 7-10 days · All major cards + UPI accepted. Ask about shipping, returns, payments, sizing, or contact for details."


# ---------------------------------------------------------------------------
# ACTION TOOLS — direct DB execution, no DOM required
# ---------------------------------------------------------------------------

def add_to_cart_tool(session_id: str, product_id: int, quantity: int = 1) -> str:
    """
    Add a product directly to the user's cart in the database.
    No page navigation or DOM interaction required.

    Args:
        session_id: The user's session ID
        product_id: The product to add
        quantity: How many to add (default 1)
    """
    db = SessionLocal()
    try:
        # Validate product
        product = db.query(models.Product).filter(
            models.Product.id == product_id,
            models.Product.is_listed == True
        ).first()

        if not product:
            return json.dumps({"success": False, "error": "Product not found."})

        if product.stock < quantity:
            return json.dumps({
                "success": False,
                "error": f"Only {product.stock} units available. Requested {quantity}."
            })

        # Get or create cart
        cart = db.query(models.Cart).filter(
            models.Cart.session_id == session_id
        ).first()

        if not cart:
            cart = models.Cart(session_id=session_id)
            db.add(cart)
            db.flush()

        # Check if item already in cart
        cart_item = db.query(models.CartItem).filter(
            models.CartItem.cart_id == cart.id,
            models.CartItem.product_id == product_id
        ).first()

        if cart_item:
            new_qty = cart_item.quantity + quantity
            if new_qty > product.stock:
                return json.dumps({
                    "success": False,
                    "error": f"Cannot add {quantity} more. You already have {cart_item.quantity} in cart and only {product.stock} are available."
                })
            cart_item.quantity = new_qty
        else:
            cart_item = models.CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity
            )
            db.add(cart_item)

        db.commit()

        return json.dumps({
            "success": True,
            "message": f"Added {quantity}x {product.name} to your cart.",
            "product": {"id": product.id, "name": product.name, "price": f"${product.price:.2f}"},
            "cart_action": "refresh"   # tells frontend to re-fetch cart count
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()


def update_cart_item_tool(session_id: str, product_id: int, quantity: int) -> str:
    """
    Update the quantity of an item in the cart. Set quantity to 0 to remove it.

    Args:
        session_id: The user's session ID
        product_id: The product to update
        quantity: New quantity (0 = remove from cart)
    """
    db = SessionLocal()
    try:
        cart = db.query(models.Cart).filter(
            models.Cart.session_id == session_id
        ).first()

        if not cart:
            return json.dumps({"success": False, "error": "Cart not found."})

        cart_item = db.query(models.CartItem).filter(
            models.CartItem.cart_id == cart.id,
            models.CartItem.product_id == product_id
        ).first()

        if not cart_item:
            return json.dumps({"success": False, "error": "Item not found in cart."})

        product = cart_item.product

        if quantity <= 0:
            db.delete(cart_item)
            db.commit()
            return json.dumps({
                "success": True,
                "message": f"Removed {product.name} from your cart.",
                "cart_action": "refresh"
            })

        if quantity > product.stock:
            return json.dumps({
                "success": False,
                "error": f"Only {product.stock} units available."
            })

        cart_item.quantity = quantity
        db.commit()

        return json.dumps({
            "success": True,
            "message": f"Updated {product.name} quantity to {quantity}.",
            "cart_action": "refresh"
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()


def remove_from_cart_tool(session_id: str, product_id: int) -> str:
    """
    Remove a specific product from the user's cart.

    Args:
        session_id: The user's session ID
        product_id: The product to remove
    """
    return update_cart_item_tool(session_id, product_id, 0)


def save_address_tool(
    session_id: str,
    name: str,
    phone: str,
    address: str,
    city: str,
    state: str,
    pincode: str
) -> str:
    """
    Save a shipping address for the session. Used during checkout flow.
    Collects address details conversationally and writes directly to DB.

    Args:
        session_id: The user's session ID
        name: Recipient full name
        phone: Contact phone number
        address: Street address
        city: City
        state: State
        pincode: PIN / ZIP code
    """
    db = SessionLocal()
    try:
        addr = models.Address(
            session_id=session_id,
            name=name,
            phone=phone,
            address=address,
            city=city,
            state=state,
            pincode=pincode
        )
        db.add(addr)
        db.commit()
        db.refresh(addr)

        return json.dumps({
            "success": True,
            "address_id": addr.id,
            "message": f"Address saved for {name}, {city}, {state} — {pincode}.",
            "summary": f"{name} · {phone} · {address}, {city}, {state} - {pincode}"
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()


def get_saved_addresses_tool(session_id: str) -> str:
    """
    Retrieve all saved addresses for the session.

    Args:
        session_id: The user's session ID
    """
    db = SessionLocal()
    try:
        addresses = db.query(models.Address).filter(
            models.Address.session_id == session_id
        ).order_by(models.Address.created_at.desc()).all()

        if not addresses:
            return json.dumps({"addresses": [], "message": "No saved addresses found."})

        result = []
        for addr in addresses:
            result.append({
                "id": addr.id,
                "name": addr.name,
                "phone": addr.phone,
                "address": addr.address,
                "city": addr.city,
                "state": addr.state,
                "pincode": addr.pincode
            })

        return json.dumps({"addresses": result}, indent=2)
    finally:
        db.close()


def place_order_tool(session_id: str, address_id: int) -> str:
    """
    Place an order using the current cart and a saved address.
    Validates stock, creates order, clears cart — all in one transaction.

    Args:
        session_id: The user's session ID
        address_id: The address ID to ship to (from save_address_tool)
    """
    db = SessionLocal()
    try:
        # Validate cart
        cart = db.query(models.Cart).filter(
            models.Cart.session_id == session_id
        ).first()

        if not cart or not cart.items:
            return json.dumps({"success": False, "error": "Your cart is empty."})

        # Validate address ownership
        address = db.query(models.Address).filter(
            models.Address.id == address_id,
            models.Address.session_id == session_id
        ).first()

        if not address:
            return json.dumps({"success": False, "error": "Address not found."})

        # Validate stock for all items
        total = 0.0
        order_items_data = []
        for item in cart.items:
            if not item.product or not item.product.is_listed:
                return json.dumps({"success": False, "error": f"Product {item.product_id} is no longer available."})
            if item.product.stock < item.quantity:
                return json.dumps({
                    "success": False,
                    "error": f"Only {item.product.stock} units of '{item.product.name}' available. Adjust your cart."
                })
            item_total = item.product.price * item.quantity
            total += item_total
            order_items_data.append({
                "product": item.product,
                "quantity": item.quantity,
                "price": item.product.price
            })

        # Create order
        order = models.Order(
            session_id=session_id,
            address_id=address_id,
            total_amount=total,
            status="Pending"
        )
        db.add(order)
        db.flush()

        # Create order items + deduct stock
        for data in order_items_data:
            order_item = models.OrderItem(
                order_id=order.id,
                product_id=data["product"].id,
                quantity=data["quantity"],
                price=data["price"]
            )
            db.add(order_item)
            data["product"].stock -= data["quantity"]

        # Clear the cart
        for item in cart.items:
            db.delete(item)

        db.commit()

        return json.dumps({
            "success": True,
            "order_id": order.id,
            "total_amount": f"${total:.2f}",
            "status": "Pending",
            "message": f"Order #{order.id} placed successfully! Total: ${total:.2f}. Estimated delivery: 5-7 business days.",
            "navigate_to": "/orders"   # hint to frontend to navigate after confirmation
        })
    except Exception as e:
        db.rollback()
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()


def submit_review_tool(
    session_id: str,
    product_id: int,
    rating: int,
    comment: Optional[str] = None
) -> str:
    """
    Submit a product review for a session user.
    Only allowed if session has ordered the product.

    Args:
        session_id: The user's session ID
        product_id: The product being reviewed
        rating: Rating from 1 to 5
        comment: Optional review comment
    """
    db = SessionLocal()
    try:
        if not 1 <= rating <= 5:
            return json.dumps({"success": False, "error": "Rating must be between 1 and 5."})

        # Check if user has ordered this product
        ordered = db.query(models.OrderItem).join(models.Order).filter(
            models.Order.session_id == session_id,
            models.OrderItem.product_id == product_id
        ).first()

        if not ordered:
            return json.dumps({
                "success": False,
                "error": "You can only review products you have ordered."
            })

        # Check for existing review
        existing = db.query(models.Review).filter(
            models.Review.product_id == product_id,
            models.Review.session_id == session_id
        ).first()

        if existing:
            existing.rating = rating
            existing.comment = comment
            db.commit()
            return json.dumps({"success": True, "message": "Your review has been updated."})

        review = models.Review(
            product_id=product_id,
            session_id=session_id,
            rating=rating,
            comment=comment
        )
        db.add(review)
        db.commit()

        return json.dumps({"success": True, "message": "Thank you for your review!"})
    except Exception as e:
        db.rollback()
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# USER TOOLS — direct DB execution, no DOM required
# ---------------------------------------------------------------------------   

def get_user_profile_tool(session_id: str) -> str:
    """
    Retrieve the user's profile information based on their session.

    Args:
        session_id: The user's session ID
    """
    db = SessionLocal()
    try:
        user = UserService(db).get_user_by_session(session_id)
        return json.dumps({
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "username": user.username,
                "phone": user.phone,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M")
            }
        }, indent=2)
    finally:
        db.close()   

def create_user_tool(email: str, full_name: str, username: str, password: str, phone: Optional[str] = None) -> str:
    """
    Create a new user account with the provided details.

    Args:
        email: User's email address
        full_name: User's full name
        username: Desired username
        password: Account password
        phone: Optional contact phone number
    """
    db = SessionLocal()
    try:
        user_service = UserService(db)
        user_create = schemas.UserCreate(
            email=email,
            full_name=full_name,
            username=username,
            password=password,
            phone=phone
        )
        user = user_service.create_user(user_create)
        return json.dumps({
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "username": user.username,
                "phone": user.phone,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M")
            }
        }, indent=2)
    except ValueError as e:
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()

def update_user_profile_tool(session_id: str, full_name: Optional[str] = None, phone: Optional[str] = None, password: Optional[str] = None) -> str:
    """
    Update the user's profile information based on their session.

    Args:
        session_id: The user's session ID
        full_name: New full name (optional)
        phone: New phone number (optional)
        password: New password (optional)
    """
    db = SessionLocal()
    try:
        user_service = UserService(db)
        user_update = schemas.UserUpdate(
            full_name=full_name,
            phone=phone,
            password=password
        )
        user = user_service.Update_user(session_id, user_update)
        return json.dumps({
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "username": user.username,
                "phone": user.phone,
                "updated_at": user.updated_at.strftime("%Y-%m-%d %H:%M")
            }
        }, indent=2)
    except ValueError as e:
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()

def login_user_tool(email: str, password: str) -> str:
    """
    Authenticate a user and create a session.

    Args:
        email: User's email address
        password: User's password
    """
    db = SessionLocal()
    try:
        user_service = UserService(db)
        user_login = schemas.UserLogin(email=email, password=password)
        session_info = user_service.create_user_session(user_login)
        return json.dumps({
            "success": True,
            "user": {
                "id": session_info.id,
                "email": session_info.email,
                "full_name": session_info.full_name,
                "username": session_info.username,
                "session_id": session_info.session_id
            }
        }, indent=2)
    except ValueError as e:
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()

def old_session_cart_transfer_tool(session_id: str, new_session_id: str) -> str:
    """
    Transfer temporary session data like cart contents from an old session to a new session after login."""
    db = SessionLocal()
    try:
        user_service = UserService(db)
        user_service.cart_item_transfer(session_id, new_session_id)
        return json.dumps({"success": True, "message": "Cart items transferred successfully."})
    except ValueError as e:
        return json.dumps({"success": False, "error": str(e)})
    finally:
        db.close()
