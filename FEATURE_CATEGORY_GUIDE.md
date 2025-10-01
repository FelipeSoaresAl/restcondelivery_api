# Guia de Desenvolvimento: Funcionalidade de Categorias de Produtos

Este documento detalha os passos para adicionar um sistema de gerenciamento de categorias ao projeto, permitindo que vendedores (usuários `OWNER`) criem categorias e as associem aos seus produtos.

## Passo 1: Atualizar os Modelos do Banco de Dados

Primeiro, precisamos definir a tabela de `Category` e a relação muitos-para-muitos com a tabela `Product`.

**Abra o arquivo `app/models.py` e adicione o seguinte:**

1.  **Importe `Table`:** Garanta que `Table` está sendo importado do `sqlalchemy` no início do arquivo.

    ```python
    from sqlalchemy import (Boolean, Column, Integer, String, Float, ForeignKey, 
                            DateTime, Enum, Table)
    ```

2.  **Tabela de Associação:** Adicione esta tabela no meio do arquivo, depois da definição de `Store` e antes de `Product`. Ela conectará produtos e categorias.

    ```python
    # Tabela de associação para o relacionamento muitos-para-muitos
    product_category_association = Table('product_category_association', Base.metadata,
        Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
        Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
    )
    ```

3.  **Modelo `Category`:** Adicione este modelo logo após a tabela de associação.

    ```python
    class Category(Base):
        __tablename__ = "categories"
        id = Column(Integer, primary_key=True, index=True)
        name = Column(String(100), index=True, nullable=False)
        store_id = Column(Integer, ForeignKey("stores.id"))

        store = relationship("Store", back_populates="categories")
        products = relationship("Product",
                                secondary=product_category_association,
                                back_populates="categories")
    ```

4.  **Atualize os Modelos `Store` e `Product`:** Adicione os relacionamentos (`relationship`) para que o SQLAlchemy entenda as novas conexões.

    *   Em `Store`, adicione:
        ```python
        categories = relationship("Category", back_populates="store", cascade="all, delete-orphan")
        ```
    *   Em `Product`, adicione:
        ```python
        categories = relationship("Category",
                                  secondary=product_category_association,
                                  back_populates="products")
        ```

## Passo 2: Definir os Esquemas Pydantic

Agora, vamos criar os esquemas de dados para validação e serialização.

**Abra o arquivo `app/schemas.py` e adicione/modifique o seguinte:**

1.  **Importe `BaseModel`:** Garanta que `BaseModel` está sendo importado do `pydantic`.

2.  **Esquemas de Categoria:** Adicione estes esquemas.

    ```python
    class CategoryBase(BaseModel):
        name: str

    class CategoryCreate(CategoryBase):
        pass

    class Category(CategoryBase):
        id: int
        store_id: int

        class Config:
            orm_mode = True
    ```

3.  **Atualize os Esquemas de Produto:** Inclua a lista de categorias nos esquemas de produto.

    *   No esquema `Product`, adicione o campo `categories`:
        ```python
        categories: list[Category] = []
        ```

## Passo 3: Criar um Novo Roteador para Categorias

Vamos criar um arquivo dedicado para os endpoints de categoria.

**Crie um novo arquivo: `app/routers/categories.py` e adicione o seguinte código:**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..deps import get_current_active_user

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    responses={404: {"description": "Not found"}},
)

@router.post("/store/{store_id}", response_model=schemas.Category)
def create_category_for_store(
    store_id: int,
    category: schemas.CategoryCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_active_user)
):
    db_store = db.query(models.Store).filter(models.Store.id == store_id).first()
    if not db_store:
        raise HTTPException(status_code=404, detail="Store not found")
    if db_store.owner_id != current_user.id or current_user.role != 'OWNER':
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return crud.create_store_category(db=db, category=category, store_id=store_id)

@router.get("/store/{store_id}", response_model=List[schemas.Category])
def read_store_categories(store_id: int, db: Session = Depends(get_db)):
    categories = crud.get_categories_by_store(db, store_id=store_id)
    return categories

# Adicione aqui outros endpoints (GET by ID, PUT, DELETE) conforme necessário.
```

## Passo 4: Adicionar Funções CRUD

O roteador acima depende de funções `crud` que ainda não existem.

**Abra o arquivo `app/crud.py` e adicione as seguintes funções:**

```python
def create_store_category(db: Session, category: schemas.CategoryCreate, store_id: int):
    db_category = models.Category(**category.dict(), store_id=store_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def get_categories_by_store(db: Session, store_id: int):
    return db.query(models.Category).filter(models.Category.store_id == store_id).all()
```

## Passo 5: Integrar o Novo Roteador na Aplicação Principal

A API principal precisa saber sobre o novo roteador de categorias.

**Abra o arquivo `app/main.py`:**

1.  Importe o novo roteador: `from .routers import categories`
2.  Inclua o roteador na sua aplicação FastAPI: `app.include_router(categories.router)`

## Passo 6: Atualizar o Banco de Dados

Finalmente, precisamos garantir que as novas tabelas sejam criadas no banco de dados.

**Abra o arquivo `create_tables.py` na raiz do projeto e adicione `Category` à lista de importações de modelos:**

```python
from app.models import User, Store, Product, Order, OrderItem, Category # Adicione Category aqui
```

**Execute o script `create_tables.py` novamente para aplicar as alterações ao banco de dados:**

```bash
python create_tables.py
```

**Atenção:** Se as tabelas já existem, este script não as alterará. Para desenvolvimento, pode ser mais fácil apagar e recriar as tabelas. Em um ambiente de produção, o ideal é usar uma ferramenta de migração como Alembic para gerenciar as alterações no esquema do banco de dados sem perder dados.

## Conclusão

Com esses passos, a API agora suporta a criação e listagem de categorias por loja. Você pode expandir essa funcionalidade adicionando endpoints para:

*   Associar/desassociar uma categoria a um produto.
*   Atualizar e deletar categorias.
*   Filtrar produtos por categoria.

Use a documentação interativa da API em `/docs` para testar os novos endpoints.
