// wa_node.js — Baileys WhatsApp connection layer
// npm install @whiskeysockets/baileys
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const fs = require('fs');

async function connectWA() {
    const { state, saveCreds } = await useMultiFileAuthState('auth-session');
    const sock = makeWASocket({ auth: state, printQRInTerminal: true });
    sock.ev.on('creds.update', saveCreds);
    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect } = update;
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error instanceof Boom)
                ?.output?.statusCode !== DisconnectReason.loggedOut;
            if (shouldReconnect) connectWA();
        }
    });
    sock.ev.on('messages.upsert', async ({ messages }) => {
        for (const msg of messages) {
            if (!msg.key.fromMe && msg.message?.conversation) {
                const text = msg.message.conversation;
                const sender = msg.key.remoteJid;
                console.log(JSON.stringify({ id: msg.key.id, sender, text, chat: sender }));
            }
        }
    });
    // CLI mode: send message
    if (process.argv[2] === 'send') {
        const [,, cmd, chatId, ...rest] = process.argv;
        await sock.sendMessage(chatId, { text: rest.join(' ') });
        process.exit(0);
    }
}

connectWA();
