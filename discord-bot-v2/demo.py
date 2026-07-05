#!/usr/bin/env python3
"""Demo: Discord Bot v2 — slash commands, buttons, modals, embeds."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from bot import DiscordBot, SlashCommand, Embed, Button, Modal

bot = DiscordBot(token="BOT_TOKEN", application_id="APP_ID")

# Register slash command
cmd = SlashCommand("ticket", "Create a support ticket")
cmd.add_string_option("subject", "Ticket subject", required=True)
cmd.add_string_option("description", "Describe your issue", required=True)
bot.command(cmd)

# Build embed
embed = Embed(title="Support Ticket", description="Click below to create a ticket", color=0x5865F2)
embed.add_field("Status", "Open", inline=True)
embed.add_field("Priority", "Normal", inline=True)
embed.footer = "DarkBot AI | BTC/USDT/ETH/XMR"

# Build buttons
btn_create = Button(custom_id="ticket_create", label="Create Ticket", style=3, emoji="🎫")
btn_close = Button(custom_id="ticket_close", label="Close", style=4, emoji="❌")

# Build modal
modal = Modal(custom_id="ticket_form", title="Create Support Ticket")
modal.add_text_input("subject", "Subject", placeholder="Brief description", required=True, max_length=100)
modal.add_text_input("description", "Description", style=2, placeholder="Detailed description", required=True, max_length=2000)

print("=== Slash Commands ===")
print(json.dumps(bot.register_commands_payload(), indent=2))

print("\n=== Embed + Buttons Response ===")
response = bot.interaction_response_embed(embed, [btn_create, btn_close])
print(json.dumps(response, indent=2)[:400])

print("\n=== Modal Response ===")
modal_resp = bot.interaction_response_modal(modal)
print(json.dumps(modal_resp, indent=2)[:300])
