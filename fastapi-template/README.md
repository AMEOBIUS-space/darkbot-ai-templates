# FastAPI Backend Template

Minimal production-shaped REST API skeleton:

- JWT register/login
- SQLite + simple migrations pattern
- CRUD items with user isolation
- WebSocket endpoint
- Pydantic validation
- Auto OpenAPI at `/docs`

## Quick start

```bash
pip install -r requirements.txt
python main.py
# open http://localhost:8000/docs
```

Docker:

```bash
docker compose up --build
```

## Tests

```bash
python3 -m pytest tests/ -q
```

## Layout

- `main.py` — app + routes
- `demo.py` — smoke client
- `docker-compose.yml` / `Dockerfile`
- `tests/` — API tests

## License

MIT · AMEOBIUS-team

## Related

- https://github.com/AMEOBIUS-team/context-mode
- https://github.com/AMEOBIUS-team/agentops-lite
- https://github.com/AMEOBIUS-team/cdp-automation-template
- Portfolio: https://ameobius-team.github.io/kwork-portfolio/

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
