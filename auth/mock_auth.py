from aiohttp import web


class MockAuth:
    def __init__(self, valid_token="test_token"):  # noqa: S107
        self.valid_token = valid_token

    def is_authorized(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return False

        token = auth_header.split("Bearer ")[1].strip()
        return token == self.valid_token

