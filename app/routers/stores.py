from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import uuid
from pathlib import Path

# Adicionando a importação de models para usar nos type hints e na lógica de roles
from .. import crud, models, schemas, deps
from ..database import get_db

router = APIRouter(
    prefix="/stores", 
    tags=["stores"]
)

# --- Configuração de Upload ---
UPLOAD_DIRECTORY = "static/store_logos"
Path(UPLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True)

def save_upload_file(upload_file: UploadFile) -> str:
    """Salva o arquivo de upload e retorna a URL de acesso."""
    extension = Path(upload_file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{extension}"
    file_path = Path(UPLOAD_DIRECTORY) / unique_filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return f"/{UPLOAD_DIRECTORY}/{unique_filename}"

@router.post("/", response_model=schemas.Store, dependencies=[Depends(deps.require_admin)])
def create_store_for_owner(
    db: Session = Depends(get_db),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    owner_id: int = Form(...),
    logo: Optional[UploadFile] = File(None)
):
    owner = crud.get_user_by_id(db, user_id=owner_id)
    if not owner:
        raise HTTPException(status_code=404, detail=f"Owner with id {owner_id} not found")

    logo_url = None
    if logo:
        logo_url = save_upload_file(logo)

    store_data = schemas.StoreCreate(name=name, description=description, owner_id=owner_id)

    if owner.role == models.UserRole.CUSTOMER:
        crud.update_user_role(db, db_user=owner, role=models.UserRole.OWNER)
    
    return crud.create_store(db=db, store=store_data, owner_id=owner_id, logo_url=logo_url)

# --- ALTERAÇÕES AQUI ---
@router.get("/", response_model=List[schemas.Store])
def read_stores(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Retorna uma lista de lojas com base no papel do usuário.
    - ADMIN: Vê todas as lojas.
    - OWNER: Vê apenas as suas lojas.
    """
    if current_user.role == models.UserRole.ADMIN:
        # Correto: Chama a função que busca TODAS as lojas, passando a paginação.
        stores = crud.get_stores(db, skip=skip, limit=limit)

    elif current_user.role == models.UserRole.OWNER:
        # Correto: Chama a função específica para o OWNER, passando seu ID e a paginação.
        stores = crud.get_stores_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)

    else:
        # Para outros papéis (ex: CUSTOMER), retorna uma lista vazia.
        stores = []
        
    return stores
# --- FIM DAS ALTERAÇÕES ---

@router.get("/{store_id}", response_model=schemas.Store)
def read_store(store_id: int, db: Session = Depends(get_db)):
    db_store = crud.get_store(db, store_id=store_id)
    if db_store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    return db_store

@router.put("/{store_id}", response_model=schemas.Store)
def update_store_details(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    owner_id: Optional[int] = Form(None),
    logo: Optional[UploadFile] = File(None)
):
    db_store = crud.get_store(db, store_id=store_id)
    if not db_store:
        raise HTTPException(status_code=404, detail="Store not found")

    is_admin = current_user.role == models.UserRole.ADMIN
    is_owner = db_store.owner_id == current_user.id
    
    if not (is_admin or is_owner):
        raise HTTPException(status_code=403, detail="Not authorized to update this store")

    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    
    if owner_id is not None and owner_id != db_store.owner_id:
        if not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to change store owner")
        new_owner = crud.get_user_by_id(db, user_id=owner_id)
        if not new_owner:
            raise HTTPException(status_code=404, detail=f"New owner with id {owner_id} not found")
        if new_owner.role == models.UserRole.CUSTOMER:
            crud.update_user_role(db, db_user=new_owner, role=models.UserRole.OWNER)
        update_data["owner_id"] = owner_id

    logo_url = None
    if logo:
        logo_url = save_upload_file(logo)

    store_in = schemas.StoreUpdate(**update_data)
    updated_store = crud.update_store(db=db, db_store=db_store, store_in=store_in, logo_url=logo_url)
    return updated_store