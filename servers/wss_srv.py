import asyncio
import logging
import ssl

from websockets import serve

from handlers.wss_client_handler import connected_clients
from handlers.wss_client_handler import handle_client


async def wss_server(event: asyncio.Event):
    """WebSocket server with SSL"""
    # Create an SSL context
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="certificate.crt", keyfile="private.key")

    async with serve(handle_client, "localhost", 8765, ssl=ssl_context) as wss_srv:
        logging.info("WebSocket server started on wss://localhost:8765")

        try:
            await event.wait()
        finally:
            logging.info("Shutting down WebSocket server...")
            for client in connected_clients:
                await client.close()
            wss_srv.close()
            await wss_srv.wait_closed()
            logging.info("WebSocket server stopped cleanly.")
