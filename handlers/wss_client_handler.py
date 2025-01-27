import asyncio
import logging
import re

from websockets import ConnectionClosed
from websockets.legacy.server import WebSocketServerProtocol

connected_clients = set()


async def handle_client(
    websocket: WebSocketServerProtocol,
    path="",
) -> None:
    """Handle WebSocket connections.
    :param websocket: WebSocketServerProtocol
    :type path: str
    """
    match = re.match(r"^/ws/chatrooms/(?P<roomId>[\w-]+)$", path)

    # Register client
    connected_clients.add(websocket)
    client_info_msg = f"Client connected: {websocket.remote_address}, room ID: {match}"
    logging.info(client_info_msg)

    try:
        await websocket.send("Welcome to the WebSocket chatroom!")

        async for message in websocket:
            # Broadcast message to all connected clients
            tasks = [
                client.send(f"Client says: {message}")
                for client in connected_clients
                if client != websocket
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Log the received message
            info_msg = f"Received message: {message}"
            logging.info(info_msg)

    except ConnectionClosed as e:
        exc_msg = f"Connection closed: {e}"
        logging.exception(exc_msg)

    finally:
        # Unregister client
        connected_clients.remove(websocket)
        disconnect_msg = f"Client disconnected: {websocket.remote_address}"
        logging.info(disconnect_msg)
