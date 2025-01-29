from enum import Enum


class MessageType(str, Enum):
    JOIN = "join"
    MESSAGE = "message"
    SYSTEM = "system"
    DISCONNECT = "disconnect"
