from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..deps import get_current_active_user
from ..websocket import manager # Importa o gerenciador de WebSocket

router = APIRouter(prefix="/orders", tags=["orders"])

# --- Endpoint WebSocket para notificações em tempo real ---
@router.websocket("/ws/{store_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    store_id: int,
    db: Session = Depends(get_db)
):
    """
    Mantém uma conexão WebSocket para uma loja específica.
    A autenticação (via token nos query params) é recomendada para produção.
    """
    # Exemplo de como proteger o endpoint:
    # token = websocket.query_params.get("token")
    # user = await get_user_from_token(token, db) # Função de dependência assíncrona
    # store = crud.get_store(db, store_id)
    # if not user or store.owner_id != user.id:
    #     await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    #     return

    await manager.connect(websocket, store_id)
    try:
        while True:
            # Mantém a conexão ativa para receber notificações do servidor
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, store_id)
        
# --- ROTAS PÚBLICAS (NÃO EXIGEM LOGIN) ---

@router.post("/", response_model=schemas.Order)
async def create_guest_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db)
):
    """
    Cria um novo pedido para um cliente convidado (não autenticado).
    Os dados do cliente são fornecidos no corpo da requisição.
    """
    try:
        new_order = crud.create_guest_order(db=db, order=order)
        
        # Carrega os dados completos para enviar via WebSocket
        full_order_data = crud.get_order(db, order_id=new_order.id)
        order_schema = schemas.Order.from_orm(full_order_data)
        
        # Notifica a loja em tempo real sobre o novo pedido
        await manager.broadcast_to_store(
            store_id=new_order.store_id,
            data=order_schema.model_dump(mode='json')
        )
        return new_order
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/track/{order_id}", response_model=schemas.Order)
def track_order(
    order_id: int,
    phone: str, # Cliente informa o telefone como parâmetro de busca para validar
    db: Session = Depends(get_db)
):
    """
    Permite que um cliente (convidado ou não) acompanhe o status de seu pedido
    usando o ID do pedido e o número de telefone associado.
    """
    order = crud.get_order(db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Valida se o telefone corresponde ao pedido (para clientes convidados)
    if order.guest_customer and order.guest_customer.phone == phone:
        return order
        
    # (Opcional) Adicionar lógica para clientes logados se necessário
    # if order.customer_user and order.customer_user.phone == phone:
    #     return order

    # Se a validação falhar para todos os casos
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this order")

# --- ROTAS QUE EXIGEM AUTENTICAÇÃO (LOJISTA/ADMIN/CLIENTE LOGADO) ---

@router.get("/me", response_model=List[schemas.Order])
def read_my_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retorna os pedidos feitos pelo usuário logado."""
    return crud.get_user_orders(db=db, user_id=current_user.id)
    
@router.get("/store/{store_id}", response_model=List[schemas.Order])
def read_store_orders(
    store_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Retorna todos os pedidos de uma loja. Acessível por ADMIN ou pelo OWNER da loja."""
    db_store = crud.get_store(db, store_id=store_id)
    if not db_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    is_admin = current_user.role == models.UserRole.ADMIN
    is_store_owner = db_store.owner_id == current_user.id

    if not is_admin and not is_store_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view these orders")
    
    return crud.get_store_orders(db, store_id=store_id, skip=skip, limit=limit)

@router.put("/{order_id}/status", response_model=schemas.Order)
async def update_order_status_route(
    order_id: int,
    status_update: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Atualiza o status de um pedido. Acessível por ADMIN ou pelo OWNER da loja do pedido."""
    db_order = crud.get_order(db, order_id=order_id)
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    db_store = crud.get_store(db, store_id=db_order.store_id)
    is_admin = current_user.role == models.UserRole.ADMIN
    is_store_owner = db_store and db_store.owner_id == current_user.id

    if not is_admin and not is_store_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this order")
        
    updated_order = crud.update_order_status(db, db_order=db_order, new_status=status_update.status)
    
    # Carrega os dados completos para enviar via WebSocket
    full_order_data = crud.get_order(db, order_id=updated_order.id)
    order_schema = schemas.Order.from_orm(full_order_data)

    # Notifica a loja em tempo real sobre a mudança de status
    await manager.broadcast_to_store(
        store_id=updated_order.store_id,
        data=order_schema.model_dump(mode='json')
    )
    
    return updated_order