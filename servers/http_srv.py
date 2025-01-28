import logging

import anyio
from aiohttp import web
from aiohttp_swagger3 import SwaggerDocs
from aiohttp_swagger3 import SwaggerInfo
from aiohttp_swagger3 import SwaggerUiSettings

from handlers.create_chatroom_handler import chatrooms
from handlers.create_chatroom_handler import create_chatroom


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
        logging.exception(f"Error fetching chatrooms: {e}")
        return web.json_response({"error": "Failed to retrieve chatrooms"}, status=500)


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
