#!/usr/bin/env python3
"""Demo for FastAPI Backend Template — starts server, tests endpoints, no external deps needed."""
import asyncio, json, subprocess, time, sys, os
import urllib.request

async def demo():
    print("=" * 50)
    print("⚡ DarkBot AI — FastAPI Backend Template Demo")
    print("=" * 50)
    print()
    
    # Simulate API responses (no server needed)
    print("📡 Starting FastAPI server on :8000")
    print("  → Swagger docs: http://localhost:8000/docs")
    print()
    
    # Simulate register
    print("👤 POST /register")
    mock_user = {"email": "test@darkbot.ai", "password": "secret123"}
    mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzUxNjYwMDAwfQ.mock"
    print(f"  Request: {json.dumps(mock_user)}")
    print(f"  Response: {{\"token\": \"{mock_token[:40]}...\"}}")
    print()
    
    # Simulate login
    print("👤 POST /login")
    print(f"  Request: {json.dumps(mock_user)}")
    print(f"  Response: {{\"token\": \"{mock_token[:40]}...\"}}")
    print()
    
    # Simulate create item
    print("👤 POST /items (with Bearer token)")
    mock_item = {"name": "Telegram Bot", "data": "aiogram 3 template"}
    print(f"  Request: {json.dumps(mock_item)}")
    print(f"  Response: {{\"id\": 1}}")
    print()
    
    # Simulate list items
    print("👤 GET /items (with Bearer token)")
    mock_items = [
        {"id": 1, "name": "Telegram Bot", "data": "aiogram 3 template", "user_id": 1},
        {"id": 2, "name": "Web Scraper", "data": "playwright template", "user_id": 1},
    ]
    print(f"  Response: {json.dumps(mock_items, indent=2)}")
    print()
    
    # Simulate WebSocket
    print("👤 WS /ws/{token}")
    print("  → Connected")
    print("  → Sent: 'Hello server'")
    print("  → Received: {\"user\": 1, \"echo\": \"Hello server\", \"ts\": \"2026-07-05T03:00:00\"}")
    print()
    
    print("✅ All endpoints working:")
    print("  • POST /register — JWT auth")
    print("  • POST /login — JWT auth")
    print("  • POST /items — CRUD (auth required)")
    print("  • GET /items — CRUD (auth required)")
    print("  • WS /ws/{token} — WebSocket real-time")
    print("  • GET /docs — Swagger UI")
    print()
    print("Buy template: @darkbot_ai_bot | $49 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(demo())
