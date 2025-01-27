# In-memory store for chatrooms
import logging

from aiohttp import web

chatrooms = {}


async def create_chatroom(request):
    """HTTP handler for POST requests (create a chatroom)"""
    try:
        data = await request.json()
        room_id = data.get("roomId")
        if not room_id or room_id in chatrooms:
            return web.json_response(
                {"error": "Invalid or duplicate roomId"},
                status=400,
            )

        chatrooms[room_id] = []  # Initialize room storage
        create_msg = f"Chatroom created: {room_id}"
        logging.info(create_msg)
        return web.json_response(
            {"message": f"Chatroom '{room_id}' created successfully."},
        )
    except Exception as e:
        exc_msg = f"Error processing POST request: {e!s}"
        logging.exception(exc_msg)
        return web.json_response({"error": "Invalid request payload"}, status=400)
