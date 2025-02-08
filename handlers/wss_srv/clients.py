import asyncio
import datetime
import json
import logging

from utils.chat_user import ChatUser


class ConnectedClients:
    _instance = None
    _lock = asyncio.Lock()  # Lock for thread-safe singleton creation

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_clients"):  # Initialize only once
            self._clients = set()
            self._lock = asyncio.Lock()

    async def add_client(self, client):
        async with self._lock:
            client_ip = client.remote_address[0]
            token = await self.get_client_token(client)
            timestamp = datetime.datetime.now(datetime.UTC).isoformat()
            logging.info(f"Adding client {token}:{client_ip} to connected clients")
            self._clients.add(client)
            system_message = {
                "type": "system",
                "content": f"Client {token}:{client_ip} added to connected clients",
                "timestamp": timestamp,
            }
            await client.send(json.dumps(system_message))
            return True, token  # ✅ Confirm client was added

    async def remove_client(self, client):
        token = await self.get_client_token(client)
        async with self._lock:
            self._clients.discard(client)
            return token

    @staticmethod
    async def get_client_token(client):
        client = ChatUser(client)
        return client.token

    async def get_clients(self):
        async with self._lock:
            return self._clients.copy()
