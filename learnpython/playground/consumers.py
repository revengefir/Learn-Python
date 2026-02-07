import json
import websockets
from channels.generic.websocket import AsyncWebsocketConsumer

EXECUTOR_WS_URL = "ws://executor:8080/ws"

class CodeExecutionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        await self.accept()

        self.executor_ws = await websockets.connect(
            f"{EXECUTOR_WS_URL}/{self.session_id}"
        )

    async def receive(self, text_data):
        await self.executor_ws.send(text_data)

    async def disconnect(self, close_code):
        await self.executor_ws.close()