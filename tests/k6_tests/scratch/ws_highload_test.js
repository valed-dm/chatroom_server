import http from "k6/http";
import ws from "k6/ws";
import {check, sleep} from "k6";
import {Trend, Counter} from "k6/metrics";

const BASE_HTTP_URL = "http://localhost:9090/chatrooms";
const BASE_WS_URL = "wss://localhost:8765/ws/chatrooms";
const VALID_TOKEN = "jwt_admin_token";

// Metrics
let successfulConnections = new Counter("successful_connections");
let failedConnections = new Counter("failed_connections");
let messagesSent = new Counter("messages_sent");
let messagesReceived = new Counter("messages_received");
let messageDelays = new Trend("message_delay_ms");

// Test Configuration
export const options = {
    scenarios: {
        create_rooms: {
            executor: "per-vu-iterations",
            vus: 1000, // Create 1000 rooms
            iterations: 1,
            startTime: "0s",
        },
        join_rooms: {
            executor: "ramping-vus",
            startVUs: 100,
            stages: [
                {duration: "10s", target: 1000}, // Ramp up to 1000 users
                {duration: "50s", target: 1000}, // Hold for testing
            ],
            startTime: "10s", // Start after room creation
        },
    },
};

// 1️⃣ **Setup: Create 1000 Rooms**
export function setup() {
    let headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${VALID_TOKEN}`,
    };
    let roomIds = [];

    for (let i = 0; i < 1000; i++) {
        let payload = JSON.stringify({
            "name": `room-${i}`,
            "description": `Load test room-${i}`,
        });

        let res = http.post(BASE_HTTP_URL, payload, {headers});
        check(res, {"Room created successfully": (r) => r.status === 201});

        let data = res.json();
        roomIds.push(data.id);
    }

    return {roomIds};
}

// 2️⃣ **Test Execution: Join Rooms & Send Messages**
export default function (data) {
    const userId = `${__VU}`;
    let room_id = data.roomIds[__VU % 1000]; // Distribute users across rooms
    let url = `${BASE_WS_URL}/${room_id}`;
    let params = {headers: {Authorization: `Bearer User_${userId}`}};

    let wsRes = ws.connect(url, params, function (socket) {
        if (!socket) {
            console.error(`❌ [User_${userId}] WebSocket connection failed`);
            failedConnections.add(1);
            return;
        }

        socket.on("open", function () {
            successfulConnections.add(1);
            socket.send(JSON.stringify({type: "join", userId, username: `User_${userId}`}));
        });

        socket.on("message", function (msg) {
            let receivedTime = Date.now();
            let parsedMsg = JSON.parse(msg);

            if (parsedMsg.type === "message") {
                let delay = receivedTime - parsedMsg.timestamp;
                messageDelays.add(delay);
                messagesReceived.add(1);

                if (delay > 5000) {
                    console.warn(`⚠️ High delay: ${delay}ms (User_${userId})`);
                }
            }
        });

        socket.on("error", function (e) {
            console.error(`🚨 Error: ${e.error()}`);
        });

        // Send messages periodically
        let interval = setInterval(() => {
            let message = {
                type: "message",
                userId: userId,
                username: `User_${userId}`,
                content: `Hello from User_${userId}`,
                timestamp: Date.now(),
            };
            socket.send(JSON.stringify(message));
            messagesSent.add(1);
        }, 2000);

        // Close WebSocket after 1 min
        socket.setTimeout(() => {
            clearInterval(interval);
            socket.close();
        }, 60 * 1000);
    });

    check(wsRes, {'Connected successfully': (r) => r && r.status === 101})
    sleep(1)
}
