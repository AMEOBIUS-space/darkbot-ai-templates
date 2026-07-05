import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from bot import Embed, Button, Modal, SlashCommand, DiscordBot


def test_embed_basic():
    embed = Embed(title="Test", description="Hello")
    d = embed.to_dict()
    assert d["title"] == "Test"
    assert d["description"] == "Hello"


def test_embed_add_field():
    embed = Embed(title="Test")
    embed.add_field("Name", "Value", inline=True)
    d = embed.to_dict()
    assert len(d["fields"]) == 1
    assert d["fields"][0]["name"] == "Name"
    assert d["fields"][0]["inline"] is True


def test_embed_footer_thumbnail():
    embed = Embed(title="T", footer="Page 1", thumbnail="https://img.com/t.png")
    d = embed.to_dict()
    assert d["footer"]["text"] == "Page 1"
    assert d["thumbnail"]["url"] == "https://img.com/t.png"


def test_button_basic():
    btn = Button(custom_id="click_1", label="Click Me")
    d = btn.to_dict()
    assert d["type"] == 2
    assert d["custom_id"] == "click_1"
    assert d["style"] == 1


def test_button_disabled():
    btn = Button(custom_id="b", label="B", disabled=True)
    assert btn.to_dict()["disabled"] is True


def test_modal_text_input():
    modal = Modal(custom_id="my_modal", title="Form")
    modal.add_text_input("name", "Your Name", placeholder="Enter name")
    d = modal.to_dict()
    assert d["custom_id"] == "my_modal"
    assert len(d["components"][0]["components"]) == 1


def test_slash_command_string_option():
    cmd = SlashCommand("greet", "Greet someone")
    cmd.add_string_option("name", "Name to greet")
    d = cmd.to_dict()
    assert d["name"] == "greet"
    assert d["options"][0]["type"] == 3
    assert d["options"][0]["required"] is True


def test_slash_command_user_option():
    cmd = SlashCommand("ban", "Ban user")
    cmd.add_user_option("user", "User to ban")
    assert cmd.to_dict()["options"][0]["type"] == 6


def test_bot_register_commands():
    bot = DiscordBot(token="test")
    cmd = SlashCommand("ping", "Ping pong")
    bot.command(cmd)
    payload = bot.register_commands_payload()
    assert len(payload) == 1
    assert payload[0]["name"] == "ping"


def test_bot_interaction_response_embed():
    bot = DiscordBot()
    embed = Embed(title="Welcome", description="Hello!")
    btn = Button(custom_id="start", label="Start", style=3)
    response = bot.interaction_response_embed(embed, [btn])
    assert response["type"] == 4
    assert len(response["data"]["embeds"]) == 1
    assert len(response["data"]["components"]) == 1


def test_bot_interaction_response_modal():
    bot = DiscordBot()
    modal = Modal(custom_id="form", title="Submit")
    response = bot.interaction_response_modal(modal)
    assert response["type"] == 9
    assert response["data"]["custom_id"] == "form"
