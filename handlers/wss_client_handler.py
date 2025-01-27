import asyncio
import logging
import re

from websockets import ServerConnection
from websockets.exceptions import ConnectionClosedError
from websockets.exceptions import ConnectionClosedOK

lock = asyncio.Lock()

connected_clients = set()


async def handle_client(connection: ServerConnection) -> None:
    """
    Handle WebSocket connections.
    :param connection: ServerConnection instance.
    """
    request = connection.request
    path = request.path
    logging.info(f"Request path: {path}")

    async with lock:
        connected_clients.add(connection)

    try:
        if path == "/":
            await connection.send("Welcome to the WebSocket server!")
        else:
            match = re.match(r"^/ws/chatrooms/(?P<roomId>[\w-]+)$", path)
            if match:
                room_id = match.group("roomId")
                logging.info(f"Client joined room: {room_id}")
                await connection.send(f"Welcome to chatroom {room_id}!")
            else:
                logging.warning(f"Invalid path: {path}")
                await connection.send("Invalid path. Disconnecting.")
                return

        # Continuously listen for messages
        async for message in connection:
            logging.info(f"Received message: {message}")
            try:
                await connection.send(f"Echo: {message}")
            except (ConnectionClosedOK, ConnectionClosedError):
                logging.warning("Connection closed before response could be sent.")
                break

    except Exception as e:
        logging.exception(f"Error handling client: {e}")
    finally:
        async with lock:
            connected_clients.remove(connection)
        logging.info("Client disconnected.")
