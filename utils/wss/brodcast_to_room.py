from handlers.wss_srv.chatrooms import Chatrooms

chatrooms = Chatrooms()


async def broadcast_to_room(room_id, message):
    """
    Broadcast a message to all clients in a specific room using Chatrooms.
    :param room_id: The ID of the room to broadcast to.
    :param message: The message to send.
    """
    await chatrooms.broadcast_to_room(room_id, message)
