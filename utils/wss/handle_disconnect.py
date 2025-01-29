import datetime
import json


async def handle_disconnect(message, connection):
    reason = message.get("reason", "No reason provided.")
    timestamp = message.get(
        "timestamp",
        datetime.datetime.now(datetime.UTC).isoformat(),
    )

    # Send system message to notify of the disconnect
    system_message = {
        "type": "system",
        "content": f"A user disconnected: {reason}",
        "timestamp": timestamp,
    }
    await connection.send(json.dumps(system_message))
