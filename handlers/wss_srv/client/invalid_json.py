import json
import logging

MAX_INVALID_MESSAGES = 5


async def handle_invalid_json(connection, invalid_message_count, client_ip):
    """Handle invalid JSON messages."""
    logging.warning("Invalid JSON received.")
    await connection.send(json.dumps(
        {"type": "system", "content": "Invalid JSON format."}),
    )
    invalid_message_count += 1
    if invalid_message_count >= MAX_INVALID_MESSAGES:
        warning_msg = (
            f"Client {client_ip} disconnected due to excessive invalid messages."
        )
        logging.warning(warning_msg)
        await connection.close()
    return invalid_message_count
