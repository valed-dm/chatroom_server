import logging

from aiohttp import web
from aiohttp_swagger3 import SwaggerDocs
from aiohttp_swagger3 import SwaggerInfo
from aiohttp_swagger3 import SwaggerUiSettings

from handlers.http_srv.create_chatroom_handler import create_chatroom
from handlers.http_srv.list_chatrooms_handler import list_chatrooms
from handlers.wss_srv.shutdown_signal import ShutdownSignalHandler


async def http_server(signal_handler: ShutdownSignalHandler):
    """HTTP app and server."""
    app = web.Application()

    # Swagger setup
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

    # Server setup
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "localhost", 9090)
    try:
        await site.start()
        logging.info("HTTP server started on http://localhost:9090")
    except Exception as e:
        logging.exception(f"Failed to start HTTP server: {e}")  # noqa: TRY401
        await runner.cleanup()
        return

    try:
        await signal_handler.stop_event.wait()
        logging.info(f"HTTP server shutting down: {signal_handler.reason}")
    finally:
        await runner.cleanup()
        logging.info("HTTP server stopped cleanly.")
