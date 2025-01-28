import logging

import anyio
from aiohttp import web
from aiohttp_swagger3 import SwaggerDocs
from aiohttp_swagger3 import SwaggerInfo
from aiohttp_swagger3 import SwaggerUiSettings

from handlers.create_chatroom_handler import create_chatroom
from handlers.list_chatrooms_handler import list_chatrooms


async def http_server(event: anyio.Event):
    """HTTP app and server"""
    app = web.Application()

    swagger = SwaggerDocs(
        app,
        swagger_ui_settings=SwaggerUiSettings(path="/docs/"),
        info=SwaggerInfo(
            title="Openapi Chatrooms",
            version="1.0.0",
        ),
        components="docs/endpoints/chatrooms.yaml",
    )
    swagger.add_routes([
        web.get("/chatrooms", list_chatrooms),
        web.post("/chatrooms", create_chatroom),
    ])

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
