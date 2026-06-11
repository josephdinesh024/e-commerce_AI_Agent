from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import models, schemas
from typing import Optional
from fastapi import HTTPException

class CartService:
    @staticmethod
    def get_or_create_cart(db: Session, session_id: str) -> models.Cart:
        cart = db.query(models.Cart).filter(models.Cart.session_id == session_id).first()
        if not cart:
            cart = models.Cart(session_id=session_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
        return cart
    
    @staticmethod
    def add_item_to_cart(db: Session, session_id: str, product_id: int, quantity: int) -> models.CartItem:
        cart = CartService.get_or_create_cart(db, session_id)
        
        # Check if product exists and is listed
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if not product.is_listed:
            raise HTTPException(status_code=400, detail="Product is not available")
        
        # Check if item already exists in cart
        cart_item = db.query(models.CartItem).filter(
            models.CartItem.cart_id == cart.id,
            models.CartItem.product_id == product_id
        ).first()
        
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = models.CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity
            )
            db.add(cart_item)
        
        db.commit()
        db.refresh(cart_item)
        return cart_item
    
    @staticmethod
    def get_cart(db: Session, session_id: str) -> Optional[dict]:
        cart = db.query(models.Cart).filter(models.Cart.session_id == session_id).first()
        if not cart:
            return None
        
        items = []
        total_amount = 0
        
        for item in cart.items:
            if item.product and item.product.is_listed:
                item_total = item.product.price * item.quantity
                total_amount += item_total
                items.append(item)
        
        return {
            "id": cart.id,
            "session_id": cart.session_id,
            "items": items,
            "total_amount": total_amount
        }
    
    @staticmethod
    def update_cart_item(db: Session, session_id: str, item_id: int, quantity: int) -> Optional[models.CartItem]:
        cart = CartService.get_or_create_cart(db, session_id)
        cart_item = db.query(models.CartItem).filter(
            models.CartItem.id == item_id,
            models.CartItem.cart_id == cart.id
        ).first()
        
        if not cart_item:
            return None
        
        cart_item.quantity = quantity
        db.commit()
        db.refresh(cart_item)
        return cart_item
    
    @staticmethod
    def remove_item_from_cart(db: Session, session_id: str, item_id: int) -> bool:
        cart = CartService.get_or_create_cart(db, session_id)
        cart_item = db.query(models.CartItem).filter(
            models.CartItem.id == item_id,
            models.CartItem.cart_id == cart.id
        ).first()
        
        if not cart_item:
            return False
        
        db.delete(cart_item)
        db.commit()
        return True
    
    @staticmethod
    def clear_cart(db: Session, session_id: str) -> bool:
        cart = db.query(models.Cart).filter(models.Cart.session_id == session_id).first()
        if not cart:
            return False
        
        db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()
        db.commit()
        return True