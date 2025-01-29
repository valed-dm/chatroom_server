import asyncio
import json
import logging

from websockets import ConnectionClosedError
from websockets import ConnectionClosedOK


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
            logging.info(f"Adding client {client}")
            self._clients.add(client)

    async def remove_client(self, client):
        async with self._lock:
            self._clients.discard(client)

    async def get_clients(self):
        async with self._lock:
            return self._clients.copy()

    async def broadcast_to_room(self, room_id, message):
        """
        Broadcast a message to all clients in a specific room.
        :param room_id: The ID of the room to broadcast to.
        :param message: The message to broadcast (should be JSON serializable).
        """
        async with self._lock:
            for client in self._clients:
                # Ensure the client has room id
                if getattr(client, "room_id", None) == room_id:
                    try:
                        await client.send(json.dumps(message))
                    except (ConnectionClosedOK, ConnectionClosedError):
                        logging.warning("Connection closed during broadcast.")
