from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import schemas
from app.db import get_db
from app.services.review import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.post("/", response_model=schemas.ReviewResponse)
def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    """Submit a review for a product"""
    return ReviewService.create_review(db, review)

@router.get("/product/{product_id}", response_model=List[schemas.ReviewResponse])
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    """Get all reviews for a product"""
    return ReviewService.get_reviews_by_product(db, product_id)

@router.get("/my-review/{product_id}")
def get_my_review(product_id: int, session_id: str, db: Session = Depends(get_db)):
    """Get user's review for a specific product"""
    review = ReviewService.get_review_by_session_and_product(db, session_id, product_id)
    if not review:
        return None
    return review

@router.put("/{review_id}", response_model=schemas.ReviewResponse)
def update_review(review_id: int, session_id: str, review_update: schemas.ReviewUpdate, db: Session = Depends(get_db)):
    """Update your review"""
    db_review = ReviewService.update_review(db, review_id, session_id, review_update)
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    return db_review

@router.delete("/{review_id}")
def delete_review(review_id: int, session_id: str, db: Session = Depends(get_db)):
    """Delete your review"""
    success = ReviewService.delete_review(db, review_id, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"message": "Review deleted successfully"}