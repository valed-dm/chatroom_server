from __future__ import annotations

import asyncio
import json
import logging
import re
from collections import deque

from aiohttp import web
from aiohttp.web_response import Response
from websockets import ServerConnection

from auth.mock_auth import MockAuth
from handlers.wss_srv.chatrooms import Chatrooms
from handlers.wss_srv.clients import ConnectedClients
from utils.wss.handle_chat import handle_chat_message
from utils.wss.handle_user_event import handle_disconnect
from utils.wss.handle_user_event import handle_join
from utils.wss.message_types import MessageType

MAX_INVALID_MESSAGES = 5
MESSAGE_RATE_LIMIT = 10  # Max 10 messages per 5 seconds
MESSAGE_RATE_WINDOW = 5  # Time window in seconds

auth = MockAuth()
chatrooms = Chatrooms()
connected_clients = ConnectedClients()
message_times = deque()


async def cancel_pending_tasks_for_client(connection):
    """Cancel all pending tasks for a misbehaving WebSocket client."""
    current_task = asyncio.current_task()
    all_tasks = {t for t in asyncio.all_tasks() if t is not current_task}

    for task in all_tasks:
        if not task.done():
            task.cancel()

    warn = f"❌ Canceled all tasks for misbehaving client: {connection.remote_address}"
    logging.warning(warn)

    await connection.close()


async def handle_client(connection: ServerConnection) -> Response | None:  # noqa: C901
    """
    Handle WebSocket connections.
    :param connection: ServerConnection instance.
    """
    client_ip = connection.remote_address[0]
    request = connection.request
    path = request.path
    request_path = f"Request path: {path}"
    logging.info(request_path)

    if not auth.is_authorized(request):
        logging.warning(f"Unauthorized access attempt: {client_ip}")
        return web.json_response(
            {"error": "Unauthorized. Missing or invalid token."}, status=401,
        )

    try:
        match = re.match(r"^/ws/chatrooms/(?P<roomId>[\w-]+)$", path)
        if match:
            room_id = match.group("roomId")
            added = await connected_clients.add_client(connection)  # ✅ Confirmation
            if not added:
                logging.error(f"Failed to add client {client_ip} to connected clients")
                return None
        else:
            invalid_path = f"Invalid path: {path}"
            logging.warning(invalid_path)
            await connection.send(json.dumps(
                {
                    "type": "system",
                    "content": f"Invalid path for ip: {client_ip}. Disconnecting.",
                },
            ))
            return None

        async for raw_message in connection:
            # now = time.time()
            # message_times.append(now)
            # while message_times and now - message_times[0] > MESSAGE_RATE_WINDOW:
            #     message_times.popleft()
            #
            # # If rate limit exceeded, disconnect client
            # if len(message_times) > MESSAGE_RATE_LIMIT:
            #     logging.warning(
            #         f"Client {client_ip} is sending messages too fast. Disconnecting.",
            #     )
            #     await connection.send(json.dumps(
            #         {"type": "system", "content": "Rate limit exceed. Disconnecting."},
            #     ))
            #     await connection.close()
            #     return None
            # invalid_message_count = 0
            try:
                message = json.loads(raw_message)
                message_type = message.get("type")
                logging.info(f"Received raw message: {message}")

                if message_type == MessageType.JOIN:
                    await handle_join(message, room_id, connection)
                elif message_type == MessageType.MESSAGE:
                    await handle_chat_message(message, room_id, connection)
                elif message_type == MessageType.DISCONNECT:
                    await handle_disconnect(message, room_id, connection)
                elif message_type != MessageType.SYSTEM:
                    msg = f"Unknown message type: {message_type}"
                    logging.warning(msg)
                    await connection.send(json.dumps(
                        {"type": "system", "content": msg},
                    ))
            except json.JSONDecodeError:
                # invalid_message_count += 1
                logging.warning("Invalid JSON received.")
                await connection.send(json.dumps(
                    {"type": "system", "content": "Invalid JSON format."},
                ))
                # if invalid_message_count >= MAX_INVALID_MESSAGES:
                #     warning_msg = (f"Client {client_ip} disconnected "
                #                    f"due to excessive invalid messages.")
                #     logging.warning(warning_msg)
                #     await connection.close()
                #     return None
            except Exception as e:
                msg_error = f"Error processing message: {e!s}"
                logging.exception(msg_error)
    finally:
        await connected_clients.remove_client(connection)
        logging.info(f"Client disconnected: {client_ip}")
