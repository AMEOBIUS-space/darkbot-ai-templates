"""Discord Bot Template v2 — slash commands, buttons, modals, embeds."""
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Embed:
    """Discord embed builder."""
    title: str = ""
    description: str = ""
    color: int = 0x00ff00
    fields: List[Dict] = None
    footer: str = ""
    thumbnail: str = ""
    timestamp: str = ""

    def __post_init__(self):
        self.fields = self.fields or []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def add_field(self, name: str, value: str, inline: bool = False):
        self.fields.append({"name": name, "value": value, "inline": inline})
        return self

    def to_dict(self) -> Dict:
        d = {"title": self.title, "description": self.description, "color": self.color, "fields": self.fields}
        if self.footer:
            d["footer"] = {"text": self.footer}
        if self.thumbnail:
            d["thumbnail"] = {"url": self.thumbnail}
        if self.timestamp:
            d["timestamp"] = self.timestamp
        return d


@dataclass
class Button:
    """Discord button component."""
    custom_id: str
    label: str
    style: int = 1  # 1=Primary, 2=Secondary, 3=Success, 4=Danger, 5=Link
    emoji: str = ""
    disabled: bool = False

    def to_dict(self) -> Dict:
        d = {"type": 2, "custom_id": self.custom_id, "label": self.label, "style": self.style}
        if self.emoji:
            d["emoji"] = {"name": self.emoji}
        if self.disabled:
            d["disabled"] = True
        return d


@dataclass
class Modal:
    """Discord modal dialog."""
    custom_id: str
    title: str
    components: List[Dict] = None

    def __post_init__(self):
        self.components = self.components or []

    def add_text_input(self, custom_id: str, label: str, style: int = 1,
                       placeholder: str = "", required: bool = True, min_length: int = 0, max_length: int = 4000):
        self.components.append({
            "type": 4,
            "custom_id": custom_id,
            "label": label,
            "style": style,
            "placeholder": placeholder,
            "required": required,
            "min_length": min_length,
            "max_length": max_length,
        })
        return self

    def to_dict(self) -> Dict:
        return {
            "custom_id": self.custom_id,
            "title": self.title,
            "components": [{"type": 1, "components": self.components}],
        }


class SlashCommand:
    """Discord slash command builder."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.options: List[Dict] = []
        self.handler = None

    def add_string_option(self, name: str, description: str, required: bool = True):
        self.options.append({"type": 3, "name": name, "description": description, "required": required})
        return self

    def add_integer_option(self, name: str, description: str, required: bool = True):
        self.options.append({"type": 4, "name": name, "description": description, "required": required})
        return self

    def add_user_option(self, name: str, description: str, required: bool = True):
        self.options.append({"type": 6, "name": name, "description": description, "required": required})
        return self

    def add_channel_option(self, name: str, description: str, required: bool = True):
        self.options.append({"type": 7, "name": name, "description": description, "required": required})
        return self

    def add_role_option(self, name: str, description: str, required: bool = True):
        self.options.append({"type": 8, "name": name, "description": description, "required": required})
        return self

    def to_dict(self) -> Dict:
        return {"name": self.name, "description": self.description, "options": self.options, "type": 1}


class DiscordBot:
    """Discord bot with slash commands, buttons, modals, and embeds."""

    def __init__(self, token: str = "", application_id: str = ""):
        self.token = token
        self.application_id = application_id
        self.commands: Dict[str, SlashCommand] = {}
        self.button_handlers: Dict[str, callable] = {}
        self.modal_handlers: Dict[str, callable] = {}

    def command(self, cmd: SlashCommand):
        self.commands[cmd.name] = cmd
        return cmd

    def button_handler(self, custom_id: str):
        def decorator(func):
            self.button_handlers[custom_id] = func
            return func
        return decorator

    def modal_handler(self, custom_id: str):
        def decorator(func):
            self.modal_handlers[custom_id] = func
            return func
        return decorator

    def register_commands_payload(self) -> List[Dict]:
        """Generate JSON payload for registering slash commands."""
        return [cmd.to_dict() for cmd in self.commands.values()]

    def interaction_response_embed(self, embed: Embed, buttons: List[Button] = None) -> Dict:
        """Build interaction response with embed and optional buttons."""
        components = []
        if buttons:
            components.append({"type": 1, "components": [b.to_dict() for b in buttons]})
        return {
            "type": 4,
            "data": {
                "embeds": [embed.to_dict()],
                "components": components,
            },
        }

    def interaction_response_modal(self, modal: Modal) -> Dict:
        """Build interaction response with modal."""
        return {"type": 9, "data": modal.to_dict()}
