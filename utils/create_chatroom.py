import datetime
import logging
import uuid

from aiohttp import web


class CreateChatroom:
    def __init__(self, chatrooms, request):
        self.chatrooms = chatrooms
        self.request = request

    async def handle_request(self):
        data = await self._extract_payload()
        if isinstance(data, web.Response):
            return data  # Return early if payload extraction failed

        error_response = self._validate_payload(data)
        if error_response:
            return error_response

        room_data = self._create_chatroom(data)
        return web.json_response(room_data, status=201)

    async def _extract_payload(self):
        try:
            return await self.request.json()
        except Exception as e:  # noqa: BLE001
            return web.json_response(
                {"error": f"Invalid JSON payload. {e!s}"}, status=400,
            )

    def _validate_payload(self, data):
        name = data.get("name")
        if not name:
            return web.json_response(
                {"error": "Missing required field: 'name'."}, status=400,
            )

        if name in self.chatrooms:
            return web.json_response(
                {"error": "Chatroom with the same name already exists."}, status=400,
            )

        max_users = data.get("max_users", 100)
        if not isinstance(max_users, int) or max_users <= 0:
            return web.json_response(
                {"error": "'max_users' must be a positive integer."}, status=400,
            )

        return None  # Validation passed

    def _create_chatroom(self, data):
        room_id = str(uuid.uuid4())
        created_at = datetime.datetime.now(datetime.UTC).isoformat()

        # Save the chatroom details
        self.chatrooms[room_id] = {
            "name": data["name"],
            "description": data.get("description", "A fun place to chat."),
            "created_at": created_at,
            "max_users": data.get("max_users", 100),
            "current_users": 0,
            "users": [],
        }
        created = f"Chatroom created: {self.chatrooms[room_id]["name"]}"
        logging.info(created)

        return {
            "id": room_id,
            "name": self.chatrooms[room_id]["name"],
            "description": self.chatrooms[room_id]["description"],
            "created_at": self.chatrooms[room_id]["created_at"],
            "max_users": self.chatrooms[room_id]["max_users"],
            "current_users": self.chatrooms[room_id]["current_users"],
        }
