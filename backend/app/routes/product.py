from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import schemas
from app.db import get_db
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    """Admin: Create a new product"""
    db_product = ProductService.create_product(db, product)
    return ProductService.get_product_with_stats(db, db_product.id)

@router.get("/", response_model=List[schemas.ProductResponse])
def list_products(skip: int = 0, limit: int = 100, listed_only: bool = False, db: Session = Depends(get_db)):
    """List products with stats. Use listed_only=true for customer view"""
    products = ProductService.get_products_with_stats(db, skip, limit, listed_only)
    return products

@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product details with average rating and reviews count"""
    product = ProductService.get_product_with_stats(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=schemas.ProductResponse)
def update_product(product_id: int, product_update: schemas.ProductUpdate, db: Session = Depends(get_db)):
    """Admin: Update product. Use is_listed to toggle visibility"""
    db_product = ProductService.update_product(db, product_id, product_update)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductService.get_product_with_stats(db, db_product.id)

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Admin: Delete product"""
    success = ProductService.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}