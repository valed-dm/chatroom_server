import asyncio
import logging

from handlers.wss_srv.shutdown_signal import ShutdownSignalHandler
from logging_config import setup_logging_from_pyproject
from servers.http_srv import http_server
from servers.wss_srv import wss_server
from tests.wss_conn_probe import wss_test


async def main():
    """Start WebSocket and HTTP servers"""
    setup_logging_from_pyproject()
    logging.info("Starting Chatroom application...")

    signal_handler = ShutdownSignalHandler()
    await signal_handler.register_signals()

    await asyncio.gather(
        http_server(signal_handler),
        wss_server(signal_handler),
        wss_test(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Application stopped manually.")
