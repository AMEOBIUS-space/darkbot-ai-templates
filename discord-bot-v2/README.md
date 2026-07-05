# Discord Bot Template v2

> Slash commands, buttons, modals, and embeds — pure Python, no discord.py dependency

## Features

- Embed builder (fields, footer, thumbnail, timestamp)
- Button components (5 styles: Primary, Secondary, Success, Danger, Link)
- Modal dialogs with text inputs (short + paragraph)
- Slash command builder (string, integer, user, channel, role options)
- Interaction response builders (embed+buttons, modal)
- Handler registration (button, modal)

## Quick Start

```python
from bot import DiscordBot, SlashCommand, Embed, Button

bot = DiscordBot(token="YOUR_TOKEN")
cmd = SlashCommand("ping", "Ping pong")
cmd.add_string_option("msg", "Message")
bot.command(cmd)
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
