# Discord Bot Template

Minimal Discord.py bot skeleton with slash commands and common utilities:

- Slash command sync
- Welcome / user-info embeds
- Moderation helpers (purge)
- Poll reactions
- Permission checks
- Optional music queue scaffolding

## Quick start

```bash
pip install -r requirements.txt
export DISCORD_TOKEN=your_token
python bot.py
```

Docker:

```bash
docker compose up --build
```

## Tests

```bash
python3 -m pytest tests/ -q
```

## Hygiene

- Never commit real tokens (use `.env` / secrets manager)
- Prefer headless/Xvfb isolation when driving browsers alongside bots

## License

MIT · AMEOBIUS-team

## Related

- https://github.com/AMEOBIUS-team/fastapi-template
- https://github.com/AMEOBIUS-team/cdp-automation-template
- https://github.com/AMEOBIUS-team/context-mode
- Portfolio: https://ameobius-team.github.io/kwork-portfolio/

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
