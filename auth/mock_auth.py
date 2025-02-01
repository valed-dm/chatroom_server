class MockAuth:
    def __init__(self, valid_token=None):
        self.valid_token = valid_token
        self.not_valid_token = "not_valid_token"  # noqa: S105

    def is_authorized(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return False

        token = auth_header.split("Bearer ")[1].strip()
        if token == self.not_valid_token:
            return False
        return token is not self.valid_token
