import {check, sleep} from 'k6';
import ws from 'k6/ws';
import {SharedArray} from 'k6/data';

const BASE_URL = 'wss://localhost:8765/ws/chatrooms';
const ROOMS = 1000;
const USERS = 5000;
const USERS_PER_ROOM = 100;
const MESSAGE_DELAY_THRESHOLD = 5000; // in ms
const VALID_TOKEN =  "JWT_ADMIN_TOKEN";

// Generate unique users
const users = new SharedArray('users', function () {
    return Array.from({length: USERS}, (_, i) => `user_${i}`);
});

// Generate unique rooms
const rooms = new SharedArray('rooms', function () {
    return Array.from({length: ROOMS}, (_, i) => `room_${i}`);
});

// export const options = {
//     vus: VUS,
//     duration: TIMEOUT_MS,
// };

export const options = {
    vus: USERS,
    duration: '1m30s',
};

// Function to get headers
function getHeaders(userToken = VALID_TOKEN) {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${userToken}`,
    };
}

export default function () {
    const userId = users[__VU % USERS];
    let params = {headers: getHeaders(`${userId}`)};

    const url = `${BASE_URL}/connect`;

    const res = ws.connect(url, params, function (socket) {
        socket.on('open', function open() {});

        socket.on('message', function (msg) {
            const message = JSON.parse(msg);
            console.log(message)
            if (message.type === 'system') {
                check(message, {
                    'Message received within threshold': (m) => new Date() - new Date(m.timestamp) <= MESSAGE_DELAY_THRESHOLD,
                });
            }
        });

        socket.on('close', () => {
            console.log(`User ${userId} disconnected.`);
        });
    });
}
