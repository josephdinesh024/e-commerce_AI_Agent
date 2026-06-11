from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import schemas
from app.db import get_db
from app.services.order import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=schemas.OrderResponse)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    """Create order from cart"""
    return OrderService.create_order(db, order)

@router.get("/{session_id}", response_model=List[schemas.OrderResponse])
def get_orders(session_id: str, db: Session = Depends(get_db)):
    """Get all orders for a session"""
    return OrderService.get_orders_by_session(db, session_id)

@router.get("/detail/{order_id}", response_model=schemas.OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get order details"""
    order = OrderService.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.get("/admin/all", response_model=List[schemas.OrderResponse])
def get_all_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Admin: Get all orders"""
    return OrderService.get_all_orders(db, skip, limit)

@router.put("/{order_id}/status")
def update_order_status(order_id: int, status: str, db: Session = Depends(get_db)):
    """Admin: Update order status"""
    order = OrderService.update_order_status(db, order_id, status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order status updated", "status": status}