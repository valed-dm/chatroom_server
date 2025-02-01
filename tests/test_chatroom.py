from aiohttp import ClientSession

BASE_URL = "http://localhost:9090/chatrooms"  # Replace with your actual base URL
VALID_TOKEN = "valid_token"
INVALID_TOKEN = "not_valid_token"


async def test_create_chatroom_success(start_websocket_server):
    """Test successful creation of a chatroom."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VALID_TOKEN}",
    }
    payload = {
        "name": "Test Room",
        "description": "This is a test room",
        "max_users": 50,
    }
    async with ClientSession() as session:  # noqa: SIM117
        async with session.post(BASE_URL, json=payload, headers=headers) as response:
            assert response.status == 201
            data = await response.json()
            assert "id" in data
            assert data["name"] == "Test Room"
            assert data["description"] == "This is a test room"
            assert data["max_users"] == 50
            assert data["current_users"] == 0


async def test_create_chatroom_missing_token(start_websocket_server):
    """Test creation of a chatroom without an authorization token."""
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "name": "Test Room",
    }
    async with ClientSession() as session:  # noqa: SIM117
        async with session.post(BASE_URL, json=payload, headers=headers) as response:
            assert response.status == 401


async def test_create_chatroom_invalid_token(start_websocket_server):
    """Test creation of a chatroom with an invalid authorization token."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {INVALID_TOKEN}",
    }
    payload = {
        "name": "Test Room",
    }
    async with ClientSession() as session:  # noqa: SIM117
        async with session.post(BASE_URL, json=payload, headers=headers) as response:
            assert response.status == 401


async def test_create_chatroom_missing_name(start_websocket_server):
    """Test creation of a chatroom without the required 'name' field."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VALID_TOKEN}",
    }
    payload = {
        "description": "This is a test room",
    }
    async with ClientSession() as session:  # noqa: SIM117
        async with session.post(BASE_URL, json=payload, headers=headers) as response:
            assert response.status == 400
            data = await response.json()
            assert data == {"error": "Missing required field: 'name'."}


async def test_create_chatroom_invalid_name_type(start_websocket_server):
    """Test creation of a chatroom with an invalid 'name' type."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VALID_TOKEN}",
    }
    payload = {
        "name": 123,  # Invalid type (should be a string)
        "description": "This is a test room",
    }
    async with ClientSession() as session:  # noqa: SIM117
        async with session.post(BASE_URL, json=payload, headers=headers) as response:
            assert response.status == 400
            data = await response.json()
            assert data == {"error": "'name' must be a string."}


async def test_create_chatroom_invalid_description_type(start_websocket_server):
    """Test creation of a chatroom with an invalid 'description' type."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VALID_TOKEN}",
    }
    payload = {
        "name": "Test Room",
        "description": 123,  # Invalid type (should be a string)
    }
    async with ClientSession() as session:  # noqa: SIM117
        async with session.post(BASE_URL, json=payload, headers=headers) as response:
            assert response.status == 400
            data = await response.json()
            assert data == {"error": "'description' must be a string."}


async def test_create_chatroom_invalid_max_users_type(start_websocket_server):
    """Test creation of a chatroom with an invalid 'max_users' type."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VALID_TOKEN}",
    }
    payload = {
        "name": "Test Room",
        "max_users": "invalid",  # Invalid type (should be an integer)
    }
    async with ClientSession() as session:  # noqa: SIM117
        async with session.post(BASE_URL, json=payload, headers=headers) as response:
            assert response.status == 400
            data = await response.json()
            assert data == {"error": "'max_users' must be a positive integer."}


async def test_create_chatroom_negative_max_users(start_websocket_server):
    """Test creation of a chatroom with a negative 'max_users' value."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VALID_TOKEN}",
    }
    payload = {
        "name": "Test Room",
        "max_users": -10,  # Invalid value (must be positive)
    }
    async with ClientSession() as session:  # noqa: SIM117
        async with session.post(BASE_URL, json=payload, headers=headers) as response:
            assert response.status == 400
            data = await response.json()
            assert data == {"error": "'max_users' must be a positive integer."}


async def test_create_chatroom_missing_max_users(start_websocket_server):
    """Test creation of a chatroom without the 'max_users' field."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VALID_TOKEN}",
    }
    payload = {
        "name": "Test Room",
        "description": "This is a test room",
    }
    async with ClientSession() as session:  # noqa: SIM117
        async with session.post(BASE_URL, json=payload, headers=headers) as response:
            assert response.status == 201
            data = await response.json()
            assert data["max_users"] == 100  # Default value


async def test_create_chatroom_duplicate_name(start_websocket_server):
    """Test creation of a chatroom with a duplicate name."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VALID_TOKEN}",
    }
    payload = {
        "name": "Test Room",
        "description": "This is a test room",
    }
    async with ClientSession() as session:
        # Create the first chatroom
        async with session.post(BASE_URL, json=payload, headers=headers) as response1:
            assert response1.status == 201

        # Attempt to create a chatroom with the same name
        async with session.post(BASE_URL, json=payload, headers=headers) as response2:
            assert response2.status == 400
            data = await response2.json()
            assert data == {"error": "Chatroom with the same name already exists."}


async def test_create_chatroom_server_error(start_websocket_server):
    """Test creation of a chatroom when the server encounters an error."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {VALID_TOKEN}",
    }
    payload = {
        "name": "Test Room",
    }
    # Simulate a server error by modifying the URL or payload
    async with ClientSession() as session:  # noqa: SIM117
        async with session.post(BASE_URL + "/invalid", json=payload, headers=headers) as response:
            assert response.status == 500
