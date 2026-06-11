from langchain.tools import tool
from langchain_core.tools import StructuredTool
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app import models
from app.db import SessionLocal
from app.ai.tools.page_context import request_page_context_tool, get_page_context_tool
from typing import Optional, List, Dict, Any
import json

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, will close after tool execution

@tool
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
        # Convert string prices to float if needed (LLM sometimes passes strings)
        if min_price is not None and isinstance(min_price, str):
            try:
                min_price = float(min_price)
            except (ValueError, TypeError):
                min_price = None
        
        if max_price is not None and isinstance(max_price, str):
            try:
                max_price = float(max_price)
            except (ValueError, TypeError):
                max_price = None
        
        query = db.query(models.Product).filter(models.Product.is_listed == True)
        
        # Apply filters
        if keyword:
            search_term = f"%{keyword.lower()}%"
            query = query.filter(
                or_(
                    func.lower(models.Product.name).like(search_term),
                    func.lower(models.Product.description).like(search_term)
                )
            )
        
        if color:
            color_term = f"%{color.lower()}%"
            query = query.filter(
                or_(
                    func.lower(models.Product.name).like(color_term),
                    func.lower(models.Product.description).like(color_term)
                )
            )
        
        if min_price is not None:
            query = query.filter(models.Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(models.Product.price <= max_price)
        
        products = query.limit(10).all()
        
        if not products:
            return "No products found matching your criteria. Try different search terms or price range."
        
        # Calculate ratings for each product
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
                "image_url":product.image_url,
                "stock": product.stock,
                "rating": f"{avg_rating}/5.0 ({review_count} reviews)" if review_count > 0 else "No reviews yet",
                "description": product.description[:100] + "..." if len(product.description) > 100 else product.description
            })
        
        return json.dumps(results, indent=2)
    
    finally:
        db.close()


@tool
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
            # Search by name
            product = db.query(models.Product).filter(
                func.lower(models.Product.name).like(f"%{product_name.lower()}%"),
                models.Product.is_listed == True
            ).first()
        
        if not product:
            return f"Product not found. Please check the product name or ID."
        
        # Get rating stats
        stats = db.query(
            func.avg(models.Review.rating).label('avg_rating'),
            func.count(models.Review.id).label('review_count')
        ).filter(models.Review.product_id == product.id).first()
        
        avg_rating = round(float(stats.avg_rating), 1) if stats.avg_rating else 0
        review_count = stats.review_count or 0
        
        # Get recent reviews
        reviews = db.query(models.Review).filter(
            models.Review.product_id == product.id
        ).order_by(models.Review.created_at.desc()).limit(3).all()
        
        review_samples = []
        for review in reviews:
            review_samples.append({
                "rating": review.rating,
                "comment": review.comment[:100] if review.comment else "No comment"
            })
        
        result = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "image_url":product.image_url,
            "price": f"${product.price:.2f}",
            "stock": product.stock,
            "availability": "In Stock" if product.stock > 0 else "Out of Stock",
            "average_rating": f"{avg_rating}/5.0",
            "total_reviews": review_count,
            "recent_reviews": review_samples if review_samples else "No reviews yet"
        }
        
        return json.dumps(result, indent=2)
    
    finally:
        db.close()


@tool
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
        message = f"**{product.name}**\n"
        message += f"Stock Status: {status}\n"
        message += f"Available Quantity: {product.stock}\n"
        
        if product.stock > 0 and product.stock < 5:
            message += "⚠️ Low stock! Only a few items left."
        elif product.stock == 0:
            message += "❌ Currently out of stock. Check back soon!"
        else:
            message += "✅ Good availability."
        
        return message
    
    finally:
        db.close()


@tool
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
            return "Your cart is empty. Browse our collection and add items to your cart!"
        
        items = []
        total = 0.0
        
        for item in cart.items:
            if item.product and item.product.is_listed:
                item_total = item.product.price * item.quantity
                total += item_total
                items.append({
                    "id": item.product.id,
                    "product": item.product.name,
                    "image_url":item.product.image_url,
                    "quantity": item.quantity,
                    "price_per_item": f"${item.product.price:.2f}",
                    "subtotal": f"${item_total:.2f}"
                })
        
        result = {
            "items": items,
            "total_items": len(items),
            "total_amount": f"${total:.2f}",
            "message": f"You have {len(items)} item(s) in your cart."
        }
        
        return json.dumps(result, indent=2)
    
    finally:
        db.close()


@tool
def order_status_tool(order_id: int) -> str:
    """
    Check the status of an order.
    
    Args:
        order_id: The order ID to check
    """
    db = SessionLocal()
    try:
        order = db.query(models.Order).filter(
            models.Order.id == order_id
        ).first()
        
        if not order:
            return f"Order #{order_id} not found. Please check the order ID."
        
        # Format order details
        items_summary = []
        for item in order.items:
            items_summary.append(f"{item.quantity}x {item.product.name}")
        
        result = {
            "order_id": order.id,
            "status": order.status,
            "total_amount": f"${order.total_amount:.2f}",
            "items": items_summary,
            "order_date": order.created_at.strftime("%Y-%m-%d %H:%M"),
            "shipping_address": {
                "name": order.address.name,
                "address": order.address.address,
                "city": order.address.city,
                "state": order.address.state,
                "pincode": order.address.pincode
            }
        }
        
        # Add delivery estimate
        if order.status == "Pending":
            result["message"] = "Your order is being processed. Estimated delivery: 5-7 business days."
        elif order.status == "Confirmed":
            result["message"] = "Your order has been confirmed and will be shipped soon. Estimated delivery: 3-5 business days."
        else:
            result["message"] = f"Order status: {order.status}"
        
        return json.dumps(result, indent=2)
    
    finally:
        db.close()


# FAQ Vector Store Tool (will be implemented with ChromaDB)
@tool
def faq_tool(question: str) -> str:
    """
    Answer questions about store policies, shipping, returns, refunds, and general FAQs.
    
    Args:
        question: The user's question about policies or general information
    """
    # This is a simplified version. In production, use vector store
    faq_database = {
        "shipping": "We offer free shipping on all orders. Delivery typically takes 5-7 business days. Express shipping is available for an additional fee with 2-3 day delivery.",
        "return": "We accept returns within 30 days of delivery. Items must be unused with original tags attached. Refund will be processed within 7-10 business days after we receive the returned item.",
        "refund": "Refunds are processed within 7-10 business days after we receive your return. The amount will be credited to your original payment method.",
        "payment": "We accept all major credit cards, debit cards, and UPI payments. Your payment information is secure and encrypted.",
        "sizing": "Please refer to our size guide on each product page. We provide detailed measurements for all our dresses. If you're between sizes, we recommend sizing up.",
        "exchange": "We offer exchanges within 30 days. Contact our support team with your order number to initiate an exchange.",
        "cancellation": "Orders can be cancelled within 24 hours of placing them. After that, the order will be processed and you'll need to return the item instead.",
        "contact": "You can reach us at support@dressstore.com or call us at 1-800-DRESS-SHOP (1-800-373-7774). Our customer service hours are 9 AM - 6 PM EST, Monday to Friday."
    }
    
    question_lower = question.lower()
    
    # Simple keyword matching (in production, use vector similarity)
    for key, answer in faq_database.items():
        if key in question_lower:
            return answer
    
    # Default response
    return """Here's some general information:
    
📦 **Shipping**: Free shipping, 5-7 business days
🔄 **Returns**: 30-day return policy
💰 **Refunds**: Processed within 7-10 business days
💳 **Payment**: All major cards and UPI accepted
📏 **Sizing**: Refer to size guide on product pages
📞 **Contact**: support@dressstore.com | 1-800-DRESS-SHOP

Please ask a specific question about shipping, returns, payments, sizing, or contact information for more details!"""

@tool
def agent_flow_rules(flow: str) -> str:
    """
    Provide specific UI action guidance based on the flow type.
    Args:        flow: The type of user flow (e.g., "navigate", "add_to_cart", "user_login")
    """
    guide = {
        "navigate":"""**Navigation Detection Rules:**
When user says:
- "Open product X" / "Show me product X" → {{"type": "navigate", "target": "url", "data":"/product/{{id}}"}}
- "Go to cart" / "Open cart" → {{"type": "navigate", "target":"url", "data":"/cart"}}
- "Checkout" / "Proceed to checkout" → {{"type": "navigate", "target": "url", "data":"/checkout"}}
- "My orders" / "Track order" → {{"type": "navigate", "target": "url", "data":"/orders"}}
- "Go home" / "Show all dresses" → {{"type": "navigate", "target": "url", "data":"/"}}
- "In home page, Show product by name or id" -> {{"type": "focus", "target": "element_selector", "data": "#product-{{id}}" or ".product-name:contains('{{name}}')"}}
- Otherwise → {{"type": "none", "target": null}}""",

        "add_to_cart":"""Add to Cart Flow:
        step 1: Navigate to product page.
        step 2: Ask no of quantity and other options if needed based on page context.
        step 3: Return action with confirmation for adding to cart:
        Note: Increase/ Decrease quantity as sparate actions.
        action:[
            {{"type":"click", "target":{{element_selector}}, "data":"1", "require_confirmation": false}},
            {{"type":"click", "target":{{element_selector}}, "data":"2", "require_confirmation": false}},
            {{"type":"click", "target":{{element_selector}}, "data": "Add to cart", "require_confirmation": True}},
        ]
        """,
        "user_login":"""**LOGIN FLOW:
            Step 1: Ask "Please tell me your email address"
            Step 2: After email → Ask "Now tell me your password"
            ...
            Step n: After get all fields → Return actions with confirmation
            action:[
                {{"type":"enter", "target":{{element_selector}}, "data":{{user email}}, "require_confirmation": false}},
                {{"type":"enter", "target":{{element_selector}}, "data":{{user password}}, "require_confirmation": false}},
                ... other fields ...
                {{"type":"click", "target":{{element_selector}}, "data": null, "require_confirmation": true}}
            ]""",
        "user_register":"""**Register FLOW:
            Step 1: Ask "Please tell me your email address"
            Step 2: After email → Ask "Now tell username you want to use"
            ...
            Step n: After get all fields → Return actions with confirmation

            Note: Each step should be based of page context, if page ask for phone number after email then ask for phone number in next step. Do not ask for all fields at once.
            action:[
                {{"type":"enter", "target":{{element_selector}}, "data":{{user email}}, "require_confirmation": false}},
                {{"type":"enter", "target":{{element_selector}}, "data":{{user username}}, "require_confirmation": false}},
                ... other fields ...
                {{"type":"click", "target":{{element_selector}}, "data": null, "require_confirmation": true}}
            ]"""
    }

    return guide.get(flow, """
**General UI Action Guide:**
- For navigation, use {{"type": "navigate", "target": "url", "data": "/path"}}.
- For adding to cart, use {{"type": "add_to_cart", "target": "button", "data": "Add to Cart", "require_confirmation": true}}.
- For clicking an element, use {{"type": "click", "target": "element_selector", "data": null, "require_confirmation": false}}.
- For focusing on an element, use {{"type": "focus", "target": "element_selector", "data": null, "require_confirmation": false}}.
- For entering text, use {{"type": "Enter_text", "target": "form_field_selector", "data": "text to enter", "require_confirmation": false}}.
- Always require confirmation for sensitive actions like adding to cart or submitting forms.)
- Never auto-submit forms or perform actions without user confirmation.
- For voice mode, keep actions simple and ask for confirmation before performing any action.
""")

# Create tool list for the agent
def get_tools():
    """Return all available tools"""
    return [
        search_products_tool,
        get_product_details_tool,
        check_stock_tool,
        cart_summary_tool,
        order_status_tool,
        faq_tool,
        agent_flow_rules,
        request_page_context_tool,  # NEW: Request page context
        get_page_context_tool 
    ]