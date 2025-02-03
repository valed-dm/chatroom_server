import asyncio
import json

import aiohttp
import pytest
import websockets

from utils.http_status import HTTPStatus

HTTP_URL = "http://localhost:9090/chatrooms"
WEBSOCKET_URL = "wss://localhost:8765/ws/chatrooms"
VALID_TOKEN = "valid_token"  # noqa: S105

NUM_USERS = 80


async def create_chatroom():
    """Creates a chat room via HTTP request."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VALID_TOKEN}",
    }
    create_room = {
        "name": "Test Room 1",
        "description": f"Test {NUM_USERS} clients join a chat room",
    }
    async with aiohttp.ClientSession() as session:  # noqa: SIM117
        async with session.post(
                HTTP_URL, json=create_room, headers=headers,
        ) as response:
            response.raise_for_status()
            assert response.status == HTTPStatus.CREATED.value
            data = await response.json()
            return data["id"]


async def join_room(room_id, user_id, ssl_context):
    """Each user joins the WebSocket chat room and returns their response."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer user_{user_id}",  # Unique token per user
    }
    join_message = {
        "type": "join", "userId": str(user_id), "username": f"User_{user_id}",
    }

    try:
        async with websockets.connect(
                f"{WEBSOCKET_URL}/{room_id}",
                additional_headers=headers,
                ssl=ssl_context,
        ) as ws:
            await ws.send(json.dumps(join_message))
            response = await ws.recv()
            return user_id, json.loads(response)  # Mark response with user_id

    except Exception as e:
        return user_id, {"error": str(e)}  # Capture failure per user


async def test_100_users_join_chat(ssl_context):
    """Main test function to verify 100 concurrent users joining."""
    room_id = await create_chatroom()
    user_id = None
    tasks = [
        join_room(room_id, user_id, ssl_context) for user_id in range(1, NUM_USERS + 1)
    ]

    for completed in asyncio.as_completed(tasks):
        try:
            user_id, data = await completed  # Get user_id and response
        except Exception as e:  # noqa: BLE001
            pytest.fail(f"❌ Error for user {user_id}: {e}")

        if "error" in data:
            pytest.fail(f"❌ User {user_id} failed: {data['error']}")

        assert data["type"] in ["message", "system"], f"Unexpected response: {data}"
        join_info = f"Пользователь User_{user_id} присоединился к чату."
        join_failure = f"Join message failed for user {user_id}: {data}"
        assert join_info in data["content"], join_failure
