import logging

from aiohttp import web

from utils.create_chatroom import CreateChatroom

chatrooms = {}


async def create_chatroom(request):
    """HTTP handler for POST requests to create a chatroom."""
    try:
        # Ensure the request has the required authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return web.json_response(
                {"error": "Unauthorized. Missing or invalid token."},
                status=401,
            )

        create_chatroom_handler = CreateChatroom(chatrooms, request)
        return await create_chatroom_handler.handle_request()

    except Exception as e:
        unexpected = f"Unexpected error: {e!s}"
        logging.exception(unexpected)
        return web.json_response(
            {"error": "An internal server error occurred."},
            status=500,
        )
