#!/usr/bin/env python3
"""AI-Powered Telegram Bot Template — production ready."""
import asyncio, logging, os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    name = State()
    question = State()

@dp.message(Command("start"))
async def start(msg: Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 AI Chat", callback_data="ai_chat"),
         InlineKeyboardButton(text="📋 Help", callback_data="help")]
    ])
    await msg.answer("Welcome! Choose an option:", reply_markup=kb)

@dp.callback_query(F.data == "ai_chat")
async def ai_chat(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.question)
    await cb.message.answer("Ask me anything:")

@dp.message(Form.question)
async def answer(msg: Message, state: FSMContext):
    # Replace with OpenAI/Claude API call
    await msg.answer(f"You asked: {msg.text}\n\n(This is a template — add your AI API key)")
    await state.clear()

@dp.callback_query(F.data == "help")
async def help_cb(cb: CallbackQuery):
    await cb.message.answer("Commands: /start, /help\nContact: @darkbot_ai_bot")

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
