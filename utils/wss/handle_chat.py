import datetime
import json

from utils.wss.brodcast_to_room import broadcast_to_room


async def handle_chat_message(message, room_id, connection):
    user_id = message.get("userId")
    username = message.get("username")
    content = message.get("content")

    if not user_id or not username or not content:
        await connection.send(json.dumps(
            {"type": "system", "content": "Missing required fields in chat message."},
        ))
        return

    # Broadcast the message to the room
    chat_message = {
        "type": "message",
        "userId": user_id,
        "username": username,
        "content": content,
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
    }
    await broadcast_to_room(room_id, chat_message)
