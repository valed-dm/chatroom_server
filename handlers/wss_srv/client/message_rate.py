import json
import logging


async def handle_message_rate_limit(connection, client_token, client_ip):
    """Handle message rate limiting."""
    logging.warning(
        f"Client {client_token}:{client_ip} "
        f"is sending messages too fast. Disconnecting.",
    )
    await connection.send(json.dumps(
        {"type": "system", "content": "Rate limit exceeded. Disconnecting."}),
    )
    await connection.close()
