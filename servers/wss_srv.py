import asyncio
import logging
import ssl

from websockets import ConnectionClosedError
from websockets import ConnectionClosedOK
from websockets import serve

from handlers.wss_srv.clients import ConnectedClients
from handlers.wss_srv.wss_handler import handle_client

connected_clients = ConnectedClients()


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
            clients = await connected_clients.get_clients()
            for client in clients:
                try:
                    # Attempt to close the connection
                    await client.close()
                except ConnectionClosedOK:  # noqa: PERF203
                    closed_ok = "Client connection already closed (ConnectionClosedOK)."
                    logging.info(closed_ok)
                except ConnectionClosedError as e:
                    closed_err = (f"Error while closing client connection "
                                  f"(ConnectionClosedError): {e!s}")
                    logging.warning(closed_err)
                except asyncio.CancelledError:
                    cancel_err = "Task was cancelled while closing a client connection."
                    logging.warning(cancel_err)
                except Exception as e:
                    unexp = f"Unexpected error while closing client connection: {e!s}"
                    logging.exception(unexp)
                finally:
                    # Ensure client is removed safely
                    await connected_clients.remove_client(client)
            wss_srv.close()
            await wss_srv.wait_closed()
            logging.info("WebSocket server stopped cleanly.")
