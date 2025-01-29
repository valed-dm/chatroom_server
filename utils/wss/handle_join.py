import datetime
import json

from handlers.wss_srv.chatrooms import Chatrooms
from utils.wss.brodcast_to_room import broadcast_to_room

chatrooms = Chatrooms()


async def handle_join(message, room_id, connection):
    user_id = message.get("userId")
    username = message.get("username")
    if not user_id or not username:
        await connection.send(json.dumps(
            {"type": "system", "content": "Missing 'userId' or 'username'."},
        ))
        return

    await chatrooms.add_member(room_id, connection)

    # Notify all users in the room
    system_message = {
        "type": "system",
        "content": f"{username} with id {user_id} joined the chat.",
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
    }
    await broadcast_to_room(room_id, system_message)
