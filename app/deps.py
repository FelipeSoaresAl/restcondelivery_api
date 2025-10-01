from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

from . import schemas, models, crud
from .database import get_db

# --- Configurações de Segurança ---
SECRET_KEY = "SUA_CHAVE_SECRETA_MUITO_SEGURA" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexto para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# --- Funções de Autenticação ---

def verify_password(plain_password, hashed_password):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, email: str, password: str) -> models.User | None:
    """Busca um usuário pelo email e verifica sua senha."""
    user = crud.get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Cria um novo token de acesso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependências de Autenticação e Autorização ---

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Decodifica o token e retorna o usuário correspondente."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    """Verifica se o usuário obtido do token está ativo."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_admin(current_user: models.User = Depends(get_current_active_user)):
    """Verifica se o usuário atual é um ADMIN."""
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges",
        )
    return current_user
