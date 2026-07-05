# Example: Freelance TG Bot for a Client

## Scenario
Client wants a Telegram bot for their online store. They need:
- Product catalog (inline keyboards)
- Order placement
- AI customer support
- Payment integration (crypto)

## Solution
1. Buy TG Bot Template ($49) or Bundle ($199)
2. Customize `bot.py`:
   - Add product catalog handler
   - Add order FSM state machine
   - Add OpenAI for customer Q&A
   - Add Crypto Payment Gateway template for checkout
3. Deploy with Docker: `docker-compose up -d`

## Time: 4-6 hours (with template) vs 20-30 hours (from scratch)
## Cost: $49 (template) + your time vs $0 + 30h from scratch

## Result
```python
# bot.py — customized
@router.message(Command("catalog"))
async def catalog(msg: Message, state: FSMContext):
    products = get_products()
    kb = InlineKeyboardBuilder()
    for p in products:
        kb.button(text=f"{p.name} — {p.price}$", callback_data=f"buy_{p.id}")
    await msg.answer("📦 Catalog:", reply_markup=kb.as_markup())
```

Contact: @darkbot_ai_bot | BTC/USDT/ETH/XMR
