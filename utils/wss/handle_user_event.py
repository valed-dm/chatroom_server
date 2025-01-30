import datetime
import json
import logging

from handlers.wss_srv.chatrooms import Chatrooms
from utils.wss.brodcast_to_room import broadcast_to_room

chatrooms = Chatrooms()


async def handle_user_event(event_type, message, room_id, connection):
    user_id = message.get("userId")
    username = message.get("username")
    client_ip = connection.remote_address[0]
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    if not user_id or not username:
        await connection.send(json.dumps({
            "type": "system",
            "content": f"ip: {client_ip}. Missing 'userId' or 'username'.",
        }))
        return

    event_context = {
        "join": {
            "action": chatrooms.add_member,
            "message": f"Пользователь {username} присоединился к чату.",
        },
        "disconnect": {
            "action": chatrooms.remove_member,
            "message": f"Пользователь {username} покинул чат.",
        },
    }

    if event_type not in event_context:
        logging.warning(f"Unknown event type: {event_type}")
        return

    await event_context[event_type]["action"](room_id, connection)
    event_message = event_context[event_type]["message"]
    logging.info(event_message)

    chat_info = {
        "type": "message",
        "userId": user_id,
        "username": username,
        "content": event_message,
        "timestamp": timestamp,
    }
    system_message = {
        "type": "system",
        "content": event_message,
        "timestamp": timestamp,
    }

    await broadcast_to_room(room_id, chat_info)
    await connection.send(json.dumps(system_message))


async def handle_join(message, room_id, connection):
    await handle_user_event("join", message, room_id, connection)


async def handle_disconnect(message, room_id, connection):
    await handle_user_event("disconnect", message, room_id, connection)
