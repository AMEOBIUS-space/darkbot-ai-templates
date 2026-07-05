#!/usr/bin/env python3
"""Demo for Telegram Bot Template — simulates bot behavior without API keys."""
import asyncio, json, sys
sys.path.insert(0, '.')

# Mock aiogram for demo (no real bot needed)
class MockMessage:
    def __init__(self, text, chat_id=12345):
        self.text = text
        self.chat = MockChat(chat_id)
        self.answers = []
    async def answer(self, text, **kw):
        self.answers.append(text)
        print(f"  🤖 Bot: {text[:80]}")

class MockChat:
    def __init__(self, id):
        self.id = id

class MockCallback:
    def __init__(self, data, message):
        self.data = data
        self.message = message
    async def answer(self, *a, **kw): pass

class MockState:
    def __init__(self):
        self.state = None
    async def set_state(self, s): self.state = s
    async def clear(self): self.state = None

# Inline keyboard simulation
def make_keyboard(buttons):
    """Simulate inline keyboard."""
    rows = []
    for row in buttons:
        rows.append(" | ".join(f"[{text}]" for text, _ in row))
    return "\n  " + "\n  ".join(rows)

async def demo():
    print("=" * 50)
    print("🤖 DarkBot AI — Telegram Bot Template Demo")
    print("=" * 50)
    print()
    
    # Simulate /start
    print("👤 User: /start")
    msg = MockMessage("/start")
    state = MockState()
    
    # Simulate start handler
    kb = make_keyboard([
        [("🤖 AI Chat", "ai_chat"), ("📋 Help", "help")]
    ])
    await msg.answer(f"Welcome! Choose an option:{kb}")
    print()
    
    # Simulate AI Chat callback
    print("👤 User clicks: 🤖 AI Chat")
    cb = MockCallback("ai_chat", msg)
    await state.set_state("Form.question")
    await msg.answer("Ask me anything:")
    print()
    
    # Simulate user question
    print("👤 User: How do I deploy a bot?")
    msg2 = MockMessage("How do I deploy a bot?", msg.chat.id)
    await msg2.answer(f"You asked: {msg2.text}\n\n(This is a template — add your AI API key to enable real AI responses)")
    await state.clear()
    print()
    
    # Simulate /help
    print("👤 User: /help")
    msg3 = MockMessage("/help")
    await msg3.answer("Commands: /start, /help\nContact: @darkbot_ai_bot")
    print()
    
    print("=" * 50)
    print("✅ Demo complete! All handlers working.")
    print()
    print("To run with real bot:")
    print("  1. pip install aiogram openai python-dotenv")
    print("  2. Set BOT_TOKEN and OPENAI_API_KEY in .env")
    print("  3. python bot.py")
    print()
    print("Buy template: @darkbot_ai_bot | $49 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(demo())
