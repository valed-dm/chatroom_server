import json
import logging


async def handle_unknown_message_type(message_type, connection):
    """Handle unknown message types."""
    msg = f"Unknown message type: {message_type}"
    logging.warning(msg)
    await connection.send(json.dumps({"type": "system", "content": msg}))
