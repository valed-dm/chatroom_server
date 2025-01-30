class MockAuth:
    def __init__(self, valid_token=None):
        self.valid_token = valid_token

    def is_authorized(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return False

        token = auth_header.split("Bearer ")[1].strip()
        return token is not self.valid_token
