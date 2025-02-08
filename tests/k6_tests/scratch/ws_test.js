// import ws from "k6/ws";
// import http from "k6/http";
// import {check, sleep} from 'k6';
//
// const BASE_WS_URL = "wss://localhost:8765/ws/chatrooms";
// const API_HTTP_URL = "http://localhost:9090/chatrooms";
// const TOTAL_USERS = 10000;
// const TOTAL_ROOMS = 100;
// const USERS_PER_ROOM = 100;
// const MESSAGE_INTERVAL = 10000;
// const MESSAGE_DELAY_THRESHOLD = 5000;
// const VALID_TOKEN = "jwt_admin_token";
//
//
// // Function to get headers
// function getHeaders(userToken = VALID_TOKEN) {
//     return {
//         "Content-Type": "application/json",
//         "Authorization": `Bearer ${userToken}`,
//     };
// }
//
//
// // ✅ Step 1: Create Rooms and Store Real IDs
// export function setup() {
//     const params = {headers: getHeaders()}
//     let roomCreationPayloads = [];
//     for (let i = 0; i < TOTAL_ROOMS; i++) {
//         roomCreationPayloads.push({
//             method: "POST",
//             url: `${API_HTTP_URL}`,
//             body: JSON.stringify({name: `Room_${i}`}),
//             params: params,
//         });
//     }
//
//     let responses = http.batch(roomCreationPayloads);
//     let createdRooms = responses
//         .filter(res => res.status === 201)
//         .map(res => JSON.parse(res.body).id);
//
//     console.log(`✅ Created ${createdRooms.length} rooms`);
//
//     if (!Array.isArray(createdRooms) || createdRooms.length === 0) {
//         throw new Error("❌ createdRooms is empty or undefined.");
//     }
//
//     // Initialize assignments
//     let assignments = Object.fromEntries(createdRooms.map(room => [room, new Set()]));
//
//     // Fisher-Yates shuffle function
//     function shuffleArray(array) {
//         for (let i = array.length - 1; i > 0; i--) {
//             const j = Math.floor(Math.random() * (i + 1));
//             [array[i], array[j]] = [array[j], array[i]];
//         }
//         return array;
//     }
//
//     // Create a shuffled user list
//     let shuffledUsers = shuffleArray(Array.from(
//         {length: TOTAL_USERS},
//         (_, i) => `user_${i}`
//     ));
//
//     for (let room of createdRooms) {
//         while (assignments[room].size < USERS_PER_ROOM) {
//             let randomUser = shuffledUsers[Math.floor(Math.random() * TOTAL_USERS)];
//
//             if (!assignments[room].has(randomUser)) {
//                 assignments[room].add(randomUser);
//             }
//         }
//     }
//
//     // Convert sets to arrays
//     let assignmentArray = Object.entries(assignments).map(([room, users]) => ({
//         room,
//         users: Array.from(users), // Convert Set to Array
//     }));
//
//     // Validate results
//     const resultSizes = assignmentArray.map(({users}) => users.length);
//     console.log(
//         "Are all rooms correctly assigned?",
//         `✅  ${resultSizes.every(size => size === USERS_PER_ROOM)}`
//     );
//
//     // return {rooms: createdRooms, assignments: assignmentArray};
//     return {assignments: assignmentArray};
// }
//
// // ✅ Step 2: Define Test Execution & Join Rooms
// export const options = {
//     scenarios: {
//         join_rooms: {
//             executor: 'ramping-arrival-rate',
//             startRate: 100,
//             timeUnit: '1s',
//             preAllocatedVUs: 500,
//             stages: [
//                 {duration: '10s', target: 1000},
//                 {duration: '50s', target: 1000},
//             ],
//             gracefulStop: '30s',
//         },
//     },
// };
//
// export default function (setupData) {
//     // Access the pre-assigned room assignments from setup
//     const roomAssignments = setupData.assignments;
//     if (!roomAssignments || roomAssignments.length === 0) {
//         console.error("❌ Room assignments are empty or not initialized!");
//         return;
//     }
//
//     // Randomly select a room assignment for the VU
//     const assignment = roomAssignments[Math.floor(Math.random() * roomAssignments.length)];
//     const {room, users} = assignment;
//
//     // Each VU will handle a subset of users in the selected room
//     const user = users[__VU % users.length];
//     const wsUrl = `${BASE_WS_URL}/${room}`;
//     const params = getHeaders(user);
//
//     const res = ws.connect(wsUrl, params, function (socket) {
//         socket.on('open', function () {
//             console.log(`✅ [${user}] joined room: ${room}`);
//             socket.send(JSON.stringify({type: 'join', userId: user, username: user}));
//
//             // Periodically send messages
//             const sendMessage = () => {
//                 if (socket.readyState === socket.OPEN) {
//                     socket.send(JSON.stringify({
//                         type: 'message',
//                         userId: user,
//                         username: user,
//                         content: `Hello to ${room} from ${user}`,
//                         timestamp: new Date(),
//                     }));
//                     console.log(`User ${user} sent a message to room ${room}`);
//                 }
//             };
//
//             // Send messages at regular intervals
//             const messageInterval = setInterval(sendMessage, MESSAGE_INTERVAL);
//
//             // Clear interval on socket close
//             socket.on('close', () => clearInterval(messageInterval));
//         });
//
//         socket.on('message', function (msg) {
//             try {
//                 const message = JSON.parse(msg);
//                 if (message.type === 'system') {
//                     if (!message.timestamp || isNaN(new Date(message.timestamp).getTime())) {
//                         console.error(`❌ [${user}] Invalid or missing timestamp in message:`, message);
//                         return;
//                     }
//                     check(message, {
//                         'System message received within threshold': (m) =>
//                             new Date() - new Date(m.timestamp) <= MESSAGE_DELAY_THRESHOLD,
//                     });
//                 }
//                 if (message.type === 'message') {
//                     check(message, {
//                         'Chat user message received within threshold': (m) =>
//                             new Date() - new Date(m.timestamp) <= MESSAGE_DELAY_THRESHOLD,
//                     });
//                 }
//             } catch (error) {
//                 console.error(`❌ [${user}] Error parsing message: ${error.message}`);
//             }
//         });
//
//         socket.on('close', function () {
//             console.log(`❌ [${user}] disconnected from room: ${room}`);
//         });
//
//         socket.on('error', function (error) {
//             console.error(`❌ [${user}] WebSocket error: ${error.message}`);
//         });
//     });
//
//     if (!res) {
//         console.error(`❌ [${user}] Failed to connect to room: ${room}`);
//     }
//
//     sleep(1); // Simulate user think time
// }
