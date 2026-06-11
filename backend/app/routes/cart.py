from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas
from app.db import get_db
from app.services.cart import CartService

router = APIRouter(prefix="/cart", tags=["cart"])

@router.post("/items")
def add_to_cart(item: schemas.CartItemCreate, db: Session = Depends(get_db)):
    """Add item to cart"""
    cart_item = CartService.add_item_to_cart(db, item.session_id, item.product_id, item.quantity)
    return {"message": "Item added to cart", "item_id": cart_item.id}

@router.get("/{session_id}", response_model=schemas.CartResponse)
def get_cart(session_id: str, db: Session = Depends(get_db)):
    """Get cart with all items and total"""
    cart = CartService.get_cart(db, session_id)
    if not cart:
        # Return empty cart
        return {
            "id": 0,
            "session_id": session_id,
            "items": [],
            "total_amount": 0
        }
    return cart

@router.put("/items/{item_id}")
def update_cart_item(item_id: int, session_id: str, update: schemas.CartItemUpdate, db: Session = Depends(get_db)):
    """Update item quantity in cart"""
    cart_item = CartService.update_cart_item(db, session_id, item_id, update.quantity)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"message": "Cart item updated"}

@router.delete("/items/{item_id}")
def remove_from_cart(item_id: int, session_id: str, db: Session = Depends(get_db)):
    """Remove item from cart"""
    success = CartService.remove_item_from_cart(db, session_id, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cart item not found")
    return {"message": "Item removed from cart"}

@router.delete("/{session_id}")
def clear_cart(session_id: str, db: Session = Depends(get_db)):
    """Clear all items from cart"""
    CartService.clear_cart(db, session_id)
    return {"message": "Cart cleared"}