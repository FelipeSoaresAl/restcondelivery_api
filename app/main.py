from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Importa StaticFiles
from . import models
from .database import engine
from .routers import auth, stores, products, orders, users

# Cria as tabelas no banco de dados (se não existirem)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Delivery SaaS API",
    description="API para uma aplicação de Delivery multi-loja.",
    version="0.1.0",
)

# Monta um diretório para servir arquivos estáticos (logos das lojas)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ===================================================================
# Adicionado o middleware de CORS
# ===================================================================
origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)
# ===================================================================

# Inclui as rotas dos diferentes módulos
app.include_router(auth.router)
app.include_router(stores.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(users.router)


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bem-vindo à API de Delivery!"}

