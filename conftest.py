import ssl
import subprocess
import time

import pytest
import requests

WEBSOCKET_URL = "wss://localhost:8765/ws/chatrooms/"


@pytest.fixture(scope="session", autouse=True)
def start_websocket_server():
    """Start the WebSocket server before running tests"""
    server_process = subprocess.Popen(["python", "main.py"])  # noqa: S607, S603

    # Give the server a moment to start
    time.sleep(2)

    yield

    # Kill the server after tests are done
    server_process.terminate()
    server_process.wait()


@pytest.fixture(scope="session")
def ssl_context():
    """Load SSL context for secure WebSocket connections"""
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context


@pytest.fixture
def websocket_server_info():
    """
    Fixture to pass information to the WebSocket server with a dynamic route suffix.
    """

    def _send_info(room_id: str, info: dict):
        # Construct the full URL with the room_id as a route suffix
        url = f"{WEBSOCKET_URL}{room_id}"
        # Send the information to the server
        response = requests.post(url, json=info)  # noqa: S113
        response.raise_for_status()
        return response.json()

    return _send_info
