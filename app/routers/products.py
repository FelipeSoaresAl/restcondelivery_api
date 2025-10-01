from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import uuid
import os

from .. import crud, models, schemas
from ..database import get_db
from ..deps import get_current_active_user

router = APIRouter(prefix="/products", tags=["products"])

# --- Helper Function to Save Image ---
def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    """Salva o arquivo enviado e retorna o caminho do arquivo."""
    try:
        # Garante que o diretório de destino exista
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()
    return destination

# --- Product Routes ---
@router.post("/stores/{store_id}", response_model=schemas.Product)
def create_product_for_store(
    store_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_store = crud.get_store(db, store_id=store_id)
    if not db_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    is_admin = current_user.role == models.UserRole.ADMIN
    is_store_owner = db_store.owner_id == current_user.id
    if not is_admin and not is_store_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to add products to this store"
        )

    image_url = None
    if image:
        file_extension = image.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"static/images/products/{unique_filename}"
        save_upload_file(image, file_path)
        image_url = f"/{file_path}"

    product_data = schemas.ProductCreate(name=name, description=description, price=price)
    return crud.create_store_product(db=db, product=product_data, store_id=store_id, image_url=image_url)

@router.put("/{product_id}", response_model=schemas.Product)
def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_product = crud.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    db_store = crud.get_store(db, store_id=db_product.store_id)
    is_admin = current_user.role == models.UserRole.ADMIN
    is_store_owner = db_store.owner_id == current_user.id
    if not is_admin and not is_store_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized to update this product"
        )

    if image:
        file_extension = image.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"static/images/products/{unique_filename}"
        save_upload_file(image, file_path)
        db_product.image_url = f"/{file_path}" # Atualiza a URL da imagem diretamente

    product_update_data = schemas.ProductUpdate(name=name, description=description, price=price)
    return crud.update_product(db=db, db_product=db_product, product_in=product_update_data)


@router.get("/stores/{store_id}", response_model=List[schemas.Product])
def read_products_from_store(store_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_store = crud.get_store(db, store_id=store_id)
    if db_store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        
    products = crud.get_products_by_store(db, store_id=store_id, skip=skip, limit=limit)
    return products

