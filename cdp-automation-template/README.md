# CDP Browser Automation Template

Production-oriented Chrome DevTools Protocol helpers for agent/browser automation:

- CDP mouse events (real pointer events for Vue/React)
- Native value setter (bypasses framework-controlled inputs)
- `Input.insertText` for React typeaheads
- Tab management via `Target.createTarget` patterns
- Patterns useful against CF / stubborn SPA form controls

Default port: **9222** (override for CloakBrowser 9223/9224).

## Quick start

```bash
pip install -r requirements.txt
# Chrome / Chromium / CloakBrowser with --remote-debugging-port=9222
python cdp_agent.py
python demo.py
```

## API sketch

```python
from cdp_agent import CDPAgent

agent = CDPAgent(port=9224)
await agent.connect()
await agent.navigate("https://example.com")
await agent.fill_input("#email", "user@example.com")
await agent.click_element("button[type=submit]")
```

## Tests

```bash
python3 -m pytest tests/ -q
```

## Hygiene

- Prefer **headless** or **Xvfb :99** — never drive `DISPLAY=:0` on the main monitor
- Do not close the last browser tab in Restart=always fleets

## License

MIT · AMEOBIUS-team

## Related

- https://github.com/AMEOBIUS-team/context-mode
- https://github.com/AMEOBIUS-team/agentops-lite
- Portfolio: https://ameobius-team.github.io/kwork-portfolio/

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
