from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models, schemas
from typing import List, Optional
from fastapi import HTTPException

class ProductService:
    @staticmethod
    def create_product(db: Session, product: schemas.ProductCreate) -> models.Product:
        db_product = models.Product(**product.model_dump())
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    
    @staticmethod
    def get_product(db: Session, product_id: int) -> Optional[models.Product]:
        return db.query(models.Product).filter(models.Product.id == product_id).first()
    
    @staticmethod
    def get_products(db: Session, skip: int = 0, limit: int = 100, listed_only: bool = False) -> List[models.Product]:
        query = db.query(models.Product)
        if listed_only:
            query = query.filter(models.Product.is_listed == True)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_product(db: Session, product_id: int, product_update: schemas.ProductUpdate) -> Optional[models.Product]:
        db_product = ProductService.get_product(db, product_id)
        if not db_product:
            return None
        
        update_data = product_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_product, key, value)
        
        db.commit()
        db.refresh(db_product)
        return db_product
    
    @staticmethod
    def delete_product(db: Session, product_id: int) -> bool:
        db_product = ProductService.get_product(db, product_id)
        if not db_product:
            return False
        
        db.delete(db_product)
        db.commit()
        return True
    
    @staticmethod
    def get_product_with_stats(db: Session, product_id: int) -> Optional[dict]:
        product = ProductService.get_product(db, product_id)
        if not product:
            return None
        
        # Calculate average rating and total reviews
        stats = db.query(
            func.avg(models.Review.rating).label('average_rating'),
            func.count(models.Review.id).label('total_reviews')
        ).filter(models.Review.product_id == product_id).first()
        
        product_dict = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "image_url": product.image_url,
            "is_listed": product.is_listed,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "average_rating": float(stats.average_rating) if stats.average_rating else None,
            "total_reviews": stats.total_reviews or 0
        }
        
        return product_dict
    
    @staticmethod
    def get_products_with_stats(db: Session, skip: int = 0, limit: int = 100, listed_only: bool = False) -> List[dict]:
        products = ProductService.get_products(db, skip, limit, listed_only)
        result = []
        
        for product in products:
            stats = db.query(
                func.avg(models.Review.rating).label('average_rating'),
                func.count(models.Review.id).label('total_reviews')
            ).filter(models.Review.product_id == product.id).first()
            
            product_dict = {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock": product.stock,
                "image_url": product.image_url,
                "is_listed": product.is_listed,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
                "average_rating": float(stats.average_rating) if stats.average_rating else None,
                "total_reviews": stats.total_reviews or 0
            }
            result.append(product_dict)
        
        return result