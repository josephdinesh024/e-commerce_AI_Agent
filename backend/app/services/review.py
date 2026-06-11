from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import models, schemas
from typing import List, Optional
from fastapi import HTTPException

class ReviewService:
    @staticmethod
    def create_review(db: Session, review: schemas.ReviewCreate) -> models.Review:
        db_review = models.Review(**review.model_dump())
        try:
            db.add(db_review)
            db.commit()
            db.refresh(db_review)
            return db_review
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="You have already reviewed this product")
    
    @staticmethod
    def get_review(db: Session, review_id: int) -> Optional[models.Review]:
        return db.query(models.Review).filter(models.Review.id == review_id).first()
    
    @staticmethod
    def get_reviews_by_product(db: Session, product_id: int) -> List[models.Review]:
        return db.query(models.Review).filter(models.Review.product_id == product_id).order_by(models.Review.created_at.desc()).all()
    
    @staticmethod
    def get_review_by_session_and_product(db: Session, session_id: str, product_id: int) -> Optional[models.Review]:
        return db.query(models.Review).filter(
            models.Review.session_id == session_id,
            models.Review.product_id == product_id
        ).first()
    
    @staticmethod
    def update_review(db: Session, review_id: int, session_id: str, review_update: schemas.ReviewUpdate) -> Optional[models.Review]:
        db_review = ReviewService.get_review(db, review_id)
        if not db_review:
            return None
        
        # Check ownership
        if db_review.session_id != session_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this review")
        
        update_data = review_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_review, key, value)
        
        db.commit()
        db.refresh(db_review)
        return db_review
    
    @staticmethod
    def delete_review(db: Session, review_id: int, session_id: str) -> bool:
        db_review = ReviewService.get_review(db, review_id)
        if not db_review:
            return False
        
        # Check ownership
        if db_review.session_id != session_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this review")
        
        db.delete(db_review)
        db.commit()
        return True