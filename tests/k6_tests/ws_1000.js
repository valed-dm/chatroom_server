import http from "k6/http";
import ws from "k6/ws";
import {check, sleep} from "k6";
import {Counter} from "k6/metrics";

// Constants
const BASE_HTTP_URL = "http://localhost:9090/chatrooms";
const BASE_WS_URL = "wss://localhost:8765/ws/chatrooms";
const VALID_TOKEN = "jwt_admin_token";
const MESSAGE_DELAY_THRESHOLD = 1.5 * 1000;
const TOTAL_USERS = 1000
const TEST_DURATION = 30 * 1000

// Metrics
let successfulConnections = new Counter("successful_connections");
let successfullyClosed = new Counter("successfully_closed");
let systemMessageCounter = new Counter("system_msg_received");
let messageMessageCounter = new Counter("message_msg_received");


// Function to get headers
function getHeaders(userToken = VALID_TOKEN) {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${userToken}`,
    };
}

// Function to create chat room
export function setup() {
    let res = http.post(BASE_HTTP_URL, JSON.stringify({
        name: `Chat_${TOTAL_USERS}`,
        description: `Chat for ${TOTAL_USERS} users`,
        maxUsers: TOTAL_USERS,
    }), {headers: getHeaders()});

    check(res, {"Room created successfully": (r) => r.status === 201});
    let url = `${BASE_WS_URL}/${res.json().id}`;
    let users = Array.from({length: TOTAL_USERS}, (_, i) => `User_${i}`);
    return {url: url, users: users};
}

export const options = {
    vus: TOTAL_USERS,
    duration: TEST_DURATION,
};

// WebSocket chat test function
export default function (setupData) {
    // Assign a unique user to each VU
    const vuIndex = (__VU - 1) % setupData.users.length; // Ensure each VU gets a unique user
    const user = setupData.users[vuIndex]; // Pick the assigned user
    const url = setupData.url; // Common URL for all users

    // Each VU runs only for its assigned user
    let res = ws.connect(url, {headers: getHeaders(user)}, function (socket) {
        if (!socket) {
            console.warn(`❌ [${user}] WebSocket connection failed.`);
            return;
        }

        socket.on("open", () => {
            socket.send(JSON.stringify({type: "join", userId: user, username: user}));
            successfulConnections.add(1);
            // console.log(`✅ [${user}] joined chat!`);
            sleep(1);
        });

        socket.on("close", () => successfullyClosed.add(1));

        socket.on("message", (msg) => {
            try {
                const message = JSON.parse(msg);
                if (message.type === 'system') {
                    systemMessageCounter.add(1);

                    if (!message.timestamp || isNaN(new Date(message.timestamp).getTime())) {
                        console.error(`❌ [${user}] Invalid or missing timestamp in message:`, message);
                        return;
                    }
                    check(message, {
                        'System message received within threshold': (m) =>
                            new Date() - new Date(m.timestamp) <= MESSAGE_DELAY_THRESHOLD,
                    });
                }
                if (message.type === 'message') {
                    messageMessageCounter.add(1);

                    check(message, {
                        'Chat user message received within threshold': (m) =>
                            new Date() - new Date(m.timestamp) <= MESSAGE_DELAY_THRESHOLD,
                    });
                }
            } catch (error) {
                console.error(`❌ [${user}] Error parsing message: ${error.message}`);
            }
        });

        socket.on("error", (e) => console.warn(`🚨 Error: ${e.error()}`));

    });
    if (!res) {
        console.warn(`❌ [${user}] WebSocket connection failed.`);
    }
};
