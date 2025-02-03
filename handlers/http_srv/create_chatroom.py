import datetime
import json
import logging
import uuid

from aiohttp import web

from utils.http_status import HTTPStatus


class CreateChatroom:
    def __init__(self, request):
        """Initialize CreateChatroom with an HTTP request."""
        self.request = request

    async def handle_request(self, chatrooms):
        """Handle the chatroom creation request."""
        data = await self._extract_payload()
        if isinstance(data, web.Response):  # Return early if JSON extraction failed
            return data

        error_response, validated_data = await self._validate_payload(data, chatrooms)
        if error_response:
            return error_response

        if validated_data:
            room_id, room_data = await self._create_chatroom(validated_data)
            room_exists = await chatrooms.chatroom_exists_by_name(room_data)
            if room_exists:
                return web.json_response(
                    data={"error": "Chatroom with the same name already exists."},
                    status=HTTPStatus.CONFLICT.value,
                )
            await chatrooms.add_chatroom(room_id, room_data)

            return web.json_response(
                {
                    "id": room_id,
                    **room_data,
                    "current_users": len(room_data["current_users"]),
                },
                status=HTTPStatus.CREATED.value,
            )
        return error_response

    async def _extract_payload(self):
        """Extract and parse the JSON payload from the request."""
        try:
            data = await self.request.json()
            logging.info(f"Extracted payload: {data}")
        except json.JSONDecodeError as e:
            logging.exception("Invalid JSON payload")
            return web.json_response(
                {"error": f"Invalid JSON payload. {e}"},
                status=HTTPStatus.BAD_REQUEST.value,
            )
        else:
            return data

    @staticmethod
    async def _validate_payload(data, chatrooms):
        """Validate the JSON payload for required fields and constraints."""
        required_fields = {"name"}
        if missing := required_fields - data.keys():
            return web.json_response(
                {"error": f"Missing fields: {', '.join(missing)}"},
                status=HTTPStatus.BAD_REQUEST.value,
            ), None

        name = data["name"]
        if not isinstance(name, str):
            return web.json_response(
                {"error": "'name' must be a string."},
                status=HTTPStatus.BAD_REQUEST.value,
            ), None

        existing_rooms = await chatrooms.get_chatrooms()
        if name in existing_rooms.values():
            return web.json_response(
                {"error": "Chatroom with the same name already exists."},
                status=HTTPStatus.BAD_REQUEST.value,
            ), None

        # Optional field validation
        description = data.get("description", "A fun place to chat.")
        if not isinstance(description, str):
            return web.json_response(
                {"error": "'description' must be a string."},
                status=HTTPStatus.BAD_REQUEST.value,
            ), None

        # Validate 'max_users'
        try:
            max_users = int(data.get("max_users", 100))
            if max_users <= 0:
                raise ValueError  # noqa: TRY301
        except (ValueError, TypeError):
            return web.json_response(
                {"error": "'max_users' must be a positive integer."},
                status=HTTPStatus.BAD_REQUEST.value,
            ), None

        return None, {
            "name": name,
            "description": description,
            "max_users": max_users,
        }

    @staticmethod
    async def _create_chatroom(data):
        """Create chatroom details based on the validated data."""
        room_id = str(uuid.uuid4())
        created_at = datetime.datetime.now(datetime.UTC).isoformat()

        room_data = {
            **data,
            "created_at": created_at,
            "current_users": set(),
        }

        logging.info(f"Chatroom '{room_data['name']}' created: {room_data}")
        return room_id, room_data
