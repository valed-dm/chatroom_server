import json
import time
from uuid import uuid4

from locust import HttpUser
from locust import User
from locust import between
from locust import events
from locust import task
from websocket import WebSocketTimeoutException
from websocket import create_connection


class WebSocketClient:
    def __init__(self, url, user_id, token):
        self.url = url
        self.user_id = user_id
        self.token = token
        self.ws = None

    def connect(self):
        self.ws = create_connection(self.url, header=self._get_headers())
        self._send_join_message()

    def _get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

    def _send_join_message(self):
        join_message = json.dumps({
            "type": "join",
            "userId": self.user_id,
            "username": self.user_id,
        })
        self.ws.send(join_message)

    def send_message(self, content):
        message = json.dumps({
            "type": "message",
            "userId": self.user_id,
            "username": self.user_id,
            "content": content,
            "timestamp": time.time(),
        })
        self.ws.send(message)

    def receive_message(self):
        try:
            response = self.ws.recv()
            return json.loads(response)
        except WebSocketTimeoutException:
            return None

    def close(self):
        if self.ws:
            self.ws.close()


class WebSocketUser(User):
    wait_time = between(1, 5)  # Simulate user think time between actions

    def on_start(self):
        self.user_id = f"user_{uuid4().hex}"
        self.room_id = f"room_{uuid4().hex}"
        self.client = WebSocketClient(
            url=f"wss://localhost:8765/ws/chatrooms/{self.room_id}",
            user_id=self.user_id,
            token=self.user_id,
        )
        self.client.connect()

    @task
    def send_and_receive(self):
        self.client.send_message(f"Hello to {self.room_id} from {self.user_id}")
        response = self.client.receive_message()
        if response:
            self._validate_response(response)

    @staticmethod
    def _validate_response(message):
        if message.get("type") in ["system", "message"]:
            timestamp = message.get("timestamp")
            if timestamp and (time.time() - timestamp) <= 5:  # noqa: PLR2004
                events.request_success.fire(
                    request_type="WebSocket",
                    name="receive_message",
                    response_time=0,
                    response_length=len(str(message)),
                )
            else:
                events.request_failure.fire(
                    request_type="WebSocket",
                    name="receive_message",
                    response_time=0,
                    response_length=0,
                    exception=Exception("Message delay threshold exceeded"),
                )

    def on_stop(self):
        self.client.close()


class WebsiteUser(HttpUser):
    tasks = [WebSocketUser]
    wait_time = between(1, 5)
