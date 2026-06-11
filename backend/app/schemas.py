from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    image_url: Optional[str] = None
    is_listed: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    is_listed: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    average_rating: Optional[float] = None
    total_reviews: int = 0
    
    model_config = ConfigDict(from_attributes=True)


# Review Schemas
class ReviewBase(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    product_id: int
    session_id: str

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None

class ReviewResponse(ReviewBase):
    id: int
    product_id: int
    session_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Cart Schemas
class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)

class CartItemCreate(CartItemBase):
    session_id: str

class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    product: ProductResponse
    
    model_config = ConfigDict(from_attributes=True)

class CartResponse(BaseModel):
    id: int
    session_id: str
    items: List[CartItemResponse]
    total_amount: float
    
    model_config = ConfigDict(from_attributes=True)


# Address Schemas
class AddressBase(BaseModel):
    name: str
    phone: str
    address: str
    city: str
    state: str
    pincode: str

class AddressCreate(AddressBase):
    session_id: str

class AddressResponse(AddressBase):
    id: int
    session_id: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Order Schemas
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderItemResponse(OrderItemBase):
    id: int
    product: ProductResponse
    
    model_config = ConfigDict(from_attributes=True)

class OrderCreate(BaseModel):
    session_id: str
    address_id: int

class OrderResponse(BaseModel):
    id: int
    session_id: str
    address_id: int
    total_amount: float
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    address: AddressResponse
    items: List[OrderItemResponse]
    
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    email: str
    full_name: str
    username: str
    phone: Optional[str] = None
    password: str

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    username: str
    phone: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: str
    password: str
    temp_session_id: Optional[str] = None  # For merging guest cart on login

class UserLoginResponse(BaseModel):
    id: int
    email: str
    full_name: str
    username: str
    session_id: str
    
    model_config = ConfigDict(from_attributes=True)
