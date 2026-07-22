# Tor Hidden Service Template

Generate v3 `.onion` configs + hardened nginx + optional Docker layout.

- ed25519 v3 onion address generation
- torrc snippet
- privacy-hardened nginx (no logs, no tokens)
- server hardening shell script
- docker-compose skeleton
- optional PHP location block

## Quick start

```bash
pip install -r requirements.txt
python setup.py
# or
python demo.py
```

Hardening script (print only — review before running on a host):

```bash
python -c "from setup import TorHiddenService; print(TorHiddenService().generate_hardening_script())"
```

## Tests

```bash
python3 -m pytest tests/ -q
```

## Layout

- `setup.py` — `TorHiddenService` generators
- `demo.py` — offline smoke demo (no network)
- `Dockerfile` / `Makefile`
- `tests/` — compile + demo smoke

## License

MIT · AMEOBIUS-team

## Related

- https://github.com/AMEOBIUS-team/security-audit-toolkit
- https://github.com/AMEOBIUS-team/fastapi-template
- https://github.com/AMEOBIUS-team/cdp-automation-template
- Portfolio: https://ameobius-team.github.io/kwork-portfolio/

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
