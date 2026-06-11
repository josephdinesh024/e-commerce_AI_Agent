from sqlalchemy.orm import Session
from app import models, schemas
from typing import List, Optional

class AddressService:
    @staticmethod
    def create_address(db: Session, address: schemas.AddressCreate) -> models.Address:
        db_address = models.Address(**address.model_dump())
        db.add(db_address)
        db.commit()
        db.refresh(db_address)
        return db_address
    
    @staticmethod
    def get_address(db: Session, address_id: int) -> Optional[models.Address]:
        return db.query(models.Address).filter(models.Address.id == address_id).first()
    
    @staticmethod
    def get_addresses_by_session(db: Session, session_id: str) -> List[models.Address]:
        return db.query(models.Address).filter(models.Address.session_id == session_id).order_by(models.Address.created_at.desc()).all()