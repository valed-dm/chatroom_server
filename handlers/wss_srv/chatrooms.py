import asyncio
import logging


class Chatrooms:
    """
    Singleton class to manage chatrooms and their members.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._chatrooms = {}  # Chatrooms dictionary  # noqa: SLF001
            cls._instance._lock = asyncio.Lock()  # noqa: SLF001
        return cls._instance

    async def add_chatroom(self, room_id: str, room_data: dict):
        """
        Add a chatroom to the collection.
        :param room_id: Unique ID of the chatroom.
        :param room_data: Dictionary containing chatroom details.
        """
        async with self._lock:
            logging.info(f"Adding chatroom {room_id} with data: {room_data}")
            self._chatrooms[room_id] = room_data

    async def remove_chatroom(self, room_id: str):
        """
        Remove a chatroom from the collection.
        :param room_id: Unique ID of the chatroom to remove.
        """
        async with self._lock:
            self._chatrooms.pop(room_id, None)

    async def get_chatrooms(self) -> dict[str, dict]:
        """
        Retrieve all chatrooms.
        :return: Dictionary of chatrooms.
        """
        async with self._lock:
            return dict(self._chatrooms)  # Return a copy to avoid race conditions

    async def add_member(self, room_id: str, connection):
        """
        Add a member (connection) to a chatroom.
        :param room_id: Unique ID of the chatroom.
        :param connection: Connection object to add as a member.
        """
        async with self._lock:
            if room_id in self._chatrooms:
                self._chatrooms[room_id]["current_users"].add(connection)
                logging.info(f"Client has been added to room {room_id}.")

    async def remove_member(self, room_id: str, connection):
        """
        Remove a member (connection) from a chatroom.
        :param room_id: Unique ID of the chatroom.
        :param connection: Connection object to remove.
        """
        async with (self._lock):
            if room_id in self._chatrooms:  # noqa: SIM102
                if connection in self._chatrooms[room_id]["current_users"]:
                    self._chatrooms[room_id]["current_users"].remove(connection)

    async def get_members(self, room_id: str) -> set:
        """
        Get all members (connections) of a chatroom.
        :param room_id: Unique ID of the chatroom.
        :return: Set of members in the chatroom.
        """
        async with self._lock:
            if room_id in self._chatrooms:
                return set(self._chatrooms[room_id]["current_users"])  # Return a copy
            return set()

    async def get_member_count(self, room_id: str) -> int:
        """
        Get the current number of members in a chatroom.
        :param room_id: Unique ID of the chatroom.
        :return: Number of members in the chatroom.
        """
        async with self._lock:
            if room_id in self._chatrooms:
                return self._chatrooms[room_id]["current_users"].count()
            return 0

    async def broadcast_to_room(self, room_id: str, message: dict):
        """
        Broadcast a message to all members of a chatroom.
        :param room_id: Unique ID of the chatroom.
        :param message: Message to send.
        """
        async with self._lock:
            if room_id in self._chatrooms:
                members = self._chatrooms[room_id]["members"]
                for member in members:
                    try:
                        await member.send(message)
                    except Exception as e:  # noqa: PERF203, BLE001
                        # Handle any exceptions during message sending
                        exc_msg = f"Failed to send message to a member: {e!s}"
                        logging.warning(exc_msg)
