import datetime
import json
import logging

import aiohttp
import pytest
import websockets

HTTP_URL = "http://localhost:9090/chatrooms"
WEBSOCKET_URL = "wss://localhost:8765/ws/chatrooms/"
VALID_TOKEN = "valid_token"  # noqa: S105


async def test_wss_server(ssl_context):
    """Test WebSocket server response."""
    uri = "wss://localhost:8765/ws/chatrooms/test-room"
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    test_message = {
        "type": "system",
        "userId": "tester_user_id",
        "username": "Tester",
        "content": "Hello, WSS Server!",
        "timestamp": created_at,
    }
    headers = [("Authorization", "Bearer wss_test")]

    try:
        async with websockets.connect(
                f"{WEBSOCKET_URL}test-room",
                ssl=ssl_context,
                additional_headers=headers,
        ) as websocket:
            # Send the test message to the server
            await websocket.send(json.dumps(test_message))

            # Receive the response from the server
            response = await websocket.recv()
            logging.info(f"Received: {response}")

            # Parse the response
            response_data = json.loads(response)

            # Assert the response structure and content
            assert "type" in response_data, "Response missing 'type' field"
            assert response_data["type"] == "message", "Expected 'type' to be 'message'"
            assert "userId" in response_data, "Response missing 'userId' field"
            assert "username" in response_data, "Response missing 'username' field"
            assert "content" in response_data, "Response missing 'content' field"
            assert "timestamp" in response_data, "Response missing 'timestamp' field"

            # Log the response for debugging
            logging.info("WebSocket test passed with response: %s", response_data)

    except websockets.exceptions.ConnectionClosedOK:
        logging.info("Test WebSocket connection closed normally.")
    except Exception as e:
        logging.exception(f"An error occurred: {e!s}")
        pytest.fail(f"Test failed due to an error: {e!s}")


async def test_join_room_success(ssl_context):
    # Step 1: Communicate with the server via HTTP to set up the room
    room_id = "room1"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VALID_TOKEN}",
    }
    create_room = {
        "name": "Test Room 1",
        "description": "Description 1",
        "maxUsers": 200,
    }

    join_chat = {"type": "join", "userId": "1", "username": "User_1"}

    # Step 1: Send HTTP POST request to set up the room
    async with aiohttp.ClientSession() as session, session.post(
            f"{HTTP_URL}",
            headers=headers,
            json=create_room,
    ) as http_response:
        http_response.raise_for_status()
        response_data = await http_response.json()
        print("HTTP setup complete:", response_data)

    # Step 2: Connect to the WebSocket server and join the room
    async with websockets.connect(
            f"{WEBSOCKET_URL}{room_id}",
            ssl=ssl_context,
    ) as ws:
        # Send the join message
        await ws.send(json.dumps(join_chat))

        # Receive the response from the server
        response = await ws.recv()
        data = json.loads(response)

        # Assert the response
        assert data["message"] == "Joined chatroom successfully"
        print("WebSocket test passed:", data)
