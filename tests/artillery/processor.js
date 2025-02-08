// const http = require('http');
// const WebSocket = require('ws');
// const TOTAL_USERS = 10000;
// const TOTAL_ROOMS = 1000;
// const USERS_PER_ROOM = 100;
// const MESSAGE_INTERVAL = 30000;
// const MESSAGE_DELAY_THRESHOLD = 5000;
// const VALID_TOKEN = "jwt_admin_token";
//
// function getHeaders(userToken = VALID_TOKEN) {
//     return {
//         "Content-Type": "application/json",
//         "Authorization": `Bearer ${userToken}`,
//     };
// }
//
// module.exports = {setup, joinRoomAndSendMessages};
//
// async function setup(context, events, done) {
//     const params = {headers: getHeaders()};
//     let roomCreationPayloads = [];
//     for (let i = 0; i < TOTAL_ROOMS; i++) {
//         roomCreationPayloads.push({
//             method: "POST",
//             url: `${context.vars.target}/chatrooms`,
//             body: JSON.stringify({name: `Room_${i}`}),
//             headers: params.headers,
//         });
//     }
//
//     let responses = await Promise.all(roomCreationPayloads.map(payload => httpRequest(payload)));
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
//     let assignments = Object.fromEntries(createdRooms.map(room => [room, new Set()]));
//     let shuffledUsers = shuffleArray(Array.from({length: TOTAL_USERS}, (_, i) => `user_${i}`));
//
//     for (let room of createdRooms) {
//         while (assignments[room].size < USERS_PER_ROOM) {
//             let randomUser = shuffledUsers[Math.floor(Math.random() * TOTAL_USERS)];
//             if (!assignments[room].has(randomUser)) {
//                 assignments[room].add(randomUser);
//             }
//         }
//     }
//
//     let assignmentArray = Object.entries(assignments).map(([room, users]) => ({
//         room,
//         users: Array.from(users),
//     }));
//
//     context.vars.assignments = assignmentArray;
//     done();
// }
//
// function joinRoomAndSendMessages(context, events, done) {
//     const roomAssignments = context.vars.assignments;
//     if (!roomAssignments || roomAssignments.length === 0) {
//         console.error("❌ Room assignments are empty or not initialized!");
//         return done();
//     }
//
//     const vuIndex = (context._uid - 1) % roomAssignments.length;
//     const {room, users} = roomAssignments[vuIndex];
//
//     if (!room || !Array.isArray(users) || users.length === 0) {
//         console.error(`❌ Invalid assignment data - Room: ${room}, Users: ${users}`);
//         return done();
//     }
//
//     users.forEach((user) => {
//         const wsUrl = `${context.vars.ws.baseUrl}/${room}`;
//         const socket = new WebSocket(wsUrl, {headers: getHeaders(user)});
//
//         socket.on('open', function () {
//             console.log(`✅ [${user}] joined room: ${room}`);
//             socket.send(JSON.stringify({type: 'join', userId: user, username: user}));
//
//             const sendMessage = () => {
//                 if (socket.readyState === WebSocket.OPEN) {
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
//             const messageInterval = setInterval(sendMessage, MESSAGE_INTERVAL);
//             socket.on('close', () => clearInterval(messageInterval));
//         });
//
//         socket.on('message', function (msg) {
//             try {
//                 const message = JSON.parse(msg);
//                 if (message.type === 'system' || message.type === 'message') {
//                     const delay = new Date() - new Date(message.timestamp);
//                     if (delay > MESSAGE_DELAY_THRESHOLD) {
//                         console.error(`❌ [${user}] Message delay exceeded threshold: ${delay}ms`);
//                     }
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
//     done();
// }
//
// function shuffleArray(array) {
//     for (let i = array.length - 1; i > 0; i--) {
//         const j = Math.floor(Math.random() * (i + 1));
//         [array[i], array[j]] = [array[j], array[i]];
//     }
//     return array;
// }
//
// function httpRequest(options) {
//     return new Promise((resolve, reject) => {
//         const req = http.request(options, (res) => {
//             let data = '';
//             res.on('data', (chunk) => data += chunk);
//             res.on('end', () => resolve({status: res.statusCode, body: data}));
//         });
//         req.on('error', reject);
//         req.write(options.body || '');
//         req.end();
//     });
// }
