import datetime
import logging
import uuid

from aiohttp import web


class CreateChatroom:
    def __init__(self, request):
        """
        Initialize CreateChatroom with an HTTP request.
        :param request: The HTTP request object.
        """
        self.request = request

    async def handle_request(self, chatrooms):
        """
        Handle the chatroom creation request.
        :param chatrooms: An instance of the Chatrooms class.
        :return: JSON response indicating success or failure.
        """
        data = await self._extract_payload()
        if isinstance(data, web.Response):
            return data  # Return early if payload extraction failed

        error_response = await self._validate_payload(data, chatrooms)
        if error_response:
            return error_response

        room_id, room_data = await self._create_chatroom(data)
        await chatrooms.add_chatroom(room_id, room_data)
        return web.json_response({
            "id": room_id,
            "name": room_data["name"],
            "description": room_data["description"],
            "created_at": room_data["created_at"],
            "max_users": room_data["max_users"],
            "current_users": len(room_data["current_users"]),
        },
            status=201,
        )

    async def _extract_payload(self):
        """
        Extract and parse the JSON payload from the request.
        :return: Parsed JSON data or an error response.
        """
        try:
            return await self.request.json()
        except Exception as e:  # noqa: BLE001
            return web.json_response(
                {"error": f"Invalid JSON payload. {e!s}"}, status=400,
            )

    @staticmethod
    async def _validate_payload(data, chatrooms):
        """
        Validate the JSON payload for required fields and constraints.
        :param data: The JSON payload.
        :param chatrooms: An instance of the Chatrooms class.
        :return: An error response if validation fails, otherwise None.
        """
        name = data.get("name")
        if not name:
            return web.json_response(
                {"error": "Missing required field: 'name'."}, status=400,
            )

        if name in (await chatrooms.get_chatrooms()).values():
            return web.json_response(
                {"error": "Chatroom with the same name already exists."}, status=400,
            )

        max_users = data.get("max_users", 100)
        if not isinstance(max_users, int) or max_users <= 0:
            return web.json_response(
                {"error": "'max_users' must be a positive integer."}, status=400,
            )

        return None  # Validation passed

    @staticmethod
    async def _create_chatroom(data):
        """
        Create chatroom details based on the request data.
        :param data: The JSON payload.
        :return: A tuple containing room_id and room_data.
        """
        room_id = str(uuid.uuid4())
        created_at = datetime.datetime.now(datetime.UTC).isoformat()

        room_data = {
            "name": data["name"],
            "description": data.get("description", "A fun place to chat."),
            "created_at": created_at,
            "max_users": data.get("max_users", 100),
            "current_users": set(),
        }

        logging.info(f"Chatroom {room_data['name']} data prepared: ")

        return room_id, room_data
