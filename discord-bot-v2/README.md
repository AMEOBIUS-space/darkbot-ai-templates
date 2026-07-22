# Discord Bot Template v2

Pure-Python Discord interaction builders — **no discord.py dependency**.

- Embed builder (fields, footer, thumbnail, timestamp)
- Button components (Primary / Secondary / Success / Danger / Link)
- Modal dialogs (short + paragraph inputs)
- Slash command builder (string, integer, user, channel, role options)
- Interaction response builders (embed+buttons, modal)
- Handler registration for buttons/modals

Useful as a lightweight payload layer when you talk to Discord REST/gateway yourself
or wrap a minimal client.

## Quick start

```python
from bot import DiscordBot, SlashCommand, Embed, Button

bot = DiscordBot(token="YOUR_TOKEN")
cmd = SlashCommand("ping", "Ping pong")
cmd.add_string_option("msg", "Message")
bot.command(cmd)
```

```bash
python demo.py
python -m pytest tests/ -q
```

## Layout

```
src/bot.py     # builders + DiscordBot shell
demo.py
tests/
```

## Hygiene

- Never commit tokens (`.env` / secret store)
- Pair with headless browser stacks only via Xvfb :99 / CloakBrowser headless — never DISPLAY=:0

## License

MIT · AMEOBIUS-team

## Related

- https://github.com/AMEOBIUS-team/discord-bot-template
- https://github.com/AMEOBIUS-team/fastapi-template
- Portfolio: https://ameobius-team.github.io/kwork-portfolio/

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
