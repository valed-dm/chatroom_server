import json
import random
import ssl
import time
from datetime import datetime
from threading import Thread

import requests
from locust import HttpUser
from locust import between
from locust import events
from locust import task
from websocket import create_connection

from utils.http_status import HTTPStatus

# Constants
BASE_WS_URL = "wss://localhost:8765/ws/chatrooms"
API_HTTP_URL = "http://localhost:9090/chatrooms"
TOTAL_USERS = 10000
TOTAL_ROOMS = 1000
USERS_PER_ROOM = 100
MESSAGE_INTERVAL = 30  # in seconds
MESSAGE_DELAY_THRESHOLD = 5  # in seconds
VALID_TOKEN = "jwt_admin_token"  # noqa: S105

# Global setup data
assignments = []


# Function to get headers
def get_headers(user_token=VALID_TOKEN):
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user_token}",
    }


# Fisher-Yates shuffle function
def shuffle_array(array):
    for i in range(len(array) - 1, 0, -1):
        j = random.randint(0, i)  # noqa: S311
        array[i], array[j] = array[j], array[i]
    return array


# Step 1: Create Rooms and Assign Users
def setup_rooms():
    global assignments  # noqa: PLW0603
    headers = get_headers()

    # Create rooms
    created_rooms = []
    for i in range(TOTAL_ROOMS):
        payload = {"name": f"Room_{i}"}
        response = requests.post(API_HTTP_URL, json=payload, headers=headers)  # noqa: S113
        if response.status_code == HTTPStatus.CREATED.value:
            created_rooms.append(response.json()["id"])

    print(f"✅ Created {len(created_rooms)} rooms")

    if not created_rooms:
        raise Exception("❌ createdRooms is empty or undefined.")

    # Initialize assignments
    assignments = {room: set() for room in created_rooms}

    # Create a shuffled user list
    shuffled_users = shuffle_array([f"user_{i}" for i in range(TOTAL_USERS)])

    # Assign users to rooms
    for room in created_rooms:
        while len(assignments[room]) < USERS_PER_ROOM:
            random_user = random.choice(shuffled_users)  # noqa: S311
            if random_user not in assignments[room]:
                assignments[room].add(random_user)

    # Convert sets to lists
    assignments = [
        {"room": room, "users": list(users)} for room, users in assignments.items()
    ]

    # Validate results
    result_sizes = [len(assignment["users"]) for assignment in assignments]
    print(
        "Are all rooms correctly assigned?",
        f"✅  {all(size == USERS_PER_ROOM for size in result_sizes)}",
    )


# Step 2: Define Test Execution & Join Rooms
class ChatroomUser(HttpUser):
    wait_time = between(1, 1)  # Simulate user think time

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_assignment = None
        self.room = None
        self.user = None
        self.ws_url = None
        self.headers = None
        self.socket = None
        self.message_thread = None

    def on_start(self):
        try:
            self.room_assignment = random.choice(assignments)  # noqa: S311
            self.room = self.room_assignment["room"]
            self.user = random.choice(self.room_assignment["users"])  # noqa: S311
            self.ws_url = f"{BASE_WS_URL}/{self.room}"
            self.headers = get_headers(self.user)

            print(f"🔄 [{self.user}] Connecting to {self.ws_url}")

            # Connect to WebSocket
            self.socket = create_connection(
                self.ws_url,
                header=self.headers,
                sslopt={"cert_reqs": ssl.CERT_NONE},
            )
            self.socket.send(
                json.dumps(
                    {"type": "join", "userId": self.user, "username": self.user},
                ),
            )
            print(f"✅ [{self.user}] joined room: {self.room_assignment['room']}")

            # Start sending messages periodically
            self.message_thread = Thread(target=self.send_messages)
            self.message_thread.daemon = True
            self.message_thread.start()

        except Exception as e:
            print(f"❌ Error in on_start for {self.user}: {e}")
            self.socket = None  # Ensure self.socket exists, even if connection fails

    def send_messages(self):
        while True:
            time.sleep(MESSAGE_INTERVAL)
            if self.socket and self.socket.connected:
                self.socket.send(json.dumps({
                    "type": "message",
                    "userId": self.user,
                    "username": self.user,
                    "content": f"Hello to {self.room} from {self.user}",
                    "timestamp": time.time(),
                }))
                print(f"User {self.user} sent a message to room {self.room}")

    @task
    def receive_messages(self):
        if not self.socket:
            print(f"⚠️ [{self.user}] No socket connection, skipping message receive")
            return
        try:
            message = self.socket.recv()
            message = json.loads(message)
            if message["type"] in ["system", "message"]:
                timestamp_dt = datetime.fromisoformat(message["timestamp"].replace("Z", "+00:00"))
                timestamp_float = timestamp_dt.timestamp()
                delay = time.time() - timestamp_float
                if delay > MESSAGE_DELAY_THRESHOLD:
                    print(f"❌ [{self.user}] Message delay exceeded threshold: {delay}")
        except Exception as e:
            print(f"❌ [{self.user}] Error receiving message: {e}")

    def on_stop(self):
        if self.socket:
            self.socket.close()
        print(f"❌ [{self.user}] disconnected from room: {self.room_assignment['room']}")


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    setup_rooms()
