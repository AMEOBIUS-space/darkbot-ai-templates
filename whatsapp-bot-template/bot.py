#!/usr/bin/env python3
"""WhatsApp Bot Template — Baileys (no official API needed), message handling, groups, media."""
import asyncio, os, logging, json
from typing import Callable, Optional

logging.basicConfig(level=logging.INFO)

# Uses @whiskeysockets/baileys — Node.js library
# Python wrapper via subprocess or direct Node integration
# This template provides the Python orchestration layer

BOT_CONFIG = {
    "session_name": "darkbot-wa",
    "auto_reply": True,
    "welcome_message": "Hello! I'm DarkBot AI. How can I help you today?",
    "admin_numbers": [],  # Add admin phone numbers
    "blocked_numbers": [],
    "rate_limit": {"max_messages": 10, "per_seconds": 60},
}

class Message:
    """WhatsApp message representation."""
    def __init__(self, msg_id: str, sender: str, text: str, chat: str, is_group: bool = False):
        self.id = msg_id
        self.sender = sender  # phone number
        self.text = text
        self.chat = chat      # chat ID
        self.is_group = is_group
        self.timestamp = asyncio.get_event_loop().time()

class WhatsAppBot:
    """WhatsApp bot orchestration layer."""
    
    def __init__(self, config: dict = None):
        self.config = config or BOT_CONFIG
        self.handlers = {}
        self.rate_tracker = {}
        self.node_script = os.path.join(os.path.dirname(__file__), "wa_node.js")
    
    def command(self, cmd: str):
        """Register command handler."""
        def decorator(func: Callable):
            self.handlers[cmd.lower()] = func
            return func
        return decorator
    
    def on_message(self, func: Callable):
        """Register global message handler."""
        self.handlers["*"] = func
        return func
    
    def check_rate_limit(self, sender: str) -> bool:
        """Check if sender exceeded rate limit."""
        now = asyncio.get_event_loop().time()
        if sender not in self.rate_tracker:
            self.rate_tracker[sender] = []
        # Clean old entries
        self.rate_tracker[sender] = [t for t in self.rate_tracker[sender] if now - t < self.config["rate_limit"]["per_seconds"]]
        if len(self.rate_tracker[sender]) >= self.config["rate_limit"]["max_messages"]:
            return False
        self.rate_tracker[sender].append(now)
        return True
    
    async def process_message(self, msg: Message):
        """Process incoming message through handlers."""
        if msg.sender in self.config["blocked_numbers"]:
            return
        if not self.check_rate_limit(msg.sender):
            logging.warning(f"Rate limited: {msg.sender}")
            return
        
        text = msg.text.strip()
        # Check commands
        if text.startswith("/"):
            parts = text[1:].split(" ", 1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            if cmd in self.handlers:
                await self.handlers[cmd](msg, args)
                return
        
        # Global handler
        if "*" in self.handlers:
            await self.handlers["*"](msg)
    
    async def send_message(self, chat_id: str, text: str):
        """Send message via Node.js Baileys subprocess."""
        cmd = ["node", self.node_script, "send", chat_id, text]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logging.error(f"Send failed: {stderr.decode()}")
        return proc.returncode == 0
    
    async def send_media(self, chat_id: str, file_path: str, caption: str = ""):
        """Send media file."""
        cmd = ["node", self.node_script, "media", chat_id, file_path, caption]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        return proc.returncode == 0

# Example usage
bot = WhatsAppBot()

@bot.command("start")
async def start_handler(msg: Message, args: str):
    await bot.send_message(msg.chat, bot.config["welcome_message"])

@bot.command("help")
async def help_handler(msg: Message, args: str):
    await bot.send_message(msg.chat, "Commands: /start, /help, /info\nContact: @darkbot_ai_bot")

@bot.command("info")
async def info_handler(msg: Message, args: str):
    await bot.send_message(msg.chat, "DarkBot AI — WhatsApp bot template\nPayment: BTC/USDT/ETH/XMR")

@bot.on_message
async def default_handler(msg: Message):
    if not msg.text.startswith("/"):
        await bot.send_message(msg.chat, f"Echo: {msg.text}\n\nUse /help for commands")

async def main():
    # Demo: simulate incoming message
    msg = Message("msg1", "1234567890", "/help", "1234567890@s.whatsapp.net")
    await bot.process_message(msg)
    print("Bot template ready. Run wa_node.js for actual WhatsApp connection.")

if __name__ == "__main__":
    asyncio.run(main())
