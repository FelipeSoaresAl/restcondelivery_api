from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from .models import OrderStatus, UserRole

# --- Guest User Schemas (NOVOS) ---
class GuestUserBase(BaseModel):
    phone: str
    name: str
    address: str
    cpf: Optional[str] = None

class GuestUserCreate(GuestUserBase):
    pass

class GuestUser(GuestUserBase):
    id: int

    class Config:
        from_attributes = True

# --- Product Schemas ---
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

class Product(ProductBase):
    id: int
    store_id: int
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

# --- Store Schemas ---
class StoreBase(BaseModel):
    name: str
    description: Optional[str] = None

class StoreCreate(StoreBase):
    owner_id: int

class StoreUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None

class Store(StoreBase):
    id: int
    owner_id: int
    logo_url: Optional[str] = None
    products: List[Product] = []

    class Config:
        from_attributes = True

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr

class User(UserBase): # Schema simplificado para exibição em outros modelos
    id: int

    class Config:
        from_attributes = True

class UserCreate(UserBase):
    password: str

class UserRoleUpdate(BaseModel):
    role: UserRole

class UserDetail(UserBase): # Schema completo do usuário
    id: int
    is_active: bool
    role: UserRole
    stores: List[Store] = []

    class Config:
        from_attributes = True

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Order Schemas (ATUALIZADOS) ---
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    store_id: int
    items: List[OrderItemCreate]
    customer_details: GuestUserCreate # <-- Dados do cliente são enviados aqui
    payment_method: str

class OrderItem(BaseModel):
    id: int
    product: Product
    quantity: int
    price_at_purchase: float

    class Config:
        from_attributes = True

class Order(BaseModel):
    id: int
    store_id: int
    created_at: datetime
    total_price: float
    status: OrderStatus
    payment_method: str
    items: List[OrderItem] = []
    
    # O pedido pode ter um cliente registrado ou um convidado
    customer_user: Optional[User] = None
    guest_customer: Optional[GuestUser] = None

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

Order.model_rebuild()

