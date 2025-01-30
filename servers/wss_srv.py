import asyncio
import datetime
import json
import logging
import ssl

from websockets import serve

from handlers.wss_srv.clients import ConnectedClients
from handlers.wss_srv.wss_handler import handle_client

connected_clients = ConnectedClients()


async def wss_server(
        event: asyncio.Event,
        shutdown_reason: str = "Server is shutting down.",
):
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
            clients = await connected_clients.get_clients()
            disconnect_message = json.dumps({
                "type": "disconnect",
                "reason": shutdown_reason,
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            })

            await asyncio.gather(
                *[
                    client.send(disconnect_message)
                    for client in clients if not client.close
                ],
                return_exceptions=True,
            )

            await asyncio.gather(
                *[
                    connected_clients.remove_client(client)
                    for client in clients if not client.close
                ],
                return_exceptions=True,
            )

            wss_srv.close()
            await wss_srv.wait_closed()
            logging.info("WebSocket server stopped cleanly.")
