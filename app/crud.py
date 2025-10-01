from sqlalchemy.orm import Session, joinedload
from typing import Optional
from . import models, schemas
from passlib.context import CryptContext

# Configuração para hashing de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Funções CRUD para Usuários (User) ---

def get_user_by_email(db: Session, email: str) -> models.User | None:
    """Busca um usuário registrado pelo seu email."""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> models.User | None:
    """Busca um usuário registrado pelo seu ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[models.User]:
    """Retorna uma lista de usuários registrados."""
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Cria um novo usuário registrado. O primeiro usuário criado é definido como ADMIN."""
    count = db.query(models.User).count()
    # Define o papel do usuário: o primeiro é ADMIN, os demais são CUSTOMER.
    user_role = models.UserRole.ADMIN if count == 0 else models.UserRole.CUSTOMER
    
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        email=user.email, 
        hashed_password=hashed_password,
        role=user_role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_role(db: Session, db_user: models.User, role: models.UserRole) -> models.User:
    """Atualiza o papel (role) de um usuário existente."""
    db_user.role = role
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Funções CRUD para Clientes Convidados (GuestUser) ---

def get_guest_user_by_phone(db: Session, phone: str) -> models.GuestUser | None:
    """Busca um cliente convidado pelo número de telefone."""
    return db.query(models.GuestUser).filter(models.GuestUser.phone == phone).first()

def create_or_update_guest_user(db: Session, guest_details: schemas.GuestUserCreate) -> models.GuestUser:
    """Cria um novo cliente convidado ou atualiza os dados de um existente."""
    db_guest = get_guest_user_by_phone(db, phone=guest_details.phone)
    if db_guest:
        # Atualiza os dados se o cliente já existir
        db_guest.name = guest_details.name
        db_guest.address = guest_details.address
        db_guest.cpf = guest_details.cpf
    else:
        # Cria um novo cliente convidado
        db_guest = models.GuestUser(**guest_details.model_dump())
        db.add(db_guest)
    
    db.commit()
    db.refresh(db_guest)
    return db_guest

# --- Funções CRUD para Lojas (Store) ---

def get_store(db: Session, store_id: int) -> models.Store | None:
    """Busca uma loja pelo seu ID."""
    return db.query(models.Store).filter(models.Store.id == store_id).first()

def get_stores(db: Session, skip: int = 0, limit: int = 100) -> list[models.Store]:
    """Retorna uma lista de TODAS as lojas (para Admins)."""
    # Esta função NÃO DEVE ter nenhum filtro por 'owner_id'.
    return db.query(models.Store).offset(skip).limit(limit).all()

def get_stores_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> list[models.Store]:
    """Retorna uma lista de lojas de um proprietário específico (para Owners)."""
    # Esta função DEVE ter o filtro por 'owner_id'.
    return db.query(models.Store).filter(models.Store.owner_id == owner_id).offset(skip).limit(limit).all()
# --- FIM DA NOVA FUNÇÃO ---

def create_store(db: Session, store: schemas.StoreCreate, owner_id: int, logo_url: Optional[str] = None) -> models.Store:
    """Cria uma nova loja."""
    db_store = models.Store(
        name=store.name, 
        description=store.description, 
        owner_id=owner_id, 
        logo_url=logo_url
    )
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    return db_store

def update_store(db: Session, db_store: models.Store, store_in: schemas.StoreUpdate) -> models.Store:
    """Atualiza os dados de uma loja existente."""
    update_data = store_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_store, key, value)
    
    db.commit()
    db.refresh(db_store)
    return db_store

# --- Funções CRUD para Produtos (Product) ---

def get_product(db: Session, product_id: int) -> models.Product | None:
    """Busca um produto pelo seu ID."""
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_products_by_store(db: Session, store_id: int, skip: int = 0, limit: int = 100) -> list[models.Product]:
    """Retorna uma lista de produtos de uma loja específica."""
    return db.query(models.Product).filter(models.Product.store_id == store_id).offset(skip).limit(limit).all()

def create_store_product(db: Session, product: schemas.ProductCreate, store_id: int, image_url: Optional[str] = None) -> models.Product:
    """Cria um novo produto associado a uma loja."""
    db_product = models.Product(
        **product.model_dump(), 
        store_id=store_id, 
        image_url=image_url
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, db_product: models.Product, product_in: schemas.ProductUpdate) -> models.Product:
    """Atualiza os dados de um produto existente."""
    update_data = product_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

# --- Funções CRUD para Pedidos (Order) ---

def get_order(db: Session, order_id: int) -> models.Order | None:
    """Busca um pedido e carrega os dados do cliente (seja ele registrado ou convidado)."""
    return db.query(models.Order).options(
        joinedload(models.Order.customer_user),
        joinedload(models.Order.guest_customer)
    ).filter(models.Order.id == order_id).first()

def get_user_orders(db: Session, user_id: int) -> list[models.Order]:
    """Busca os pedidos de um usuário registrado."""
    return db.query(models.Order).options(
        joinedload(models.Order.customer_user)
    ).filter(models.Order.customer_user_id == user_id).all()

def get_store_orders(db: Session, store_id: int, skip: int = 0, limit: int = 100) -> list[models.Order]:
    """Busca os pedidos de uma loja, carregando os dados de todos os tipos de cliente."""
    return db.query(models.Order).options(
        joinedload(models.Order.customer_user),
        joinedload(models.Order.guest_customer)
    ).filter(models.Order.store_id == store_id).offset(skip).limit(limit).all()

def create_guest_order(db: Session, order: schemas.OrderCreate) -> models.Order:
    """Cria um pedido para um cliente convidado."""
    # Cria ou atualiza o cliente convidado com base no telefone
    guest_customer = create_or_update_guest_user(db, guest_details=order.customer_details)
    
    total_price = 0
    db_order_items = []
    
    # Itera sobre os itens do pedido para calcular o preço total e validar os produtos
    for item in order.items:
        product = get_product(db, product_id=item.product_id)
        if not product or product.store_id != order.store_id:
            raise ValueError(f"Produto com id {item.product_id} não encontrado na loja {order.store_id}")
        
        item_total = product.price * item.quantity
        total_price += item_total
        db_order_items.append(models.OrderItem(
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=product.price
        ))

    # Cria o pedido e o associa ao ID do cliente convidado
    db_order = models.Order(
        guest_customer_id=guest_customer.id,
        store_id=order.store_id,
        total_price=total_price,
        payment_method=order.payment_method,
        items=db_order_items
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order_status(db: Session, db_order: models.Order, new_status: models.OrderStatus) -> models.Order:
    """Atualiza o status de um pedido."""
    db_order.status = new_status
    db.commit()
    db.refresh(db_order)
    return db_order