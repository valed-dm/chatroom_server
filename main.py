import asyncio
import logging
import signal

from anyio import Event

from logging_config import setup_logging_from_pyproject
from servers.http import http_server
from servers.wss import wss_server
from tests.wss_test import wss_test


async def main():
    """Start WebSocket and HTTP servers"""
    setup_logging_from_pyproject()
    logging.info("Starting Chatroom application...")

    stop_event = Event()

    async def shutdown():
        logging.info("Shutdown signal received. Stopping servers...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

    await asyncio.gather(http_server(stop_event), wss_server(stop_event), wss_test())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Application stopped manually.")
