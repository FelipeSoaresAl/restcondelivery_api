from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas, deps

# Para otimizar e evitar repetição, a dependência que exige o papel de ADMIN
# é aplicada a todas as rotas deste router de uma só vez.
router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(deps.require_admin)] 
)

@router.get("/", response_model=List[schemas.UserDetail])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
):
    """
    Retorna uma lista de todos os usuários com detalhes completos.
    Acesso restrito a administradores.
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.UserDetail)
def read_user(
    user_id: int, 
    db: Session = Depends(deps.get_db)
):
    """
    Retorna os detalhes de um usuário específico pelo seu ID.
    Acesso restrito a administradores.
    """
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}/role", response_model=schemas.UserDetail)
def set_user_role(
    user_id: int,
    user_role: schemas.UserRoleUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Define o papel (role) de um usuário específico.
    Acesso restrito a administradores.
    """
    # Primeiro, verifica se o usuário existe
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Se o usuário for encontrado, atualiza seu papel
    updated_user = crud.update_user_role(
        db=db, 
        db_user=db_user, 
        role=user_role.role
    )
    return updated_user