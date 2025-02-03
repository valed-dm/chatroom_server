import json
import logging

from handlers.wss_srv.client.invalid_json import handle_invalid_json
from handlers.wss_srv.client.unknown_message import handle_unknown_message_type
from utils.wss.handle_chat import handle_chat_message
from utils.wss.handle_user_event import handle_disconnect
from utils.wss.handle_user_event import handle_join
from utils.wss.message_types import MessageType


async def process_message(
        raw_message,
        room_id,
        connection,
        invalid_message_count,
        client_ip,
):
    """Process incoming WebSocket messages."""
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
            await handle_unknown_message_type(message_type, connection)
    except json.JSONDecodeError:
        invalid_message_count = await handle_invalid_json(
            connection,
            invalid_message_count,
            client_ip,
        )
    except Exception as e:
        msg_error = f"Error processing message: {e!s}"
        logging.exception(msg_error)
    return invalid_message_count
