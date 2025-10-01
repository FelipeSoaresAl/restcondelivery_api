from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from .. import crud, models, schemas, deps
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=schemas.UserDetail)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    # Usa a função centralizada em deps.py para autenticar
    user = deps.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Usa a função centralizada em deps.py para criar o token
    access_token_expires = timedelta(minutes=deps.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = deps.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=schemas.UserDetail) # <-- CORREÇÃO PRINCIPAL
def read_users_me(current_user: models.User = Depends(deps.get_current_active_user)):
    """
    Retorna os dados do usuário atualmente autenticado.
    O token JWT é usado para identificar o usuário.
    """
    return current_user

