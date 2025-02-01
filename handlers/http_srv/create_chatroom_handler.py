
from aiohttp import web

from auth.mock_auth import MockAuth
from handlers.http_srv.create_chatroom import CreateChatroom
from handlers.wss_srv.chatrooms import Chatrooms

auth = MockAuth()
chatrooms = Chatrooms()


async def create_chatroom(request):
    """HTTP handler for POST requests to create a chatroom."""
    if not auth.is_authorized(request):
        return web.json_response(
            {"error": "Unauthorized. Missing or invalid token."}, status=401,
        )
    chatroom = CreateChatroom(request)
    return await chatroom.handle_request(chatrooms)
