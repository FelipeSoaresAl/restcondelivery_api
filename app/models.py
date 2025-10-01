import enum
from sqlalchemy import (Boolean, Column, Integer, String, Float, ForeignKey, 
                        DateTime, Enum)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    OWNER = "OWNER"
    CUSTOMER = "CUSTOMER"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    
    stores = relationship("Store", back_populates="owner")
    orders = relationship("Order", back_populates="customer_user") # <-- Relacionamento atualizado

# --- NOVO MODELO ---
class GuestUser(Base):
    __tablename__ = "guest_users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    cpf = Column(String(20), nullable=True)

    orders = relationship("Order", back_populates="guest_customer")

class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(String(255), index=True)
    logo_url = Column(String(255), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="stores")
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(String(255), index=True)
    price = Column(Float, nullable=False)
    image_url = Column(String(255), nullable=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    
    store = relationship("Store", back_populates="products")

class OrderStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    IN_PRODUCTION = "IN_PRODUCTION"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELED = "CANCELED"

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    
    # --- COLUNAS ATUALIZADAS ---
    # Agora um pedido pode pertencer a um usuário registrado OU a um convidado
    customer_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    guest_customer_id = Column(Integer, ForeignKey("guest_users.id"), nullable=True)

    store_id = Column(Integer, ForeignKey("stores.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    total_price = Column(Float)
    status = Column(Enum(OrderStatus), default=OrderStatus.REQUESTED)
    
    # --- COLUNAS REMOVIDAS (MOVEMOS PARA GUESTUSER) ---
    # customer_name = Column(String(100), nullable=False)
    # customer_phone = Column(String(20), nullable=False)
    # delivery_address = Column(String(255), nullable=False)
    # customer_cpf = Column(String(20), nullable=True)
    
    payment_method = Column(String(50), nullable=False)
    
    # --- RELACIONAMENTOS ATUALIZADOS ---
    customer_user = relationship("User", back_populates="orders")
    guest_customer = relationship("GuestUser", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

