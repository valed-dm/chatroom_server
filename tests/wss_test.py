import asyncio
import datetime
import json
import logging
import ssl

import websockets


async def wss_test():
    """Test wss server"""
    uri = "wss://localhost:8765/ws/chatrooms/test-room"

    # Create an SSL context that skips certificate verification
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    created_at = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
    test_message = {
        "type": "message",
        "userId": "tester_user_id",
        "username": "Tester",
        "content": "Hello, WSS Server!",
        "timestamp": created_at,
    }
    headers = [("Authorization", "Bearer test_token")]  # ✅ Add authorization header

    try:
        async with websockets.connect(
                uri,
                ssl=ssl_context,
                additional_headers=headers,
        ) as websocket:
            await websocket.send(json.dumps(test_message))
            response = await websocket.recv()
            logging.info(response)
    except Exception as e:
        exc_msg = f"An error occurred: {e!s}"
        logging.exception(exc_msg)


if __name__ == "__main__":
    asyncio.run(wss_test())
