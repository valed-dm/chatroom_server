import asyncio
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

    try:
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            await websocket.send("Hello, WSS Server!")
            response = await websocket.recv()
            logging.info(response)
            await asyncio.sleep(.1)
    except Exception as e:
        exc_msg = f"An error occurred: {e}"
        logging.exception(exc_msg)


if __name__ == "__main__":
    asyncio.run(wss_test())
