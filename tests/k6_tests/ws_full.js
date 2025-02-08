import ws from "k6/ws";
import http from "k6/http";
import {check, sleep} from 'k6';
import {Counter} from "k6/metrics";

const BASE_WS_URL = "wss://localhost:8765/ws/chatrooms";
const API_HTTP_URL = "http://localhost:9090/chatrooms";
const TOTAL_ROOMS = 500;
const USERS_PER_ROOM = 50;
const VU_USERS = TOTAL_ROOMS * USERS_PER_ROOM + TOTAL_ROOMS;
const TEST_DURATION = 600 * 1000;
const MESSAGE_INTERVAL = TEST_DURATION / 2;
const MESSAGE_DELAY_THRESHOLD = 5 * 1000;
const VALID_TOKEN = "jwt_admin_token";

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


// ✅ Step 1: Create Rooms and Store Real IDs
export function setup() {
    const params = {headers: getHeaders()}
    let roomCreationPayloads = [];
    for (let i = 0; i < TOTAL_ROOMS; i++) {
        roomCreationPayloads.push({
            method: "POST",
            url: `${API_HTTP_URL}`,
            body: JSON.stringify({name: `Room_${i}`}),
            params: params,
        });
    }

    let responses = http.batch(roomCreationPayloads);
    let createdRooms = responses
        .filter(res => res.status === 201)
        .map(res => JSON.parse(res.body).id);

    console.log(`✅ Created ${createdRooms.length} rooms`);

    if (!Array.isArray(createdRooms) || createdRooms.length === 0) {
        throw new Error("❌ createdRooms is empty or undefined.");
    }

    // Initialize assignments
    let assignments = Object.fromEntries(createdRooms.map(room => [room, new Set()]));

    // Fisher-Yates shuffle function
    function shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }

    // Create a shuffled user list
    let shuffledUsers = shuffleArray(Array.from(
        {length: TOTAL_ROOMS * USERS_PER_ROOM},
        (_, i) => `user_${i}`
    ));

    for (let room of createdRooms) {
        while (assignments[room].size < USERS_PER_ROOM) {
            let randomUser = shuffledUsers[Math.floor(Math.random() * TOTAL_ROOMS * USERS_PER_ROOM)];

            if (!assignments[room].has(randomUser)) {
                assignments[room].add(randomUser);
            }
        }
    }

    // Convert sets to arrays
    let assignmentArray = Object.entries(assignments).map(([room, users]) => ({
        room,
        users: Array.from(users), // Convert Set to Array
    }));

    // Validate results
    const resultSizes = assignmentArray.map(({users}) => users.length);
    console.log(
        "Are all rooms correctly assigned?",
        `✅  ${resultSizes.every(size => size === USERS_PER_ROOM)}`
    );

    // return {rooms: createdRooms, assignments: assignmentArray};
    return {assignments: assignmentArray};
}

// ✅ Step 2: Define Test Execution & Join Rooms
export const options = {
    scenarios: {
        join_rooms: {
            executor: 'ramping-arrival-rate',
            startRate: 100,
            timeUnit: '1s',
            preAllocatedVUs: VU_USERS,
            maxVUs: VU_USERS,
            stages: [
                {duration: TEST_DURATION, target: VU_USERS},
            ],
            gracefulStop: '120s',
        },
    },
};

export default function (setupData) {
    // Access the pre-assigned room assignments from setup
    const roomAssignments = setupData.assignments;
    if (!roomAssignments || roomAssignments.length === 0) {
        console.error("❌ Room assignments are empty or not initialized!");
        return;
    }

    // Calculate the total number of users across all rooms
    const totalUsers = roomAssignments.reduce((sum, {users}) => sum + users.length, 0);

    // Determine the index for the current VU
    const vuIndex = (__VU - 1) % totalUsers;

    // Find the room and user for the current VU
    let userIndex = vuIndex;
    let room, user;
    for (const assignment of roomAssignments) {
        if (userIndex < assignment.users.length) {
            room = assignment.room;
            user = assignment.users[userIndex];
            break;
        }
        userIndex -= assignment.users.length;
    }

    if (!room || !user) {
        console.error(`❌ Invalid assignment data - Room: ${room}, User: ${user}`);
        return;
    }

    console.log(`[VU ${__VU}] Assigned to room: ${room}, user: ${user}`);

    const wsUrl = `${BASE_WS_URL}/${room}`;
    const params = {headers: getHeaders(user)};

    let res = ws.connect(wsUrl, params, function (socket) {
        if (!socket) {
            console.warn(`❌ [${user}] WebSocket connection failed.`);
            return;
        }

        socket.on('open', function () {
            socket.send(JSON.stringify({type: 'join', userId: user, username: user}));
            successfulConnections.add(1);
            console.log(`✅ [${user}] joined room: ${room}`);
            sleep(1);

            // Periodically send messages
            const sendMessage = () => {
                if (socket.readyState === socket.OPEN) {
                    socket.send(JSON.stringify({
                        type: 'message',
                        userId: user,
                        username: user,
                        content: `Hello to ${room} from ${user}`,
                        timestamp: new Date(),
                    }));
                    console.log(`User ${user} sent a message to room ${room}`);
                } else {
                    console.error(`❌ [${user}] Socket not open, cannot send message`);
                }
            };

            // Send messages at regular intervals
            const messageInterval = setInterval(sendMessage, MESSAGE_INTERVAL);

            // Clear interval on socket close
            socket.on('close', () => {
                clearInterval(messageInterval);
                console.log(`[${user}] Stopped message interval for room: ${room} on close`);
            });
            socket.on('error', () => {
                clearInterval(messageInterval);
                console.log(`[${user}] Stopped message interval for room: ${room} on error`);
            });
        });

        socket.on('message', function (msg) {
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

        socket.on('close', function () {
            successfullyClosed.add(1)
            console.log(`❌ [${user}] disconnected from room: ${room}`);
        });

        socket.on('error', function (error) {
            console.error(`❌ [${user}] WebSocket error: ${error.message}`);
        });

        setTimeout(() => {
            successfullyClosed.add(1);
            socket.close();
        }, TEST_DURATION - 1);
    });

    if (!res) {
        console.warn(`❌ [${user}] WebSocket connection failed.`);
    }
}
