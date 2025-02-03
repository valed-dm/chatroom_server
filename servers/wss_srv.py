import logging
import ssl

from websockets import serve

from handlers.wss_srv.client.handle_client import handle_client
from handlers.wss_srv.clients import ConnectedClients
from handlers.wss_srv.shutdown_signal import ShutdownSignalHandler
from handlers.wss_srv.shutdown_websockets import shutdown_websockets

connected_clients = ConnectedClients()


async def wss_server(signal_handler: ShutdownSignalHandler):
    """WebSocket server with SSL."""
    # Create an SSL context
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        ssl_context.load_cert_chain(certfile="certificate.crt", keyfile="private.key")
    except Exception as e:
        logging.exception(f"Failed to load SSL certificate: {e!s}")  # noqa: TRY401
        return

    try:
        async with serve(
                handle_client, "localhost", 8765, ssl=ssl_context,
                backlog=1000,
                max_size=10 ** 6,  # Allow messages up to 1MB
                ping_interval=20,  # Prevent disconnects on slow clients
        ) as _wss_srv:
            logging.info("✅ WebSocket server started on wss://localhost:8765")

            await signal_handler.stop_event.wait()
            logging.info(f"⚠️ WebSocket server shutting down: {signal_handler.reason}")

            # Gracefully disconnect all clients
            clients = await connected_clients.get_clients()
            await shutdown_websockets(clients, signal_handler.reason)

    except Exception as e:
        logging.exception(f"🔥 WebSocket server error: {e}")  # noqa: TRY401

    finally:
        logging.info("✅ WebSocket server stopped cleanly.")
