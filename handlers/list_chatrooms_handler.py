import logging

from aiohttp import web

from handlers.create_chatroom_handler import chatrooms


async def list_chatrooms(request):
    """HTTP handler for GET requests (list all chatrooms with full info)"""
    try:
        rooms_info = [
            {
                "id": room_id,
                "name": room.get("name"),
                "description": room.get("description"),
                "created_at": room.get("created_at"),
                "max_users": room.get("max_users"),
                "current_users": len(room.get("users", [])),
            }
            for room_id, room in chatrooms.items()
        ]

        return web.json_response({"chatrooms": rooms_info})
    except Exception as e:
        fetch_err = f"Error fetching chatrooms: {e!s}"
        logging.exception(fetch_err)
        return web.json_response({"error": "Failed to retrieve chatrooms"}, status=500)
