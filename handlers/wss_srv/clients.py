import asyncio
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
            logging.info(
                f"Adding client {await self.get_client_token(client)} "
                f"to connected clients",
            )
            self._clients.add(client)

    async def remove_client(self, client):
        async with self._lock:
            self._clients.discard(client)

    @staticmethod
    async def get_client_token(client):
        client = ChatUser(client)
        return client.token

    async def get_clients(self):
        async with self._lock:
            return self._clients.copy()
