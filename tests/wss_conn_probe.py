import asyncio
import datetime
import json
import logging
import ssl

import websockets

VALID_TOKEN = "valid_token"  # noqa: S105


async def wss_test():
    """Test wss server"""
    uri = "wss://localhost:8765/ws/chatrooms/test-room"

    # Create an SSL context that skips certificate verification
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    created_at = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VALID_TOKEN}",
    }
    test_message = {
        "type": "system",
        "userId": "tester_user_id",
        "username": "Tester",
        "content": "Hello, WSS Server!",
        "timestamp": created_at,
    }

    try:
        async with websockets.connect(
                uri,
                additional_headers=headers,
                ssl=ssl_context,
        ) as websocket:
            await websocket.send(json.dumps(test_message))

            try:
                response = await websocket.recv()
                logging.info(f"Received: {response}")
            except websockets.exceptions.ConnectionClosedOK:
                logging.info("Test WebSocket connection closed normally.")

    except Exception as e:
        logging.exception(f"An error occurred: {e!s}")  # noqa: TRY401


if __name__ == "__main__":
    asyncio.run(wss_test())
