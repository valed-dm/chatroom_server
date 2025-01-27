import logging

import anyio
from aiohttp import web

from handlers.create_chatroom_handler import chatrooms
from handlers.create_chatroom_handler import create_chatroom


async def list_chatrooms(request):
    """HTTP handler for GET requests (list chatrooms)"""
    return web.json_response({"chatrooms": list(chatrooms.keys())})


async def http_server(event: anyio.Event):
    """HTTP app and server"""
    app = web.Application()

    app.router.add_get("/api/chatrooms", list_chatrooms)
    app.router.add_post("/api/chatrooms", create_chatroom)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "localhost", 9090)
    await site.start()
    logging.info("HTTP server started on http://localhost:9090")

    try:
        await event.wait()
    finally:
        await runner.cleanup()
        logging.info("HTTP server stopped cleanly.")
