from __future__ import annotations

import json
import logging
import re
import time
from collections import deque

from aiohttp import web
from aiohttp.web_response import Response
from websockets import ServerConnection

from auth.mock_auth import MockAuth
from handlers.wss_srv.chatrooms import Chatrooms
from handlers.wss_srv.client.message_rate import handle_message_rate_limit
from handlers.wss_srv.client.process_message import process_message
from handlers.wss_srv.clients import ConnectedClients
from utils.http_status import HTTPStatus

MESSAGE_RATE_LIMIT = 5000  # Max 5000 messages per .5 second
MESSAGE_RATE_WINDOW = .5  # Time window in seconds

auth = MockAuth()
chatrooms = Chatrooms()
connected_clients = ConnectedClients()
message_times = deque()


async def handle_client(connection: ServerConnection) -> Response | None:
    """
    Handle WebSocket connections.
    :param connection: ServerConnection instance.
    """
    client_token = ""
    client_ip = connection.remote_address[0]
    request = connection.request
    path = request.path
    request_path = f"Request path: {path}"
    logging.info(request_path)

    if not auth.is_authorized(request):
        logging.warning(f"Unauthorized access attempt: {client_ip}")
        return web.json_response(
            {"error": "Unauthorized. Missing or invalid token."},
            status=HTTPStatus.UNAUTHORIZED.value,
        )

    match = re.match(r"^/ws/chatrooms/(?P<roomId>[\w-]+)$", path)
    if not match:
        logging.warning(f"Invalid path: {path}")
        await connection.send(json.dumps({
            "type": "system",
            "content": f"Invalid path for {client_token}:{client_ip}. Disconnecting.",
        }))
        return None

    room_id = match.group("roomId")
    added, client_token = await connected_clients.add_client(connection)
    if not added:
        logging.error(
            f"Failed to add client {client_token}:{client_ip} to connected clients",
        )
        return None

    invalid_message_count = 0
    try:
        async for raw_message in connection:
            now = time.time()
            message_times.append(now)
            while message_times and now - message_times[0] > MESSAGE_RATE_WINDOW:
                message_times.popleft()

            if len(message_times) > MESSAGE_RATE_LIMIT:
                await handle_message_rate_limit(connection, client_token, client_ip)
                return None

            invalid_message_count = await process_message(
                raw_message,
                room_id,
                connection,
                invalid_message_count,
                client_ip,
            )
    finally:
        client_token = await connected_clients.remove_client(connection)
        logging.info(f"Client disconnected: {client_token}:{client_ip}")
