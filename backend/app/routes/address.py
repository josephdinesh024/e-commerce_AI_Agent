from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import schemas
from app.db import get_db
from app.services.address import AddressService

router = APIRouter(prefix="/addresses", tags=["addresses"])

@router.post("/", response_model=schemas.AddressResponse)
def create_address(address: schemas.AddressCreate, db: Session = Depends(get_db)):
    """Create a new shipping address"""
    return AddressService.create_address(db, address)

@router.get("/{session_id}", response_model=List[schemas.AddressResponse])
def get_addresses(session_id: str, db: Session = Depends(get_db)):
    """Get all addresses for a session"""
    return AddressService.get_addresses_by_session(db, session_id)

@router.get("/detail/{address_id}", response_model=schemas.AddressResponse)
def get_address(address_id: int, db: Session = Depends(get_db)):
    """Get address details"""
    address = AddressService.get_address(db, address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address