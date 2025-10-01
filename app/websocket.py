from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # Dicionário para armazenar conexões ativas por ID de loja
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, store_id: int):
        await websocket.accept()
        if store_id not in self.active_connections:
            self.active_connections[store_id] = []
        self.active_connections[store_id].append(websocket)

    def disconnect(self, websocket: WebSocket, store_id: int):
        if store_id in self.active_connections:
            self.active_connections[store_id].remove(websocket)

    async def broadcast_to_store(self, store_id: int, data: dict):
        if store_id in self.active_connections:
            # Envia a mensagem para todas as conexões daquela loja
            for connection in self.active_connections[store_id]:
                await connection.send_json(data)

# Instância global do gerenciador
manager = ConnectionManager()