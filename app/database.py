import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configuração para o Banco de Dados MySQL ---
# As credenciais agora são lidas das variáveis de ambiente
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# Validação para garantir que as variáveis de ambiente foram carregadas
if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    raise ValueError("Uma ou mais variáveis de ambiente do banco de dados não foram definidas. Crie um arquivo .env a partir do .env.example.")

# String de conexão para o MySQL com o driver pymysql
# Esta é a linha que foi alterada para resolver o erro.
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# A flag 'pool_pre_ping' verifica as conexões antes de usá-las
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- Dependência para obter a sessão do banco ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
