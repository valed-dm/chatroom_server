import asyncio
import datetime
import json
import logging

from handlers.wss_srv.clients import ConnectedClients

connected_clients = ConnectedClients()


async def shutdown_websockets(clients, shutdown_reason):
    """Send a disconnect message to all clients before shutting down."""
    disconnect_message = json.dumps({
        "type": "message",
        "reason": shutdown_reason,
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
    })

    logging.info(f"Sending disconnect message to {len(clients)} clients...")

    async def safe_send(client, message):
        try:
            await client.send(message)
        except Exception as e:
            logging.exception(f"Failed to send message to client: {e}")  # noqa: TRY401

    # Send messages first
    send_tasks = [
        asyncio.create_task(safe_send(client, disconnect_message))
        for client in clients
    ]

    results = await asyncio.gather(*send_tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            logging.error(f"Error sending message: {result}")

    logging.info("All disconnect messages sent. Waiting briefly before cleanup...")

    # Remove clients from connected_clients
    remove_tasks = [
        asyncio.create_task(connected_clients.remove_client(client))
        for client in clients
    ]

    await asyncio.gather(*remove_tasks, return_exceptions=True)

    # Explicitly close the connections
    close_tasks = [
        asyncio.create_task(client.close())
        for client in clients
    ]
    await asyncio.gather(*close_tasks, return_exceptions=True)

    logging.info("Client cleanup completed. Shutdown process continuing...")
