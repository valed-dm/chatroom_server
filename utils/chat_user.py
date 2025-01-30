class ChatUser:
    """Example user info template, not fully operational."""
    def __init__(self, connection):
        self.connection = connection
        self._headers = connection.request.headers

    @property
    def user_id(self):
        return str(self.connection["id"])

    @property
    def token(self):
        auth_header = self._headers.get("authorization")
        return auth_header.split("Bearer ")[1].strip() if auth_header else None

    @property
    def user_agent(self):
        return self._headers.get("user-agent")

    def to_dict(self):
        """Return user info as a dictionary."""
        return {
            "user_id": self.user_id,
            "token": self.token,
            "user_agent": self.user_agent,
        }
