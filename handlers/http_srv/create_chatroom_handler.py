import logging

from aiohttp import web

from auth.mock_auth import MockAuth
from handlers.http_srv.create_chatroom import CreateChatroom
from handlers.wss_srv.chatrooms import Chatrooms

auth = MockAuth()
chatrooms = Chatrooms()


async def create_chatroom(request):
    """HTTP handler for POST requests to create a chatroom."""
    try:
        # Ensure the request has the required authorization header
        if not auth.is_authorized(request):
            return web.json_response(
                {"error": "Unauthorized. Missing or invalid token."}, status=401,
            )
        chatroom = CreateChatroom(request)
        return await chatroom.handle_request(chatrooms)
    except Exception as e:
        unexpected = f"Unexpected error: {e!s}"
        logging.exception(unexpected)
        return web.json_response(
            {"error": "An internal server error occurred."},
            status=500,
        )
