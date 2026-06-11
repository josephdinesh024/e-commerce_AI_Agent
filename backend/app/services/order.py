from sqlalchemy.orm import Session
from app import models, schemas
from app.services.cart import CartService
from typing import List, Optional
from fastapi import HTTPException

class OrderService:
    @staticmethod
    def create_order(db: Session, order_create: schemas.OrderCreate) -> models.Order:
        # Get cart
        cart = CartService.get_cart(db, order_create.session_id)
        if not cart or not cart['items']:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        # Verify address
        address = db.query(models.Address).filter(
            models.Address.id == order_create.address_id,
            models.Address.session_id == order_create.session_id
        ).first()
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
        
        # Validate stock for all items
        for item in cart['items']:
            if item.product.stock < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient stock for {item.product.name}. Available: {item.product.stock}"
                )
        
        # Create order
        total_amount = cart['total_amount']
        db_order = models.Order(
            session_id=order_create.session_id,
            address_id=order_create.address_id,
            total_amount=total_amount,
            status="Pending"
        )
        db.add(db_order)
        db.flush()
        
        # Create order items and reduce stock
        for item in cart['items']:
            order_item = models.OrderItem(
                order_id=db_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
            db.add(order_item)
            
            # Reduce stock
            item.product.stock -= item.quantity
        
        # Clear cart
        db.query(models.CartItem).filter(models.CartItem.cart_id == cart['id']).delete()
        
        db.commit()
        db.refresh(db_order)
        return db_order
    
    @staticmethod
    def get_order(db: Session, order_id: int) -> Optional[models.Order]:
        return db.query(models.Order).filter(models.Order.id == order_id).first()
    
    @staticmethod
    def get_orders_by_session(db: Session, session_id: str) -> List[models.Order]:
        return db.query(models.Order).filter(
            models.Order.session_id == session_id
        ).order_by(models.Order.created_at.desc()).all()
    
    @staticmethod
    def get_all_orders(db: Session, skip: int = 0, limit: int = 100) -> List[models.Order]:
        return db.query(models.Order).order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_order_status(db: Session, order_id: int, status: str) -> Optional[models.Order]:
        db_order = OrderService.get_order(db, order_id)
        if not db_order:
            return None
        
        db_order.status = status
        db.commit()
        db.refresh(db_order)
        return db_order