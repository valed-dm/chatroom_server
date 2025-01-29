from __future__ import annotations

import json
import logging
import re

from aiohttp import web
from aiohttp.web_response import Response
from websockets import ServerConnection

from auth.mock_auth import MockAuth
from handlers.wss_srv.chatrooms import Chatrooms
from handlers.wss_srv.clients import ConnectedClients
from utils.wss.handle_chat import handle_chat_message
from utils.wss.handle_disconnect import handle_disconnect
from utils.wss.handle_join import handle_join
from utils.wss.message_types import MessageType

auth = MockAuth()
chatrooms = Chatrooms()
connected_clients = ConnectedClients()


async def handle_client(connection: ServerConnection) -> Response | None:
    """
    Handle WebSocket connections.
    :param connection: ServerConnection instance.
    """
    request = connection.request
    path = request.path
    request_path = f"Request path: {path}"
    logging.info(request_path)

    if not auth.is_authorized(request):
        return web.json_response(
            {"error": "Unauthorized. Missing or invalid token."}, status=401,
        )

    try:
        await connected_clients.add_client(connection)

        match = re.match(r"^/ws/chatrooms/(?P<roomId>[\w-]+)$", path)
        if match:
            room_id = match.group("roomId")
            await chatrooms.add_member(room_id, connection)
            joined = f"Client joined room: {room_id}"
            logging.info(joined)
            await connection.send(json.dumps(
                {"type": "system", "content": f"Welcome to chatroom {room_id}!"},
            ))
        else:
            invalid_path = f"Invalid path: {path}"
            logging.warning(invalid_path)
            await connection.send(json.dumps(
                {"type": "system", "content": "Invalid path. Disconnecting."},
            ))
            return None

        async for raw_message in connection:
            try:
                message = json.loads(raw_message)
                message_type = message.get("type")
                msg_received = f"Received raw message: {message}"
                logging.info(msg_received)

                if message_type == MessageType.JOIN:
                    await handle_join(message, room_id, connection)
                elif message_type == MessageType.MESSAGE:
                    await handle_chat_message(message, room_id, connection)
                elif message_type == MessageType.DISCONNECT:
                    await handle_disconnect(message, connection)
                else:
                    await connection.send(json.dumps(
                        {"type": "system", "content": "Unknown message type."},
                    ))
            except json.JSONDecodeError:
                logging.warning("Invalid JSON received.")
                await connection.send(json.dumps(
                    {"type": "system", "content": "Invalid JSON format."},
                ))
            except Exception as e:
                msg_error = f"Error processing message: {e!s}"
                logging.exception(msg_error)
    finally:
        await connected_clients.remove_client(connection)
        logging.info("Client disconnected.")
